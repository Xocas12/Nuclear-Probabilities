"""Cut the SAC 1956 target-list scans into numbered line strips for transcription.

Each page of the Part I complex list and the Part II airfield list is rendered at 300 dpi.
Only character-sized ink is kept (scanner specks, punch holes, rules and the redaction box
are dropped by connected-component size), and printed lines are found from the horizontal
profile of what remains, left of the redaction box. Every line gets an id such as
``C166-L07`` (document C or A, page 166, line 7) and is drawn, enlarged, into a strip image
with its id in the left margin. Two transcription passes read the same strips, so their
readings line up by id.

Writes ``data/interim/sac1956/strips/*.png`` and ``data/interim/sac1956/manifest.json``.

    python scripts/sac1956_strips.py                # all pages
    python scripts/sac1956_strips.py C166 A003      # selected pages only (for checking)
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

# Two sets of documents, each with its own workspace. SAC_SET=excerpts selects the sections the
# Archive released only in part: the cross-reference list (X), the Part I airfield list (F),
# the Part II complex list (R) and the summary of requirements (S).
SETS = {
    "main": (
        {
            "C": Path("data/raw/sac1956/1st_city_list_complete.pdf"),  # Part I complex list
            "A": Path("data/raw/sac1956/section6.pdf"),  # Part II airfield list
        },
        Path("data/interim/sac1956"),
    ),
    "excerpts": (
        {
            "X": Path("data/raw/sac1956/section2.pdf"),
            "F": Path("data/raw/sac1956/section4.pdf"),
            "R": Path("data/raw/sac1956/section7.pdf"),
            "S": Path("data/raw/sac1956/section8.pdf"),
        },
        Path("data/interim/sac1956_excerpts"),
    ),
}
DOCS, OUT = SETS[os.environ.get("SAC_SET", "main")]
# usual x of the redaction box's left edge; X and S pages have no box, so they run to the frame
BOX_FALLBACK = {"C": 1215, "A": 1315, "R": 1215, "F": 1315, "X": 2380, "S": 2380}
NO_BOX = {"X", "S"}
DPI = 300
SCALE = 1.6  # strips are enlarged so small glyphs are easier to read
MAX_LINES_PER_STRIP = 14
MARGIN = 170  # white margin on the left of a strip, for the line ids
PROFILE_LEFT = (
    300  # table text starts right of x=330; the frame, a fold line and specks lie left of 300
)
CROP_LEFT = 250  # strips still show from here, in case a page is shifted a little
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 34)


def render(doc: pymupdf.Document, index: int) -> np.ndarray:
    pix = doc[index].get_pixmap(
        matrix=pymupdf.Matrix(DPI / 72, DPI / 72), colorspace=pymupdf.csGRAY
    )
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)


# Pages where the first long rule is not the box's edge (R006: a rule inside the table).
BOX_OVERRIDE = {"R006": 1215}


def box_left(ink: np.ndarray, code: str, key: str = "") -> int:
    """x of the redaction box's left edge: the first long vertical rule in the middle band."""
    if key in BOX_OVERRIDE:
        return BOX_OVERRIDE[key]
    if code in NO_BOX:
        return BOX_FALLBACK[code]
    height = ink.shape[0]
    rules = np.where(ink.sum(axis=0) > 0.25 * height)[0]
    candidates = [x for x in rules if 900 <= x <= 1500]
    return int(min(candidates)) if candidates else BOX_FALLBACK[code]


def characters(ink: np.ndarray) -> np.ndarray:
    """Keep only character-sized connected components (drops specks, rules, holes, boxes)."""
    labels, count = ndimage.label(ink, structure=np.ones((3, 3)))
    if count == 0:
        return ink
    index = np.arange(1, count + 1)
    area = ndimage.sum_labels(ink, labels, index=index)
    keep = np.zeros(count + 1, dtype=bool)
    for i, box in enumerate(ndimage.find_objects(labels), start=1):
        h, w = box[0].stop - box[0].start, box[1].stop - box[1].start
        keep[i] = 25 <= area[i - 1] <= 400 and 10 <= h <= 30 and 3 <= w <= 60
    return keep[labels]


