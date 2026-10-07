"""Assemble the transcribed SAC 1956 list into tables, and check them.

    python scripts/sac1956_assemble.py

Inputs (data/interim/sac1956/): compare/agreed.tsv (lines both passes read identically and that
pass the rules) and adjudicate/decisions/*.tsv (lines settled by adjudication). Every line id
of the manifest should be in exactly one of them; gaps are reported.

Outputs (data/curated/sac1956/):
  lines.csv          every line: id, page, kind, text, source (agreed / adjudicated), type
  complexes.csv      one row per complex or sub-complex, with counts of DGZs and installations
  dgz.csv            one row per designated ground zero (aim point)
  installations.csv  one row per installation line (category code, BE number)
  msites.csv         the "M-n" rows
  airfields.csv      the Part II airfield list
  anomalies.csv      lines that still do not parse, or that carry a "?"
  REPORT.md          counts and validation checks
and data/curated/labels/us_1956_sac_complexes.csv in the shared label schema.
"""

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sac1956_compare as cmp  # noqa: E402

ROOT = Path("data/interim/sac1956")
OUT = Path("data/curated/sac1956")
SOURCE_URL = {
    "C": "https://nsarchive.gwu.edu/document/15800-09-urban-industrial-target-list-part-i",
    "A": "https://nsarchive2.gwu.edu/nukevault/ebb538-Cold-War-Nuclear-Target-List-Declassified-First-Ever/",
}
# Country suffixes as printed after a complex name; no suffix means the USSR.
SUFFIXES = [
    ("N KOREA", "North Korea"), ("N. KOREA", "North Korea"), ("KOREA", "North Korea"),
    ("N VIETNAM", "North Vietnam"), ("VIETNAM", "North Vietnam"),
    ("GER SOVZONE", "East Germany"), ("E GER", "East Germany"), ("E. GER", "East Germany"), ("E.GER", "East Germany"),
    ("CZECH", "Czechoslovakia"), ("CZEC", "Czechoslovakia"), ("CZE", "Czechoslovakia"), ("CZ", "Czechoslovakia"),
    ("POL", "Poland"), ("HUNG", "Hungary"), ("RUM", "Romania"),
    ("BULG", "Bulgaria"), ("BUL", "Bulgaria"), ("ALB", "Albania"), ("AL8", "Albania"),
    ("MANCH", "China (Manchuria)"), ("CHINA", "China"), ("CHIN", "China"),
]


def degrees(dm: str, hem: str | None = None) -> float:
    """'5545' -> 55.75; '03737' -> 37.6167; W hemisphere -> negative."""
    value = int(dm[:-2]) + int(dm[-2:]) / 60
    return round(-value if hem == "W" else value, 4)


def country_of(name: str) -> tuple[str, str]:
    clean = re.sub(r"[.,]", " ", name).strip()
    clean = re.sub(r"\s+", " ", clean)
    for suffix, country in SUFFIXES:
        if clean.endswith(" " + suffix) or clean == suffix:
            return clean[: -len(suffix)].strip(" -"), country
    return clean, "USSR"


def load_final(manifest: dict) -> tuple[dict, list]:
    final = {}
    for raw in (ROOT / "compare" / "agreed.tsv").read_text(encoding="utf-8").splitlines():
        if raw.strip():
            line_id, kind, text = (raw.split("\t") + ["", ""])[:3]
            final[line_id] = {"kind": kind, "text": text, "source": "agreed", "confidence": "high", "note": ""}
    for tsv in sorted((ROOT / "adjudicate" / "decisions").glob("*.tsv")):
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                parts = (raw.split("\t") + [""] * 6)[:6]
                final[parts[0].strip()] = {
                    "kind": parts[1].strip().lower(), "text": parts[2].strip(), "source": "adjudicated",
                    "choice": parts[3].strip(), "confidence": parts[4].strip(), "note": parts[5].strip(),
                }
    gaps = [line["id"] for page in manifest.values() for line in page["lines"] if line["id"] not in final]
    return final, gaps


