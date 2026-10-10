"""Audit the curated SAC 1956 transcription against an independent re-reading of a sample.

    python scripts/sac1956_audit.py prep     # compare, crop the disagreements, write batches
    python scripts/sac1956_audit.py report   # after adjudication: error rates, data/curated/...

A random 5% of the data lines of data/curated/sac1956/lines.csv (seed 1956) was re-read by
readers who saw neither the passes nor the curated text (data/interim/sac1956_excerpts/AUDIT.md;
sample in audit/audit*.json, readings in audit/out_audit*.tsv). Where a reading and the curated
text differ (after the comparison normalisation of sac1956_compare.norm), the line is cropped
from the scan and judged blind: the judge sees the two readings as X and Y, in a random order,
and does not know which is the curated one. Decisions go to audit/decisions/*.tsv:
id, verdict (X, Y, neither), the text as printed, confidence, note.

The report gives the residual error rate of the curated lines (lines whose curated text the
judge rejects), with a Wilson 95% interval, by line type.
"""

import csv
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import pymupdf
import sac1956_compare as cmp
import sac1956_strips as strips

MAIN = Path("data/interim/sac1956")
AUDIT = Path("data/interim/sac1956_excerpts/audit")
CURATED = Path("data/curated/sac1956")
ZOOM = 2.5


def sample() -> list[str]:
    return [
        i
        for f in sorted(AUDIT.glob("audit[0-9].json"))
        for p in json.loads(f.read_text())["pages"]
        for i in p["ids"]
    ]


def readings() -> dict[str, tuple[str, str]]:
    out = {}
    for f in sorted(AUDIT.glob("out_audit*.tsv")):
        for raw in f.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                parts = [*raw.split("\t"), "", ""][:3]
                out[parts[0].strip()] = (parts[1].strip(), parts[2].strip())
    return out


def curated() -> dict[str, dict]:
    return {r["id"]: r for r in csv.DictReader(open(CURATED / "lines.csv", encoding="utf-8"))}


def disagreements() -> tuple[list[str], list[dict]]:
    ids, read, cur = sample(), readings(), curated()
    rng = random.Random(1956)
    out = []
    for i in ids:
        a = cur[i]["text"]
        b = read.get(i, ("", ""))[0]
        if cmp.norm(a) == cmp.norm(b):
            continue
        swap = rng.random() < 0.5
        out.append(
            {
                "id": i,
                "page": i.split("-")[0],
                "x": b if swap else a,
                "y": a if swap else b,
                "curated_is": "Y" if swap else "X",
            }
        )
    return ids, out


def crop(manifest: dict, docs: dict, line_id: str, path: Path) -> None:
    page = line_id.split("-")[0]
    info = manifest[page]
    gray = strips.render(docs[page[0]], int(page[1:]) - 1)
    lines = info["lines"]
    index = {line["id"]: n for n, line in enumerate(lines)}
    base = line_id.rstrip("+")
    i = index[base]
    if line_id.endswith("+"):
        top = lines[i]["y0"] - 6
        bottom = lines[i + 1]["y1"] + 6 if i + 1 < len(lines) else lines[i]["y1"] + 40
        mark = (lines[i]["y1"], bottom - 6)
    else:
        top = lines[i - 1]["y0"] - 6 if i else lines[i]["y0"] - 20
        bottom = lines[i + 1]["y1"] + 6 if i + 1 < len(lines) else lines[i]["y1"] + 20
        mark = (lines[i]["y0"], lines[i]["y1"])
    top, bottom = max(top, 0), min(bottom, gray.shape[0])
    x0, x1 = info["x"]
    img = Image.fromarray(gray[top:bottom, x0:x1])
    img = img.resize((round(img.width * ZOOM), round(img.height * ZOOM)), Image.LANCZOS)
    img = img.convert("RGB")
    pen = ImageDraw.Draw(img)
    pen.rectangle(
        [0, round((mark[0] - top - 3) * ZOOM), 14, round((mark[1] - top + 3) * ZOOM)],
        fill=(220, 0, 0),
    )
    img.save(path, optimize=True)


