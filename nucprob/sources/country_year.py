"""Country-year political, economic and military data, 1940-2025, keyed by COW state code.

    python -m nucprob.sources.country_year              # build data/processed/country_year.parquet
    python -m nucprob.sources.country_year --crosswalk  # rewrite data/curated/features/country_codes.csv
    python -m nucprob.sources.country_year --alliances  # rewrite data/curated/features/alliance_membership.csv

Sources (all open; raw files under data/raw/country_year/, listed in
data/sources.d/country_year.yaml; card in data/curated/features/country_year.md):

- political: V-Dem v16 core (polyarchy, liberal democracy, Regimes of the World), Polity5
  (polity2), Boix-Miller-Rosato v4 (democracy 0/1), Lexical Index of Electoral Democracy v5.2;
- economic: Maddison Project Database 2023 (GDP per capita, population);
- military: COW National Material Capabilities v7 (milex, milper, irst, pec, tpop, upop, cinc),
  SIPRI Military Expenditure Database 1949-2025, COW formal alliances v4.1 (NATO, Warsaw Pact,
  US and Soviet defence pacts; NATO after 2012 from nato.int), US troops abroad (Allen, Flynn
  and Machain's troopdata, the rebuilt Kane series), and a hand-curated table of nuclear
  weapon status (first tests, arsenals, hosts of US and Soviet weapons).

The key is (cow_code, year). A (cow_code, year) row exists when the state existed that year: its
COW state-system membership, with the Second World War occupation gaps filled and the FRG,
GDR, Austria and Japan given their post-war years before COW admits them (see EXTENSIONS).
Sources that use other codes are mapped to COW here (POLITY_TO_COW; Maddison by ISO3 with the
territory rules in maddison(); SIPRI by name through the crosswalk).

`lookup(name, year)` resolves a country name (as the project's tables write it, or as any of the
sources write it) through the crosswalk and returns that country-year's row.
"""

import argparse
import io
import re
import unicodedata
import zipfile
from functools import cache

import numpy as np
import pandas as pd

from nucprob.paths import CURATED, PROCESSED, RAW

RAW_DIR = RAW / "country_year"
FEATURES_DIR = CURATED / "features"
CROSSWALK = FEATURES_DIR / "country_codes.csv"
ALLIANCES = FEATURES_DIR / "alliance_membership.csv"
NUCLEAR = FEATURES_DIR / "nuclear_status.csv"
OUT = PROCESSED / "country_year.parquet"

FIRST_YEAR, LAST_YEAR = 1940, 2025
COW_LAST_YEAR = 2024  # COW state list v2024 ends on 31 Dec 2024; states then are carried to 2025
ALLIANCE_LAST_YEAR = 2012  # COW alliances v4.1 end in 2012
UNDATED_HOST_WINDOW = (1955, 1991)  # years a host flag is NA when the host's dates are unknown

VDEM = RAW_DIR / "vdem" / "V-Dem-CY-Core-v16_csv.zip"
POLITY = RAW_DIR / "polity5" / "p5v2018.xls"
BMR = RAW_DIR / "bmr" / "democracy-v4.0.txt"
LIED = RAW_DIR / "lied" / "lied_v5.2.xls"
MADDISON = RAW_DIR / "maddison" / "mpd2023_web.xlsx"
NMC = RAW_DIR / "cow_nmc" / "NMCv7.zip"
SIPRI = RAW_DIR / "sipri" / "SIPRI-Milex-data-1949-2025.xlsx"
ALLIANCE_ZIP = RAW_DIR / "cow_alliance" / "version4.1_csv.zip"
STATES = RAW_DIR / "cow_states" / "States2024.zip"
TROOPS = RAW_DIR / "troopdata" / "troopdata-rebuild-country-year.csv"

# --- codes -----------------------------------------------------------------------------------

# Years a state existed before COW admits it (cow_code: first year, last year, reason).
EXTENSIONS = {
    260: (1949, 1954, "FRG founded 23 May 1949; COW admits it on 5 May 1955"),
    265: (1949, 1953, "GDR founded 7 Oct 1949; COW admits it on 25 Mar 1954"),
    305: (1945, 1954, "Austria under four-power occupation 1945-55; COW gap 1938-55"),
}

# Polity5 codes that differ from COW's.
POLITY_TO_COW = {
    364: 365,  # USSR
    341: 347,  # Kosovo
    342: 345,  # Serbia
    347: 345,  # Yugoslavia (FRY) / Serbia and Montenegro
    348: 341,  # Montenegro
    525: 626,  # South Sudan
    529: 530,  # Ethiopia from 1993
    626: 625,  # Sudan-North
    769: 770,  # Pakistan before 1971
    818: 816,  # Vietnam from 1976
}
# Where two Polity codes map to one COW code in the same year, the higher rank (successor) wins.
POLITY_SUCCESSOR_RANK = {347: 1, 342: 2, 529: 1, 626: 1, 818: 1, 770: 1}

# ISO3 where it changed while the COW code did not, or where COW's state has no default.
ISO3_PERIODS = {
    365: [(FIRST_YEAR, 1991, "SUN"), (1992, LAST_YEAR, "RUS")],
    315: [(FIRST_YEAR, 1992, "CSK")],
    345: [(FIRST_YEAR, 2002, "YUG"), (2003, 2005, "SCG"), (2006, LAST_YEAR, "SRB")],
    255: [(FIRST_YEAR, LAST_YEAR, "DEU")],
    260: [(FIRST_YEAR, LAST_YEAR, "DEU")],
    265: [(FIRST_YEAR, LAST_YEAR, "DDR")],
    816: [(FIRST_YEAR, 1975, "VDR"), (1976, LAST_YEAR, "VNM")],
    817: [(FIRST_YEAR, LAST_YEAR, "VNM")],
    678: [(FIRST_YEAR, LAST_YEAR, "YEM")],
    679: [(FIRST_YEAR, LAST_YEAR, "YEM")],
    680: [(FIRST_YEAR, LAST_YEAR, "YMD")],
    347: [(FIRST_YEAR, LAST_YEAR, "XKX")],  # Kosovo: user-assigned code, not ISO
}

