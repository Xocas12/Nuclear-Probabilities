"""Settlements of the bloc outside the USSR and pop-stat's pages (PLAN section 3.1), each from
the best source for its 1950s populations:

- East Germany: Statistisches Jahrbuch der DDR 1956, table I.10 (every municipality of 10,000+
  at the end of 1956, with 1939 to 1956), interpolated between end-1955 and end-1956;
- Poland: Rocznik Statystyczny 1957, table 7 (every town of 10,000+ at the end of 1956, with
  the 1950 census), interpolated between December 1950 and December 1956;
- Hungary: the 2011 census's historical series by settlement (1941, 1949, 1960), interpolated
  between the 1949 and 1960 censuses;
- Slovakia: Votrubec (1959), the 25 Slovak towns of 10,000+ in 1953 with their population in
  January 1954 and 1958 (data/curated/gazetteer/slovakia_towns_1954_1958.csv), interpolated;
  towns that passed 10,000 after 1953 are missing;
- China: the 1953 census's 163 cities (shi), as tabulated on Wikipedia from Shabad (1959): the
  towns (zhen) are not in it, so China's universe is its cities;
- North Korea, North Vietnam, Mongolia: the UN's World Urbanization Prospects 2018 estimates for
  1956 (cities of 300,000+ today only, and model-based).

Every builder returns the columns of nucprob.places.from_popstat_eastern, ready for GeoNames.
"""

import io
import re
import zipfile

import numpy as np
import pandas as pd

from nucprob.paths import CURATED, RAW
from nucprob.sources import ddr, gus, ksh

STUDY_DAY = "1956-06-15"
# Names in use in June 1956 that the sources give in their later form.
RENAMED_1956 = {"Katowice": "Stalinogród"}
WUP_COUNTRIES = {
    "Dem. People's Republic of Korea": ("North Korea", "KP"),
    "Viet Nam": ("North Vietnam", "VN"),
    "Mongolia": ("Mongolia", "MN"),
}
NORTH_VIETNAM_LAT = 17.0  # the demarcation line of 1954


def years(date: str) -> float:
    day = pd.Timestamp(date)
    return day.year + (day.dayofyear - 1) / 365.25


def interpolate(a, b, date_a: str, date_b: str):
    """Population on the study date, growing geometrically from figure a to figure b."""
    share = (years(STUDY_DAY) - years(date_a)) / (years(date_b) - years(date_a))
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    return (a * (b / a) ** share).fillna(b).fillna(a)


def frame(
    *,
    page: str,
    geonames: str,
    country: str,
    unit: str,
    region,
    name,
    pop,
    pop_year: int,
    source: str,
    prewar=np.nan,
    prewar_year=np.nan,
    notes="",
) -> pd.DataFrame:
    name = pd.Series(name).reset_index(drop=True)
    df = pd.DataFrame(
        {
            "republic": page,
            "country_today": geonames,
            "region": pd.Series(region).reset_index(drop=True)
            if not isinstance(region, str)
            else region,
            "name_ru": name,
            "name_lat": name,
            "is_city": True,
            "notes": notes,
            "pop_1926": np.nan,
            "pop_1939": np.nan,
            "pop_1959": np.nan,
            "modern_pop": np.nan,
            "source": source,
            "country_1956": country,
            "unit_1956": unit,
            "pop": pd.Series(pop, dtype=float).reset_index(drop=True).round(),
            "pop_year": pop_year,
            "pop_prewar": pd.Series(prewar, dtype=float).reset_index(drop=True)
            if not np.isscalar(prewar)
            else prewar,
            "pop_prewar_year": prewar_year,
        }
    )
    df["name_1956"] = df["name_ru"].map(lambda n: RENAMED_1956.get(n, n))
    return df


def east_germany() -> pd.DataFrame:
    d = ddr.parse()
    return frame(
        page="east germany",
        geonames="DE",
        country="East Germany",
        unit="east germany",
        region=d["bezirk"],
        name=d["name"],
        pop=interpolate(d["pop_1955"], d["pop_1956"], "1955-12-31", "1956-12-31"),
        pop_year=1956,
        source="Statistisches Jahrbuch der DDR 1956",
        prewar=d["pop_1939"],
        prewar_year=1939,
    )


