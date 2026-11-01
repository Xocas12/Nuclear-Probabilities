"""Build the place universe as of the study date (PLAN section 3.1).

    python -m nucprob.places

USSR sources: pop-stat's city pages for 14 republics (census populations 1926, 1939, 1959 and
renaming notes) and, for Uzbekistan, which pop-stat lacks, Demoscope's 1959 table. Every
settlement is matched to a GeoNames populated place for its coordinates.

Every row carries its country and first-order unit on the study date (`country_1956`,
`unit_1956`: the union republic in the USSR), `pop` (the census nearest the study date: 1959 in
the USSR) and `pop_prewar` (the last pre-war census: 1939), each with its year.

Writes data/processed/places_1956.parquet: every settlement with at least MIN_KEEP people (the
universe proper is >= 10,000; 5,000 and 20,000 are the sensitivity thresholds), and for review
data/processed/places_1956_unmatched.csv and places_1956_population_check.csv (`population_check`:
matches to a GeoNames place with no population or far fewer people than the settlement had).
"""

import numpy as np
import pandas as pd

from nucprob import places_bloc
from nucprob.gazetteer.match import match
from nucprob.gazetteer.names import name_on
from nucprob.geo import Points
from nucprob.paths import CURATED, PROCESSED, RAW
from nucprob.places_bloc import interpolate
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
CLOSED = CURATED / "gazetteer" / "closed_cities_1956.csv"
REVIEWED = CURATED / "gazetteer" / "population_check_reviewed.csv"
EAST_GERMAN_LAENDER = {"11", "12", "13", "14", "15", "16"}  # GeoNames admin1 codes, Berlin incl.


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
        pop, pop_year = interpolate(a, b, *dates).set_axis(df.index), PLAN_YEAR
    prewar = df[f"pop_{spec['prewar']}"] if spec["prewar"] else pd.Series(np.nan, index=df.index)
    # Pages of Latin-script countries have no transliteration column (the parser reads the first
    # census figure there instead): the name itself is the Latin name, for fuzzy matching.
    latin = df["name_lat"].where(~df["name_lat"].str.fullmatch(r"[\d,.…\s]*"), "")
    is_latin = df["name_ru"].str.contains(r"[A-Za-z]")
    latin = latin.mask(is_latin & latin.eq(""), df["name_ru"])
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


def located(
    settlements: pd.DataFrame,
    country: str,
    page: str,
    admin1: set[str] | None = None,
    admin1_of: dict[str, tuple[str, ...]] | None = None,
) -> pd.DataFrame:
    """Match `settlements` to GeoNames places of `country` (only those in `admin1`, if given;
    `admin1_of` restricts each census region to its own admin1 codes, see `match`)."""
    gn = geonames.load_country(country)
    if admin1 is not None:
        gn = gn[gn["admin1"].isin(admin1)]
    matched = apply_links(match(settlements, gn, admin1_of), gn, page)
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
    if CLOSED.exists():
        places = pd.concat([places, closed_cities(places)], ignore_index=True)
    places["pop_imputed"] = places.get("pop_imputed", pd.Series(False, index=places.index))
    places["pop_imputed"] = places["pop_imputed"].fillna(False).astype(bool)
    places["country_1956"] = "USSR"
    # Karelia was the Karelo-Finnish SSR, a union republic, until 16 July 1956.
    karelia = places["region"].eq("Республика Карелия")
    places["unit_1956"] = places["republic"].mask(karelia, "karelo-finnish")
    places["pop"], places["pop_year"] = places["pop_1959"], 1959
    places["pop_prewar"], places["pop_prewar_year"] = places["pop_1939"], 1939
    return places


def closed_cities(ussr: pd.DataFrame) -> pd.DataFrame:
    """Closed towns founded by the study date and missing from the published 1959 tables
    (PLAN section 3.1), from the curated table: population imputed from the nearest later
    figure (`pop_imputed`), union republic and region taken from the nearest listed town.
    They are in because they existed, not because of how they were targeted."""
    c = pd.read_csv(CLOSED)
    keep = (c["founded"] <= PLAN_YEAR) & c["lat"].notna() & (c["pop_estimate"] >= MIN_KEEP)
    c = c[keep].reset_index(drop=True)
    listed = ussr[ussr["lat"].notna()].reset_index(drop=True)
    dist, idx = Points(listed["lat"].to_numpy(), listed["lon"].to_numpy()).nearest(
        c["lat"].to_numpy(), c["lon"].to_numpy()
    )
    near = listed.iloc[idx[:, 0]].reset_index(drop=True)
    # A closed town that the census tables do list (within 5 km, same name) is not added twice.
    known = (dist[:, 0] < 5) & (near["name_ru"].to_numpy() == c["name_ru"].to_numpy())
    c, near = c[~known].reset_index(drop=True), near[~known].reset_index(drop=True)
    return pd.DataFrame(
        {
            "republic": near["republic"],
            "country_today": near["country_today"],
            "region": near["region"],
            "name_ru": c["name_ru"],
            "name_lat": c["name"],
            "is_city": True,
            "notes": "closed town; code names " + c["code_names"].fillna(""),
            "pop_1926": np.nan,
            "pop_1939": np.nan,
            "pop_1959": c["pop_estimate"],
            "modern_pop": np.nan,
            "source": "curated closed town",
            "name_1956": c["name_ru"],
            "match_method": "curated closed town",
            "lat": c["lat"],
            "lon": c["lon"],
            "pop_imputed": True,
            "pop_imputed_year": c["pop_year"],
            # a stable id, since closed towns have no GeoNames match of their own
            "place_key": "closed-"
            + c["name"].str.lower().str.replace(r"\W+", "-", regex=True).str.strip("-"),
        }
    )


