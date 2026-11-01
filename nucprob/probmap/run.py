"""P(area struck | stockpile scenario): configs/scenarios.yaml through the protocol's fourth amendment.

    python -m nucprob.probmap.run [--quick]

Steps: choose the score by transfer (leave one plan out); draw models and stockpiles together; allocate
each scenario's delivered warheads by score share (nucprob.probmap.allocate); summarise each grid cell.
Then the validation against SAC 1956 and the domain shift of the modern towns.

Writes runs/probmap/: model_choice.csv, cells/<scenario>.csv.gz (one row per cell, sorted by position,
no names), scenarios.csv, delivered.csv, by_delivery.csv, validation.csv, reliability.csv, domain_shift.csv, manifest.json.
--quick uses 10 draws and writes to runs/probmap-quick/.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import argparse
import datetime as dt
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
import yaml
from joblib import Parallel, delayed
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import cross_val_predict

from nucprob.classifier import evaluate as ev
from nucprob.classifier.fit import N_BAGS, Spec, bag_rows, fit_bagged, lightgbm_quiet, logistic_all
from nucprob.classifier.run import SAC, positives_of, scopes, usable
from nucprob.classifier.table import transfer_towns
from nucprob.model.cv import git_commit
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.plans import protocol
from nucprob.probmap import allocate as al
from nucprob.probmap import modern
from nucprob.probmap.modern import PORTABLE
from nucprob.probmap.stockpile import MIX, TABLE, by_delivery_draws, delivered_draws
from nucprob.sources.fetch import sha256

SCENARIOS = ROOT / "configs" / "scenarios.yaml"
GLOBAL = "global, all attacker documents"
N_DRAWS = 200
SEED = 1956
QUANTILES = [5, 50, 95]


def candidates() -> list[Spec]:
    return [
        Spec("population rule", logistic_all, ["log_pop"]),
        Spec("portable logistic", logistic_all, PORTABLE),
        Spec("portable LightGBM", lightgbm_quiet, PORTABLE),
    ]


def load_scenarios(path=SCENARIOS) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["scenarios"]


def choose_model(train: pd.DataFrame, bags: int) -> tuple[Spec, pd.DataFrame]:
    """The rule of the protocol: highest weighted PR-AUC on a left-out plan, towns removed. Spatial
    blocks are read beside it and choose nothing."""
    models = candidates()
    _, held = ev.leave_one_plan_out(train, models, bags)
    spatial = ev.spatial_scores(train, models, bags)
    y, doc = train["listed"].to_numpy(int), train["plan_id"].to_numpy()
    rest = held["plan_id"] != SAC
    rows = [
        {
            "model": m.name,
            "lopo_pr_auc": ev.weighted_pr_auc(
                held["listed"].to_numpy(int), held[m.name].to_numpy(), held["plan_id"].to_numpy()
            ),
            "lopo_pr_auc_without_sac": ev.weighted_pr_auc(
                held.loc[rest, "listed"].to_numpy(int),
                held.loc[rest, m.name].to_numpy(),
                held.loc[rest, "plan_id"].to_numpy(),
            ),
            "spatial_pr_auc": ev.weighted_pr_auc(y, spatial[m.name], doc),
        }
        for m in models
    ]
    table = pd.DataFrame(rows)
    best = table.loc[table["lopo_pr_auc"].idxmax(), "model"]
    table["selected"] = table["model"] == best
    return next(m for m in models if m.name == best), table


def fit_draw(spec: Spec, train: pd.DataFrame, seed: int):
    """One model draw: whole blocks resampled with replacement, then one positive-unlabeled bag."""
    rng = np.random.default_rng(seed)
    blocks = train["block"].to_numpy()
    members = {k: np.flatnonzero(blocks == k) for k in np.unique(blocks)}
    keys = list(members)
    picks = rng.integers(len(keys), size=len(keys))
    rows = np.concatenate([members[keys[i]] for i in picks])
    t = train.iloc[rows].reset_index(drop=True)
    y, complete = t["listed"].to_numpy(int), t["complete"].to_numpy(bool)
    bag = bag_rows(y, t["plan_id"].to_numpy(), complete, t["place_id"].to_numpy(), rng)
    return spec.factory(seed=seed).fit(t.iloc[bag][spec.columns], y[bag])


@dataclass
class Universe:
    towns: pd.DataFrame  # lat, lon, country, pop, sealed, and PORTABLE
    unsealed_population_share: float


def bloc_universe(full: pd.DataFrame) -> Universe:
    sac = full[full["plan_id"] == SAC]
    share = sac.loc[~sac["sealed"].astype(bool), "pop"].sum() / sac["pop"].sum()
    return Universe(sac.reset_index(drop=True), float(share))


def west_universe() -> Universe:
    t = transfer_towns()
    t = t[(t["region"] == "wp_west_1965") & t["lat"].notna()].reset_index(drop=True)
    return Universe(t.assign(sealed=False), 1.0)


def modern_universe() -> Universe:
    t = modern.read_towns()
    t = pd.concat([t, modern.features(t)], axis=1)
    return Universe(t.assign(sealed=False), 1.0)


def scenario_probabilities(
    towns: pd.DataFrame,
    scores: np.ndarray,
    attackers: list[dict],
    warheads: dict[str, np.ndarray],
    cell_deg: float,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Cells and P(struck) by cell and draw. Each attacker allocates over its own target countries;
    an area is unstruck only if every attacker's warheads miss it."""
    cell = al.cell_ids(towns["lat"], towns["lon"], cell_deg)
    codes, names = pd.factorize(cell)
    n_cells = len(names)
    keep = np.ones((n_cells, scores.shape[1]))
    for a in attackers:
        mask = towns["country"].isin(a["targets"]).to_numpy()
        if not mask.any():
            raise ValueError(f"no towns for {a['state']} in {a['targets']}")
        shares = al.score_shares(scores[mask])
        area = al.area_shares(shares, codes[mask], n_cells)
        keep *= al.survival(area, warheads[a["state"]])
    return pd.DataFrame({"cell": names}), 1.0 - keep


