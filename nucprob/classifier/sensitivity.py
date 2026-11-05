"""The protocol's repeats, under spatial blocks: what the selected model's gain rests on.

    python -m nucprob.classifier.sensitivity

Each scope's selected candidate against population + country, with features removed:
- `none flagged`: today's data standing in for a document's date (data/FEATURES.md flags them);
- `strict as-of`: also the defence tables, most of them post-Soviet knowledge of the sites;
- `no national power`: COW values identify the document (one value per country and year);
- `no source markers`: no defence, military or national-power columns, whose presence or absence
  marks which table, and so which document, a row came from.

Then the Soviet towns of the SAC list, whose population is the 1959 census for a June 1956 document:
the population rule and LightGBM on the 1939 census instead (earlier than the document, and missing
for towns founded after it), against the same on 1959.

Then two later checks (configs/protocol_amendment_6.yaml):
- how far SAC's "complete" negatives lie beside the study's own airfield list, and the SAC gain without
  those within 10 km;
- how well a town's columns identify its document, with folds grouped by place.

and how near a held-out town's nearest training town lies, since spatial blocks have no buffer.

Writes runs/classifier/sensitivity.csv, ussr_population.csv, airfield_negatives.csv,
document_identification.csv, block_neighbours.csv and sensitivity_manifest.json.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import datetime as dt
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from nucprob.classifier import evaluate as ev
from nucprob.classifier.features import DEFENCE, MILITARY, NMC_FEATURES
from nucprob.classifier.fit import (
    ALL_FEATURES,
    FAMILIES,
    N_BAGS,
    Spec,
    lightgbm_quiet,
    logistic_all,
    logistic_country,
)
from nucprob.classifier.run import SAC, positives_of, scopes, usable
from nucprob.features.registry import FEATURES
from nucprob.geo import Points
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.outputs import hashes, start_record
from nucprob.paths import CURATED, PROCESSED, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier"
PLUS = "population + country"
FACTORY = {"logistic, all permitted": logistic_all, "LightGBM, all permitted": lightgbm_quiet}


def flagged() -> list[str]:
    return [f for f in ALL_FEATURES if f in FEATURES and FEATURES[f].anachronism]


def clean_columns() -> list[str]:
    drop = set(flagged())
    return [f for f in ALL_FEATURES if f not in drop]


def without(*groups: list[str]) -> list[str]:
    drop = {c for g in groups for c in g}
    return [f for f in ALL_FEATURES if f not in drop]


VARIANTS = {
    "all permitted": ALL_FEATURES,
    "none flagged": clean_columns(),
    "strict as-of": without(flagged(), DEFENCE),
    "no national power": without(NMC_FEATURES),
    "no source markers": without(NMC_FEATURES, DEFENCE, MILITARY),
}


def repeat_scope(scope: str, rows: pd.DataFrame, selected: str) -> list[dict]:
    models = [Spec(PLUS, logistic_country, ["log_pop", "country"])]
    models += [Spec(k, FACTORY[selected], cols) for k, cols in VARIANTS.items()]
    s = ev.spatial_scores(rows, models, N_BAGS)
    y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
    block = rows["block"].to_numpy()
    out = []
    for variant, cols in VARIANTS.items():
        out.append(
            {
                "scope": scope,
                "model": selected,
                "variant": variant,
                "features": len(cols),
                "positives": int(y.sum()),
                "a_pr_auc": ev.weighted_pr_auc(y, s[variant], doc),
                "b_pr_auc": ev.weighted_pr_auc(y, s[PLUS], doc),
            }
            | ev.paired_bootstrap(y, s[variant], s[PLUS], doc)
            | ev.block_bootstrap(y, s[variant], s[PLUS], doc, block)
        )
    return out


def imputed_logistic(seed: int = 0):
    """`seed` is part of every factory's signature; nothing here is random."""
    return make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=5000)
    )


