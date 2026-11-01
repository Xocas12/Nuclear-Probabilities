"""Economic and political readings of configs/protocol_amendment_5.yaml, beside the primary analysis.

    python -m nucprob.classifier.extended

Adds, in memory, the target state's regime, defence pacts and GDP per capita as of each document's
year, and reads them against the population family and the primary model under spatial blocks and leave
one plan out. On Soviet towns of SAC 1956 it also reads the defence-industry counts. No primary score
changes. Writes runs/classifier/extended.csv and extended_manifest.json.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import datetime as dt
import io
import json
import zipfile

import numpy as np
import pandas as pd

from nucprob.classifier import evaluate as ev
from nucprob.classifier.evaluate import GRID_OFFSETS, MIN_TRAIN_POSITIVES, N_FOLDS
from nucprob.classifier.features import COW, NMC_FEATURES, NMC_ZIP
from nucprob.classifier.fit import ALL_FEATURES, FAMILIES, N_BAGS, Spec, lightgbm_quiet
from nucprob.classifier.run import SAC, positives_of, scopes, usable
from nucprob.model.cv import git_commit
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.paths import PROCESSED, RAW, ROOT, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier"
AMENDMENT = ROOT / "configs" / "protocol_amendment_5.yaml"
ALLIANCES = RAW / "cow" / "alliances_v4.1_csv.zip"
REGIME = RAW / "owid" / "political-regime.csv"
GDP = RAW / "owid" / "gdp-per-capita-maddison-project-database.csv"
POLITICAL = [
    "pol_regime",
    "pol_defence_pact_usa",
    "pol_defence_pact_ussr",
    "pol_log_defence_pacts",
]
ECONOMIC = ["econ_log_gdp_pc"]
NEW_COLUMNS = [*POLITICAL, *ECONOMIC]
SCOPES = ["global, all attacker documents", "Warsaw Pact, pooled, exercise-based"]
USA, USSR = 2, 365  # COW state codes
SAME_NAME = [
    "Albania",
    "Austria",
    "Belgium",
    "Bulgaria",
    "Canada",
    "China",
    "Denmark",
    "Hungary",
    "Italy",
    "Japan",
    "Mongolia",
    "Netherlands",
    "North Korea",
    "Poland",
    "Romania",
]
BOTH = {"USA": "United States", "UK": "United Kingdom"}
REGIME_ENTITY = {n: n for n in SAME_NAME} | BOTH
REGIME_ENTITY |= {
    "USSR": "Russia",
    "East Germany": "East Germany",
    "FRG": "West Germany",
    "Czechoslovakia": "Czechia",
    "North Vietnam": "Democratic Republic of Vietnam",
}
# Maddison has no separate GDR or Democratic Republic of Vietnam: those stay missing.
GDP_ENTITY = {n: n for n in SAME_NAME} | BOTH
GDP_ENTITY |= {"USSR": "USSR", "FRG": "Germany", "Czechoslovakia": "Czechoslovakia"}


def last_at_or_before(series: pd.DataFrame, entity: str | None, column: str, year: int) -> float:
    rows = series[(series["Entity"] == entity) & (series["Year"] <= year)]
    return float(rows.sort_values("Year").iloc[-1][column]) if len(rows) else np.nan


def read_pacts(path=ALLIANCES) -> pd.DataFrame:
    """Directed dyad-years of COW's defence pacts: ccode1, ccode2, year."""
    with zipfile.ZipFile(path) as z:
        raw = z.read("version4.1_csv/alliance_v4.1_by_directed_yearly.csv")
    d = pd.read_csv(io.BytesIO(raw), usecols=["ccode1", "ccode2", "defense", "year"])
    return d[d["defense"] == 1][["ccode1", "ccode2", "year"]].drop_duplicates()