# Names the project's own tables use (target_country, country_1956, country columns; bloc.py),
# with their codes and years. "Germany" in a Cold War table means the FRG.
PROJECT_NAMES = [
    ("USSR", 365, 1922, 1991, ""),
    ("Soviet Union", 365, 1922, 1991, ""),
    ("Russia", 365, 1992, LAST_YEAR, "Russian Federation; same COW code as the USSR"),
    ("East Germany", 265, 1949, 1990, ""),
    ("GDR", 265, 1949, 1990, ""),
    ("FRG", 260, 1949, 1990, ""),
    ("West Germany", 260, 1949, 1990, ""),
    ("Germany", 255, FIRST_YEAR, 1945, ""),
    ("Germany", 260, 1949, 1990, "in Cold War tables 'Germany' means the FRG"),
    ("Germany", 255, 1991, LAST_YEAR, "unified Germany from 3 Oct 1990 (COW 255)"),
    ("DE", 260, 1949, 1990, "ISO2 code as used in feature tables"),
    ("DE", 255, 1991, LAST_YEAR, "ISO2 code as used in feature tables"),
    ("Czechoslovakia", 315, FIRST_YEAR, 1992, ""),
    ("Yugoslavia", 345, FIRST_YEAR, 2002, "FRY kept the name until Feb 2003"),
    ("Serbia and Montenegro", 345, 2003, 2006, ""),
    ("China", 710, FIRST_YEAR, LAST_YEAR, "Republic of China to 1949, PRC after"),
    ("PRC", 710, 1949, LAST_YEAR, ""),
    ("China (Manchuria)", 710, 1949, LAST_YEAR, "region of the PRC"),
    ("North Korea", 731, 1948, LAST_YEAR, ""),
    ("North Vietnam", 816, 1954, 1975, "DRV; continues as Vietnam (816)"),
    ("South Vietnam", 817, 1954, 1975, ""),
    ("Vietnam", 816, 1976, LAST_YEAR, ""),
    ("Mongolia", 712, FIRST_YEAR, LAST_YEAR, ""),
    ("Poland", 290, FIRST_YEAR, LAST_YEAR, ""),
    ("Hungary", 310, FIRST_YEAR, LAST_YEAR, ""),
    ("Romania", 360, FIRST_YEAR, LAST_YEAR, ""),
    ("Bulgaria", 355, FIRST_YEAR, LAST_YEAR, ""),
    ("Albania", 339, FIRST_YEAR, LAST_YEAR, ""),
    ("UK", 200, FIRST_YEAR, LAST_YEAR, ""),
    ("United Kingdom", 200, FIRST_YEAR, LAST_YEAR, ""),
    ("England", 200, FIRST_YEAR, LAST_YEAR, "constituent country of the UK"),
    ("Scotland", 200, FIRST_YEAR, LAST_YEAR, "constituent country of the UK"),
    ("Wales", 200, FIRST_YEAR, LAST_YEAR, "constituent country of the UK"),
    ("Northern Ireland", 200, FIRST_YEAR, LAST_YEAR, "part of the UK"),
    ("USA", 2, FIRST_YEAR, LAST_YEAR, ""),
    ("United States", 2, FIRST_YEAR, LAST_YEAR, ""),
    ("United States (Alaska)", 2, FIRST_YEAR, LAST_YEAR, "territory until 1959, then state"),
    ("USA (Territory of Alaska)", 2, FIRST_YEAR, 1958, "statehood 3 Jan 1959"),
    ("USA (Territory of Hawaii)", 2, FIRST_YEAR, 1959, "statehood 21 Aug 1959"),
    ("USA (Puerto Rico)", 2, FIRST_YEAR, LAST_YEAR, "US territory"),
    ("Puerto Rico", 2, FIRST_YEAR, LAST_YEAR, "US territory"),
    ("Guam", 2, FIRST_YEAR, LAST_YEAR, "US territory (Japanese-occupied Dec 1941-Aug 1944)"),
    ("Panama Canal Zone (US)", 2, FIRST_YEAR, 1979, "US-administered until 1 Oct 1979"),
    ("Canada", 20, FIRST_YEAR, LAST_YEAR, ""),
    (
        "Canada (Labrador)",
        20,
        1949,
        LAST_YEAR,
        "part of Newfoundland, which joined Canada 31 Mar 1949",
    ),
    ("Canada (Newfoundland)", 20, 1949, LAST_YEAR, "joined Canada 31 Mar 1949"),
    ("Japan", 740, FIRST_YEAR, LAST_YEAR, ""),
    ("Denmark", 390, FIRST_YEAR, LAST_YEAR, ""),
    ("DK", 390, FIRST_YEAR, LAST_YEAR, "ISO2"),
    ("Greenland", 390, FIRST_YEAR, LAST_YEAR, "Danish territory"),
    ("Netherlands", 210, FIRST_YEAR, LAST_YEAR, ""),
    ("NL", 210, FIRST_YEAR, LAST_YEAR, "ISO2"),
    ("Belgium", 211, FIRST_YEAR, LAST_YEAR, ""),
    ("BE", 211, FIRST_YEAR, LAST_YEAR, "ISO2"),
    ("Austria", 305, 1945, LAST_YEAR, ""),
    ("AT", 305, 1945, LAST_YEAR, "ISO2"),
    ("Italy", 325, FIRST_YEAR, LAST_YEAR, ""),
    ("IT", 325, FIRST_YEAR, LAST_YEAR, "ISO2"),
    ("France", 220, FIRST_YEAR, LAST_YEAR, ""),
    ("FR", 220, FIRST_YEAR, LAST_YEAR, "ISO2"),
    ("Morocco", 600, 1956, LAST_YEAR, "French/Spanish protectorate until 1956"),
    ("Taiwan", 713, 1949, LAST_YEAR, "Republic of China on Taiwan"),
    ("South Korea", 732, 1948, LAST_YEAR, ""),
    ("Cuba", 40, FIRST_YEAR, LAST_YEAR, ""),
    ("Sino-Soviet Bloc", None, FIRST_YEAR, LAST_YEAR, "aggregate; no single country"),
]

