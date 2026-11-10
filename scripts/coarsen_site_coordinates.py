"""Hold every site row at the centre of its 0.5-degree cell (nineteenth and twentieth amendments).

    uv run python scripts/coarsen_site_coordinates.py           # rewrite the site tables in place
    uv run python scripts/coarsen_site_coordinates.py --check   # exit 1 if any table still needs it

The nineteenth amendment did this for rows with no recorded end year. The twentieth does it for every row: an end
year dates the role at the table's date, not the facility, which may be in use today. A coordinate becomes
floor(2x)/2 + 0.25 in latitude and longitude, and coordinate text and remarks on what a site holds today are taken
out of the row's text cells. Running it twice changes nothing.
"""

import argparse
import csv
import io
import math
import re
import sys
from pathlib import Path

FEATURES = Path(__file__).resolve().parents[1] / "data" / "curated" / "features"
# table -> (latitude, longitude, end-year column (kept for what reads it; every row is held), text columns to clean)
TABLES = {
    "military_sites_1956.csv": ("lat", "lon", "until_year", ("note", "source")),
    "bloc_air_defence_1956.csv": ("lat", "lon", "until_year", ("note", "source")),
    "weurope_military_sites_1965.csv": (
        "lat",
        "lon",
        "until_year",
        ("note", "coord_source", "source"),
    ),
    "sac_bases_1956.csv": ("lat", "lon", None, ("role", "basis")),
}
# Coordinate text as the tables cite it: {{Coord|...}} templates, "lat=..., lon=..." pairs, decimal pairs.
COORD = [
    re.compile(r":?\s*\{\{\s*[Cc]oord\s*\|[^}]*\}\}"),
    re.compile(r":?\s*lat\s*=\s*-?[\d.]+[^)]*?lon\w*\s*=\s*-?[\d.]+"),
    re.compile(
        r":?\s*(?:long?\s*=\s*-?[\d.]+\s*\|?\s*)?lat\s*=\s*-?[\d.]+(?:\s*\|?\s*long?\s*=\s*-?[\d.]+)?"
    ),
    re.compile(r"-?\d{1,3}\.\d{2,}\s*[,/ ]\s*-?\d{1,3}\.\d{2,}"),
    # degrees, minutes and seconds: "[46 53 10N, 142 43 09E]", "46°53′10″N 142°43′09″E"
    re.compile(
        r"\s*\[?\d{1,3}[° ]\s?\d{1,2}[′' ]\s?(?:\d{1,2}(?:\.\d+)?[″\"]?\s?)?[NS],?\s*\d{1,3}[° ]\s?\d{1,2}[′' ]\s?(?:\d{1,2}(?:\.\d+)?[″\"]?\s?)?[EW]\]?"
    ),
]
# Remarks on what a site holds or is today, which the 1956 and 1965 features do not need. A date range ending
# "today" stays: it says how long a site served, not what it holds.
TODAY = re.compile(
    r"[^.;()]*\b(B61|B28|B43|nuclear[- ]weapons? (?:site|storage) today|present-day|still (?:holds|hosts|stores))\b"
    r"[^.;()]*[.;]?",
    re.IGNORECASE,
)


def cell_centre(x: float) -> float:
    return math.floor(2 * x) / 2 + 0.25


def clean(text: str) -> str:
    for pat in COORD:
        text = pat.sub("", text)
    text = TODAY.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).replace("( ", "(").replace(" )", ")").replace("()", "")
    text = re.sub(r"\s+\.", ".", re.sub(r"\s(?:location at|at|grid)\)", ")", text))
    return text.strip(" ;,")


def coarsen(
    path: Path, lat: str, lon: str, end: str | None, texts: tuple[str, ...]
) -> tuple[str, int]:
    raw = path.read_bytes().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw, newline=""))
    rows = list(reader)
    changed = 0
    for row in rows:
        if not row[lat].strip():
            continue
        new = dict(row)
        new[lat] = f"{cell_centre(float(row[lat])):.2f}"
        new[lon] = f"{cell_centre(float(row[lon])):.2f}"
        for col in texts:
            new[col] = clean(row[col])
        if new != row:
            changed += 1
            row.update(new)
    out = io.StringIO(newline="")
    eol = "\r\n" if raw.split("\n", 1)[0].endswith("\r") else "\n"
    w = csv.DictWriter(out, fieldnames=reader.fieldnames, lineterminator=eol)
    w.writeheader()
    w.writerows(rows)
    return out.getvalue(), changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pending = 0
    for name, spec in TABLES.items():
        path = FEATURES / name
        text, changed = coarsen(path, *spec)
        print(f"{name}: {changed} rows {'to change' if args.check else 'changed'}")
        pending += changed
        if changed and not args.check:
            path.write_bytes(text.encode("utf-8"))
    if args.check and pending:
        sys.exit(1)


if __name__ == "__main__":
    main()
