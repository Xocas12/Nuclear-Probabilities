"""The pre-committed analysis of configs/protocol.yaml, except the sealed set.

    python -m nucprob.classifier.run [--quick]

Reads data/processed/classifier_table.parquet. For each scope: spatial blocks, leave one plan out,
temporal holdouts, the candidates against both baselines with a paired bootstrap. Then the US 1956
complexes alone: calibration, and the gain of each feature family. Then the defence reading.

--quick uses 3 bags and 50 bootstrap resamples, writes to runs/classifier-quick/, and is for
checking the code; the protocol's numbers come from the full run.

Writes runs/classifier/: lists.csv (every list, model and holdout), comparison.csv (paired
bootstrap), selection.csv, scopes.csv (what each scope holds, or why it was refused),
calibration.csv, family_gain.csv, defence.csv, spatial_scores.csv.gz and manifest.json.
"""

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from nucprob.classifier import evaluate as ev
from nucprob.classifier.features import DEFENCE
from nucprob.classifier.fit import ALL_FEATURES, FAMILIES, N_BAGS, Spec, fit_bagged, specs
from nucprob.model.cv import git_commit
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import lightgbm
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.plans import exercise_gate, gate, plans, protocol
from nucprob.sources.fetch import sha256

SAC = "us_1956_sac_complexes"
BASELINES = ("population rule", "population + country")
CANDIDATES = ("logistic, all permitted", "LightGBM, all permitted")
EXERCISE_TYPES = {"exercise", "wargame", "training"}


def usable(table: pd.DataFrame) -> pd.DataFrame:
    """What models may read: never a sealed place, never an unlinked document."""
    return table[~table["sealed"].astype(bool)].reset_index(drop=True)


def positives_of(table: pd.DataFrame) -> dict[str, int]:
    return table.groupby("plan_id")["listed"].sum().astype(int).to_dict()


def scopes(table: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Scope name -> rows, and the gate's decisions. Only documents with role train fit a model."""
    reg = plans()
    rule = protocol()["state_models"]
    positives = positives_of(table)
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


def compare(rows: pd.DataFrame, scores: dict[str, np.ndarray], boot: int, scope: str, holdout: str):
    """Each candidate against each baseline on the same rows."""
    y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
    out = []
    for a in CANDIDATES:
        for b in BASELINES:
            r = ev.paired_bootstrap(y, scores[a], scores[b], doc, n=boot)
            out.append({"scope": scope, "holdout": holdout, "model": a, "against": b} | r)
    return out


def analyse_scope(name: str, rows: pd.DataFrame, models: list[Spec], bags: int, boot: int):
    print(f"--- {name}: {len(rows)} rows", flush=True)
    lists, comparison = [], []
    spatial = ev.spatial_scores(rows, models, bags)
    lists += [r | {"scope": name} for r in ev.by_list(rows, spatial, "spatial blocks")]
    comparison += compare(rows, spatial, boot, name, "spatial blocks")
    y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
    weighted = {m: ev.weighted_pr_auc(y, s, doc) for m, s in spatial.items()}
    best = max(CANDIDATES, key=weighted.__getitem__)
    print(" spatial:", {k: round(v, 3) for k, v in weighted.items()}, "best", best, flush=True)
    selection = [
        {"scope": name, "model": m, "weighted_pr_auc": v, "selected": m == best}
        for m, v in weighted.items()
    ]
    lists += [r | {"scope": name} for r in ev.leave_one_plan_out(rows, models, bags)]
    print(" leave-one-plan-out done", flush=True)
    lists += [r | {"scope": name} for r in ev.temporal(rows, models, bags)]
    print(" temporal done", flush=True)
    return lists, comparison, selection, spatial


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


def calibration(rows: pd.DataFrame, models: list[Spec], bags: int, boot: int) -> pd.DataFrame:
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


def family_gain(rows: pd.DataFrame, boot: int) -> pd.DataFrame:
    """Each family over population and country, LightGBM, spatial blocks, US 1956 complexes.
    Repeated for the USSR alone, the only country whose defences the 1956 tables cover in depth."""
    out = []
    sac = rows[rows["plan_id"] == SAC].reset_index(drop=True)
    for label, part in (("all countries", sac), ("USSR", sac[sac["country"] == "USSR"])):
        part, country = with_country(part.reset_index(drop=True))
        base_cols = [*FAMILIES["population"], *country]
        models = [Spec("base", lambda seed=0: lightgbm(seed).set_params(n_jobs=3), base_cols)]
        for fam, cols in FAMILIES.items():
            if fam == "population":
                continue
            models.append(
                Spec(fam, lambda seed=0: lightgbm(seed).set_params(n_jobs=3), [*base_cols, *cols])
            )
        scores = ev.spatial_scores(part, models, 1)
        y, doc = part["listed"].to_numpy(int), part["plan_id"].to_numpy()
        for fam in scores:
            if fam == "base":
                continue
            r = ev.paired_bootstrap(y, scores[fam], scores["base"], doc, n=boot)
            out.append(
                {
                    "rows": label,
                    "family": fam,
                    "base_pr_auc": ev.weighted_pr_auc(y, scores["base"], doc),
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
        for column in DEFENCE:
            if part[column].notna().sum() < 50 or part[column].nunique() < 3:
                out.append({"rows_described": label, "feature": column, "note": "too few values"})
                continue
            out.append(
                {"rows_described": label, "feature": column} | odds_per_tenfold(part, column, boot)
            )
    return pd.DataFrame(out)


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--quick", action="store_true")
    quick = args.parse_args().quick
    bags, boot = (3, 50) if quick else (N_BAGS, ev.N_BOOT)
    out_dir = RUNS / ("classifier-quick" if quick else "classifier")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = PROCESSED / "classifier_table.parquet"
    full = pd.read_parquet(path)
    table = usable(full)
    groups, decisions = scopes(table)
    models = specs()
    lists, comparison, selection, described, kept = [], [], [], [], []
    for name, rows in groups.items():
        described.append(describe(name, rows))
        a, b, c, spatial = analyse_scope(name, rows, models, bags, boot)
        lists += a
        comparison += b
        selection += c
        lists += expectations(table, rows, models, bags, name)
        # Keep the scores behind the comparison, so the bootstrap can be redone from the file.
        kept.append(
            rows[["plan_id", "place_id", "listed"]].assign(
                scope=name, **{m: spatial[m] for m in spatial}
            )
        )
        pd.DataFrame(lists).to_csv(out_dir / "lists.csv", index=False, float_format="%.4f")
        pd.DataFrame(comparison).to_csv(
            out_dir / "comparison.csv", index=False, float_format="%.4f"
        )
    us = groups["state: US"] if "state: US" in groups else groups["global, plan documents only"]
    pd.DataFrame(selection).to_csv(out_dir / "selection.csv", index=False, float_format="%.4f")
    pd.DataFrame(described).to_csv(out_dir / "scopes.csv", index=False)
    decisions.to_csv(out_dir / "state_gate.csv", index=False)
    pd.concat(kept, ignore_index=True).to_csv(
        out_dir / "spatial_scores.csv.gz", index=False, float_format="%.5f"
    )
    print("--- calibration", flush=True)
    calibration(us, models, bags, boot).to_csv(
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
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "configs" / "protocol.yaml"),
        "table_sha256": sha256(path),
        "bags": bags,
        "bootstrap": boot,
        "features": ALL_FEATURES,
        "sealed_rows_excluded": int(full["sealed"].astype(bool).sum()),
        "quick": quick,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(manifest)


if __name__ == "__main__":
    main()