def pact_columns(pacts: pd.DataFrame, ccode: int, year: int) -> dict[str, float]:
    """COW records a pact only in years it is in force, so the document's own year is as-of."""
    partners = set(pacts.loc[(pacts["ccode1"] == ccode) & (pacts["year"] == year), "ccode2"])
    return {
        "pol_defence_pact_usa": float(ccode == USA or USA in partners),
        "pol_defence_pact_ussr": float(ccode == USSR or USSR in partners),
        "pol_log_defence_pacts": float(np.log10(1 + len(partners))),
    }


def state_codes(path=NMC_ZIP) -> dict[str, int]:
    with zipfile.ZipFile(path) as outer:
        inner = io.BytesIO(outer.read("NMCv7/NMC-v7-abridged.zip"))
    with zipfile.ZipFile(inner) as z:
        d = pd.read_csv(io.BytesIO(z.read("NMC-70-abridged.csv")), usecols=["stateabb", "ccode"])
    return dict(zip(d["stateabb"], d["ccode"], strict=False))


def state_year_table(
    countries_years: pd.DataFrame,
    regime: pd.DataFrame,
    gdp: pd.DataFrame,
    pacts: pd.DataFrame,
    codes: dict[str, int],
) -> pd.DataFrame:
    rows = []
    for country, year in countries_years[["country", "year"]].drop_duplicates().to_numpy():
        year = int(year)
        code = codes.get(COW.get(country))
        row = {
            "country": country,
            "year": year,
            "pol_regime": last_at_or_before(
                regime, REGIME_ENTITY.get(country), "Political regime", year
            ),
            "econ_log_gdp_pc": np.log10(
                last_at_or_before(gdp, GDP_ENTITY.get(country), "GDP per capita", year)
            ),
        }
        missing = dict.fromkeys(POLITICAL[1:], np.nan)
        row |= pact_columns(pacts, code, year) if code is not None else missing
        rows.append(row)
    return pd.DataFrame(rows)


