"""Build the place universe as of the study date (PLAN section 3.1).

    python -m nucprob.places

USSR sources: pop-stat's city pages for 14 republics (census populations 1926, 1939, 1959 and
renaming notes) and, for Uzbekistan, which pop-stat lacks, Demoscope's 1959 table. Every
settlement is matched to a GeoNames populated place for its coordinates.

Every row carries its country and first-order unit on the study date (`country_1956`,
`unit_1956`: the union republic in the USSR), `pop` (the census nearest the study date: 1959 in
the USSR) and `pop_prewar` (the last pre-war census: 1939), each with its year.

Writes data/processed/places_1956.parquet: every settlement with at least MIN_KEEP people (the
universe proper is >= 10,000; 5,000 and 20,000 are the sensitivity thresholds), and
data/processed/places_1956_unmatched.csv for review.
"""

import datetime as dt

import numpy as np
import pandas as pd

from nucprob.gazetteer.match import match
from nucprob.gazetteer.names import name_on
from nucprob.paths import CURATED, PROCESSED, RAW
from nucprob.sources import demoscope, geonames, popstat

MIN_KEEP = 5_000
UNIVERSE = 10_000
PLAN_YEAR = 1956
REPUBLICS = {  # pop-stat page -> GeoNames country (today's state)
    "russia": "RU",
    "ukraine": "UA",
    "belarus": "BY",
    "moldova": "MD",
    "lithuania": "LT",
    "latvia": "LV",
    "estonia": "EE",
    "georgia": "GE",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "kazakhstan": "KZ",
    "kyrgyzstan": "KG",
    "tajikistan": "TJ",
    "turkmenistan": "TM",
}


# Eastern Europe from pop-stat (populations within today's municipal borders): the census or
# censuses nearest the study date (two are interpolated geometrically to it) and the last
# pre-war census.
EASTERN_PAGES = {
    "albania": dict(country="Albania", geonames="AL", pop=("1955-10-02",), prewar=None),
    "bulgaria": dict(country="Bulgaria", geonames="BG", pop=("1956-12-01",), prewar="1934-12-31"),
    "romania": dict(country="Romania", geonames="RO", pop=("1956-02-21",), prewar="1930-12-29"),
    "czechia": dict(
        country="Czechoslovakia",
        unit="czech lands",
        geonames="CZ",
        pop=("1950-03-01", "1961-03-01"),
        prewar="1930-12-01",
    ),
}
PREFIX = {
    "USSR": "su",
    "Poland": "pl",
    "East Germany": "dd",
    "Czechoslovakia": "cs",
    "Hungary": "hu",
    "Romania": "ro",
    "Bulgaria": "bg",
    "Albania": "al",
    "China": "cn",
    "North Korea": "kp",
    "North Vietnam": "vn",
    "Mongolia": "mn",
}
STUDY_DAY = dt.date(1956, 6, 15)


def years(date: str) -> float:
    d = dt.date.fromisoformat(date)
    return d.year + (d.timetuple().tm_yday - 1) / 365.25


def interpolate(a: pd.Series, b: pd.Series, date_a: str, date_b: str) -> pd.Series:
    """Population on the study date, growing geometrically from census a to census b."""
    study = years(STUDY_DAY.isoformat())
    share = (study - years(date_a)) / (years(date_b) - years(date_a))
    return a * (b / a) ** share


def census(df: pd.DataFrame, year: str) -> pd.Series:
    cols = [c for c in df.columns if c.startswith(f"pop_{year}")]
    return df[cols[0]] if cols else pd.Series(np.nan, index=df.index)


def latest(df: pd.DataFrame) -> pd.Series:
    """The most recent census figure of each settlement (to compare with GeoNames)."""
    cols = sorted(c for c in df.columns if c.startswith("pop_"))
    return df[cols].ffill(axis=1).iloc[:, -1]


def from_popstat(page: str) -> pd.DataFrame:
    df = popstat.parse(RAW / "popstat" / f"{page}-cities.htm", page)
    out = pd.DataFrame(
        {
            "republic": page,
            "country_today": REPUBLICS[page],
            "region": df["region"],
            "name_ru": df["name_ru"],
            "name_lat": df["name_lat"],
            "is_city": df["is_city"],
            "notes": df["notes"],
            "pop_1926": census(df, "1926"),
            "pop_1939": census(df, "1939"),
            "pop_1959": census(df, "1959"),
            "modern_pop": latest(df),
            "source": "pop-stat",
        }
    )
    out["name_1956"] = [
        name_on(n, notes, PLAN_YEAR) for n, notes in zip(out["name_ru"], out["notes"], strict=True)
    ]
    return out[out["pop_1959"] >= MIN_KEEP]


def from_popstat_eastern(page: str) -> pd.DataFrame:
    spec = EASTERN_PAGES[page]
    df = popstat.parse(RAW / "popstat" / f"{page}-cities.htm", page)
    dates = spec["pop"]
    if len(dates) == 1:
        pop, pop_year = df[f"pop_{dates[0]}"], int(dates[0][:4])
    else:
        a, b = df[f"pop_{dates[0]}"], df[f"pop_{dates[1]}"]
        pop, pop_year = interpolate(a, b, *dates).fillna(a).fillna(b), STUDY_DAY.year
    prewar = df[f"pop_{spec['prewar']}"] if spec["prewar"] else pd.Series(np.nan, index=df.index)
    latin = df["name_lat"].where(~df["name_lat"].str.fullmatch(r"[\d,.…\s]*"), "")
    out = pd.DataFrame(
        {
            "republic": page,
            "country_today": spec["geonames"],
            "region": df["region"],
            "name_ru": df["name_ru"],
            "name_lat": latin,
            "is_city": df["is_city"],
            "notes": df["notes"],
            "pop_1926": np.nan,
            "pop_1939": np.nan,
            "pop_1959": np.nan,
            "modern_pop": latest(df),
            "source": "pop-stat",
            "country_1956": spec["country"],
            "unit_1956": spec.get("unit", page),
            "pop": pop.round(),
            "pop_year": pop_year,
            "pop_prewar": prewar,
            "pop_prewar_year": int(spec["prewar"][:4]) if spec["prewar"] else np.nan,
        }
    )
    out["name_1956"] = [
        name_on(n, notes, PLAN_YEAR) for n, notes in zip(out["name_ru"], out["notes"], strict=True)
    ]
    return out[out["pop"] >= MIN_KEEP]


