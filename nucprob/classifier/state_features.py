"""The target state's regime, defence pacts and GDP per capita as of a document's year
(configs/protocol_amendment_5.yaml). State-years only: nothing here reads a label.

A state maps to the entity its source names for it. Where a source has none the value stays missing.
"""

import io
import zipfile

import numpy as np
import pandas as pd

from nucprob.classifier.features import COW, NMC_ZIP
from nucprob.paths import RAW

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