def summarise(cells: pd.DataFrame, draws: np.ndarray, fixed_stock, fixed_model) -> pd.DataFrame:
    low, mid, high = np.percentile(draws, QUANTILES, axis=1)
    m_low, _, m_high = np.percentile(fixed_stock, QUANTILES, axis=1)
    s_low, _, s_high = np.percentile(fixed_model, QUANTILES, axis=1)
    parts = cells["cell"].str.split("_", expand=True).astype(float)
    out = pd.DataFrame(
        {
            "cell_lat": parts[0],
            "cell_lon": parts[1],
            "p_median": mid,
            "p_low": low,
            "p_high": high,
            "p_low_model_only": m_low,
            "p_high_model_only": m_high,
            "p_low_stockpile_only": s_low,
            "p_high_stockpile_only": s_high,
        }
    )
    return out.sort_values(["cell_lat", "cell_lon"]).reset_index(drop=True)


def run_scenario(
    sc: dict, universe: Universe, score_matrix: np.ndarray, draws: int, rng
) -> tuple[pd.DataFrame, dict]:
    # Only the scenario's target countries are on its map.
    named = {c for a in sc["attackers"] for c in a["targets"]}
    in_scope = universe.towns["country"].isin(named).to_numpy()
    towns = universe.towns[in_scope].reset_index(drop=True)
    score_matrix = score_matrix[in_scope]
    active = ~towns["sealed"].astype(bool).to_numpy()
    all_draws, median_w = {}, {}
    records, by_delivery = [], []
    for a in sc["attackers"]:
        parts = by_delivery_draws(a, draws, rng)
        w = sum(p["delivered"] for p in parts.values()) * universe.unsealed_population_share
        all_draws[a["state"]] = w
        for delivery, p in parts.items():
            have = np.percentile(p["available"], QUANTILES)
            sent = np.percentile(p["delivered"] * universe.unsealed_population_share, QUANTILES)
            by_delivery.append(
                {
                    "scenario": sc["id"],
                    "attacker": a["state"],
                    "stock_year": a["stock_year"],
                    "delivery": delivery,
                    "available_low": have[0],
                    "available_median": have[1],
                    "available_high": have[2],
                    "delivered_low": sent[0],
                    "delivered_median": sent[1],
                    "delivered_high": sent[2],
                }
            )
        median_w[a["state"]] = np.full(draws, np.median(w))
        q = np.percentile(w, QUANTILES)
        records.append(
            {
                "scenario": sc["id"],
                "attacker": a["state"],
                "delivered_low": q[0],
                "delivered_median": q[1],
                "delivered_high": q[2],
            }
        )
    t = towns[active].reset_index(drop=True)
    s = score_matrix[active]
    cells, p = scenario_probabilities(t, s, sc["attackers"], all_draws, sc["cell_deg"])
    _, p_model = scenario_probabilities(t, s, sc["attackers"], median_w, sc["cell_deg"])
    centre = np.tile(np.median(s, axis=1, keepdims=True), (1, s.shape[1]))
    _, p_stock = scenario_probabilities(t, centre, sc["attackers"], all_draws, sc["cell_deg"])
    out = summarise(cells, p, p_model, p_stock)
    if (~active).any():
        hidden = al.cell_ids(towns.loc[~active, "lat"], towns.loc[~active, "lon"], sc["cell_deg"])
        parts = hidden.str.split("_", expand=True).astype(float)
        out["holds_sealed_town"] = (
            pd.MultiIndex.from_frame(out[["cell_lat", "cell_lon"]])
            .isin(pd.MultiIndex.from_frame(parts))
            .astype(int)
        )
    else:
        out["holds_sealed_town"] = 0
    counts = (p > 0.5).sum(axis=0)
    width = float((out["p_high"] - out["p_low"]).mean())
    summary = {
        "scenario": sc["id"],
        "era": sc["era"],
        "evidence": sc["evidence"],
        "cell_deg": sc["cell_deg"],
        "towns": len(t),
        "cells": len(out),
        "cells_over_half_low": float(np.percentile(counts, 5)),
        "cells_over_half_median": float(np.median(counts)),
        "cells_over_half_high": float(np.percentile(counts, 95)),
        "mean_p": float(p.mean()),
        "mean_interval_width": width,
        "mean_width_model_only": float((out["p_high_model_only"] - out["p_low_model_only"]).mean()),
        "mean_width_stockpile_only": float(
            (out["p_high_stockpile_only"] - out["p_low_stockpile_only"]).mean()
        ),
    }
    return out, {"summary": summary, "warheads": records, "by_delivery": by_delivery}