# Names the sources use that do not match a COW, V-Dem, Polity or troopdata name for the same
# code. (name, cow_code, first year, last year)
EXTRA_ALIASES = [
    ("Congo, DR", 490, 1960, LAST_YEAR),
    ("Congo, Republic", 484, 1960, LAST_YEAR),
    ("Gambia, The", 420, 1965, LAST_YEAR),
    ("Korea, North", 731, 1948, LAST_YEAR),
    ("Korea, South", 732, 1948, LAST_YEAR),
    ("Viet Nam", 816, 1976, LAST_YEAR),
    ("Kyrgyz Republic", 703, 1991, LAST_YEAR),
    ("Czechia", 316, 1993, LAST_YEAR),
    ("German Democratic Republic", 265, 1949, 1990),
    ("North Macedonia", 343, 1993, LAST_YEAR),
    ("Türkiye", 640, FIRST_YEAR, LAST_YEAR),
    ("Turkey", 640, FIRST_YEAR, LAST_YEAR),
    ("Yemen, North", 678, FIRST_YEAR, 1989),
    ("Yemen", 679, 1990, LAST_YEAR),
    ("Timor Leste", 860, 2002, LAST_YEAR),
    ("Eswatini", 572, 1968, LAST_YEAR),
    ("Cape Verde", 402, 1975, LAST_YEAR),
    ("Brunei", 835, 1984, LAST_YEAR),
    ("Laos", 812, 1953, LAST_YEAR),
    ("Bosnia and Herzegovina", 346, 1992, LAST_YEAR),
    ("Cote d'Ivoire", 437, 1960, LAST_YEAR),
    ("Serbia", 345, 1992, LAST_YEAR),
    ("Montenegro", 341, 2006, LAST_YEAR),
    ("Kosovo", 347, 2008, LAST_YEAR),
]

NMC_COLUMNS = ["milex", "milper", "irst", "pec", "tpop", "upop", "cinc"]
SIPRI_SHEETS = {
    "sipri_milex_usd2024": "Constant (2024) US$",
    "sipri_milex_usd": "Current US$",
    "sipri_milex_gdp": "Share of GDP",
}

# Column documentation (also printed in the card).
COLUMNS = {
    "cow_code": "Correlates of War state code (key)",
    "year": "calendar year (key)",
    "iso3": "ISO 3166 alpha-3 valid that year (SUN, CSK, YUG, DDR, VDR, YMD, SCG for former states)",
    "country": "COW state name",
    "cow_member": "1 if a COW state-system member at any time in the year (else 0: an extension year)",
    "vdem_polyarchy": "V-Dem electoral democracy index v2x_polyarchy, 0-1",
    "vdem_libdem": "V-Dem liberal democracy index v2x_libdem, 0-1",
    "vdem_regime": "V-Dem Regimes of the World v2x_regime: 0 closed autocracy, 1 electoral autocracy, "
    "2 electoral democracy, 3 liberal democracy",
    "polity2": "Polity5 polity2, -10 (autocracy) to +10 (democracy); to 2018",
    "bmr_democracy": "Boix-Miller-Rosato v4 dichotomous democracy (1 = democracy); to 2015",
    "lied_lexical": "Lexical Index of Electoral Democracy v5.2, 0-6; to 2019",
    "mad_gdppc": "Maddison 2023 GDP per capita, 2011 international dollars; to 2022",
    "mad_pop": "Maddison 2023 population, thousands; to 2022",
    "nmc_milex": "COW NMC v7 military expenditure, thousands of current US$ (pre-1914 pounds converted)",
    "nmc_milper": "COW NMC v7 military personnel, thousands",
    "nmc_irst": "COW NMC v7 iron and steel production, thousands of tons",
    "nmc_pec": "COW NMC v7 primary energy consumption, thousands of coal-ton equivalents",
    "nmc_tpop": "COW NMC v7 total population, thousands",
    "nmc_upop": "COW NMC v7 urban population (cities over 100,000), thousands",
    "nmc_cinc": "COW NMC v7 Composite Index of National Capability, share of the system (0-1)",
    "sipri_milex_usd2024": "SIPRI military expenditure, US$ million at constant 2024 prices",
    "sipri_milex_usd": "SIPRI military expenditure, US$ million at current prices",
    "sipri_milex_gdp": "SIPRI military expenditure as a share of GDP (fraction, 0.05 = 5%)",
    "us_troops": "US active-duty troops in the country, highest value reported in the year "
    "(troopdata); for the USA itself, troops at home",
    "nato": "member of NATO at any time in the year",
    "warsaw_pact": "member of the Warsaw Pact at any time in the year",
    "us_defense_pact": "in a COW defence pact with the USA (NATO, Rio, ANZUS, bilaterals...); NA after 2012",
    "us_bilateral_pact": "in a bilateral COW defence pact with the USA; NA after 2012",
    "ussr_defense_pact": "in a COW defence pact with the USSR/Russia; NA after 2012",
    "nuc_first_test_year": "year of the state's first nuclear test (constant; NA if none)",
    "nuc_tested": "1 if the state had tested a nuclear device by this year",
    "nuc_arsenal": "1 if the state held its own nuclear weapons this year (approximate starts flagged in "
    "nuclear_status.csv)",
    "nuc_inherited": "1 if Soviet weapons were left on its territory after 1991 (Ukraine, Kazakhstan, Belarus)",
    "host_us_nukes": "1 if US nuclear weapons or components were stored in the country (Norris, Arkin and "
    "Burr 1999); NA where the end date is unknown",
    "host_ussr_nukes": "1 if Soviet/Russian weapons were stationed there; NA in 1955-1991 for the hosts whose "
    "dates are unknown (GDR, Czechoslovakia, Hungary, Poland, Mongolia)",
}