def spans_columns(chars: np.ndarray, band: list[int]) -> bool:
    """A printed line spreads across the page; a streak of scanner specks does not."""
    xs = np.where(chars[band[0] : band[1] + 1].any(axis=0))[0]
    return len(xs) > 0 and xs.max() - xs.min() >= 50 and len(set(xs // 40)) >= 2


def line_bands(chars: np.ndarray) -> list[tuple[int, int]]:
    """Printed lines as (top, bottom) row ranges, from the profile of character ink."""
    profile = chars.sum(axis=1)
    bands, start = [], None
    for y, value in enumerate(profile):
        if value >= 2 and start is None:
            start = y
        elif value < 2 and start is not None:
            bands.append([start, y - 1])
            start = None
    if start is not None:
        bands.append([start, len(profile) - 1])
    merged = []
    for band in bands:  # close tiny gaps inside one line of characters
        if merged and band[0] - merged[-1][1] <= 3:
            merged[-1][1] = band[1]
        else:
            merged.append(band)
    merged = [
        b
        for b in merged
        if b[1] - b[0] >= 6 and profile[b[0] : b[1] + 1].sum() >= 40 and spans_columns(chars, b)
    ]
    if not merged:
        return []
    typical = float(np.median([b[1] - b[0] for b in merged if 8 <= b[1] - b[0] <= 40] or [15]))
    out = []
    for top, bottom in merged:  # split bands that hold two touching lines
        if bottom - top > 1.75 * typical:
            pieces = max(2, round((bottom - top) / (typical * 1.5)))
            cuts = [top]
            for k in range(1, pieces):
                guess = top + k * (bottom - top) // pieces
                window = profile[guess - 5 : guess + 6]
                cuts.append(guess - 5 + int(np.argmin(window)))
            cuts.append(bottom)
            out += [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
        else:
            out.append((top, bottom))
    return out


def draw_strip(
    gray: np.ndarray, x0: int, x1: int, lines: list[dict], top: int, bottom: int, path: Path
) -> None:
    crop = Image.fromarray(gray[top:bottom, x0:x1])
    crop = crop.resize(
        (round(crop.width * SCALE), round(crop.height * SCALE)), Image.LANCZOS
    ).convert("RGB")
    canvas = Image.new("RGB", (crop.width + MARGIN, crop.height), "white")
    canvas.paste(crop, (MARGIN, 0))
    pen = ImageDraw.Draw(canvas)
    for i, line in enumerate(lines):
        mid = round(((line["y0"] + line["y1"]) / 2 - top) * SCALE)
        pen.text((8, mid - 20), line["id"].split("-")[1], fill=(200, 0, 0), font=FONT)
        if i:  # faint rule halfway between this line and the previous one
            y = round(((lines[i - 1]["y1"] + line["y0"]) / 2 - top) * SCALE)
            pen.line([(0, y), (canvas.width, y)], fill=(120, 170, 255), width=1)
    canvas.save(path, optimize=True)


def process(code: str, index: int, doc: pymupdf.Document) -> dict:
    gray = render(doc, index)
    ink = gray < 128
    right = box_left(ink, code, f"{code}{index + 1:03d}") - 8
    chars = characters(ink[:, PROFILE_LEFT:right])
    page = index + 1
    bands = line_bands(chars)
    lines = [
        {"id": f"{code}{page:03d}-L{n:02d}", "y0": int(t), "y1": int(b)}
        for n, (t, b) in enumerate(bands, 1)
    ]
    x0, x1 = CROP_LEFT, right + 10
    strips = []
    for k in range(0, len(lines), MAX_LINES_PER_STRIP):
        chunk = lines[k : k + MAX_LINES_PER_STRIP]
        before = lines[k - 1] if k else None
        after = lines[k + MAX_LINES_PER_STRIP] if k + MAX_LINES_PER_STRIP < len(lines) else None
        top = (before["y1"] + chunk[0]["y0"]) // 2 if before else max(chunk[0]["y0"] - 14, 0)
        bottom = (
            (chunk[-1]["y1"] + after["y0"]) // 2
            if after
            else min(chunk[-1]["y1"] + 14, gray.shape[0])
        )
        name = f"{code}{page:03d}_s{k // MAX_LINES_PER_STRIP + 1}.png"
        draw_strip(gray, x0, x1, chunk, top, bottom, OUT / "strips" / name)
        strips.append({"file": f"strips/{name}", "lines": [line["id"] for line in chunk]})
    return {"doc": code, "page": page, "x": [x0, x1], "lines": lines, "strips": strips}


def main(selected: list[str]) -> None:
    (OUT / "strips").mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if selected and manifest_path.exists() else {}
    for code, pdf in DOCS.items():
        doc = pymupdf.open(pdf)
        for index in range(doc.page_count):
            key = f"{code}{index + 1:03d}"
            if selected and key not in selected:
                continue
            manifest[key] = process(code, index, doc)
            print(key, len(manifest[key]["lines"]), "lines", len(manifest[key]["strips"]), "strips")
    manifest_path.write_text(json.dumps(dict(sorted(manifest.items())), indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
