"""Hungary's settlements: the 2011 census's territorial tables (KSH, Népszámlálás 2011, Területi
adatok), table 4.1.1.1, "A népesség számának alakulása" (one workbook per county and one for
Budapest): the present population of every settlement at each census from 1870 to 1970,
within the settlement's 2011 boundaries (so Budapest's 1949 figure is Greater Budapest, as
formed in 1950).

Settlement rows are labelled with their district codes ("J08 K08 Miskolc"); Budapest is the
"Főváros összesen" row of its own workbook.
"""

import re
from pathlib import Path

import pandas as pd

from nucprob.paths import RAW

DIR = RAW / "ksh"
COUNTIES = {
    "01": "Budapest",
    "02": "Baranya",
    "03": "Bács-Kiskun",
    "04": "Békés",
    "05": "Borsod-Abaúj-Zemplén",
    "06": "Csongrád",
    "07": "Fejér",
    "08": "Győr-Moson-Sopron",
    "09": "Hajdú-Bihar",
    "10": "Heves",
    "11": "Komárom-Esztergom",
    "12": "Nógrád",
    "13": "Pest",
    "14": "Somogy",
    "15": "Szabolcs-Szatmár-Bereg",
    "16": "Jász-Nagykun-Szolnok",
    "17": "Tolna",
    "18": "Vas",
    "19": "Veszprém",
    "20": "Zala",
}
YEARS = ("1930", "1941", "1949", "1960")
SETTLEMENT = re.compile(r"^J\d\d K\d\d (?P<name>.+)$")


def path(county: str, root: Path = DIR) -> Path:
    return root / f"{county}_4_1_1_1.xls"


def parse_county(county: str, root: Path = DIR) -> pd.DataFrame:
    raw = pd.read_excel(path(county, root), header=None)
    header = next(i for i in range(10) if str(raw.iat[i, 2]).startswith("1870"))
    cols = {}
    for j in range(2, raw.shape[1]):
        year = str(raw.iat[header, j]).split(".")[0]
        if year in YEARS and year not in cols:  # present population comes first
            cols[year] = j
    rows = []
    for i in range(header + 1, len(raw)):
        label = str(raw.iat[i, 0]).strip()
        m = SETTLEMENT.match(label)
        name = m.group("name") if m else ("Budapest" if label == "Főváros összesen" else None)
        if name:
            rows.append(
                {"county": COUNTIES[county], "name": name}
                | {
                    f"pop_{y}": pd.to_numeric(raw.iat[i, j], errors="coerce")
                    for y, j in cols.items()
                }
            )
    return pd.DataFrame(rows)


def parse(root: Path = DIR) -> pd.DataFrame:
    return pd.concat([parse_county(c, root) for c in COUNTIES], ignore_index=True)