# --- helpers ---------------------------------------------------------------------------------


def norm(name: str) -> str:
    """Case-, accent- and punctuation-insensitive form of a country name."""
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9()]+", " ", text).strip()


def _zip_csv(path, member, **kw) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        return pd.read_csv(z.open(member), **kw)


def _span(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """First and last year per group (years from FIRST_YEAR)."""
    df = df[df.year >= FIRST_YEAR]
    return df.groupby(by).year.agg(["min", "max"]).reset_index()


# --- states and the universe -----------------------------------------------------------------


@cache
def states() -> pd.DataFrame:
    """COW state-system membership periods (ccode, stateabb, statenme, styear, endyear)."""
    st = _zip_csv(STATES, "States2024/statelist2024.csv", encoding="latin1")
    st = st[["ccode", "stateabb", "statenme", "styear", "endyear"]].copy()
    st.loc[st.endyear >= COW_LAST_YEAR, "endyear"] = LAST_YEAR
    return st


def state_periods() -> pd.DataFrame:
    """Periods a state existed for this panel: COW membership, Second World War occupation
    gaps (starting 1939 or later and ending by 1955) filled, plus EXTENSIONS."""
    rows = []
    for _code, g in states().sort_values("styear").groupby("ccode"):
        g = g.to_dict("records")
        for i, r in enumerate(g):
            rows.append({**r, "kind": "cow_state"})
            if i + 1 < len(g):
                gap = (r["endyear"], g[i + 1]["styear"])
                if gap[0] >= 1939 and gap[1] <= 1955:
                    rows.append({**r, "styear": gap[0], "endyear": gap[1], "kind": "gap_filled"})
    names = states().drop_duplicates("ccode", keep="last").set_index("ccode")
    for code, (y0, y1, _why) in EXTENSIONS.items():
        rows.append(
            {
                "ccode": code,
                "stateabb": names.stateabb[code],
                "statenme": names.statenme[code],
                "styear": y0,
                "endyear": y1,
                "kind": "extension",
            }
        )
    return pd.DataFrame(rows)


def universe() -> pd.DataFrame:
    """One row per (cow_code, year) that existed, FIRST_YEAR-LAST_YEAR, with the COW name and
    whether COW counted it as a member that year."""
    rows = {}
    for r in state_periods().itertuples():
        for y in range(max(r.styear, FIRST_YEAR), min(r.endyear, LAST_YEAR) + 1):
            key = (r.ccode, y)
            member = r.kind == "cow_state"
            old = rows.get(key)
            rows[key] = (r.statenme, member or (old[1] if old else False))
    df = pd.DataFrame(
        [(c, y, n, int(m)) for (c, y), (n, m) in rows.items()],
        columns=["cow_code", "year", "country", "cow_member"],
    )
    df["iso3"] = [iso3(c, y) for c, y in zip(df.cow_code, df.year, strict=True)]
    return df.sort_values(["cow_code", "year"]).reset_index(drop=True)


@cache
def _default_iso3() -> dict[int, str]:
    """ISO3 per COW code from troopdata (countrycode's mapping), V-Dem's text ids as fallback."""
    t = pd.read_csv(TROOPS, usecols=["ccode", "iso3c"]).dropna()
    out = t.groupby("ccode").iso3c.agg(lambda s: s.mode().iloc[0]).to_dict()
    v = _vdem_ids()
    for code, tid in v.items():
        out.setdefault(code, tid)
    return {int(k): v for k, v in out.items()}


@cache
def _vdem_ids() -> dict[int, str]:
    v = _zip_csv(VDEM, "V-Dem-CY-Core-v16.csv", usecols=["country_text_id", "COWcode", "year"])
    v = v.dropna().sort_values("year")
    return {int(c): t for c, t in v.groupby("COWcode").country_text_id.last().items()}


def iso3(cow_code: int, year: int) -> str | None:
    for y0, y1, code in ISO3_PERIODS.get(cow_code, []):
        if y0 <= year <= y1:
            return code
    return _default_iso3().get(cow_code)


# --- political -------------------------------------------------------------------------------


def vdem() -> pd.DataFrame:
    cols = ["COWcode", "year", "v2x_polyarchy", "v2x_libdem", "v2x_regime"]
    v = _zip_csv(VDEM, "V-Dem-CY-Core-v16.csv", usecols=cols).dropna(subset=["COWcode"])
    v = v.rename(
        columns={
            "COWcode": "cow_code",
            "v2x_polyarchy": "vdem_polyarchy",
            "v2x_libdem": "vdem_libdem",
            "v2x_regime": "vdem_regime",
        }
    )
    v["cow_code"] = v.cow_code.astype(int)
    return v


def polity() -> pd.DataFrame:
    """Polity5 polity2 on COW codes. In a transition year Polity has a row for both the old and
    the new entity (SFRY and FRY in 1991, Ethiopia in 1993...); the successor's is kept."""
    p = pd.read_excel(POLITY, usecols=["ccode", "year", "polity2"])
    return _polity_codes_to_cow(p)[["cow_code", "year", "polity2"]]


def _polity_codes_to_cow(df: pd.DataFrame) -> pd.DataFrame:
    """Map Polity-style codes (column ccode) to COW, keeping the successor in transition years."""
    df = df.dropna(subset=["ccode"]).copy()
    df["cow_code"] = df.ccode.map(lambda c: POLITY_TO_COW.get(int(c), int(c))).astype(int)
    df["rank"] = df.ccode.map(POLITY_SUCCESSOR_RANK).fillna(0)
    return df.sort_values("rank").drop_duplicates(["cow_code", "year"], keep="last")


def bmr() -> pd.DataFrame:
    """BMR v4 uses Polity's codes for the USSR (364), Vietnam (818), Ethiopia (529) etc."""
    b = pd.read_csv(BMR, sep=" ", usecols=["ccode", "year", "democracy"])
    b = _polity_codes_to_cow(b).rename(columns={"democracy": "bmr_democracy"})
    return b[["cow_code", "year", "bmr_democracy"]]


def lied() -> pd.DataFrame:
    lx = pd.read_excel(LIED, usecols=["cow", "year", "lexical_index"])
    lx = lx.rename(columns={"cow": "cow_code", "lexical_index": "lied_lexical"})
    lx = lx.dropna(subset=["cow_code"]).astype({"cow_code": int})
    return lx.drop_duplicates()  # v5.2 repeats Japan 2018 with the same values


# --- economic --------------------------------------------------------------------------------


def maddison() -> pd.DataFrame:
    """Maddison series are for each country's present territory (Germany is all of Germany,
    Vietnam all of Vietnam) or a former state's whole territory (SUN, CSK, YUG). So DEU is
    not used for 1949-90 (no separate FRG/GDR series), VNM only from 1976, SUN, CSK and YUG
    only while those states existed, and SRB (Serbia alone) for COW 345 from 1992."""
    m = pd.read_excel(MADDISON, sheet_name="Full data")
    m = m[m.year >= FIRST_YEAR]
    keep = ~(
        ((m.countrycode == "DEU") & m.year.between(1949, 1990))
        | ((m.countrycode == "VNM") & (m.year < 1976))
        | ((m.countrycode == "SUN") & (m.year > 1991))
        | ((m.countrycode == "RUS") & (m.year <= 1991))
        | ((m.countrycode == "CSK") & (m.year > 1992))
        | ((m.countrycode == "YUG") & (m.year > 1991))
        | ((m.countrycode == "SRB") & (m.year <= 1991))
    )
    m = m[keep]
    special = {"SUN": 365, "RUS": 365, "CSK": 315, "YUG": 345, "SRB": 345, "DEU": 255, "VNM": 816}
    u = universe()[["cow_code", "year", "iso3"]].drop_duplicates(["iso3", "year"], keep=False)
    by_iso = u.set_index(["iso3", "year"]).cow_code
    m["cow_code"] = [
        special.get(c, by_iso.get((c, y))) for c, y in zip(m.countrycode, m.year, strict=True)
    ]
    m.loc[(m.countrycode == "YEM") & (m.year < 1990), "cow_code"] = 678  # North Yemen
    m.loc[(m.countrycode == "YEM") & (m.year >= 1990), "cow_code"] = 679
    m = m.dropna(subset=["cow_code"]).astype({"cow_code": int})
    return m.rename(columns={"gdppc": "mad_gdppc", "pop": "mad_pop"})[
        ["cow_code", "year", "mad_gdppc", "mad_pop"]
    ]


# --- military --------------------------------------------------------------------------------


def nmc() -> pd.DataFrame:
    with zipfile.ZipFile(NMC) as z:
        inner = zipfile.ZipFile(io.BytesIO(z.read("NMCv7/NMC-v7-abridged.zip")))
        n = pd.read_csv(inner.open("NMC-70-abridged.csv"))
    n[NMC_COLUMNS] = n[NMC_COLUMNS].where(n[NMC_COLUMNS] != -9)
    n = n.rename(columns={"ccode": "cow_code", **{c: f"nmc_{c}" for c in NMC_COLUMNS}})
    return n[["cow_code", "year", *[f"nmc_{c}" for c in NMC_COLUMNS]]]


def _sipri_sheet(sheet: str, value: str) -> pd.DataFrame:
    raw = pd.read_excel(SIPRI, sheet_name=sheet, header=None)
    header = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "Country"][0]
    df = raw.iloc[header + 1 :].copy()
    df.columns = raw.iloc[header].tolist()
    years = [c for c in df.columns if isinstance(c, (int, float)) and not pd.isna(c)]
    df = df[["Country", *years]].dropna(subset=["Country"])
    long = df.melt(id_vars="Country", var_name="year", value_name=value)
    long["year"] = long.year.astype(int)
    long[value] = pd.to_numeric(long[value], errors="coerce")
    return long.dropna(subset=[value])


