"""Make zoomed crops of disputed lines and split the disputes into adjudication batches.

    python scripts/sac1956_adjudicate_prep.py [batch_size] [disputes|flags]

Reads data/interim/sac1956/compare/disputes.csv and the manifest. For every disputed line,
crops the line with one line of context above and below from the 300-dpi render, enlarges it
2.5x, and marks the disputed line with a red bar. Writes crops to
data/interim/sac1956/adjudicate/crops/<id>.png and batches to
data/interim/sac1956/adjudicate/batchNN.json.

Incremental: pages that either pass has not finished are skipped, lines already in an existing
batch are skipped, and new batches are numbered after the existing ones. Run it again when the
passes are complete to batch the rest.

With `flags`, it reads compare/flags.csv instead (lines both passes agree on but that a
consistency check of sac1956_assemble.py flags) and writes checkNN.json batches.
"""

import csv
import json
import os
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import sac1956_strips as strips

ROOT = Path(os.environ.get("SAC_ROOT", "data/interim/sac1956"))
OUT = ROOT / "adjudicate"
ZOOM = 2.5


def complete(manifest: dict, pass_name: str, page: str, compared_at: float) -> bool:
    """The pass has every line of the page, and has not changed it since the comparison ran."""
    tsv = ROOT / pass_name / f"{page}.tsv"
    if not tsv.exists() or tsv.stat().st_mtime > compared_at:
        return False
    have = {
        r.split("\t")[0].rstrip("+")
        for r in tsv.read_text(encoding="utf-8").splitlines()
        if r.strip()
    }
    return {line["id"] for line in manifest[page]["lines"]} <= have


def main(batch_size: int, source: str) -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    prefix = "batch" if source == "disputes" else "check"
    batched = {
        item["id"] for f in OUT.glob(f"{prefix}*.json") for item in json.loads(f.read_text())
    }
    first = 1 + max((int(f.stem[len(prefix) :]) for f in OUT.glob(f"{prefix}*.json")), default=0)
    disputes_csv = ROOT / "compare" / f"{source}.csv"
    compared_at = disputes_csv.stat().st_mtime
    disputes = [
        d
        for d in csv.DictReader(open(disputes_csv, encoding="utf-8"))
        if d["id"] not in batched
        and all(complete(manifest, p, d["page"], compared_at) for p in ("passA", "passB"))
    ]
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
            crop = crop.resize(
                (round(crop.width * ZOOM), round(crop.height * ZOOM)), Image.LANCZOS
            ).convert("RGB")
            pen = ImageDraw.Draw(crop)
            y_a, y_b = round((mark[0] - top - 3) * ZOOM), round((mark[1] - top + 3) * ZOOM)
            pen.rectangle([0, y_a, 14, y_b], fill=(220, 0, 0))
            path = OUT / "crops" / f"{d['id'].replace('+', 'plus')}.png"
            crop.save(path, optimize=True)
            items.append({**d, "crop": str(path.relative_to(ROOT))})
    for n in range(0, len(items), batch_size):
        batch = items[n : n + batch_size]
        (OUT / f"{prefix}{first + n // batch_size:02d}.json").write_text(
            json.dumps(batch, indent=1, ensure_ascii=False)
        )
    print(
        f"{len(items)} new crops, {(len(items) + batch_size - 1) // batch_size} new batches from {prefix}{first:02d}"
    )


if __name__ == "__main__":
    main(
        int(sys.argv[1]) if len(sys.argv) > 1 else 40,
        sys.argv[2] if len(sys.argv) > 2 else "disputes",
    )
