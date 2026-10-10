"""Render the county tables of NAPB-90 Annex A (direct effects risk) upright for transcription.

    python scripts/napb90_pages.py

FEMA, Nuclear Attack Planning Base - 1990 (April 1987), the 510-page compilation in
data/raw/civil_defence/. Annex A Part 2, "Highest Direct Effects Risk by County", runs from PDF
page 135 to 292; its pages are scanned on their side (1-bit, 200 ppi), so they are rotated a
quarter turn here. Writes data/interim/napb90/pages/A<pdf page>.png and chunk files of
PAGES_PER_CHUNK pages for the transcription workers.
"""

import json
from pathlib import Path

import pymupdf

PDF = Path("data/raw/civil_defence/FEMA_1990_Nuclear_attack_planning_base_(NAPB-90).pdf")
OUT = Path("data/interim/napb90")
FIRST, LAST = 135, 292
PAGES_PER_CHUNK = 8


def main() -> None:
    doc = pymupdf.open(PDF)
    (OUT / "pages").mkdir(parents=True, exist_ok=True)
    (OUT / "chunks").mkdir(exist_ok=True)
    names = []
    for number in range(FIRST, LAST + 1):
        page = doc[number - 1]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72).prerotate(90))
        if pix.height > pix.width:  # a page that was scanned upright
            pix = page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72))
        name = f"A{number:03d}"
        pix.save(OUT / "pages" / f"{name}.png")
        names.append(name)
    for n in range(0, len(names), PAGES_PER_CHUNK):
        chunk = {"chunk": n // PAGES_PER_CHUNK + 1, "pages": names[n : n + PAGES_PER_CHUNK]}
        (OUT / "chunks" / f"chunk{chunk['chunk']:02d}.json").write_text(json.dumps(chunk))
    print(f"{len(names)} pages, {(len(names) + PAGES_PER_CHUNK - 1) // PAGES_PER_CHUNK} chunks")


if __name__ == "__main__":
    main()