def sipri() -> pd.DataFrame:
    """SIPRI's three main sheets, matched to COW codes by name and year through the crosswalk
    (regional totals and other non-country rows find no match and are dropped)."""
    out = None
    for col, sheet in SIPRI_SHEETS.items():
        s = _sipri_sheet(sheet, col)
        out = s if out is None else out.merge(s, on=["Country", "year"], how="outer")
    out["cow_code"] = [_resolve(n, y) for n, y in zip(out.Country, out.year, strict=True)]
    out = out.dropna(subset=["cow_code"]).astype({"cow_code": int})
    return out.drop(columns="Country")


def troops() -> pd.DataFrame:
    """US active-duty troops by host country. troopdata codes West Germany as 255 throughout,
    so 255 is moved to 260 for 1949-1990, and Vietnam as 816, so 816 up to 1975 is moved to
    South Vietnam (817); duplicate name variants keep the larger value."""
    t = pd.read_csv(TROOPS, usecols=["ccode", "year", "troops_ad"])
    t.loc[(t.ccode == 255) & t.year.between(1949, 1990), "ccode"] = 260
    t.loc[(t.ccode == 816) & (t.year <= 1975), "ccode"] = 817  # US troops were in the South
    t = t.groupby(["ccode", "year"], as_index=False).troops_ad.max()
    return t.rename(columns={"ccode": "cow_code", "troops_ad": "us_troops"})