def poland() -> pd.DataFrame:
    d = gus.parse()
    region = d["voivodeship"].mask(d["city_voivodeship"], d["name"])
    return frame(
        page="poland",
        geonames="PL",
        country="Poland",
        unit="poland",
        region=region,
        name=d["name"],
        pop=interpolate(d["pop_1950"], d["pop_1956"], "1950-12-03", "1956-12-31"),
        pop_year=1956,
        source="Rocznik Statystyczny 1957",
    )


def hungary() -> pd.DataFrame:
    d = ksh.parse()
    return frame(
        page="hungary",
        geonames="HU",
        country="Hungary",
        unit="hungary",
        region=d["county"],
        name=d["name"],
        pop=interpolate(d["pop_1949"], d["pop_1960"], "1949-01-01", "1960-01-01"),
        pop_year=1956,
        source="KSH 2011 census, historical series",
        prewar=d["pop_1941"],
        prewar_year=1941,
    )


def slovakia() -> pd.DataFrame:
    d = pd.read_csv(CURATED / "gazetteer" / "slovakia_towns_1954_1958.csv")
    return frame(
        page="slovakia",
        geonames="SK",
        country="Czechoslovakia",
        unit="slovakia",
        region="",
        name=d["name"],
        pop=interpolate(
            d["pop_1958"] - d["change_1954_1958"], d["pop_1958"], "1954-01-01", "1958-01-01"
        ),
        pop_year=1956,
        source="Votrubec (1959)",
    )


def china() -> pd.DataFrame:
    tables = pd.read_html(
        io.StringIO((RAW / "wikipedia" / "1953_Chinese_census.html").read_text(encoding="utf-8"))
    )
    d = next(t for t in tables if any(str(c).startswith("City") for c in t.columns))
    pop_col = next(c for c in d.columns if str(c).startswith("Population 1953"))
    region_col = next(c for c in d.columns if str(c).startswith("Province"))
    text = d[pop_col].astype(str)
    pop = pd.to_numeric(text.str.replace(r"[^\d]", "", regex=True), errors="coerce")
    # "Botou（Cangzhou）": the parenthesis names the town's prefecture, not another name.
    name = d["City"].astype(str).str.replace(r"\s*[（(].*?[）)]", "", regex=True)
    name = name.str.replace(r"\s+City$", "", regex=True).str.strip()
    notes = np.where(text.str.startswith(">"), "1953 census gives only a lower bound", "")
    return frame(
        page="china",
        geonames="CN",
        country="China",
        unit="china",
        region=d[region_col].astype(str),
        name=name,
        pop=pop,
        pop_year=1953,
        source="1953 census (Wikipedia, from Shabad 1959)",
        notes=notes,
    )


def wup() -> pd.DataFrame:
    """North Korea, North Vietnam and Mongolia: the UN's 1956 estimates, with their own
    coordinates (no GeoNames match is needed)."""
    with zipfile.ZipFile(RAW / "un" / "WUP2018-Excel-files.zip") as z:
        data = z.read("WUP2018-F22-Cities_Over_300K_Annual.xls")
    d = pd.read_excel(io.BytesIO(data), header=16)
    d = d[d["Country or area"].isin(WUP_COUNTRIES)]
    d = d[(d["Country or area"] != "Viet Nam") | (d["Latitude"] > NORTH_VIETNAM_LAT)]
    parts = []
    for area, group in d.groupby("Country or area"):
        country, code = WUP_COUNTRIES[area]
        f = frame(
            page=country.lower(),
            geonames=code,
            country=country,
            unit=country.lower(),
            region="",
            name=group["Urban Agglomeration"].map(lambda n: re.sub(r"\s*\(.*\)", "", n)),
            pop=group[1956] * 1000,
            pop_year=1956,
            source="UN World Urbanization Prospects 2018 (model estimate)",
        )
        f["lat"] = group["Latitude"].to_numpy()
        f["lon"] = group["Longitude"].to_numpy()
        f["match_method"] = "WUP coordinates"
        parts.append(f)
    return pd.concat(parts, ignore_index=True)
