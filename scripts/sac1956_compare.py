"""Compare two independent transcription passes of the SAC 1956 list and run rule checks.

    python scripts/sac1956_compare.py passA passB

Reads data/interim/sac1956/<pass>/<page>.tsv (id, kind, text, note), aligns the passes by line
id, and writes to data/interim/sac1956/compare/:
  agreed.tsv     lines both passes read identically (after normalising spaces), kind and text
  disputes.csv   lines to adjudicate: the passes differ, a character is unreadable, a line is
                 missing from one pass, or an agreed reading breaks a rule (see RULES below)
  summary.txt    counts
"""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("data/interim/sac1956")
CODES = {
    row["code"].strip()
    for row in csv.DictReader(open("data/curated/labels/sac1956_category_codes.csv", encoding="utf-8"))
}

# Line formats (after normalisation: single spaces, no spaces next to hyphens).
COMPLEX = re.compile(r"^(?P<prio>\d{1,4}) (?P<ref>\d{4}) (?P<name>.+?) (?P<lat>\d{4})-(?P<lon>\d{5})$")
SUBCOMPLEX = re.compile(r"^(?P<name>[A-Z][^\d].*?) (?P<lat>\d{4})-(?P<lon>\d{5})$")
DGZ = re.compile(r"^(?P<lat>\d{4})-(?P<lon>\d{4,5})(?P<hem>[EW]) (?P<label>[A-Z]{1,2})$")
INSTALL = re.compile(r"^(?P<cat>\d{3}) (?P<wac>\d{4})-(?P<num>\d{4})?$")
AIRFIELD = re.compile(
    r"^(?P<prio>\d{1,4}) (?P<ref>\d{4,5}) (?P<name>.+?) (?P<wac>\d{4})-(?P<num>\d{4}) "
    r"(?P<lat>\d{4})-(?P<lon>\d{5})(?P<hem>[EW]?) (?P<code>[A-Z])$"
)


def norm(text: str) -> str:
    text = text.replace("‐", "-").replace("–", "-").replace("—", "-").upper()
    text = re.sub(r"\s*-\s*", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def load(pass_name: str) -> dict[str, tuple[str, str, str]]:
    rows = {}
    for tsv in sorted((ROOT / pass_name).glob("*.tsv")):
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            parts = (raw.split("\t") + ["", "", ""])[:4]
            rows[parts[0].strip()] = (parts[1].strip().lower(), parts[2].strip(), parts[3].strip())
    return rows


def coords_ok(lat: str, lon: str) -> list[str]:
    problems = []
    if int(lat[2:]) >= 60 or int(lon[-2:]) >= 60:
        problems.append("minutes>=60")
    if not 15 <= int(lat[:2]) <= 78:
        problems.append("latitude out of range")
    return problems


def classify(page: str, text: str) -> tuple[str, dict, list[str]]:
    """Return (line type, fields, rule problems) for one normalised data line."""
    if page.startswith("A"):
        m = AIRFIELD.match(text)
        if not m:
            return "unparsed", {}, ["airfield row does not match the expected format"]
        return "airfield", m.groupdict(), coords_ok(m["lat"], m["lon"])
    for kind, pattern in (("complex", COMPLEX), ("dgz", DGZ), ("installation", INSTALL), ("subcomplex", SUBCOMPLEX)):
        m = pattern.match(text)
        if m:
            fields, problems = m.groupdict(), []
            if kind in ("complex", "subcomplex"):
                problems = coords_ok(fields["lat"], fields["lon"])
            elif kind == "dgz":
                problems = coords_ok(fields["lat"], fields["lon"].zfill(5))
            elif kind == "installation":
                if fields["cat"] not in CODES:
                    problems.append(f"category {fields['cat']} not in code list")
                if fields["cat"] == "275" and fields["num"] and not fields["num"].startswith("9"):
                    problems.append("population line without a 9xxx number")
            return kind, fields, problems
    return "unparsed", {}, ["line does not match any expected format"]


def main(pass_a: str, pass_b: str) -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    a, b = load(pass_a), load(pass_b)
    out = ROOT / "compare"
    out.mkdir(exist_ok=True)
    agreed, disputes, stats = [], [], Counter()
    for page, info in manifest.items():
        ids = [line["id"] for line in info["lines"]]
        ids += sorted({i for i in list(a) + list(b) if i.startswith(page + "-") and i.endswith("+")})
        for line_id in ids:
            ra, rb = a.get(line_id), b.get(line_id)
            if ra is None and rb is None:
                if not line_id.endswith("+"):
                    stats["missing in both"] += 1
                    disputes.append([line_id, page, "", "", "", "", "missing in both passes"])
                continue
            if ra is None or rb is None:
                have = ra or rb
                if have[0] != "data" and line_id.endswith("+") is False:
                    stats["one-sided non-data"] += 1
                stats["missing in one pass"] += 1
                disputes.append([line_id, page, (ra or ("",))[0], (rb or ("",))[0], (ra or ("", ""))[1], (rb or ("", ""))[1], "missing in one pass"])
                continue
            kind_a, kind_b = ra[0], rb[0]
            if kind_a != "data" and kind_b != "data":
                stats["furniture agreed"] += 1
                agreed.append([line_id, kind_a if kind_a == kind_b else "furniture", norm(ra[1])])
                continue
            text_a, text_b = norm(ra[1]), norm(rb[1])
            reasons = []
            if kind_a != kind_b:
                reasons.append(f"kind differs ({kind_a} vs {kind_b})")
            if text_a != text_b:
                reasons.append("text differs")
            if "?" in text_a or "?" in text_b:
                reasons.append("unreadable character")
            if not reasons:
                line_type, _, problems = classify(page, text_a)
                if problems:
                    reasons += problems
                    stats["agreed but breaks a rule"] += 1
                else:
                    stats["agreed"] += 1
                    agreed.append([line_id, "data", text_a])
                    continue
            else:
                stats["passes differ"] += 1
            disputes.append([line_id, page, kind_a, kind_b, ra[1], rb[1], "; ".join(reasons)])
    with open(out / "agreed.tsv", "w", encoding="utf-8") as f:
        for row in agreed:
            f.write("\t".join(row) + "\n")
    with open(out / "disputes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "page", "kind_a", "kind_b", "text_a", "text_b", "reasons"])
        writer.writerows(disputes)
    total = sum(stats.values())
    lines = [f"{k}: {v}" for k, v in stats.most_common()] + [f"total lines: {total}", f"disputes: {len(disputes)}"]
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
