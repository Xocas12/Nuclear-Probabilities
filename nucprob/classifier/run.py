"""The pre-committed analysis of configs/protocol.yaml, except the sealed set.

    python -m nucprob.classifier.run [--quick]

Reads data/processed/classifier_table.parquet. For each scope: spatial blocks, leave one document out,
temporal holdouts, the candidates against both baselines with a paired bootstrap. Then the US 1956
complexes alone: calibration, and the gain of each feature family. Then the defence reading.

--quick uses 3 bags and 50 bootstrap resamples, writes to runs/classifier-quick/, and is for
checking the code; the protocol's numbers come from the full run.

Writes runs/classifier/: lists.csv (every list, model and holdout), comparison.csv (paired
bootstrap), selection.csv, scopes.csv (what each scope holds, or why it was refused),
calibration.csv, family_gain.csv, defence.csv, held_out_scores.csv.gz and manifest.json, which holds
the hashes of every input (tests/test_classifier_report.py compares them).
"""

import os

# The machine rule is at most 3 cores: BLAS must not add threads of its own to the 3 bags.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from nucprob.classifier import evaluate as ev
from nucprob.classifier.features import DEFENCE, NO_S25
from nucprob.classifier.fit import ALL_FEATURES, FAMILIES, N_BAGS, Spec, fit_bagged, specs
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import lightgbm
from nucprob.outputs import hashes, start_record
from nucprob.paths import CURATED, PROCESSED, ROOT, RUNS
from nucprob.plans import exercise_gate, gate, plans, protocol
from nucprob.sources.fetch import sha256

SAC = "us_1956_sac_complexes"
BASELINES = ("population rule", "population + country")
CANDIDATES = ("logistic, all permitted", "LightGBM, all permitted")
EXERCISE_TYPES = {"exercise", "wargame", "training", "disputed_plan_or_exercise"}
SAC_ONLY = "single document: SAC 1956 (not a state model)"
LOPO = "leave one document out"
LOPO_KEPT = "leave one document out, towns kept in training"


def usable(table: pd.DataFrame) -> pd.DataFrame:
    """What models may read: never a sealed place, never an unlinked document."""
    return table[~table["sealed"].astype(bool)].reset_index(drop=True)


def positives_of(table: pd.DataFrame) -> dict[str, int]:
    return table.groupby("plan_id")["listed"].sum().astype(int).to_dict()