def ussr_population(table: pd.DataFrame) -> pd.DataFrame:
    """The Soviet published no town census between 1939 and 1959."""
    su = table[(table["plan_id"] == SAC) & (table["country"] == "USSR")].reset_index(drop=True)
    su = su.assign(
        prewar_missing=su["log_pop_prewar"].isna().astype(float),
        log_pop_prewar=su["log_pop_prewar"].where(su["log_pop_prewar"] > 0),
    )
    # Every population column is the 1959 count or built on it.
    later = set(FAMILIES["population"])
    rest = [c for c in without(flagged(), DEFENCE) if c not in later]
    models = [
        Spec("rule, 1959", imputed_logistic, ["log_pop"]),
        Spec("rule, 1939", imputed_logistic, ["log_pop_prewar", "prewar_missing"]),
        Spec("LightGBM, 1959", lightgbm_quiet, ["log_pop", *rest]),
        Spec("LightGBM, 1939", lightgbm_quiet, ["log_pop_prewar", "prewar_missing", *rest]),
    ]
    s = ev.spatial_scores(su, models, N_BAGS)
    y, doc, block = su["listed"].to_numpy(int), su["plan_id"].to_numpy(), su["block"].to_numpy()
    out = []
    for kind in ("rule", "LightGBM"):
        a, b = s[f"{kind}, 1939"], s[f"{kind}, 1959"]
        out.append(
            {
                "model": kind,
                "towns": len(su),
                "positives": int(y.sum()),
                "towns_without_1939": int(su["prewar_missing"].sum()),
                "pr_auc_1939": ev.weighted_pr_auc(y, a, doc),
                "pr_auc_1959": ev.weighted_pr_auc(y, b, doc),
            }
            | ev.paired_bootstrap(y, a, b, doc)
            | ev.block_bootstrap(y, a, b, doc, block)
        )
    return pd.DataFrame(out)


def airfield_distance_km(rows: pd.DataFrame) -> np.ndarray:
    """Each town's distance to the nearest row of SAC's airfield list."""
    fields = pd.read_csv(CURATED / "labels" / "us_1956_sac_airfields.csv")
    fields = fields[fields["lat"].notna() & fields["lon"].notna()]
    dist, _ = Points(fields["lat"].to_numpy(), fields["lon"].to_numpy()).nearest(
        rows["lat"].to_numpy(), rows["lon"].to_numpy()
    )
    return np.ravel(dist)


def airfield_negatives(rows: pd.DataFrame, selected: str, bags: int) -> pd.DataFrame:
    """SAC's town list is complete for towns, but a town off it may sit beside an airfield SAC lists
    apart. The reading on all towns, and with negatives within 10 km of such an airfield left out."""
    sac = rows[rows["plan_id"] == SAC].reset_index(drop=True)
    near = airfield_distance_km(sac)
    negative = sac["listed"].to_numpy(int) == 0
    keep = ~(negative & (near <= 10))
    out = []
    for label, part in (("all towns", sac), ("negatives within 10 km left out", sac[keep])):
        part = part.reset_index(drop=True)
        models = [
            Spec(PLUS, logistic_country, ["log_pop", "country"]),
            Spec(selected, FACTORY[selected], ALL_FEATURES),
        ]
        s = ev.spatial_scores(part, models, bags)
        y, doc, block = part["listed"].to_numpy(int), part["plan_id"].to_numpy(), part["block"]
        out.append(
            {
                "towns": label,
                "rows": len(part),
                "negatives": int((y == 0).sum()),
                "negatives_within_5km": int((negative & (near <= 5)).sum()),
                "negatives_within_10km": int((negative & (near <= 10)).sum()),
                "a_pr_auc": ev.weighted_pr_auc(y, s[selected], doc),
                "b_pr_auc": ev.weighted_pr_auc(y, s[PLUS], doc),
            }
            | ev.paired_bootstrap(y, s[selected], s[PLUS], doc)
            | ev.block_bootstrap(y, s[selected], s[PLUS], doc, block.to_numpy())
        )
    return pd.DataFrame(out)