def eastern_europe() -> pd.DataFrame:
    parts = [
        located(from_popstat_eastern(page), spec["geonames"], page)
        for page, spec in EASTERN_PAGES.items()
    ]
    parts.append(
        located(
            places_bloc.east_germany(),
            "DE",
            "east germany",
            EAST_GERMAN_LAENDER,
            admin1_of=places_bloc.EAST_GERMANY_ADMIN1,
        )
    )
    parts.append(located(places_bloc.poland(), "PL", "poland"))
    parts.append(located(places_bloc.hungary().query("pop >= @MIN_KEEP"), "HU", "hungary"))
    parts.append(located(places_bloc.slovakia(), "SK", "slovakia"))
    return pd.concat(parts, ignore_index=True)


def east_asia() -> pd.DataFrame:
    """China's 1953 cities, matched to GeoNames; North Korea, North Vietnam and Mongolia from
    the UN's estimates, which carry their own coordinates."""
    wup = places_bloc.wup()
    wup["has_match"] = True
    china = located(places_bloc.china(), "CN", "china", admin1_of=places_bloc.CHINA_ADMIN1)
    return pd.concat([china, wup], ignore_index=True)


def build() -> pd.DataFrame:
    places = pd.concat([ussr(), eastern_europe(), east_asia()], ignore_index=True)
    places = places.drop(columns="has_match", errors="ignore")
    places["pop_imputed"] = places["pop_imputed"].astype("boolean").fillna(False).astype(bool)
    # A GeoNames place matched twice keeps the settlement with the larger population.
    places = places.sort_values("pop", ascending=False)
    dup = places["geonameid"].notna() & places.duplicated("geonameid", keep="first")
    places.loc[dup, "match_method"] = "duplicate of a larger settlement"
    places.loc[dup, ["geonameid", "lat", "lon"]] = np.nan
    prefix = places["country_1956"].map(PREFIX)
    keys = places["place_key"] if "place_key" in places else pd.Series(None, index=places.index)
    places["place_id"] = [
        f"{p}-{int(g)}" if pd.notna(g) else f"{p}-{k}" if isinstance(k, str) else f"{p}-x{i}"
        for i, (p, g, k) in enumerate(zip(prefix, places["geonameid"], keys, strict=True))
    ]
    places["in_universe"] = places["pop"] >= UNIVERSE
    places["has_coords"] = places["lat"].notna()
    return places.sort_values(["country_1956", "republic", "region", "name_ru"]).reset_index(
        drop=True
    )


def population_check(places: pd.DataFrame, reviewed: pd.DataFrame | None = None) -> pd.DataFrame:
    """GeoNames matches to review: the place matched has no population in GeoNames, or fewer
    than a tenth of the settlement's own figure (`pop`). A town put on a same-named hamlet
    shows up here; so do towns GeoNames records without a population, and towns that shrank
    or were absorbed into a neighbour, which are right. Curated links (`apply_links`) are
    included: they are checked by hand, but not their population.

    `reviewed` (columns republic, name, geonameid, explanation; REVIEWED) explains matches
    already checked. An explanation holds only for the place it names, so a match that moves
    comes back unexplained."""
    matched = places[places["geonameid"].notna() & places["lat"].notna()]
    gn_pop = matched["gn_population"].fillna(0)
    flag = gn_pop.le(0) | gn_pop.lt(matched["pop"] / 10)
    out = matched.loc[
        flag,
        [
            "place_id",
            "country_1956",
            "republic",
            "region",
            "name_ru",
            "pop",
            "pop_year",
            "geonameid",
            "gn_name",
            "gn_population",
            "feature_code",
            "admin1",
            "lat",
            "lon",
            "n_candidates",
            "match_method",
        ],
    ].copy()
    out["check"] = np.where(
        out["gn_population"].fillna(0) <= 0,
        "GeoNames population 0",
        "GeoNames population under a tenth of pop",
    )
    out["explanation"] = ""
    if reviewed is not None and len(reviewed):
        notes = {
            (r, n, float(g)): e
            for r, n, g, e in reviewed[["republic", "name", "geonameid", "explanation"]].itertuples(
                index=False
            )
        }
        out["explanation"] = [
            notes.get((r, n, float(g)), "")
            for r, n, g in zip(out["republic"], out["name_ru"], out["geonameid"], strict=True)
        ]
    return out.sort_values(["country_1956", "pop"], ascending=[True, False]).reset_index(drop=True)


def main() -> None:
    places = build()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    places.to_parquet(PROCESSED / "places_1956.parquet", index=False)
    unmatched = places[~places["has_coords"]]
    unmatched.to_csv(PROCESSED / "places_1956_unmatched.csv", index=False)
    check = population_check(places, pd.read_csv(REVIEWED))
    check.to_csv(PROCESSED / "places_1956_population_check.csv", index=False)
    u = places[places["in_universe"]]
    for country, c in u.groupby("country_1956"):
        print(
            f"{country}: universe (>= {UNIVERSE:,}) {len(c)} settlements, "
            f"{c['has_coords'].sum()} with coordinates"
        )
    print(f"unmatched in the universe: {(~u['has_coords']).sum()} (places_1956_unmatched.csv)")
    open_rows = check[check["explanation"].eq("")]
    print(
        f"population check: {len(check)} matches with a GeoNames population of 0 or under a "
        f"tenth of pop, {len(open_rows)} not yet explained in {REVIEWED.name} "
        f"(places_1956_population_check.csv): {open_rows['country_1956'].value_counts().to_dict()}"
    )


if __name__ == "__main__":
    main()
