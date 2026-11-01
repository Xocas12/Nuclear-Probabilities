"""First read of the 1961 FRG census table: the OCR text layer of VZ 1961 Vorbericht 3.

    python scripts/frg_1961_read.py > data/interim/frg/ranked.csv

Table 2 (pp. 8-20, 583 Gemeinden by size) is read by word position, one row per Gemeinde;
scripts/frg_1961_build.py applies the checked corrections.
"""

import re
import sys

import pandas as pd
import pymupdf

PDF = "data/raw/frg_official/FS-A-VZ1961-Vorbericht-03-1961.pdf"
LAND = {
    "SchH": "Schleswig-Holstein",
    "Hmb": "Hamburg",
    "Ndsa": "Niedersachsen",
    "Brm": "Bremen",
    "NrhW": "Nordrhein-Westfalen",
    "Hess": "Hessen",
    "RhPf": "Rheinland-Pfalz",
    "BaWü": "Baden-Württemberg",
    "Bay": "Bayern",
    "Saar": "Saarland",
    "BlnW": "Berlin (West)",
}


def digits(tokens: list[str]) -> str:
    s = "".join(tokens)
    return re.sub(r"\D", "", s.translate(str.maketrans("OoIlbB", "001160")))


def lines(words, tol=6.5):
    out, cur, y = [], [], None
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        c = (w[1] + w[3]) / 2
        if y is not None and c - y > tol:
            out.append(cur)
            cur, y = [], None
        cur.append(w)
        y = c if y is None else (y * (len(cur) - 1) + c) / len(cur)
    if cur:
        out.append(cur)
    return [sorted(x, key=lambda w: w[0]) for x in out]


def land_of(t: str) -> str:
    s = re.sub(r"[^A-Za-zü]", "", t).lower()
    for k in LAND:
        if s == k.lower() or (len(s) >= 3 and s[:3] == k.lower()[:3]):
            return k
    return ""


def ranked(doc) -> pd.DataFrame:
    rows = []
    for n in range(8, 21):
        page = doc[n - 1]
        words = page.get_text("words")
        heads = [w for w in words if re.fullmatch(r"6\.6\.19[6b]1", w[4])]
        x61 = max(w[0] for w in heads) if heads else 419.0
        dx = x61 - 419.0
        for ln in lines(words):

            def col(a, b, ln=ln, dx=dx):
                return [w[4] for w in ln if a <= w[0] - dx < b]

            nr = digits(col(40, 80))
            name = " ".join(col(80, 240))
            name = re.sub(r"[\s.,:;·•'\"]+$", "", re.sub(r"\.{2,}.*$", "", name)).strip()
            if not name or "Gemeinden mit" in name or name.startswith("Gemeinde"):
                continue
            pop61 = digits(col(412, 470))
            if not pop61 or len(pop61) < 4:
                continue
            rows.append(
                {
                    "page": n,
                    "nr": int(nr) if nr else None,
                    "name": name,
                    "land_raw": " ".join(col(240, 276)),
                    "land": land_of(" ".join(col(240, 276))),
                    "area": "".join(col(276, 322)),
                    "pop39": digits(col(322, 372)),
                    "pop50": digits(col(372, 412)),
                    "pop61": pop61,
                    "pct39": "".join(col(470, 512)),
                    "pct50": "".join(col(512, 570)),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    ranked(pymupdf.open(PDF)).to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
