"""Split the strip manifest into transcription chunks, and check pass outputs for completeness.

    python scripts/sac1956_chunks.py make             # writes data/interim/sac1956/chunks/*.json
    python scripts/sac1956_chunks.py check passA      # which pages of each chunk are done / missing

A pass writes one TSV per page, data/interim/sac1956/<pass>/<page>.tsv, with the columns
id, kind, text, note (no header). A page is complete when every line id of the page appears.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("SAC_ROOT", "data/interim/sac1956"))
STRIPS_PER_CHUNK = 45


def make() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    chunks, current, count = [], [], 0
    for key, page in manifest.items():  # keys sort as A001..A043, C001..C306
        current.append({"page": key, "strips": page["strips"]})
        count += len(page["strips"])
        if count >= STRIPS_PER_CHUNK:
            chunks.append(current)
            current, count = [], 0
    if current:
        chunks.append(current)
    out = ROOT / "chunks"
    out.mkdir(parents=True, exist_ok=True)
    for i, pages in enumerate(chunks, start=1):
        (out / f"chunk{i:02d}.json").write_text(json.dumps({"chunk": i, "pages": pages}, indent=1))
        strips = sum(len(p["strips"]) for p in pages)
        print(
            f"chunk{i:02d}: {pages[0]['page']}..{pages[-1]['page']}  pages={len(pages)} strips={strips}"
        )


def check(pass_name: str) -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for path in sorted((ROOT / "chunks").glob("chunk*.json")):
        pages = json.loads(path.read_text())["pages"]
        done, missing = [], []
        for p in pages:
            tsv = ROOT / pass_name / f"{p['page']}.tsv"
            want = {line["id"] for line in manifest[p["page"]]["lines"]}
            have = set()
            if tsv.exists():
                for row in tsv.read_text().splitlines():
                    if row.strip():
                        have.add(row.split("\t")[0].rstrip("+").strip())
            (done if want <= have else missing).append(p["page"])
        print(
            f"{path.stem}: {len(done)}/{len(pages)} pages complete"
            + (f"; missing {missing}" if missing else "")
        )


if __name__ == "__main__":
    {"make": lambda: make(), "check": lambda: check(sys.argv[2])}[sys.argv[1]]()
