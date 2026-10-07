"""Parse Demoscope Weekly's table of the 1959 census urban settlements of the union republics
other than the RSFSR (ussr59_reg2.php), with their 1959 names and 1959 oblasts.

Rows are `<tr>` with a label cell and three numbers (both sexes, men, women). Territorial
rows (republic, oblast, district) are printed in blue; settlement rows start with a status
abbreviation: г. (city), пгт (urban-type settlement), рп / кп (workers' / resort settlement).
"(рц)" marks a district centre.
"""

import re
from pathlib import Path

import pandas as pd

ROW = re.compile(r"<tr>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
TAG = re.compile(r"<[^>]+>")
STATUS = re.compile(r"^(г\.|пгт|рп|кп|дп|гп)\s+(.+?)(\s+\(рц\))?$")


def clean(fragment: str) -> str:
    text = TAG.sub("", fragment).replace("&nbsp", " ").replace("\xa0", " ").replace(";", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse(path: Path) -> pd.DataFrame:
    """One row per urban settlement: republic, oblast, status, name_ru, district_centre, pop_1959."""
    raw = path.read_bytes().decode("cp1251", errors="replace")
    republic = oblast = ""
    rows = []
    for body in ROW.findall(raw):
        cells = CELL.findall(body)
        if len(cells) < 2:
            continue
        label = clean(cells[0])
        blue = "#0000FF" in cells[0].upper()
        if blue:
            if label.endswith("ССР") and "АССР" not in label:
                republic, oblast = label, ""
            elif re.search(
                r"(област[ьъ]|АССР|край|горсовет)$", label
            ):  # "областъ": typo in the source
                oblast = label
            continue
        m = STATUS.match(label)
        value = clean(cells[1]).replace(" ", "")
        if not m or not value.isdigit():
            continue
        rows.append(
            {
                "republic": republic,
                "oblast": oblast,
                "status": m[1],
                "name_ru": m[2].strip(),
                "district_centre": bool(m[3]),
                "pop_1959": int(value),
            }
        )
    return pd.DataFrame(rows)
