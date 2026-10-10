"""US counties in the 1980s: the Census Bureau's intercensal population estimates and its 1990
county boundaries.

- `e8089co.txt` (Census Bureau, "Intercensal Estimates of the Resident Population of States
  and Counties 1980-1989", issued March 1992): one line per state and county with its FIPS code,
  the 1980 census and the estimates for 1 July 1981-1989, printed in two blocks (1980-1984,
  then 1985-1989).
- `co99_d90` (Census Bureau cartographic boundary file, counties as of the 1990 census): one
  polygon (or several) per county, with state and county FIPS codes and the county name.
"""

import re

import pandas as pd

from nucprob.paths import RAW

DIR = RAW / "census"
ESTIMATES_URL = (
    "https://www2.census.gov/programs-surveys/popest/tables/1980-1990/counties/totals/e8089co.txt"
)
BOUNDARIES_URL = "https://www2.census.gov/geo/tiger/PREVGENZ/co/co90shp/co99_d90_shp.zip"
LINE = re.compile(r"^(\d{5}) (.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")
NAME_ONLY = re.compile(r"^\d{5} \D+$")
YEARS = re.compile(r"^Code\s+Area Name\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})")


def estimates() -> pd.DataFrame:
    """One row per state (fips ending 000) and county: fips, name, pop_1980 ... pop_1989."""
    rows: dict[str, dict] = {}
    years: list[str] = []
    held = ""  # a long name wraps: "24033 Prince George's" then "       Co.   665071 ..."
    for line in (DIR / "e8089co.txt").read_text(encoding="latin-1").splitlines():
        if m := YEARS.match(line):
            years = list(m.groups())
            continue
        if NAME_ONLY.match(line):
            held = line.rstrip()
            continue
        if held and line.startswith(" "):
            line, held = f"{held} {line.strip()}", ""
        held = ""
        if (m := LINE.match(line)) and years:
            fips, name, *values = m.groups()
            row = rows.setdefault(fips, {"fips": fips, "name": name.strip()})
            row |= {f"pop_{y}": int(v) for y, v in zip(years, values, strict=True)}
    out = pd.DataFrame(rows.values())
    out["level"] = out["fips"].map(
        lambda f: "nation" if f == "00000" else "state" if f.endswith("000") else "county"
    )
    return out