def prep(batch_size: int = 40) -> None:
    ids, rows = disagreements()
    read = readings()
    missing = [i for i in ids if i not in read]
    print(f"sample {len(ids)}, read {len(ids) - len(missing)}, disagreements {len(rows)}")
    if missing:
        print("not read:", missing[:20])
    manifest = json.loads((MAIN / "manifest.json").read_text())
    docs = {code: pymupdf.open(p) for code, p in strips.SETS["main"][0].items()}
    (AUDIT / "crops").mkdir(exist_ok=True)
    key = []
    items = []
    for r in rows:
        path = AUDIT / "crops" / f"{r['id'].replace('+', 'plus')}.png"
        crop(manifest, docs, r["id"], path)
        items.append({"id": r["id"], "X": r["x"], "Y": r["y"], "crop": str(path)})
        key.append({"id": r["id"], "curated_is": r["curated_is"]})
    for n in range(0, len(items), batch_size):
        (AUDIT / f"judge{n // batch_size + 1:02d}.json").write_text(
            json.dumps(items[n : n + batch_size], indent=1, ensure_ascii=False)
        )
    # The key stays out of the judges' way: they are told not to open it.
    (AUDIT / "key.json").write_text(json.dumps(key, indent=1))
    print(f"{len(items)} crops in {(len(items) + batch_size - 1) // batch_size} batches")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def report() -> None:
    ids = sample()
    cur, read = curated(), readings()
    key = {k["id"]: k["curated_is"] for k in json.loads((AUDIT / "key.json").read_text())}
    decisions = {}
    for f in sorted((AUDIT / "decisions").glob("*.tsv")):
        for raw in f.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                p = (raw.split("\t") + [""] * 5)[:5]
                decisions[p[0].strip()] = {
                    "verdict": p[1].strip().upper(),
                    "text": p[2].strip(),
                    "confidence": p[3].strip(),
                    "note": p[4].strip(),
                }
    rows = []
    for i in ids:
        a, b = cur[i]["text"], read.get(i, ("", ""))[0]
        if cmp.norm(a) == cmp.norm(b):
            outcome, judged = "agree", ""
        elif i not in decisions:
            outcome, judged = "not judged", ""
        else:
            d = decisions[i]
            judged = d["text"]
            if d["verdict"] == key[i]:
                outcome = "curated right"
            elif d["verdict"] in ("X", "Y"):
                outcome = "curated wrong"
            else:  # neither reading matches the judge's
                outcome = "curated wrong" if cmp.norm(judged) != cmp.norm(a) else "curated right"
        rows.append(
            {
                "id": i,
                "type": cur[i]["type"],
                "source": cur[i]["source"],
                "curated": a,
                "audit": b,
                "judged": judged,
                "outcome": outcome,
                "note": decisions.get(i, {}).get("note", ""),
            }
        )
    with open(CURATED / "audit.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    count = Counter(r["outcome"] for r in rows)
    k = count["curated wrong"]
    lo, hi = wilson(k, n)
    lines = [
        f"Sample: {n} data lines; agree {count['agree']}; disagree {n - count['agree']} "
        f"(curated right {count['curated right']}, curated wrong {k}, not judged "
        f"{count['not judged']})",
        f"Residual error rate of the curated lines: {k}/{n} = {k / n:.2%} (95% CI {lo:.2%} to "
        f"{hi:.2%})",
        f"Audit reader's own error rate: {n - count['agree'] - k - count['not judged']}/{n}",
    ]
    by_type = Counter((r["type"], r["outcome"] == "curated wrong") for r in rows)
    for typ in sorted({r["type"] for r in rows}):
        tot = by_type[(typ, True)] + by_type[(typ, False)]
        lines.append(f"  {typ}: {by_type[(typ, True)]} wrong of {tot}")
    by_source = Counter((r["source"], r["outcome"] == "curated wrong") for r in rows)
    for src in sorted({r["source"] for r in rows}):
        tot = by_source[(src, True)] + by_source[(src, False)]
        lines.append(f"  {src}: {by_source[(src, True)]} wrong of {tot}")
    print("\n".join(lines))


if __name__ == "__main__":
    {"prep": prep, "report": report}[sys.argv[1]]()
