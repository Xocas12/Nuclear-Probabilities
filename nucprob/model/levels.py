"""Milestones M6 and M7: the model zoo across datasets (level G), per-country and per-regime
models (levels C and R), and the transfer matrix (PLAN section 5.3), under the frozen
protocol (configs/protocol.yaml).

    python -m nucprob.model.levels zoo     [--datasets a,b] [--algos ...]
    python -m nucprob.model.levels levels  [--dataset pooled]

`zoo` cross-validates every algorithm on every dataset with spatial blocks on the protocol's
shifted grids and seeds. `levels` works on the pooled towns, which hold every plan:
- the specialisation gain: per country with enough targets, a model fitted on that country
  (C), on its regime group (R) and on everything (G), all scored on the same held-out
  blocks of that country;
- the transfer matrix: fit on country i, score country j (ROC-AUC).

Results go to runs/m6-zoo/ and runs/m7-levels/ with the protocol hash and data hashes. If
the processed tables come from an incomplete build (data/processed/INCOMPLETE_BUILD.txt),
they go to runs/incomplete/ instead (git-ignored), because they are not results.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.model.cv import git_commit
from nucprob.model.evaluate import metrics
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.paths import PROCESSED, RUNS
from nucprob.playground.algos import algorithms
from nucprob.playground.datasets import Data, load
from nucprob.playground.evaluate import evaluate
from nucprob.protocol import load as load_protocol
from nucprob.protocol import protocol_hash, recorded_hash

ZOO_DATASETS = ["sac1956", "sac1956:has_dgz", "napb90:very_high", "napb90:medium_plus"]
LEVEL_ALGOS = ["logit", "lgbm", "rf"]
MIN_CLASS = 30  # PLAN 5.3: a country gets its own model with >= 30 targeted and untargeted


def out_dir(name: str) -> Path:
    flag = PROCESSED / "INCOMPLETE_BUILD.txt"
    base = RUNS / "incomplete" if flag.exists() else RUNS
    if flag.exists():
        print(f"incomplete build ({flag.read_text().strip()}): writing to {base / name}")
    return base / name


def manifest(extra: dict) -> dict:
    if protocol_hash() != recorded_hash():
        raise RuntimeError("configs/protocol.yaml differs from its recorded hash")
    return {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "protocol_sha256": protocol_hash(),
        **extra,
    }


def zoo(datasets: list[str], algos: str) -> pd.DataFrame:
    cv = load_protocol()["splits"]["cv"]
    rows = []
    for name in datasets:
        try:
            d = load(name)
        except (FileNotFoundError, KeyError) as err:
            print(f"{name}: skipped ({err})")
            continue
        print(d.summary())
        for shift in cv["shifts_km"]:
            d.frame["block"] = assign_blocks(d.frame["lat"], d.frame["lon"], BLOCK_KM, shift)
            for seed in cv["seeds"]:
                b = evaluate(d, algos, "spatial", cv["k"], seed, verbose=False)
                rows += [
                    {"dataset": name, "shift_km": shift, "seed": seed, **r}
                    for r in b.to_dict("records")
                ]
        b = evaluate(d, algos, "random", cv["k"], 0, verbose=False)
        rows += [
            {"dataset": name, "shift_km": "random", "seed": 0, **r} for r in b.to_dict("records")
        ]
    df = pd.DataFrame(rows)
    spatial = df[df["shift_km"] != "random"]
    board = (
        spatial.groupby(["dataset", "algorithm"])
        .agg(
            pr_auc=("pr_auc_mean", "mean"),
            pr_auc_spread=("pr_auc_mean", "std"),
            roc_auc=("roc_auc_mean", "mean"),
            brier=("brier_mean", "mean"),
            base_rate=("base_rate", "mean"),
        )
        .reset_index()
    )
    rand = df[df["shift_km"] == "random"].set_index(["dataset", "algorithm"])["pr_auc_mean"]
    board["pr_auc_random_cv"] = [
        rand.get((a, b), np.nan) for a, b in zip(board["dataset"], board["algorithm"], strict=True)
    ]
    board = board.sort_values(["dataset", "pr_auc"], ascending=[True, False])
    out = out_dir("m6-zoo")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "runs.csv", index=False, float_format="%.4f")
    board.to_csv(out / "leaderboard.csv", index=False, float_format="%.4f")
    (out / "manifest.json").write_text(
        json.dumps(manifest({"datasets": datasets, "algorithms": algos, "cv": cv}), indent=2)
    )
    print(board.round(3).to_string(index=False))
    return board


def regime_group(country: str, year: int) -> str:
    """Primary regime coding of the protocol: V-Dem Regimes of the World."""
    from nucprob.sources import country_year as cy

    row = cy.lookup(country, int(year)) if isinstance(country, str) and country else None
    if row is None or pd.isna(row.get("vdem_regime")):
        return "unknown"
    r = int(row["vdem_regime"])
    return {0: "closed autocracy", 1: "electoral autocracy"}.get(r, "democracy")


def _fit_score(train: pd.DataFrame, test: pd.DataFrame, cols, algo) -> np.ndarray | None:
    if train["y"].nunique() < 2:
        return None
    m = algorithms(algo)[algo].factory().fit(train[cols], train["y"])
    return m.predict_proba(test[cols])[:, 1]


def levels(dataset: str = "pooled", algos=LEVEL_ALGOS, k: int = 5) -> dict:
    d: Data = load(dataset)
    f = d.frame.copy()
    f["country"] = f["nation"].fillna(f["country"])
    f["regime"] = [regime_group(c, y) for c, y in zip(f["country"], f["year"], strict=True)]
    cols = d.features
    counts = f.groupby("country")["y"].agg(["sum", "size"])
    counts["neg"] = counts["size"] - counts["sum"]
    big = counts[(counts["sum"] >= MIN_CLASS) & (counts["neg"] >= MIN_CLASS)].index.tolist()
    print(f"countries with own models: {big}")
    gain_rows = []
    for country in big:
        mask = (f["country"] == country).to_numpy()
        sub = f[mask]
        fold = folds(sub["block"], sub["y"], k, 0)
        regime = sub["regime"].mode().iloc[0]
        for algo in algos:
            preds = {lvl: np.full(len(sub), np.nan) for lvl in ("G", "R", "C")}
            for i in np.unique(fold):
                test_idx = sub.index[fold == i]
                held = f.index.isin(test_idx)
                pools = {
                    "G": f[~held],
                    "R": f[~held & (f["regime"] == regime).to_numpy()],
                    "C": f[~held & mask],
                }
                for lvl, train in pools.items():
                    p = _fit_score(train, f.loc[test_idx], cols, algo)
                    if p is not None:
                        preds[lvl][fold == i] = p
            for lvl, p in preds.items():
                ok = ~np.isnan(p)
                m = metrics(sub["y"].to_numpy()[ok], p[ok]) or {}
                gain_rows.append(
                    {"country": country, "regime": regime, "algorithm": algo, "level": lvl, **m}
                )
    gains = pd.DataFrame(gain_rows)
    # Transfer matrix: fit on one country, score another (LightGBM, common features).
    scored = [c for c in counts.index if counts.at[c, "sum"] >= 5 and counts.at[c, "neg"] >= 5]
    mat = pd.DataFrame(index=big, columns=scored, dtype=float)
    for i in big:
        tr = f[f["country"] == i]
        for j in scored:
            te = f[f["country"] == j]
            if i == j:
                continue
            p = _fit_score(tr, te, cols, "lgbm")
            if p is not None:
                mat.at[i, j] = (metrics(te["y"].to_numpy(), p) or {}).get("roc_auc", np.nan)
    out = out_dir("m7-levels")
    out.mkdir(parents=True, exist_ok=True)
    gains.to_csv(out / "specialisation.csv", index=False, float_format="%.4f")
    mat.to_csv(out / "transfer_matrix.csv", float_format="%.3f")
    f.groupby(["regime", "country"])["y"].agg(["sum", "size"]).to_csv(out / "groups.csv")
    (out / "manifest.json").write_text(
        json.dumps(
            manifest({"dataset": dataset, "algorithms": list(algos), "min_class": MIN_CLASS}),
            indent=2,
        )
    )
    piv = gains.pivot_table(index=["country", "algorithm"], columns="level", values="pr_auc")
    print(piv.round(3).to_string())
    print(mat.round(2).to_string())
    return {"gains": gains, "transfer": mat}


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m nucprob.model.levels")
    sub = p.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zoo")
    z.add_argument("--datasets", default=",".join(ZOO_DATASETS))
    z.add_argument("--algos", default="all")
    lv = sub.add_parser("levels")
    lv.add_argument("--dataset", default="pooled")
    args = p.parse_args(argv)
    if args.cmd == "zoo":
        zoo(args.datasets.split(","), args.algos)
    else:
        levels(args.dataset)


if __name__ == "__main__":
    main()