def ordered_ids(manifest: dict, final: dict) -> list[str]:
    """Manifest order, with unlabelled '+' lines placed after the label they follow."""
    extra = defaultdict(list)
    for line_id in final:
        if line_id.endswith("+"):
            extra[line_id.rstrip("+")].append(line_id)
    ids = []
    for page in manifest.values():
        for line in page["lines"]:
            ids.append(line["id"])
            ids += sorted(extra.get(line["id"], []), key=len)
    return ids


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    final, gaps = load_final(manifest)
    OUT.mkdir(parents=True, exist_ok=True)
    lines, complexes, dgzs, installs, msites, airfields, anomalies = [], [], [], [], [], [], []
    codes = {r["code"]: r["description"] for r in csv.DictReader(open("data/curated/labels/sac1956_category_codes.csv"))}
    current = None  # the complex or sub-complex that following lines belong to
    parent = None  # the enclosing complex (for sub-complexes)

    def handle(line_id: str, page: str, text: str, typ: str, f: dict) -> None:
        nonlocal current, parent
        if typ == "airfield":
            airfields.append({
                "id": line_id, "page": page, "priority": f["prio"], "ref": f["ref"], "name": f["name"],
                "be": f"{f['wac']}-{f['num'] or ''}", "lat": degrees(f["lat"]), "lon": degrees(f["lon"], f.get("hem")),
                "code": f["code"], "text": text,
            })
        elif typ in ("complex", "subcomplex"):
            name, country = country_of(f["name"])
            row = {
                "id": line_id, "page": page, "level": typ, "priority": f.get("prio", ""), "ref": f.get("ref", ""),
                "name": name, "name_printed": f["name"], "country": country,
                "lat": degrees(f["lat"]), "lon": degrees(f["lon"], f.get("hem")),
                "parent_id": parent["id"] if typ == "subcomplex" and parent else "",
                "n_dgz": 0, "n_installations": 0, "n_population": 0, "n_msites": 0, "last_page": page,
            }
            complexes.append(row)
            current = row
            if typ == "complex":
                parent = row
        elif current is None:
            anomalies.append({"id": line_id, "text": text, "problem": "line before any complex header"})
        elif typ == "dgz":
            dgzs.append({
                "id": line_id, "page": page, "complex_id": current["id"], "label": f["label"],
                "lat": degrees(f["lat"]), "lon": degrees(f["lon"].zfill(5), f.get("hem")), "text": text,
            })
            current["n_dgz"] += 1
            current["last_page"] = page
        elif typ == "installation":
            installs.append({
                "id": line_id, "page": page, "complex_id": current["id"], "category": f["cat"],
                "category_name": codes.get(f["cat"], ""), "be_wac": f["wac"], "be_number": f["num"] or "", "text": text,
            })
            current["n_installations"] += 1
            current["n_population"] += f["cat"] == "275"
            current["last_page"] = page
        elif typ == "msite":
            msites.append({
                "id": line_id, "page": page, "complex_id": current["id"], "ref": f.get("ref") or "", "name": f["name"],
                "m_number": f["mnum"], "lat": degrees(f["lat"]), "lon": degrees(f["lon"]), "label": f["label"], "text": text,
            })
            current["n_msites"] += 1

    for line_id in ordered_ids(manifest, final):
        rec = final.get(line_id)
        if rec is None:
            continue
        page = line_id.split("-")[0]
        text = rec["text"]
        if rec["kind"] != "data":
            lines.append({"id": line_id, "page": page, "kind": rec["kind"], "text": text, "source": rec["source"], "type": ""})
            continue
        typ, f, problems = cmp.classify(page, cmp.norm(text), cmp.light(text))
        lines.append({"id": line_id, "page": page, "kind": "data", "text": text, "source": rec["source"], "type": typ})
        if "?" in text or problems:
            anomalies.append({"id": line_id, "text": text, "problem": "; ".join(problems) or "contains ?"})
        if typ == "merged":
            for part_typ, part_f, _ in f["parts"]:
                handle(line_id, page, text, part_typ, part_f)
        elif typ != "unparsed":
            handle(line_id, page, text, typ, f)

    def write(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    for name, rows in [("lines.csv", lines), ("complexes.csv", complexes), ("dgz.csv", dgzs),
                       ("installations.csv", installs), ("msites.csv", msites), ("airfields.csv", airfields),
                       ("anomalies.csv", anomalies)]:
        write(name, rows)

    # Shared-schema label file: one row per top-level complex.
    label_rows = []
    for c in complexes:
        if c["level"] != "complex":
            continue
        label_rows.append({
            "plan_id": "us_1956_sac_complexes", "planner": "US (SAC)", "target_country": c["country"], "plan_year": 1956,
            "provenance": "study", "seq": c["priority"], "name_source": c["name_printed"], "name_modern": "",
            "target_class": "urban-industrial complex", "selected": 1, "priority": c["priority"], "weapons": "",
            "yield_kt": "", "lat": c["lat"], "lon": c["lon"],
            "source_doc": "SAC Atomic Weapons Requirements Study for 1959 (June 1956), Part I complex list (NSA EBB 538)",
            "source_url": SOURCE_URL["C"], "source_page": c["page"], "quote": f"{c['priority']} {c['ref']} {c['name_printed']}",
            "notes": f"DGZs={c['n_dgz']}; installations={c['n_installations']} (sub-complexes counted separately)",
        })
    labels_path = Path("data/curated/labels/us_1956_sac_complexes.csv")
    if label_rows:
        with open(labels_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(label_rows[0].keys()))
            w.writeheader()
            w.writerows(label_rows)

    report(complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final)


def report(complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final) -> None:
    top = [c for c in complexes if c["level"] == "complex"]
    by_id = {c["id"]: c for c in complexes}

    def totals(c):  # a complex plus its sub-complexes
        kids = [k for k in complexes if k["parent_id"] == c["id"]]
        return c["n_dgz"] + sum(k["n_dgz"] for k in kids), c["n_installations"] + sum(k["n_installations"] for k in kids)

    out = ["# SAC 1956 list: assembly report", ""]
    src = Counter(r["source"] for r in final.values())
    out += [f"- Lines with a final reading: {len(final)} ({src['agreed']} agreed by both passes, "
            f"{src['adjudicated']} adjudicated); lines with no reading yet: {len(gaps)}",
            f"- Complexes: {len(top)}; sub-complexes: {len(complexes) - len(top)}; DGZs: {len(dgzs)}; "
            f"installation lines: {len(installs)}; M-n rows: {len(msites)}; airfields: {len(airfields)}",
            f"- Lines still carrying '?' or failing a rule: {len(anomalies)}", ""]
    out += ["## Anchors", "", "| Complex | Priority | DGZs | Installations (with sub-complexes) |", "|---|---|---|---|"]
    for name in ["MOSCOW", "LENINGRAD", "BERLIN"]:
        for c in top:
            if c["name"].startswith(name):
                d, i = totals(c)
                out.append(f"| {c['name_printed']} | {c['priority']} | {d} | {i} |")
    prios = [c["priority"] for c in top if c["priority"]]
    nums = sorted(int(re.sub(r"\D", "", p)) for p in prios if re.sub(r"\D", "", p))
    dup = [p for p, n in Counter(prios).items() if n > 1]
    missing = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
    out += ["", "## Priority numbers", "",
            f"- {len(prios)} complexes carry a priority; highest {max(nums) if nums else '-'}; "
            f"duplicates: {len(dup)} {dup[:20]}; numbers missing from 1..max: {len(missing)} {missing[:30]}"]
    refs = [int(c["ref"]) for c in top if c["ref"].isdigit()]
    drops = sum(1 for x, y in zip(refs, refs[1:]) if y < x)
    out += [f"- Reference numbers that drop below the previous complex (alphabetical order check): {drops}"]
    out += ["", "## Complexes by country", "", "| Country | Complexes | DGZs | Installations |", "|---|---|---|---|"]
    agg = defaultdict(lambda: [0, 0, 0])
    for c in top:
        d, i = totals(c)
        agg[c["country"]][0] += 1
        agg[c["country"]][1] += d
        agg[c["country"]][2] += i
    for country, (n, d, i) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        out.append(f"| {country} | {n} | {d} | {i} |")
    cats = Counter(r["category"] for r in installs)
    out += ["", "## Most common installation categories", ""]
    out += [f"- {code} {next((r['category_name'] for r in installs if r['category'] == code), '')}: {n}" for code, n in cats.most_common(15)]
    unknown = sorted({r["category"] for r in installs if not r["category_name"]})
    out += ["", f"- Category codes not in the code list: {unknown}"]
    (OUT / "REPORT.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