# --- alliances -------------------------------------------------------------------------------

NATO_ID, WARSAW_ID = 227, 243
# NATO accessions missing from COW v4.1, which lacks the 2004 and 2009 enlargements and ends
# in 2012 (nato.int, "NATO member countries": member and year of accession, with the deposit
# date where the page gives it).
NATO_NOT_IN_COW = [
    (355, "Bulgaria", "2004"),
    (366, "Estonia", "2004"),
    (367, "Latvia", "2004"),
    (368, "Lithuania", "2004"),
    (360, "Romania", "2004"),
    (317, "Slovakia", "2004"),
    (349, "Slovenia", "2004"),
    (339, "Albania", "2009"),
    (344, "Croatia", "2009"),
    (341, "Montenegro", "2017-06-05"),
    (343, "North Macedonia", "2020"),
    (375, "Finland", "2023-04-04"),
    (380, "Sweden", "2024-03-07"),
]


def _date(y, m, d) -> str:
    if pd.isna(y):
        return ""
    parts = [int(y)] + [int(x) for x in (m, d) if not pd.isna(x)]
    return "-".join(f"{p:04d}" if i == 0 else f"{p:02d}" for i, p in enumerate(parts))


def build_alliances() -> pd.DataFrame:
    """Membership of NATO, the Warsaw Pact and every COW defence pact with the USA or the
    USSR/Russia in force after 1940, with membership start and end dates."""
    a = _zip_csv(ALLIANCE_ZIP, "version4.1_csv/alliance_v4.1_by_member.csv", encoding="latin1")
    # A defence pact can be asymmetric (the US-Japan treaty binds only the US), so a pact
    # counts when any member's obligation is a defence one, and all its members are kept.
    a = a[a.version4id.isin(a.version4id[a.defense == 1])]
    a = a[a.mem_end_year.isna() | (a.mem_end_year >= FIRST_YEAR)]
    size = a.groupby("version4id").ccode.nunique()
    rows = []
    for partner, bloc in ((2, "us_defense"), (365, "ussr_defense")):
        ids = set(a.version4id[a.ccode == partner])
        for r in a[a.version4id.isin(ids) & (a.ccode != partner)].itertuples():
            name = {NATO_ID: "nato", WARSAW_ID: "warsaw_pact"}.get(r.version4id)
            for b in filter(None, (bloc, name)):
                rows.append(
                    {
                        "cow_code": r.ccode,
                        "country": r.state_name,
                        "bloc": b,
                        "alliance_id": r.version4id,
                        "bilateral": int(size[r.version4id] == 2),
                        "start_date": _date(r.mem_st_year, r.mem_st_month, r.mem_st_day),
                        "end_date": _date(r.mem_end_year, r.mem_end_month, r.mem_end_day),
                        "right_censored": int(r.right_censor == 1),
                        "source": "COW alliances v4.1",
                    }
                )
    for code, name, start in NATO_NOT_IN_COW:
        rows.append(
            {
                "cow_code": code,
                "country": name,
                "bloc": "nato",
                "alliance_id": NATO_ID,
                "bilateral": 0,
                "start_date": start,
                "end_date": "",
                "right_censored": 1,
                "source": "nato.int member countries",
            }
        )
    # COW ends Hungary's Warsaw Pact membership on 15 Nov 1956 (Nagy's withdrawal) and never
    # restores it; the Kadar government reversed the withdrawal, so Hungary is put back until
    # 1989, the year COW ends the other members' commitments.
    rows.append(
        {
            "cow_code": 310,
            "country": "Hungary",
            "bloc": "warsaw_pact",
            "alliance_id": WARSAW_ID,
            "bilateral": 0,
            "start_date": "1956-11-15",
            "end_date": "1989",
            "right_censored": 0,
            "source": "hand correction (withdrawal of Nov 1956 reversed)",
        }
    )
    # The US and USSR themselves are members of their blocs.
    for code, name, b, start, end in (
        (2, "United States of America", "nato", "1949-08-24", ""),
        (365, "Russia", "warsaw_pact", "1955-06-04", "1991-07-01"),
    ):
        src = a[(a.ccode == code) & (a.version4id == {"nato": NATO_ID}.get(b, WARSAW_ID))]
        r = src.iloc[0]
        rows.append(
            {
                "cow_code": code,
                "country": name,
                "bloc": b,
                "alliance_id": r.version4id,
                "bilateral": 0,
                "start_date": _date(r.mem_st_year, r.mem_st_month, r.mem_st_day) or start,
                "end_date": _date(r.mem_end_year, r.mem_end_month, r.mem_end_day) or end,
                "right_censored": int(r.right_censor == 1),
                "source": "COW alliances v4.1",
            }
        )
    df = pd.DataFrame(rows).drop_duplicates()
    return df.sort_values(["bloc", "cow_code", "start_date"]).reset_index(drop=True)


def _year(date: str) -> int | None:
    return int(date[:4]) if isinstance(date, str) and date else None


