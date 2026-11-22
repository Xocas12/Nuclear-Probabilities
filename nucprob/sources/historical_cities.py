"""Historical city populations with coordinates, as one tidy table (one row per city and year).

- Reba, Reitsma and Seto (2016), "Spatializing 6,000 years of global urbanization from 3700 BC
  to AD 2000", Scientific Data 3:160034 (figshare, CC BY 4.0): Chandler's (1987) and
  Modelski's (2003) city populations, geocoded. Three files (version 2 of each):
  - `chandlerV2.csv`: 1,597 cities, 2250 BC to AD 1975 (AD 1950: 430 cities; 1970: 73;
    1975: 393);
  - `modelskiAncientV2.csv`: 154 cities, 3700 BC to AD 1000;
  - `modelskiModernV2.csv`: 293 cities over one million in AD 2000.
  Columns: City, OtherName, Country (today's), Latitude, Longitude, Certainty (1 = sure of the
  location .. 3 = doubtful), and one column per year (`BC_2250`, `AD_1950`), in persons.
- UN World Urbanization Prospects 2018, file 12 (CC BY 3.0 IGO): the 1,860 urban agglomerations
  of 300,000 or more in 2018, every five years 1950-2035 (2020-2035 are projections), in
  thousands, with coordinates and a note number on the area each figure refers to (city proper,
  urban agglomeration or metropolitan area; the notes sheet gives the wording).

    python -m nucprob.sources.historical_cities

writes `data/processed/historical_cities.parquet` with columns source, name, other_name,
country, lat, lon, year (negative = BC), pop (persons), certainty (Reba only), city_code and
note (WUP only), projected (WUP years after 2018).
"""

import pandas as pd

from nucprob.paths import PROCESSED, RAW

DIR = RAW / "population_grids"
REBA = {
    "reba_chandler": "chandlerV2.csv",
    "reba_modelski_ancient": "modelskiAncientV2.csv",
    "reba_modelski_modern": "modelskiModernV2.csv",
}
WUP_F12 = DIR / "wup" / "WUP2018-F12-Cities_Over_300K.xls"
OUT = PROCESSED / "historical_cities.parquet"


def year_of(column: str) -> int | None:
    """'AD_1950' -> 1950, 'BC_2250' -> -2250, anything else -> None."""
    era, _, num = column.partition("_")
    if era not in ("AD", "BC") or not num.isdigit():
        return None
    return int(num) if era == "AD" else -int(num)


def load_reba(source: str) -> pd.DataFrame:
    wide = pd.read_csv(DIR / "reba" / REBA[source], encoding="latin-1", dtype=str)
    years = {c: year_of(c) for c in wide.columns if year_of(c) is not None}
    long = wide.melt(
        id_vars=["City", "OtherName", "Country", "Latitude", "Longitude", "Certainty"],
        value_vars=list(years),
        var_name="column",
        value_name="pop",
    )
    long["pop"] = pd.to_numeric(long["pop"].str.replace(",", ""), errors="coerce")
    long = long.dropna(subset=["pop"])
    return pd.DataFrame(
        {
            "source": source,
            "name": long["City"].str.strip(),
            "other_name": long["OtherName"].fillna(""),
            "country": long["Country"].str.strip(),
            "lat": pd.to_numeric(long["Latitude"].str.strip()),
            "lon": pd.to_numeric(long["Longitude"].str.strip()),
            "year": long["column"].map(years).astype(int),
            "pop": long["pop"].astype(float),
            "certainty": pd.to_numeric(long["Certainty"].str.strip()).astype("Int64"),
        }
    )


def load_wup(path=WUP_F12) -> pd.DataFrame:
    wide = pd.read_excel(path, sheet_name="Data", header=16)
    years = [c for c in wide.columns if isinstance(c, (int, float)) and 1900 < c < 2100]
    long = wide.melt(
        id_vars=[
            "Country or area",
            "City Code",
            "Urban Agglomeration",
            "Note",
            "Latitude",
            "Longitude",
        ],
        value_vars=years,
        var_name="year",
        value_name="pop",
    ).dropna(subset=["pop"])
    year = long["year"].astype(int)
    return pd.DataFrame(
        {
            "source": "wup2018",
            "name": long["Urban Agglomeration"].astype(str).str.strip(),
            "other_name": "",
            "country": long["Country or area"].astype(str).str.strip(),
            "lat": long["Latitude"].astype(float),
            "lon": long["Longitude"].astype(float),
            "year": year,
            "pop": long["pop"].astype(float) * 1000,
            "city_code": long["City Code"].astype("Int64"),
            "note": long["Note"].astype("Int64"),
            "projected": year > 2018,
        }
    )


def wup_notes(path=WUP_F12) -> pd.Series:
    """Note number -> text, from the NOTES sheet ('(38) Refers to ...')."""
    text = pd.read_excel(path, sheet_name="NOTES", header=None)[0].dropna().astype(str)
    found = text.str.extract(r"^\((\d+)\)\s*(.*)$").dropna()
    return pd.Series(found[1].values, index=found[0].astype(int).values, name="note_text")


def load(wup: bool = True) -> pd.DataFrame:
    parts = [load_reba(s) for s in REBA]
    if wup and WUP_F12.exists():
        parts.append(load_wup())
    table = pd.concat(parts, ignore_index=True)
    table["projected"] = table["projected"].fillna(False).astype(bool)
    return table.sort_values(["source", "country", "name", "year"], ignore_index=True)


def as_of(table: pd.DataFrame, year: float, source: str = "wup2018") -> pd.DataFrame:
    """One row per city of `source` whose observations bracket `year`, with `pop` interpolated
    linearly between the two nearest observations (no extrapolation)."""
    rows = []
    for _, city in table[table["source"] == source].groupby(["name", "country", "lat", "lon"]):
        city = city.sort_values("year")
        before, after = city[city["year"] <= year], city[city["year"] >= year]
        if before.empty or after.empty:
            continue
        a, b = before.iloc[-1], after.iloc[0]
        w = 0.0 if b["year"] == a["year"] else (year - a["year"]) / (b["year"] - a["year"])
        row = a.copy()
        row["pop"] = (1 - w) * a["pop"] + w * b["pop"]
        row["year"] = year
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def main() -> None:
    table = load()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(OUT, index=False)
    summary = table.groupby("source").agg(
        rows=("pop", "size"),
        cities=("name", "nunique"),
        first=("year", "min"),
        last=("year", "max"),
    )
    print(summary.to_string())
    print(f"wrote {OUT} ({len(table):,} rows)")


if __name__ == "__main__":
    main()
