"""East Germany's towns: Statistisches Jahrbuch der Deutschen Demokratischen Republik 1956
(Staatliche Zentralverwaltung für Statistik, Berlin 1957), table I.10, "Gemeinden mit 10000
und mehr Einwohnern am 31. Dezember 1956 und ihre Wohnbevölkerung 1939, 1946, 1950, 1955 und
1956" (pp. 19-21), digitised by UB Mannheim (Public Domain Mark 1.0).

Every municipality of 10,000 or more on 31 December 1956, East Berlin included, with its
resident population on 17 May 1939, 29 October 1946, 31 August 1950 and 31 December 1955 and
1956, each within the boundaries of its own date.

The pages are read from the PDFs' text layer by word position: names on the left, the Bezirk
in the middle, five numeric columns found from the header's year labels. Towns merged after 1946
(Annaberg-Buchholz) print the parts' 1939 and 1946 figures on the line above; they are summed.
The text layer lacks a few names, read off the page images (MISSING), and misreads others
(NAMES).
"""

import itertools
import re
from pathlib import Path

import pandas as pd
import pymupdf

from nucprob.paths import RAW

DIR = RAW / "ddr"
PAGES = ["0041", "0042", "0043"]
YEARS = ["1939", "1946", "1950", "1955", "1956"]
# Rows with no name in the text layer, keyed by page and 1956 figure: (name, Bezirk).
MISSING = {
    ("0041", 19791): ("Anklam", "Neubrandenburg"),
    ("0042", 44668): ("Halberstadt", "Magdeburg"),
    ("0042", 21815): ("Haldensleben", "Magdeburg"),
    ("0042", 19225): ("Heidenau", "Dresden"),
    ("0043", 13357): ("Rodewisch", "Karl-Marx-Stadt"),
    ("0043", 16449): ("Roßlau", "Halle"),
    ("0043", 12058): ("Saßnitz", "Rostock"),
}
# Bezirk cells left blank in the text layer.
BEZIRKE = {"Gera": "Gera", "Görlitz": "Dresden", "Greifswald": "Rostock", "Greiz": "Gera"}
BEZIRKE |= {"Guben": "Cottbus"}
# Figures the text layer garbles, read off the page images: (page, name) -> {column: value}.
FIGURES = {("0043", "Stralsund"): {"pop_1956": 65166}}
NAMES = {
    "brankenberg": "Frankenberg",
    "breital": "Freital",
    "bürstenwalde (Spree)": "Fürstenwalde (Spree)",
    "Tliale (Harz)": "Thale (Harz)",
    "Berlin, demokratischer Sektor": "Berlin",
    "Zelidcnick": "Zehdenick",
    "Osch atz": "Oschatz",
    "Groß Raschen": "Großräschen",
}


def page_path(page: str, root: Path = DIR) -> Path:
    return root / f"514402644_{page}.pdf"


def _clusters(values: list[float], tolerance: float) -> list[list[int]]:
    """Indices of `values` grouped where consecutive sorted values differ by <= tolerance."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    groups: list[list[int]] = []
    for i in order:
        if groups and values[i] - values[groups[-1][-1]] <= tolerance:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def _text(words: list) -> str:
    """Words in reading order: printed lines top to bottom, words left to right."""
    lines = _clusters([(w[1] + w[3]) / 2 for w in words], 2.5)
    text = " ".join(w[4] for g in lines for w in sorted((words[i] for i in g), key=lambda w: w[0]))
    text = re.sub(r"\.{2,}[\s.,]*", " ", text)  # dotted leaders
    return re.sub(r"\s+", " ", text).strip(" .,;:—-")


def _number(words: list) -> int | None:
    digits = re.sub(r"\D", "", "".join(w[4] for w in sorted(words, key=lambda w: w[0])))
    return int(digits) if digits else None


def parse_page(path: Path, page: str) -> list[dict]:
    """One row per municipality. Rows are anchored on the 1956 column, which every row fills;
    every other word joins the nearest anchor (a name or Bezirk wrapped onto the line above
    joins the anchor below it), and a column holding two stacked figures (the parts of a town
    merged later) is summed."""
    words = pymupdf.open(path)[0].get_text("words")
    labels = [w for w in words if w[4] in YEARS and w[1] > 80]
    centres = [next((w[0] + w[2]) / 2 for w in labels if w[4] == y) for y in YEARS]
    edges = [centres[0] - 30] + [(a + b) / 2 for a, b in itertools.pairwise(centres)]
    bezirk_x = next(w[0] for w in words if w[4].startswith("Zugeh")) - 15
    top = max(w[3] for w in labels) + 2
    body = [w for w in words if w[1] > top and re.search(r"\w", w[4])]
    y = lambda w: (w[1] + w[3]) / 2  # noqa: E731
    last = [w for w in body if w[0] >= edges[4]]
    anchors = [sum(y(last[i]) for i in g) / len(g) for g in _clusters([y(w) for w in last], 2.5)]
    cells: list[dict] = [{"name": [], "bezirk": [], **{c: [] for c in range(5)}} for _ in anchors]
    for w in body:
        if w[0] >= edges[0]:
            col = sum(w[0] + 1 >= e for e in edges) - 1
            i = min(range(len(anchors)), key=lambda a: abs(anchors[a] - y(w)))
            cells[i][col].append(w)
        else:
            below = [a for a in range(len(anchors)) if anchors[a] >= y(w) - 3]
            if below:
                i = min(below, key=lambda a: anchors[a] - y(w))
                cells[i]["name" if w[2] <= bezirk_x else "bezirk"].append(w)
    rows = []
    for c in cells:
        row = {"page": page, "name": _text(c["name"]), "bezirk": _text(c["bezirk"]), "parts": 1}
        for col, year in enumerate(YEARS):
            ws = c[col]
            parts = [_number([ws[i] for i in g]) for g in _clusters([y(w) for w in ws], 2.0)]
            parts = [v for v in parts if v is not None]
            row[f"pop_{year}"] = sum(parts) if parts else None
            row["parts"] = max(row["parts"], len(parts))
        if not row["name"] and (page, row["pop_1956"]) in MISSING:
            row["name"], row["bezirk"] = MISSING[(page, row["pop_1956"])]
        row["name"] = NAMES.get(row["name"], row["name"])
        row["bezirk"] = row["bezirk"] or BEZIRKE.get(row["name"], "")
        row |= FIGURES.get((page, row["name"]), {})
        rows.append(row)
    return rows


def parse(root: Path = DIR) -> pd.DataFrame:
    rows = [r for p in PAGES for r in parse_page(page_path(p, root), p)]
    df = pd.DataFrame(rows)
    df.loc[df["name"] == "Berlin", "bezirk"] = "Berlin"
    return df