def alliance_flags(panel: pd.DataFrame) -> pd.DataFrame:
    """Per (cow_code, year): member at any time in the year. NATO memberships still open in
    2012 continue to LAST_YEAR (checked against nato.int's list); other open pacts are NA after
    ALLIANCE_LAST_YEAR."""
    al = pd.read_csv(ALLIANCES, dtype={"start_date": str, "end_date": str}, keep_default_na=False)
    out = panel[["cow_code", "year"]].copy()
    cols = {
        "nato": al.bloc == "nato",
        "warsaw_pact": al.bloc == "warsaw_pact",
        "us_defense_pact": al.bloc == "us_defense",
        "us_bilateral_pact": (al.bloc == "us_defense") & (al.bilateral == 1),
        "ussr_defense_pact": al.bloc == "ussr_defense",
    }
    for col, mask in cols.items():
        flag = pd.Series(0.0, index=out.index)
        for r in al[mask].itertuples():
            y0 = _year(r.start_date)
            y1 = _year(r.end_date) or LAST_YEAR
            hit = (out.cow_code == r.cow_code) & out.year.between(y0, y1)
            flag[hit] = 1.0
        if col not in ("nato", "warsaw_pact"):
            flag[out.year > ALLIANCE_LAST_YEAR] = np.nan
        out[col] = flag
    return out


# --- nuclear ---------------------------------------------------------------------------------


def nuclear_flags(panel: pd.DataFrame) -> pd.DataFrame:
    """Flags from the curated nuclear_status.csv. A host row with no end year sets 1 in its
    start year and NA after, unless its precision says it continues (blank end with a known
    start and precision day/month/year/approx/reported means "continuing")."""
    nu = pd.read_csv(NUCLEAR, keep_default_na=False)
    out = panel[["cow_code", "year"]].copy()
    first = (
        pd.to_numeric(nu[nu.role == "first_test"].set_index("cow_code").start_year)
        .groupby(level=0)
        .min()
    )
    out["nuc_first_test_year"] = out.cow_code.map(first).astype("Float64")
    out["nuc_tested"] = (out.year >= out.nuc_first_test_year).astype("Float64").fillna(0)
    for col, roles, base in (
        ("nuc_arsenal", {"arsenal"}, 0.0),
        ("nuc_inherited", {"inherited"}, 0.0),
        ("host_us_nukes", {"host_us"}, 0.0),
        ("host_ussr_nukes", {"host_ussr"}, 0.0),
    ):
        flag = pd.Series(base, index=out.index)
        flag[out.year < 1945] = 0.0
        for r in nu[nu.role.isin(roles)].itertuples():
            rows = out.cow_code == r.cow_code
            if r.start_year == "":
                lo, hi = UNDATED_HOST_WINDOW
                flag[rows & out.year.between(lo, hi) & (flag != 1)] = np.nan
                continue
            y0 = int(r.start_year)
            if r.end_year != "":
                flag[rows & out.year.between(y0, int(r.end_year))] = 1.0
            elif r.precision == "unknown_end":
                flag[rows & (out.year == y0)] = 1.0
                flag[rows & (out.year > y0) & (flag != 1)] = np.nan
            else:
                flag[rows & (out.year >= y0)] = 1.0
        out[col] = flag
    return out


# --- crosswalk -------------------------------------------------------------------------------


def _source_aliases() -> pd.DataFrame:
    """(name, cow_code, first, last, source) for every name the coded sources use."""
    v = _zip_csv(VDEM, "V-Dem-CY-Core-v16.csv", usecols=["country_name", "COWcode", "year"])
    v = _span(v.dropna(), ["country_name", "COWcode"]).assign(source="V-Dem v16")
    v.columns = ["name", "cow_code", "start_year", "end_year", "source"]
    p = pd.read_excel(POLITY, usecols=["ccode", "country", "year"])
    p["ccode"] = p.ccode.map(lambda c: POLITY_TO_COW.get(c, c))
    p = _span(p, ["country", "ccode"]).assign(source="Polity5")
    p.columns = v.columns
    t = pd.read_csv(TROOPS, usecols=["countryname", "ccode", "year"])
    t = _span(t, ["countryname", "ccode"]).assign(source="troopdata")
    t.columns = v.columns
    b = pd.read_csv(BMR, sep=" ", usecols=["country", "ccode", "year"]).dropna()
    b["ccode"] = b.ccode.map(lambda c: POLITY_TO_COW.get(int(c), int(c)))
    b = _span(b, ["country", "ccode"]).assign(source="BMR v4")
    b.columns = v.columns
    extra = pd.DataFrame(EXTRA_ALIASES, columns=["name", "cow_code", "start_year", "end_year"])
    extra["source"] = "hand (SIPRI and other spellings)"
    out = pd.concat([v, p, t, b, extra], ignore_index=True)
    return out[out.cow_code.isin(states().ccode)]  # troopdata's territory codes (1000+) etc.


def _split_by_iso(rows: list[dict]) -> list[dict]:
    """Split each name row where its code's ISO3 changes, so every row has one iso3."""
    out = []
    for r in rows:
        if r["cow_code"] is None or pd.isna(r["cow_code"]):
            out.append({**r, "cow_code": None, "iso3": ""})
            continue
        code, y, start = int(r["cow_code"]), r["start_year"], r["start_year"]
        current = iso3(code, y)
        for y in range(r["start_year"], r["end_year"] + 1):
            if iso3(code, y) != current:
                out.append({**r, "start_year": start, "end_year": y - 1, "iso3": current or ""})
                start, current = y, iso3(code, y)
        out.append({**r, "start_year": start, "end_year": r["end_year"], "iso3": current or ""})
    return out


