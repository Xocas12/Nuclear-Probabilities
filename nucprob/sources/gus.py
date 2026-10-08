"""Poland's towns: Rocznik Statystyczny 1957 (GUS, Warsaw), table 7, "Ludność w miastach liczących
10 tys. i więcej mieszkańców" (pp. 13-15), from the ABBYY OCR (ALTO XML) of Polona's scan
(Biblioteka Narodowa, public domain).

Every town of 10,000 or more on 31 December 1956, grouped by voivodeship, with its population
at the census of 3 December 1950 and the estimate for 31 December 1956, in thousands with one
decimal. "X": the town did not exist in 1950. Voivodeship rows give the voivodeship's urban
total and are dropped; "M." marks the towns with voivodeship status.

Pages 14 and 15 print two tables side by side; each half is read on its own. In each half the
two numeric columns are found from the header's year labels, and every line of figures is
paired with the nearest line of text (the scan is skewed, so names can sit a few pixels off
their figures). Names the OCR missed were read off the page images (MISSING); misread letters
in figures are repaired (DIGITS).
"""

import re
from pathlib import Path

import pandas as pd
from lxml import etree

from nucprob.paths import RAW

DIR = RAW / "gus"
PAGES = {13: "b6990766-8108-49ca-a322-9e04bc70de4e", 14: "2dbb1717-a7d5-4758-9982-3e5ee409d0db"}
PAGES |= {15: "086fccd8-c653-4cb5-a313-adf48dad5036"}
URL = "https://polona.pl/api/download/digital-content/{}"
DIGITS = str.maketrans({"C": "0", "O": "0", "o": "0", "b": "6", "u": "0", "l": "1", "I": "1"})
VOIVODESHIP = re.compile(r"^[A-ZŁŚŻ][a-ząćęłńóśźż]+(?:skie|ckie|dzkie)(?: \(dok\.\))?$")
NAMES = {"Fruszków": "Pruszków", "Zary": "Żary", "Nakło n/Notecią": "Nakło nad Notecią"}
# Lines of figures with no name in the OCR, keyed by (page, 1956 figure in thousands): the name
# on the page image.
MISSING = {
    (14, 328.3): "Kieleckie",
    (14, 118.8): "Radom",
    (14, 32.4): "Starachowice",
    (14, 26.7): "Chełm",
    (14, 18.9): "Łomża",
    (14, 60.4): "Olsztyn",
    (14, 15.6): "Ostróda",
    (14, 259.9): "Gdańsk",
    (14, 133.3): "Gdynia",
    (14, 44.0): "Sopot",
    (14, 30.9): "Tczew",
    (14, 22.5): "Malbork",
    (14, 22.0): "Wejherowo",
    (14, 17.6): "Kwidzyn",
    (14, 12.1): "Rumia",
}
FOOTNOTE = re.compile(r"^(U\)|Uwaga|Ob\.)")


def path(page: int, root: Path = DIR) -> Path:
    return root / f"rs1957_p{page}_alto.xml"


def _strings(page: int, root: Path) -> list[tuple[str, float, float]]:
    tree = etree.parse(str(path(page, root)))
    ns = {"a": tree.getroot().nsmap.get(None)}
    out = []
    for s in tree.findall(".//a:String", ns):
        x, y = int(s.get("HPOS")), int(s.get("VPOS")) + int(s.get("HEIGHT")) / 2
        out.append((s.get("CONTENT"), x, y))
    return out


def _lines(items: list, tolerance: float = 7.0) -> list[list]:
    items = sorted(items, key=lambda s: s[2])
    lines: list[list] = []
    for s in items:
        if lines and s[2] - lines[-1][-1][2] <= tolerance:
            lines[-1].append(s)
        else:
            lines.append([s])
    return [sorted(line, key=lambda s: s[1]) for line in lines]