def validation(
    spec: Spec, train: pd.DataFrame, full: pd.DataFrame, sc: dict, bags: int, rng
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The 1956 scenario against SAC's own list. Cell probabilities from models that never saw the
    cell's block, and from models with no SAC row at all. Cells are read at the stockpile's median."""
    sac = train[train["plan_id"] == SAC].reset_index(drop=True)
    y = sac["listed"].to_numpy(int)
    blocks = pd.Series(sac["block"].to_numpy())
    fold = folds(blocks, pd.Series(y), ev.N_FOLDS, seed=0)
    spatial = np.zeros(len(sac))
    others = train[train["plan_id"] != SAC]
    for f in range(ev.N_FOLDS):
        test = np.asarray(fold == f)
        held = set(sac.loc[test, "place_id"])
        rest = train[~train["place_id"].isin(held)].reset_index(drop=True)
        spatial[test] = fit_bagged(spec, rest, bags).score(sac[test])
    # Towns of other lists stay out of the left-out fit too, as in leave one plan out.
    left_out = fit_bagged(
        spec, others[~others["place_id"].isin(set(sac["place_id"]))].reset_index(drop=True), bags
    ).score(sac)
    attacker = sc["attackers"][0]
    w = float(np.median(delivered_draws(attacker, 2000, rng)))
    w *= bloc_universe(full).unsealed_population_share
    rows, bins = [], []
    cell = al.cell_ids(sac["lat"], sac["lon"], sc["cell_deg"])
    codes, names = pd.factorize(cell)
    observed = pd.Series(y).groupby(codes).max().to_numpy()
    for label, score in (("spatial blocks held out", spatial), ("SAC list left out", left_out)):
        area = al.area_shares(al.score_shares(score[:, None]), codes, len(names))
        p = 1.0 - al.survival(area, np.array([w]))[:, 0]
        rows.append(
            {
                "reading": label,
                "cells": len(names),
                "cells_listed": int(observed.sum()),
                "base_rate": float(observed.mean()),
                "median_delivered_warheads": w,
                "pr_auc": float(average_precision_score(observed, p)),
                "roc_auc": float(roc_auc_score(observed, p)),
                "brier": float(np.mean((p - observed) ** 2)),
                "brier_of_base_rate": float(np.mean((observed.mean() - observed) ** 2)),
                "mean_p": float(p.mean()),
            }
        )
        curve = ev.calibration_curve(observed, p, bins=5)
        bins.append(curve.assign(reading=label))
    return pd.DataFrame(rows), pd.concat(bins, ignore_index=True)


def shift_auc(a: pd.DataFrame, b: pd.DataFrame, seed: int = 0) -> float:
    """Cross-validated ROC-AUC of telling two sets of towns apart on the portable features. 0.5 means
    the features cannot tell them apart; 1.0 means no town of one set resembles the other."""
    x = pd.concat([a[PORTABLE], b[PORTABLE]], ignore_index=True)
    y = np.r_[np.zeros(len(a)), np.ones(len(b))]
    p = cross_val_predict(lightgbm_quiet(seed), x, y, cv=5, method="predict_proba")[:, 1]
    return float(roc_auc_score(y, p))


def domain_shift(
    train: pd.DataFrame, modern_towns: pd.DataFrame, countries: set[str]
) -> pd.DataFrame:
    hist = train.drop_duplicates("place_id")
    mod = modern_towns[modern_towns["country"].isin(countries)]
    sac = hist[hist["plan_id"] == SAC]
    west = hist[hist["plan_id"] != SAC]
    rows = [
        {
            "comparison": "training towns against modern towns",
            "measure": "two-sample ROC-AUC",
            "value": shift_auc(hist, mod),
            "towns_a": len(hist),
            "towns_b": len(mod),
        },
        {
            "comparison": "for scale: SAC 1956 towns against the other training towns",
            "measure": "two-sample ROC-AUC",
            "value": shift_auc(sac, west),
            "towns_a": len(sac),
            "towns_b": len(west),
        },
    ]
    for c in PORTABLE:
        low, high = np.nanpercentile(hist[c].astype(float), [1, 99])
        v = mod[c].astype(float)
        rows.append(
            {
                "comparison": f"modern towns outside the 1st-99th percentile of training: {c}",
                "measure": "share of modern towns",
                "value": float(((v < low) | (v > high)).mean()),
                "towns_a": len(hist),
                "towns_b": len(mod),
            }
        )
    return pd.DataFrame(rows)


def score_matrix(models: list, towns: pd.DataFrame, columns: list[str]) -> np.ndarray:
    """Towns by draws. A sealed town is never passed to a model: its row stays NaN."""
    out = np.full((len(towns), len(models)), np.nan, dtype="float32")
    active = ~towns["sealed"].astype(bool).to_numpy()
    for j, m in enumerate(models):
        out[active, j] = m.predict_proba(towns.loc[active, columns])[:, 1]
    return out


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--quick", action="store_true")
    quick = args.parse_args().quick
    n_draws, bags = (10, 3) if quick else (N_DRAWS, N_BAGS)
    out_dir = RUNS / ("probmap-quick" if quick else "probmap")
    (out_dir / "cells").mkdir(parents=True, exist_ok=True)
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = usable(full)
    groups, _ = scopes(table, positives_of(full))
    train = groups[GLOBAL].copy()
    train["block"] = assign_blocks(train["lat"].to_numpy(), train["lon"].to_numpy(), BLOCK_KM)
    spec, choice = choose_model(train, bags)
    choice.to_csv(out_dir / "model_choice.csv", index=False, float_format="%.4f")
    print(choice.to_string(index=False), flush=True)
    models = Parallel(n_jobs=3, prefer="threads")(
        delayed(fit_draw)(spec, train, SEED + i) for i in range(n_draws)
    )
    universes = {
        "bloc_1956": bloc_universe(full),
        "wp_west_1965": west_universe(),
        "modern": modern_universe(),
    }
    matrices = {k: score_matrix(models, u.towns, spec.columns) for k, u in universes.items()}
    rng = np.random.default_rng(SEED)
    summaries, warheads, by_delivery = [], [], []
    for sc in load_scenarios():
        cells, rec = run_scenario(
            sc, universes[sc["universe"]], matrices[sc["universe"]], n_draws, rng
        )
        cells.to_csv(out_dir / "cells" / f"{sc['id']}.csv.gz", index=False, float_format="%.4f")
        summaries.append(rec["summary"])
        warheads += rec["warheads"]
        by_delivery += rec["by_delivery"]
        print(sc["id"], rec["summary"], flush=True)
    pd.DataFrame(summaries).to_csv(out_dir / "scenarios.csv", index=False, float_format="%.4f")
    pd.DataFrame(warheads).to_csv(out_dir / "delivered.csv", index=False, float_format="%.0f")
    pd.DataFrame(by_delivery).to_csv(out_dir / "by_delivery.csv", index=False, float_format="%.0f")
    first = next(s for s in load_scenarios() if s["id"] == protocol_validation_scenario())
    val, rel = validation(spec, train, full, first, bags, rng)
    val.to_csv(out_dir / "validation.csv", index=False, float_format="%.4f")
    rel.to_csv(out_dir / "reliability.csv", index=False, float_format="%.4f")
    countries = {
        c
        for s in load_scenarios()
        if s["era"] == "modern"
        for a in s["attackers"]
        for c in a["targets"]
    }
    domain_shift(train, universes["modern"].towns, countries).to_csv(
        out_dir / "domain_shift.csv", index=False, float_format="%.4f"
    )
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "configs" / "protocol.yaml"),
        "scenarios_sha256": sha256(SCENARIOS),
        "stockpiles_sha256": sha256(TABLE),
        "delivery_mix_sha256": sha256(MIX),
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "draws": n_draws,
        "score": spec.name,
        "features": spec.columns,
        "quick": quick,
        "model_rule": protocol()["amendments"][-1]["changes"]["probability_map"]["score"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def protocol_validation_scenario() -> str:
    return "us_1956_on_bloc"


if __name__ == "__main__":
    main()