def scopes(
    table: pd.DataFrame, positives: dict[str, int]
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Scope name -> rows, and the gate's decisions. Only documents with role train fit a model.
    `positives` counts every linked positive, sealed places too, as runs/evidence does; models
    read only the rows of `table`."""
    reg = plans()
    rule = protocol()["state_models"]
    decisions = gate(positives, reg, rule)
    pooled = exercise_gate(positives, reg, rule["warsaw_pact_exercise_model"])
    decisions = pd.concat([decisions, pd.DataFrame([pooled])], ignore_index=True)
    train = table[table["role"] == "train"]
    plan_docs = train["doc_type"].isin(rule["plan_doc_types"]) & train["grade"].isin(rule["grades"])
    out = {
        "global, all attacker documents": train,
        "global, plan documents only": train[plan_docs],
    }
    for _, d in decisions.iterrows():
        if not d["allowed"]:
            continue
        if d["attacker"].startswith("Warsaw Pact, pooled"):
            out[d["attacker"]] = train[train["plan_id"].str.startswith("wp_")]
        else:
            out[f"state: {d['attacker']}"] = train[plan_docs & (train["attacker"] == d["attacker"])]
    # The one large list, read alone and named for what it is. It cannot speak to other documents.
    out[SAC_ONLY] = train[train["plan_id"] == SAC]
    return {k: v.reset_index(drop=True) for k, v in out.items()}, decisions


def describe(name: str, rows: pd.DataFrame) -> dict:
    types = rows.groupby("doc_type")["plan_id"].nunique().to_dict()
    return {
        "scope": name,
        "rows": len(rows),
        "places": rows["place_id"].nunique(),
        "lists": rows["plan_id"].nunique(),
        "groups": rows["group"].nunique(),
        "positives": int(rows["listed"].sum()),
        "positives_outside_sac": int(rows.loc[rows["plan_id"] != SAC, "listed"].sum()),
        "exercise_based": bool(set(types) & EXERCISE_TYPES),
        "doc_types": json.dumps(types, sort_keys=True),
    }


def one_comparison(part: pd.DataFrame, a: str, b: str, boot: int) -> dict:
    y, doc = part["listed"].to_numpy(int), part["plan_id"].to_numpy()
    s, t = part[a].to_numpy(), part[b].to_numpy()
    # A list with a constant score on one model has no ranking to compare.
    scored = [d for d in np.unique(doc) if ev.MIN_POSITIVES <= y[doc == d].sum() < (doc == d).sum()]
    constant = any(np.unique(s[doc == d]).size == 1 for d in scored)
    return (
        {
            "model": a,
            "against": b,
            "positives": int(y.sum()),
            "base_rate": _base_rate(y, doc),
            "train_positives_min": int(part["train_positives"].min()),
            "constant_score": constant,
            "a_pr_auc": ev.weighted_pr_auc(y, s, doc),
            "b_pr_auc": ev.weighted_pr_auc(y, t, doc),
        }
        | ev.paired_bootstrap(y, s, t, doc, n=boot)
        | ev.block_bootstrap(y, s, t, doc, part["block"].to_numpy(), n=boot)
    )


def _base_rate(y: np.ndarray, doc: np.ndarray) -> float:
    """What a model with no information scores: the positive-weighted mean of each list's rate."""
    total, weight = 0.0, 0
    for d in np.unique(doc):
        n, size = int(y[doc == d].sum()), int((doc == d).sum())
        if ev.MIN_POSITIVES <= n < size:
            total, weight = total + n * n / size, weight + n
    return total / weight if weight else float("nan")


def compare(frame: pd.DataFrame, boot: int, scope: str, holdout: str) -> list[dict]:
    """Each candidate against each baseline on the same rows: all lists, and without the SAC
    list, which otherwise carries about nine tenths of the weight."""
    parts = {"all lists": frame, "lists other than SAC": frame[frame["plan_id"] != SAC]}
    parts = {k: p for k, p in parts.items() if len(p)}
    tasks = [(k, p, a, b) for k, p in parts.items() for a in CANDIDATES for b in BASELINES]
    results = Parallel(n_jobs=3)(delayed(one_comparison)(p, a, b, boot) for _, p, a, b in tasks)
    return [
        {"scope": scope, "holdout": holdout, "lists": k} | r
        for (k, *_), r in zip(tasks, results, strict=True)
    ]


def analyse_scope(name: str, rows: pd.DataFrame, models: list[Spec], bags: int, boot: int):
    print(f"--- {name}: {len(rows)} rows", flush=True)
    lists, comparison = [], []
    spatial = ev.spatial_scores(rows, models, bags)
    lists += [r | {"scope": name} for r in ev.by_list(rows, spatial, "spatial blocks")]
    frame = rows[["plan_id", "place_id", "listed", "block"]].assign(
        train_positives=int(rows["listed"].sum() * (ev.N_FOLDS - 1) / ev.N_FOLDS), **spatial
    )
    comparison += compare(frame, boot, name, "spatial blocks")
    held_scores = {"spatial blocks": frame}
    y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
    weighted = {m: ev.weighted_pr_auc(y, s, doc) for m, s in spatial.items()}
    best = max(CANDIDATES, key=weighted.__getitem__)
    selection = [
        {"scope": name, "model": m, "weighted_pr_auc": v, "selected": m == best}
        for m, v in weighted.items()
    ]
    print(" spatial done", flush=True)
    for holdout, keep_places in ((LOPO, False), (LOPO_KEPT, True)):
        a, held = ev.leave_one_document_out(rows, models, bags, keep_places)
        lists += [r | {"scope": name} for r in a]
        if len(held):
            comparison += compare(held, boot, name, holdout)
            held_scores[holdout] = held
    print(" leave-one-document-out done", flush=True)
    a, kept = ev.temporal(rows, models, bags)
    lists += [r | {"scope": name} for r in a]
    for holdout, frame in kept.items():
        comparison += compare(frame, boot, name, holdout)
        held_scores[holdout] = frame
    print(" temporal done", flush=True)
    frames = [f.assign(scope=name, holdout=h) for h, f in held_scores.items()]
    return lists, comparison, selection, frames


def expectations(
    table: pd.DataFrame, rows: pd.DataFrame, models: list[Spec], bags: int, scope: str
):
    """Mirrors and civil-defence lists: never training data, scored as a different kind of
    evidence by the model of a whole scope. A bloc place in the sealed set is not among them."""
    test = table[table["role"] == "test-expectation"].reset_index(drop=True)
    scores = {m.name: fit_bagged(m, rows, bags).score(test) for m in models}
    return [r | {"scope": scope} for r in ev.by_list(test, scores, "expectation lists, not plans")]


def with_country(rows: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    dummies = pd.get_dummies(rows["country"], prefix="country", dtype=float)
    return pd.concat([rows, dummies], axis=1), list(dummies.columns)


def calibration(rows: pd.DataFrame, models: list[Spec], bags: int) -> pd.DataFrame:
    """The US 1956 complexes, the only large complete list."""
    sac = rows[rows["plan_id"] == SAC].reset_index(drop=True)
    scores = ev.spatial_scores(sac, models, bags)
    blocks = pd.Series(assign_blocks(sac["lat"], sac["lon"], BLOCK_KM), index=sac.index)
    fold = folds(blocks, sac["listed"], ev.N_FOLDS, seed=0)
    out = []
    y = sac["listed"].to_numpy(int)
    for name, s in scores.items():
        for kind, p in (("raw", s), ("isotonic", ev.cross_fit_isotonic(y, s, fold))):
            curve = ev.calibration_curve(y, p)
            brier = float(np.mean((p - y) ** 2))
            ece = float(
                (curve["n"] / len(y) * (curve["mean_score"] - curve["observed"]).abs()).sum()
            )
            curve = curve.assign(model=name, kind=kind, brier=brier, expected_calibration_error=ece)
            out.append(curve)
    return pd.concat(out, ignore_index=True)


def three_threads(seed: int = 0):
    return lightgbm(seed).set_params(n_jobs=3)


def family_gain(rows: pd.DataFrame, boot: int) -> pd.DataFrame:
    """Each family over population and country, LightGBM, spatial blocks, US 1956 complexes.
    Repeated for the USSR alone, the only country whose defences the 1956 tables cover in depth."""
    out = []
    sac = rows[rows["plan_id"] == SAC].reset_index(drop=True)
    for label, part in (("all countries", sac), ("USSR", sac[sac["country"] == "USSR"])):
        part, country = with_country(part.reset_index(drop=True))
        base_cols = [*FAMILIES["population"], *country]
        models = [
            Spec("base", three_threads, base_cols),
            Spec("population only", three_threads, FAMILIES["population"]),
            Spec(
                "national_power over population",
                three_threads,
                [*FAMILIES["population"], *FAMILIES["national_power"]],
            ),
        ]
        for fam, cols in FAMILIES.items():
            if fam == "population":
                continue
            models.append(Spec(fam, three_threads, [*base_cols, *cols]))
        scores = ev.spatial_scores(part, models, 1)
        y, doc = part["listed"].to_numpy(int), part["plan_id"].to_numpy()
        block = part["block"].to_numpy()
        for fam in scores:
            if fam in ("base", "population only"):
                continue
            # National power is one value per country in one list, so over a country term it can
            # add nothing; it is also read over population alone.
            base = "population only" if fam == "national_power over population" else "base"
            r = ev.paired_bootstrap(y, scores[fam], scores[base], doc, n=boot)
            r |= ev.block_bootstrap(y, scores[fam], scores[base], doc, block, n=boot)
            # The protocol's rule for every comparison: both intervals must exclude zero.
            if r["low"] > 0 and r["block_low"] > 0:
                r["verdict"] = "gain"
            elif r["high"] < 0 and r["block_high"] < 0:
                r["verdict"] = "loss"
            else:
                r["verdict"] = "neither"
            out.append(
                {
                    "rows": label,
                    "family": fam,
                    "base": base,
                    "base_pr_auc": ev.weighted_pr_auc(y, scores[base], doc),
                    "with_family_pr_auc": ev.weighted_pr_auc(y, scores[fam], doc),
                }
                | r
            )
    return pd.DataFrame(out)


def odds_per_tenfold(part: pd.DataFrame, column: str, boot: int) -> dict:
    """Odds ratio of being listed per tenfold increase in `column`, controlling log population
    and an intercept per list and country. Bootstrap by place. A descriptive association."""
    d = part[[column, "log_pop", "listed", "plan_id", "country", "place_id"]].dropna()
    fixed = pd.get_dummies(d[["plan_id", "country"]], dtype=float)
    x = pd.concat([d[["log_pop", column]], fixed], axis=1).to_numpy(float)
    y = d["listed"].to_numpy(int)
    scale = StandardScaler(with_std=False).fit(x)

    def coef(idx: np.ndarray) -> float:
        m = LogisticRegression(C=100.0, max_iter=2000)
        m.fit(scale.transform(x[idx]), y[idx])
        return float(m.coef_[0][1])

    rng = np.random.default_rng(ev.BOOT_SEED)
    places = d["place_id"].to_numpy()
    groups = {p: np.flatnonzero(places == p) for p in np.unique(places)}
    keys = list(groups)
    draws = []
    for _ in range(boot):
        pick = rng.integers(len(keys), size=len(keys))
        draws.append(coef(np.concatenate([groups[keys[i]] for i in pick])))
    low, high = np.percentile(draws, [2.5, 97.5])
    point = coef(np.arange(len(d)))
    return {
        "rows": len(d),
        "positives": int(y.sum()),
        "odds_ratio_per_tenfold": float(np.exp(point)),
        "low": float(np.exp(low)),
        "high": float(np.exp(high)),
        "excludes_one": bool(low > 0 or high < 0),
    }


def defence_reading(rows: pd.DataFrame, boot: int) -> pd.DataFrame:
    """What the lists imply about defended places, by region: association only."""
    parts = {
        "US 1956 complexes, USSR towns": rows[
            (rows["plan_id"] == SAC) & (rows["country"] == "USSR")
        ],
        "Warsaw Pact documents, NATO Europe (attacker lists; exercises included)": rows[
            rows["plan_id"].str.startswith("wp_")
        ],
    }
    out = []
    for label, part in parts.items():
        for column in [*DEFENCE, NO_S25]:
            if column not in part or part[column].notna().sum() < 50:
                continue
            if part[column].notna().sum() < 50 or part[column].nunique() < 3:
                out.append({"rows_described": label, "feature": column, "note": "too few values"})
                continue
            out.append(
                {"rows_described": label, "feature": column} | odds_per_tenfold(part, column, boot)
            )
    return pd.DataFrame(out)


def input_hashes() -> dict[str, str]:
    """Committed files whose change would change the run's labels or what it was allowed to do."""
    files = [ROOT / "data" / "sources.yaml", *sorted((CURATED / "labels").glob("*"))]
    files = [f for f in files if f.is_file()]
    return {str(f.relative_to(ROOT)): sha256(f) for f in files}


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--quick", action="store_true")
    quick = args.parse_args().quick
    bags, boot = (3, 50) if quick else (N_BAGS, ev.N_BOOT)
    started = start_record()
    out_dir = RUNS / ("classifier-quick" if quick else "classifier")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = PROCESSED / "classifier_table.parquet"
    full = pd.read_parquet(path)
    table = usable(full)
    groups, decisions = scopes(table, positives_of(full))
    models = specs()
    lists, comparison, selection, described, kept = [], [], [], [], []
    for name, rows in groups.items():
        described.append(describe(name, rows))
        a, b, c, frames = analyse_scope(name, rows, models, bags, boot)
        lists += a
        comparison += b
        selection += c
        lists += expectations(table, rows, models, bags, name)
        # The scores behind every comparison: tests/test_classifier_report.py recomputes it.
        kept += frames
        pd.DataFrame(lists).to_csv(out_dir / "lists.csv", index=False, float_format="%.4f")
        pd.DataFrame(comparison).to_csv(
            out_dir / "comparison.csv", index=False, float_format="%.4f"
        )
    us = groups[SAC_ONLY]
    pd.DataFrame(selection).to_csv(out_dir / "selection.csv", index=False, float_format="%.4f")
    pd.DataFrame(described).to_csv(out_dir / "scopes.csv", index=False)
    decisions.to_csv(out_dir / "state_gate.csv", index=False)
    pd.concat(kept, ignore_index=True).to_csv(
        out_dir / "held_out_scores.csv.gz", index=False, float_format="%.6f"
    )
    print("--- calibration", flush=True)
    calibration(us, models, bags).to_csv(
        out_dir / "calibration.csv", index=False, float_format="%.4f"
    )
    print("--- family gain", flush=True)
    family_gain(us, boot).to_csv(out_dir / "family_gain.csv", index=False, float_format="%.4f")
    print("--- defence", flush=True)
    defence_reading(groups["global, all attacker documents"], min(boot, 500)).to_csv(
        out_dir / "defence.csv", index=False, float_format="%.4f"
    )
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "protocol_sha256": sha256(ROOT / "configs" / "protocol.yaml"),
        "table_sha256": sha256(path),
        "inputs_sha256": input_hashes(),
        "bags": bags,
        "bootstrap": boot,
        "features": ALL_FEATURES,
        "sealed_rows_excluded": int(full["sealed"].astype(bool).sum()),
        "quick": quick,
        "outputs": hashes(
            out_dir / f
            for f in (
                "lists.csv",
                "comparison.csv",
                "selection.csv",
                "scopes.csv",
                "state_gate.csv",
                "held_out_scores.csv.gz",
                "calibration.csv",
                "family_gain.csv",
                "defence.csv",
            )
        ),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(manifest)


if __name__ == "__main__":
    main()