def figure(tokens: list[str]) -> float | None:
    """Thousands from the tokens of one cell: "1", "022,9" -> 1022.9; "49", "3" -> 49.3
    (comma lost); "120,C" -> 120.0; "X" -> None."""
    text = "".join(t.translate(DIGITS) for t in tokens).replace(".", ",")
    if not re.search(r"\d", text):
        return None
    if "," not in text and len(tokens) == 2:
        text = ",".join(t.translate(DIGITS) for t in tokens)
    text = re.sub(r"[^\d,]", "", text)
    whole, _, frac = text.rpartition(",") if "," in text else (text, "", "0")
    return float(f"{whole or 0}.{frac[:1] or 0}")


def parse_half(strings: list, x_min: float, x_max: float, page: int) -> list[dict]:
    """The rows of one table half lying between x_min and x_max."""
    half = [s for s in strings if x_min <= s[1] < x_max]
    labels = [s for s in half if s[0] in ("1950", "1956")]
    if len(labels) < 2:
        return []
    col = {s[0]: s[1] for s in sorted(labels, key=lambda s: s[2])}
    top = max(s[2] for s in labels) + 40  # below the "w tysiącach" line
    split = (col["1950"] + col["1956"]) / 2 + 20
    first = col["1950"] - 45
    body = [s for s in half if s[2] > top and not re.fullmatch(r"[.…·,:;]+", s[0])]
    names = _lines([s for s in body if s[1] < first])
    figures = _lines([s for s in body if s[1] >= first])
    used: set[int] = set()
    rows = []
    for line in figures:
        y = sum(s[2] for s in line) / len(line)
        a = [s[0] for s in line if s[1] < split]
        b = [s[0] for s in line if s[1] >= split]
        free = [i for i in range(len(names)) if i not in used]
        near = [i for i in free if abs(sum(s[2] for s in names[i]) / len(names[i]) - y) <= 16]
        name = ""
        if near:
            i = min(near, key=lambda i: abs(sum(s[2] for s in names[i]) / len(names[i]) - y))
            used.add(i)
            name = " ".join(s[0] for s in names[i])
        v1956 = figure(b)
        rows.append({"page": page, "y": y, "name": name, "k1950": figure(a), "k1956": v1956})
    for i in range(len(names)):  # headers with no figures: "Poznańskie (dok.)"
        if i not in used:
            text = " ".join(s[0] for s in names[i])
            y = sum(s[2] for s in names[i]) / len(names[i])
            rows.append({"page": page, "y": y, "name": text, "k1950": None, "k1956": None})
    return sorted(rows, key=lambda r: r["y"])


def parse(root: Path = DIR) -> pd.DataFrame:
    rows = []
    for page in PAGES:
        strings = _strings(page, root)
        if page == 13:  # table 6 fills the top of the page
            start = next(s[2] for s in strings if s[0] == "TABL." and s[2] > 600)
            strings = [s for s in strings if s[2] > start]
        width = max(s[1] for s in strings)
        # The right half's names start a little left of its "WOJEWÓDZTWA" header.
        heads = [s[1] for s in strings if re.match(r"W[OÓ][Jj]EW", s[0])]
        middle = max(heads) - 75
        for x0, x1 in ((0, middle), (middle, width + 1)):
            rows += parse_half(strings, x0, x1, page)
    out, voivodeship = [], ""
    for r in rows:
        name = re.sub(r"\s+", " ", r["name"]).strip(" .")
        if not name and (r["page"], r["k1956"]) in MISSING:
            name = MISSING[(r["page"], r["k1956"])]
        if FOOTNOTE.match(name):
            continue
        if VOIVODESHIP.match(name):
            voivodeship = name.replace(" (dok.)", "")
            continue
        if r["k1956"] is None:
            continue
        capital = bool(re.match(r"^M\.", name))
        name = re.sub(r"^M\.\s*(st\.\s*)?", "", name)
        out.append(
            {
                "page": r["page"],
                "voivodeship": voivodeship,
                "name": NAMES.get(name, name),
                "city_voivodeship": capital,
                "pop_1950": None if r["k1950"] is None else round(r["k1950"] * 1000),
                "pop_1956": round(r["k1956"] * 1000),
            }
        )
    return pd.DataFrame(out)
