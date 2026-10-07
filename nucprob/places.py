"""Build the place universe of the USSR as of the 1959 census (PLAN section 3.1).

    python -m nucprob.places

Sources: pop-stat's city pages for 14 republics (census populations 1926, 1939, 1959 and
renaming notes) and, for Uzbekistan, which pop-stat lacks, Demoscope's 1959 table. Every
settlement is matched to a GeoNames populated place for its coordinates.

Writes data/processed/places_ussr1959.parquet: every settlement with at least MIN_KEEP people in
1959 (the universe proper is >= 10,000; 5,000 and 20,000 are the sensitivity thresholds), and
data/processed/places_ussr1959_unmatched.csv for review.
"""

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
            "curated link",
        ]
    return matched


def build() -> pd.DataFrame:
    parts = []
    for page, country in [*REPUBLICS.items(), ("uzbekistan", "UZ")]:
        settlements = (
            from_demoscope("Узбек", page, country) if page == "uzbekistan" else from_popstat(page)
        )
        gn = geonames.load_country(country)
        matched = apply_links(match(settlements, gn), gn, page)
        print(
            f"{page:13} {len(settlements):5} settlements >= {MIN_KEEP}; "
            f"matched {matched['geonameid'].notna().sum():5}; methods {matched['match_method'].str.split(',').str[0].value_counts().to_dict()}"
        )
        parts.append(matched)
    places = pd.concat(parts, ignore_index=True)
    # A GeoNames place matched twice keeps the settlement with the larger 1959 population.
    places = places.sort_values("pop_1959", ascending=False)
    dup = places["geonameid"].notna() & places.duplicated("geonameid", keep="first")
    places.loc[dup, "match_method"] = "duplicate of a larger settlement"
    places.loc[dup, ["geonameid", "lat", "lon"]] = np.nan
    places["place_id"] = [
        f"su-{int(g)}" if pd.notna(g) else f"su-x{i}" for i, g in enumerate(places["geonameid"])
    ]
    places["in_universe"] = places["pop_1959"] >= UNIVERSE
    places["has_coords"] = places["lat"].notna()
    return places.sort_values(["republic", "region", "name_ru"]).reset_index(drop=True)


def main() -> None:
    places = build()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    places.to_parquet(PROCESSED / "places_ussr1959.parquet", index=False)
    unmatched = places[~places["has_coords"]]
    unmatched.to_csv(PROCESSED / "places_ussr1959_unmatched.csv", index=False)
    u = places[places["in_universe"]]
    print(
        f"universe (>= {UNIVERSE:,} in 1959): {len(u)} settlements, {u['has_coords'].sum()} with coordinates; "
        f"unmatched in the universe: {(~u['has_coords']).sum()} (list in places_ussr1959_unmatched.csv)"
    )


if __name__ == "__main__":
    main()
