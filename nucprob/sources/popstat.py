"""Parse the city pages of pop-stat.mashke.org (T. Bespyatov): the towns and urban-type
settlements of one post-Soviet republic, within today's borders, with their census populations.

Each page is a single table written without closing tags, so it is split with regular
expressions rather than an HTML parser:
- the header row (`class=bt`) gives one column per census or estimate date;
- region rows are `<th>` cells (name, transliteration, regional totals);
- settlement rows are `<td>` cells: Cyrillic name, Latin transliteration, one value per date
  in thousands with a decimal comma ("34,327" = 34,327 people; "…" = no figure), and a last
  cell with notes on status and renamings ("город с 1976, до 1976 Адыгейск").
Cities are printed in bold, urban-type settlements in plain type.
"""

import re
from pathlib import Path

import pandas as pd

ROW = re.compile(r"<tr[^>]*>", re.IGNORECASE)
CELL = re.compile(r"<t([hd])([^>]*)>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")
DATE = re.compile(r"^(\d{4})(?:-\d{2}-\d{2})?'?$")


def clean(fragment: str) -> str:
    text = TAG.sub("", fragment).replace("&nbsp;", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def number(text: str) -> float | None:
    """'34,327' -> 34327; '157,0' -> 157000; '9,' -> 9000; '…' or '' -> None."""
    text = text.replace(" ", "")
    if not text or not re.fullmatch(r"\d+(,\d*)?", text):
        return None
    whole, _, frac = text.partition(",")
    return round(float(f"{whole}.{frac or 0}") * 1000)


def parse(path: Path, republic: str) -> pd.DataFrame:
    """One row per settlement: republic, region, name_ru, name_lat, is_city, notes, and one
    `pop_<date>` column per census or estimate date on the page (in persons)."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    columns: list[str] = []
    region = region_lat = ""
    rows = []
    for chunk in ROW.split(raw)[1:]:
        parts = CELL.split(chunk)
        # parts: [before, kind, attrs, content, kind, attrs, content, ...]
        cells = [(parts[i], parts[i + 1], parts[i + 2]) for i in range(1, len(parts) - 2, 3)]
        if not cells:
            continue
        if "bt" in cells[0][1]:
            columns = [clean(c[2]) for c in cells[2:]]
            continue
        kind = cells[0][0].lower()
        if kind == "h":
            region, region_lat = clean(cells[0][2]), clean(cells[1][2]) if len(cells) > 1 else ""
            continue
        name = clean(cells[0][2])
        if not name or not columns:
            continue
        values = [clean(c[2]) for c in cells[2:]]
        row = {
            "republic": republic,
            "region": region,
            "region_lat": region_lat,
            "name_ru": name,
            "name_lat": clean(cells[1][2]) if len(cells) > 1 else "",
            "is_city": "<b>" in cells[0][2].lower(),
            "notes": values[len(columns)] if len(values) > len(columns) else "",
        }
        for col, val in zip(columns, values, strict=False):
            m = DATE.match(col)
            if m and len(col) == 10:  # census dates (YYYY-MM-DD); estimates (YYYY') are skipped
                row[f"pop_{col}"] = number(val)
        rows.append(row)
    return pd.DataFrame(rows)


def census_columns(df: pd.DataFrame) -> list[str]:
    return sorted(c for c in df.columns if c.startswith("pop_"))