def from_demoscope(republic_prefix: str, page: str, country: str) -> pd.DataFrame:
    df = demoscope.parse(RAW / "demoscope" / "ussr59_reg2.html")
    df = df[df["republic"].str.startswith(republic_prefix) & (df["pop_1959"] >= MIN_KEEP)]
    return pd.DataFrame(
        {
            "republic": page,
            "country_today": country,
            "region": df["oblast"],
            "name_ru": df["name_ru"],
            "name_lat": "",
            "is_city": df["status"].eq("г."),
            "notes": "",
            "pop_1926": np.nan,
            "pop_1939": np.nan,
            "pop_1959": df["pop_1959"].astype(float),
            "modern_pop": np.nan,
            "source": "Demoscope 1959",
            "name_1956": df["name_ru"],
        }
    )


def apply_links(matched: pd.DataFrame, gn: pd.DataFrame, page: str) -> pd.DataFrame:
    """Hand-checked links (data/curated/gazetteer/geonames_links.csv) for names the matcher
    cannot resolve: towns renamed since 1959 whose old name GeoNames does not carry."""
    links = pd.read_csv(CURATED / "gazetteer" / "geonames_links.csv")
    links = links[links["republic"] == page].set_index("name")["geonameid"]
    by_id = gn.set_index("geonameid")
    for i in matched.index[matched["name_ru"].isin(links.index)]:
        g = by_id.loc[links[matched.at[i, "name_ru"]]]
        matched.loc[
            i,
            [
                "geonameid",
                "lat",
                "lon",
                "admin1",
                "feature_code",
                "gn_name",
                "gn_population",
                "gn_alternatenames",
                "gn_dem",
                "match_method",
            ],
        ] = [
            g.name,
            g["lat"],
            g["lon"],
            g["admin1"],
            g["feature_code"],
            g["name"],
            g["population"],
            g["alternatenames"],
            g["dem"],
            "curated link",
        ]
    return matched


def located(settlements: pd.DataFrame, country: str, page: str) -> pd.DataFrame:
    gn = geonames.load_country(country)
    matched = apply_links(match(settlements, gn), gn, page)
    print(
        f"{page:13} {len(settlements):5} settlements >= {MIN_KEEP}; "
        f"matched {matched['geonameid'].notna().sum():5}; methods {matched['match_method'].str.split(',').str[0].value_counts().to_dict()}"
    )
    return matched


def ussr() -> pd.DataFrame:
    parts = []
    for page, country in [*REPUBLICS.items(), ("uzbekistan", "UZ")]:
        settlements = (
            from_demoscope("Узбек", page, country) if page == "uzbekistan" else from_popstat(page)
        )
        parts.append(located(settlements, country, page))
    places = pd.concat(parts, ignore_index=True)
    places["country_1956"] = "USSR"
    # Karelia was the Karelo-Finnish SSR, a union republic, until 16 July 1956.
    karelia = places["region"].eq("Республика Карелия")
    places["unit_1956"] = places["republic"].mask(karelia, "karelo-finnish")
    places["pop"], places["pop_year"] = places["pop_1959"], 1959
    places["pop_prewar"], places["pop_prewar_year"] = places["pop_1939"], 1939
    return places


def eastern_europe() -> pd.DataFrame:
    parts = [
        located(from_popstat_eastern(page), spec["geonames"], page)
        for page, spec in EASTERN_PAGES.items()
    ]
    return pd.concat(parts, ignore_index=True)


def build() -> pd.DataFrame:
    places = pd.concat([ussr(), eastern_europe()], ignore_index=True)
    # A GeoNames place matched twice keeps the settlement with the larger population.
    places = places.sort_values("pop", ascending=False)
    dup = places["geonameid"].notna() & places.duplicated("geonameid", keep="first")
    places.loc[dup, "match_method"] = "duplicate of a larger settlement"
    places.loc[dup, ["geonameid", "lat", "lon"]] = np.nan
    prefix = places["country_1956"].map(PREFIX)
    places["place_id"] = [
        f"{p}-{int(g)}" if pd.notna(g) else f"{p}-x{i}"
        for i, (p, g) in enumerate(zip(prefix, places["geonameid"], strict=True))
    ]
    places["in_universe"] = places["pop"] >= UNIVERSE
    places["has_coords"] = places["lat"].notna()
    return places.sort_values(["country_1956", "republic", "region", "name_ru"]).reset_index(
        drop=True
    )


def main() -> None:
    places = build()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    places.to_parquet(PROCESSED / "places_1956.parquet", index=False)
    unmatched = places[~places["has_coords"]]
    unmatched.to_csv(PROCESSED / "places_1956_unmatched.csv", index=False)
    u = places[places["in_universe"]]
    for country, c in u.groupby("country_1956"):
        print(
            f"{country}: universe (>= {UNIVERSE:,}) {len(c)} settlements, "
            f"{c['has_coords'].sum()} with coordinates"
        )
    print(f"unmatched in the universe: {(~u['has_coords']).sum()} (places_1956_unmatched.csv)")


if __name__ == "__main__":
    main()
