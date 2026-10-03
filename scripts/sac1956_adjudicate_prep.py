"""Make zoomed crops of disputed lines and split the disputes into adjudication batches.

    python scripts/sac1956_adjudicate_prep.py [batch_size]

Reads data/interim/sac1956/compare/disputes.csv and the manifest. For every disputed line,
crops the line with one line of context above and below from the 300-dpi render, enlarges it
2.5x, and marks the disputed line with a red bar. Writes crops to
data/interim/sac1956/adjudicate/crops/<id>.png and batches to
data/interim/sac1956/adjudicate/batchNN.json.
"""

import csv
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import sac1956_strips as strips  # noqa: E402

ROOT = Path("data/interim/sac1956")
OUT = ROOT / "adjudicate"
ZOOM = 2.5


def main(batch_size: int) -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    disputes = list(csv.DictReader(open(ROOT / "compare" / "disputes.csv", encoding="utf-8")))
    (OUT / "crops").mkdir(parents=True, exist_ok=True)
    docs = {code: pymupdf.open(path) for code, path in strips.DOCS.items()}
    by_page: dict[str, list[dict]] = {}
    for d in disputes:
        by_page.setdefault(d["page"], []).append(d)
    items = []
    for page, rows in by_page.items():
        info = manifest[page]
        gray = strips.render(docs[page[0]], int(page[1:]) - 1)
        lines = info["lines"]
        index = {line["id"]: i for i, line in enumerate(lines)}
        x0, x1 = info["x"]
        for d in rows:
            base = d["id"].rstrip("+")
            i = index.get(base)
            if i is None:
                continue
            if d["id"].endswith("+"):  # an unlabelled line sits between this label and the next
                top = lines[i]["y0"] - 6
                bottom = lines[i + 1]["y1"] + 6 if i + 1 < len(lines) else lines[i]["y1"] + 40
                mark = (lines[i]["y1"], bottom - 6)
            else:
                top = lines[i - 1]["y0"] - 6 if i else lines[i]["y0"] - 20
                bottom = lines[i + 1]["y1"] + 6 if i + 1 < len(lines) else lines[i]["y1"] + 20
                mark = (lines[i]["y0"], lines[i]["y1"])
            top, bottom = max(top, 0), min(bottom, gray.shape[0])
            crop = Image.fromarray(gray[top:bottom, x0:x1])
            crop = crop.resize((round(crop.width * ZOOM), round(crop.height * ZOOM)), Image.LANCZOS).convert("RGB")
            pen = ImageDraw.Draw(crop)
            y_a, y_b = round((mark[0] - top - 3) * ZOOM), round((mark[1] - top + 3) * ZOOM)
            pen.rectangle([0, y_a, 14, y_b], fill=(220, 0, 0))
            path = OUT / "crops" / f"{d['id'].replace('+', 'plus')}.png"
            crop.save(path, optimize=True)
            items.append({**d, "crop": str(path.relative_to(ROOT))})
    for n in range(0, len(items), batch_size):
        batch = items[n : n + batch_size]
        (OUT / f"batch{n // batch_size + 1:02d}.json").write_text(json.dumps(batch, indent=1, ensure_ascii=False))
    print(f"{len(items)} crops, {(len(items) + batch_size - 1) // batch_size} batches")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