def with_new_columns(rows: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    return rows.merge(table, on=["country", "year"], how="left", validate="many_to_one")


def comparisons() -> dict[str, tuple[list[str], list[str]]]:
    pop = FAMILIES["population"]
    return {
        "political over population": ([*pop, *POLITICAL], pop),
        "economic over population": ([*pop, *ECONOMIC], pop),
        "national power over population": ([*pop, *NMC_FEATURES], pop),
        "all three over population": ([*pop, *POLITICAL, *ECONOMIC, *NMC_FEATURES], pop),
        "political over primary": ([*ALL_FEATURES, *POLITICAL], ALL_FEATURES),
        "economic over primary": ([*ALL_FEATURES, *ECONOMIC], ALL_FEATURES),
    }


def read_pair(frame: pd.DataFrame, a: np.ndarray, b: np.ndarray, label: dict) -> dict:
    y, doc, block = frame["listed"].to_numpy(int), frame["plan_id"].to_numpy(), frame["block"]
    return (
        label
        | {
            "positives": int(y.sum()),
            "a_pr_auc": ev.weighted_pr_auc(y, a, doc),
            "b_pr_auc": ev.weighted_pr_auc(y, b, doc),
        }
        | ev.paired_bootstrap(y, a, b, doc)
        | ev.block_bootstrap(y, a, b, doc, block.to_numpy())
    )


def spatial_train_positives(rows: pd.DataFrame) -> int:
    """The fewest positives any spatial fit trained on, as the primary table counts them."""
    lat, lon = rows["lat"].to_numpy(float), rows["lon"].to_numpy(float)
    fewest = int(rows["listed"].sum())
    for offset in GRID_OFFSETS:
        blocks = pd.Series(assign_blocks(lat, lon, BLOCK_KM, offset), index=rows.index)
        fold = folds(blocks, rows["listed"], N_FOLDS, seed=int(offset))
        for f in range(N_FOLDS):
            fewest = min(fewest, int(rows.loc[fold != f, "listed"].sum()))
    return fewest


def read_scope(scope: str, rows: pd.DataFrame, bags: int) -> list[dict]:
    rows = rows.reset_index(drop=True)
    pairs = comparisons()
    specs = [Spec(name, lightgbm_quiet, cols) for name, (cols, _) in pairs.items()]
    specs += [
        Spec("population", lightgbm_quiet, FAMILIES["population"]),
        Spec("primary", lightgbm_quiet, ALL_FEATURES),
    ]
    spatial = ev.spatial_scores(rows, specs, bags)
    _, held = ev.leave_one_plan_out(rows, specs, bags)
    held = held.reset_index(drop=True)
    spatial_trained = spatial_train_positives(rows)
    readings = [
        ("spatial blocks", rows, spatial),
        ("leave one plan out", held, {m.name: held[m.name].to_numpy() for m in specs}),
    ]
    out = []
    for holdout, frame, scores in readings:
        for name, (_, base_columns) in pairs.items():
            base = "population" if base_columns == FAMILIES["population"] else "primary"
            not_sac = (frame["plan_id"] != SAC).to_numpy()
            for which, keep in (
                ("all lists", np.ones(len(frame), bool)),
                ("other than SAC", not_sac),
            ):
                sub = frame[keep].reset_index(drop=True)
                if sub["listed"].sum() < 2:
                    continue
                trained = (
                    int(sub["train_positives"].min())
                    if holdout == "leave one plan out"
                    else spatial_trained
                )
                out.append(
                    read_pair(
                        sub,
                        scores[name][keep],
                        scores[base][keep],
                        {
                            "scope": scope,
                            "comparison": name,
                            "holdout": holdout,
                            "lists": which,
                            "train_positives": trained,
                            "constant": bool(np.unique(scores[name][keep]).size == 1),
                        },
                    )
                )
    return out


def read_defence_industry(rows: pd.DataFrame, bags: int) -> list[dict]:
    sac = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    vpk = [c for c in sac.columns if c.startswith("log_vpk")]
    su = rows[(rows["plan_id"] == SAC) & (rows["country"] == "USSR")]
    su = su.merge(sac[["place_id", *vpk]], on="place_id", how="left", validate="one_to_one")
    su = su.reset_index(drop=True)
    pop = FAMILIES["population"]
    specs = [Spec("population", lightgbm_quiet, pop), Spec("vpk", lightgbm_quiet, [*pop, *vpk])]
    s = ev.spatial_scores(su, specs, bags)
    label = {
        "scope": "SAC 1956, Soviet towns",
        "comparison": "defence industry over population",
        "holdout": "spatial blocks",
        "lists": "all lists",
        "train_positives": spatial_train_positives(su),
        "constant": False,
    }
    return [read_pair(su, s["vpk"], s["population"], label)]


def verdict(r) -> str:
    if r["train_positives"] < MIN_TRAIN_POSITIVES or r["constant"]:
        return "not a reading"
    if r["low"] > 0 and r["block_low"] > 0:
        return "gain"
    if r["high"] < 0 and r["block_high"] < 0:
        return "loss"
    return "neither"


def main() -> None:
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    groups, _ = scopes(usable(full), positives_of(full))
    table = state_year_table(
        full[["country", "year"]].dropna(),
        pd.read_csv(REGIME),
        pd.read_csv(GDP),
        read_pacts(),
        state_codes(),
    )
    out = []
    for scope in SCOPES:
        rows = with_new_columns(groups[scope], table)
        out += read_scope(scope, rows, N_BAGS)
        print(scope, flush=True)
        pd.DataFrame(out).to_csv(OUT / "extended.csv", index=False, float_format="%.4f")
    out += read_defence_industry(groups[SCOPES[0]], N_BAGS)
    d = pd.DataFrame(out)
    d["verdict"] = d.apply(verdict, axis=1)
    d.to_csv(OUT / "extended.csv", index=False, float_format="%.4f")
    missing = table[NEW_COLUMNS].isna().sum().astype(int).to_dict()
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "amendment_sha256": sha256(AMENDMENT),
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "state_years": len(table),
        "state_years_missing": missing,
    }
    (OUT / "extended_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