def document_identification(rows: pd.DataFrame) -> pd.DataFrame:
    """Cross-validated share of rows whose document a classifier names from the columns, against always
    naming the largest. Folds are grouped by place, so a town's own label cannot help."""
    y = rows["plan_id"].astype("category").cat.codes.to_numpy()
    sets = {
        "all permitted": ALL_FEATURES,
        "no national power": without(NMC_FEATURES),
        "no source markers": without(NMC_FEATURES, DEFENCE, MILITARY),
        "population only": ["log_pop"],
    }
    out = []
    for name, columns in sets.items():
        p = cross_val_predict(
            HistGradientBoostingClassifier(max_iter=60, max_depth=4, random_state=0),
            rows[columns],
            y,
            cv=GroupKFold(4),
            groups=rows["place_id"].to_numpy(),
        )
        out.append(
            {
                "columns": name,
                "rows": len(y),
                "documents": len(np.unique(y)),
                "accuracy": float((p == y).mean()),
                "largest_document_share": float(np.bincount(y).max() / len(y)),
            }
        )
    return pd.DataFrame(out)


def block_neighbours(rows: pd.DataFrame) -> pd.DataFrame:
    """Spatial folds have no buffer. The share of held-out rows with a training town within r km."""
    rows = rows.reset_index(drop=True)
    lat, lon = rows["lat"].to_numpy(float), rows["lon"].to_numpy(float)
    out = []
    for offset in ev.GRID_OFFSETS:
        blocks = pd.Series(assign_blocks(lat, lon, BLOCK_KM, offset), index=rows.index)
        fold = np.asarray(folds(blocks, rows["listed"], ev.N_FOLDS, seed=int(offset)))
        near = np.full(len(rows), np.inf)
        for f in range(ev.N_FOLDS):
            test = fold == f
            dist, _ = Points(lat[~test], lon[~test]).nearest(lat[test], lon[test])
            near[test] = np.ravel(dist)
        out.append(
            {
                "grid_offset_km": offset,
                "rows": len(rows),
                "within_25km": float((near <= 25).mean()),
                "within_50km": float((near <= 50).mean()),
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    started = start_record()
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = usable(full)
    groups, _ = scopes(table, positives_of(full))
    best = pd.read_csv(OUT / "selection.csv")
    best = best[best["selected"]].set_index("scope")["model"]
    ussr_population(table).to_csv(OUT / "ussr_population.csv", index=False, float_format="%.4f")
    out = []
    # Smallest first, and written after each: a cut-off run still leaves what it finished.
    for scope, rows in sorted(groups.items(), key=lambda kv: len(kv[1])):
        out += repeat_scope(scope, rows, best[scope])
        print(scope, flush=True)
        pd.DataFrame(out).to_csv(OUT / "sensitivity.csv", index=False, float_format="%.4f")
    assert np.isfinite(pd.DataFrame(out)["delta"]).all()
    sac_scope = "single document: SAC 1956 (not a state model)"
    airfield_negatives(groups[sac_scope], best[sac_scope], N_BAGS).to_csv(
        OUT / "airfield_negatives.csv", index=False, float_format="%.4f"
    )
    document_identification(groups["global, all attacker documents"]).to_csv(
        OUT / "document_identification.csv", index=False, float_format="%.4f"
    )
    block_neighbours(groups["global, all attacker documents"]).to_csv(
        OUT / "block_neighbours.csv", index=False, float_format="%.4f"
    )
    written = ["sensitivity.csv", "ussr_population.csv", "block_neighbours.csv"]
    written += ["airfield_negatives.csv", "document_identification.csv"]
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "outputs": hashes(OUT / f for f in written),
    }
    (OUT / "sensitivity_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
