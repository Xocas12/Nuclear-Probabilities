"""Dexter and Rodionov, The Factories, Research and Design Establishments of the Soviet Defence
Industry: a Guide (version 24, University of Warwick, 2026): one row per establishment and
location, with its branch, type, size and years. No open licence is stated, so only counts
derived from it are committed.

Entries are kept when they are the guide's main series (column 16 "s" or "w", which carry
numeric years) and not a double count (column 21 "d"). An entry is active in a year when its
first or second span of years covers it.

`parse_location` reads the guide's location strings: "Gor'kii, now Nizhnii Novgorod",
"Khar'kov, Ukraine", "Moscow (Tushino)", "Kaliningrad, Moscow obl., now Korolev",
"Chelyabinsk 40, later Chelyabinsk 65, Ozersk, Chelyabinsk obl.".
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from nucprob.paths import RAW

PATH = RAW / "vpk" / "dataset_ver24.xlsx"
COLUMNS = [
    "no",
    "name",
    "location",
    "associated",
    "branch",
    "ministry",
    "details",
    "director",
    "date",
    "sources",
    "address",
    "type",
    "subordinated",
    "subtype",
    "other_industries",
    "series",
    "start",
    "finish",
    "start2",
    "finish2",
    "double_count",
    "size",
]
BRANCHES = ("AERO", "ARMOUR", "ARMS", "MUNS", "SHIP", "ELEC", "ATOM", "AUTO", "FUEL", "RAIL")
# Union republics as the guide names them after a town ("Khar'kov, Ukraine").
REPUBLICS = {
    "ukraine": "ukraine",
    "belarus": "belarus",
    "belorussia": "belarus",
    "moldova": "moldova",
    "moldavia": "moldova",
    "lithuania": "lithuania",
    "latvia": "latvia",
    "estonia": "estonia",
    "georgia": "georgia",
    "armenia": "armenia",
    "azerbaijan": "azerbaijan",
    "kazakhstan": "kazakhstan",
    "uzbekistan": "uzbekistan",
    "turkmenistan": "turkmenistan",
    "turkmenia": "turkmenistan",
    "kyrgyzstan": "kyrgyzstan",
    "kirgizia": "kyrgyzstan",
    "tajikistan": "tajikistan",
    "tadzhikistan": "tajikistan",
    "russia": "russia",
}
ALSO = re.compile(r"\s+(?:now|former|formerly|earlier|later|or|then)\s+", re.I)
LEAD = re.compile(r"^(?:now|former|formerly|earlier|later|or|then)\s+", re.I)


def load(path: Path = PATH) -> pd.DataFrame:
    """Every entry of the database sheet. The sheet has a header row part-way down, with
    entries above it as well as below."""
    raw = pd.read_excel(path, sheet_name="Database", header=None, dtype=object)
    header = raw.index[raw[0].astype(str).str.strip() == "1. No."]
    assert len(header) == 1, "header row not found"
    df = raw.drop(index=header).reset_index(drop=True)
    df.columns = COLUMNS
    df = df[df["name"].notna() | df["location"].notna()].copy()
    for col in ["location", "branch", "type", "series", "double_count", "size"]:
        df[col] = df[col].astype(str).str.strip().replace({"nan": ""})
    for col in ["start", "finish", "start2", "finish2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def main_series(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["series"].isin(["s", "w"]) & (df["double_count"] != "d")]


def active(df: pd.DataFrame, year: int) -> pd.Series:
    first = (df["start"] <= year) & (df["finish"] >= year)
    second = (df["start2"] <= year) & (df["finish2"] >= year)
    return first | second


def branches(branch: str) -> set[str]:
    """The branches an entry names ("ELEC for AERO" counts for both)."""
    return {b for b in BRANCHES if re.search(rf"\b{b}\b", branch)}


# Bloc countries other than the USSR, as the guide names them after a town.
COUNTRIES = {
    "germany": "East Germany",
    "gdr": "East Germany",
    "poland": "Poland",
    "czechoslovakia": "Czechoslovakia",
    "hungary": "Hungary",
    "romania": "Romania",
    "bulgaria": "Bulgaria",
    "china": "China",
    "mongolia": "Mongolia",
}
REGION = re.compile(r"\s+(?:obl|krai|kray|area|raion|ASSR|republic|AO|okrug)\b\.?$", re.I)
FROM_YEAR = re.compile(r"^(?:from|in|since)\s+\d{4}\s+", re.I)
STATION = re.compile(r"^(?:st|m|pos|s|g)\.\s*")  # station, settlement, village, town


@dataclass
class Location:
    town: str
    districts: list[str] = field(default_factory=list)  # in parentheses: "Moscow (Tushino)"
    also: list[str] = field(default_factory=list)  # now / former / later / or names
    country: str = "USSR"
    republic: str | None = None
    region: str | None = None  # the stem of "Kemerovo obl.", "Khabarovsk area"
    closed: bool = False  # a numbered code name: "Chelyabinsk 40", "Arzamas-16"


def _names(text: str) -> tuple[list[str], list[str]]:
    """Names in a piece of a location string, and the districts in its parentheses."""
    districts = [d.strip() for d in re.findall(r"\(([^)]*)\)", text)]
    text = re.sub(r"\s*\([^)]*\)", "", text)
    names = [FROM_YEAR.sub("", n).strip(" .;") for n in ALSO.split(LEAD.sub("", text.strip()))]
    names = [STATION.sub("", n) for n in names]
    districts = [STATION.sub("", d) for g in districts for d in re.split(r"\s+or\s+", g)]
    return [n for n in names if n], [d for d in districts if d and not re.search(r"\d", d)]


def parse_location(text: str) -> Location | None:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text or text in {"USSR", "nan"}:
        return None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    names, districts = _names(parts[0])
    loc = Location(town=names[0] if names else "", districts=districts, also=names[1:])
    for part in parts[1:]:
        low = part.lower().rstrip(".")
        if low in REPUBLICS:
            loc.republic = REPUBLICS[low]
        elif low in COUNTRIES:
            loc.country = COUNTRIES[low]
        elif REGION.search(part):
            stem = REGION.sub("", LEAD.sub("", part)).strip()
            if not re.search(r"\braion\b", part, re.I):
                loc.region = stem
        else:
            more, extra = _names(part)
            loc.also += more
            loc.districts += extra
    loc.closed = bool(re.search(r"\d", loc.town))
    loc.also = [n for n in dict.fromkeys(loc.also) if n != loc.town and not re.search(r"\d", n)]
    return loc if loc.town else None