def build_crosswalk() -> pd.DataFrame:
    """Names to COW code and ISO3 with the years each mapping holds. `kind`: project (names
    in the project's tables), cow_state (COW state list, gaps filled and extended), alias (how
    another source spells it)."""
    rows = [
        {
            "name": n,
            "cow_code": c,
            "start_year": max(a, FIRST_YEAR),
            "end_year": b,
            "kind": "project",
            "source": "project tables",
            "note": note,
        }
        for n, c, a, b, note in PROJECT_NAMES
    ]
    notes = {k: why for k, (_a, _b, why) in EXTENSIONS.items()}
    for r in state_periods().itertuples():
        if r.endyear < FIRST_YEAR:
            continue
        rows.append(
            {
                "name": r.statenme,
                "cow_code": r.ccode,
                "start_year": max(r.styear, FIRST_YEAR),
                "end_year": r.endyear,
                "kind": "cow_state",
                "source": {
                    "cow_state": "COW states 2024",
                    "gap_filled": "COW states 2024 (WWII gap filled)",
                }.get(r.kind, "extension"),
                "note": notes.get(r.ccode, "") if r.kind == "extension" else "",
            }
        )
    for r in _source_aliases().itertuples():
        rows.append(
            {
                "name": r.name,
                "cow_code": int(r.cow_code),
                "start_year": int(r.start_year),
                "end_year": int(r.end_year),
                "kind": "alias",
                "source": r.source,
                "note": "",
            }
        )
    df = pd.DataFrame(_split_by_iso(rows))
    df["cow_abb"] = df.cow_code.map(
        states().drop_duplicates("ccode", keep="last").set_index("ccode").stateabb
    )
    df = df[
        ["name", "cow_code", "cow_abb", "iso3", "start_year", "end_year", "kind", "source", "note"]
    ]
    # One row per (name, code, years): keep the first kind (project > cow_state > alias) and
    # merge the sources that agree.
    order = {"project": 0, "cow_state": 1, "alias": 2}
    df["_o"] = df.kind.map(order)
    df = df.sort_values(["_o", "name", "start_year"])
    df["cow_code"] = df.cow_code.astype("Int64")
    key = ["name", "cow_code", "start_year", "end_year"]
    agg = df.groupby(key, dropna=False, sort=False).agg(
        cow_abb=("cow_abb", "first"),
        iso3=("iso3", "first"),
        kind=("kind", "first"),
        source=("source", lambda s: "; ".join(dict.fromkeys(s))),
        note=("note", lambda s: "; ".join(x for x in dict.fromkeys(s) if x)),
        _o=("_o", "first"),
    )
    agg = agg.reset_index().sort_values(["_o", "name", "start_year"]).drop(columns="_o")
    return agg[
        ["name", "cow_code", "cow_abb", "iso3", "start_year", "end_year", "kind", "source", "note"]
    ]


@cache
def crosswalk() -> pd.DataFrame:
    cw = pd.read_csv(CROSSWALK, dtype={"cow_code": "Int64"}, keep_default_na=False, na_values=[""])
    cw["key"] = cw.name.map(norm)
    return cw


def _resolve(name: str, year: int) -> int | None:
    """COW code for a name in a year, or None. Project names win over COW names over aliases.
    A name that sources use for two states in the same year ('Vietnam' before 1976, 'Yemen'
    before 1990) gives None; use the project or COW name instead."""
    cw = crosswalk()
    hit = cw[(cw.key == norm(name)) & (cw.start_year <= year) & (cw.end_year >= year)]
    for kind in ("project", "cow_state", "alias"):
        codes = hit[hit.kind == kind].cow_code.dropna().unique()
        if len(codes) == 1:
            return int(codes[0])
        if len(codes) > 1:
            if kind == "alias":
                return None
            raise ValueError(f"{name!r} in {year} is ambiguous: COW {sorted(codes)}")
    return None


# --- build and lookup ------------------------------------------------------------------------


def build() -> pd.DataFrame:
    """Join every source onto the universe and write data/processed/country_year.parquet."""
    panel = universe()
    for part in (vdem(), polity(), bmr(), lied(), maddison(), nmc(), sipri(), troops()):
        part = part[part.year.between(FIRST_YEAR, LAST_YEAR)]
        dup = part.duplicated(["cow_code", "year"])
        assert not dup.any(), f"duplicate keys: {part[dup].head()}"
        panel = panel.merge(part, on=["cow_code", "year"], how="left")
    panel = panel.merge(alliance_flags(panel), on=["cow_code", "year"])
    panel = panel.merge(nuclear_flags(panel), on=["cow_code", "year"])
    panel = panel[list(COLUMNS)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT, index=False)
    return panel


@cache
def _panel() -> pd.DataFrame:
    return pd.read_parquet(OUT).set_index(["cow_code", "year"])


def lookup(country_name: str, year: int) -> pd.Series | None:
    """The country-year row for a name as any project table or source writes it, or None if
    the name maps to no state that year (e.g. 'Sino-Soviet Bloc', or Morocco before 1956)."""
    code = _resolve(country_name, year)
    if code is None:
        return None
    try:
        row = _panel().loc[(code, year)]
    except KeyError:
        return None
    return pd.concat([pd.Series({"cow_code": code, "year": year}), row])


def coverage(panel: pd.DataFrame) -> pd.DataFrame:
    """Non-missing values per column by decade, with the number of country-years."""
    d = panel.assign(decade=panel.year // 10 * 10)
    cols = [c for c in COLUMNS if c not in ("cow_code", "year", "iso3", "country", "cow_member")]
    out = d.groupby("decade")[cols].count()
    out.insert(0, "rows", d.groupby("decade").size())
    out.insert(1, "states", d.groupby("decade").cow_code.nunique())
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--crosswalk", action="store_true", help="rewrite country_codes.csv")
    parser.add_argument("--alliances", action="store_true", help="rewrite alliance_membership.csv")
    args = parser.parse_args(argv)
    if args.crosswalk:
        cw = build_crosswalk()
        cw.to_csv(CROSSWALK, index=False)
        crosswalk.cache_clear()
        print(f"{CROSSWALK}: {len(cw)} rows")
    if args.alliances:
        al = build_alliances()
        al.to_csv(ALLIANCES, index=False)
        print(f"{ALLIANCES}: {len(al)} rows")
    panel = build()
    print(f"{OUT}: {len(panel)} rows, {panel.cow_code.nunique()} states")
    with pd.option_context("display.width", 250, "display.max_columns", 50):
        print(coverage(panel).T.to_string())


if __name__ == "__main__":
    main()
