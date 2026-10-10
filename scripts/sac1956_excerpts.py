"""Assemble the transcribed excerpts of the SAC 1956 study, and set them against the full lists.

    python scripts/sac1956_excerpts.py

The National Security Archive published three of the study's lists only in excerpt: the Part I
airfield list (section 4, pages F...), the Part II complex list (section 7, pages R...) and the
cross-reference list (section 2, pages X...). They were transcribed like the full lists (two
passes, compared, disputes adjudicated) under data/interim/sac1956_excerpts/, and are parsed
here with the same code (sac1956_assemble.parse).

Outputs (data/curated/sac1956/excerpts/):
  lines.csv              every line of the excerpts: id, page, kind, text, source, type
  part2_complexes.csv    Part II complexes and sub-complexes, with counts of DGZs and installations
  part2_dgz.csv          Part II aim points
  part2_installations.csv
  part1_airfields.csv    the Part I airfield rows
  crossref.csv           the cross-reference rows: entries (with a reference number) and the
                         names listed under them
  part2_vs_part1.csv     each Part II complex beside the Part I complex of the same reference
  part1_vs_part2_airfields.csv  each Part I airfield beside the Part II row of the same BE number
  lost_page.csv          cross-reference entries that fall in the gap of the lost Part I page
  REPORT.md              counts and the comparisons
"""

import csv
import difflib
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sac1956_assemble as asm
import sac1956_compare as cmp

ROOT = Path("data/interim/sac1956_excerpts")
OUT = asm.OUT / "excerpts"
# Cross-reference rows: "5112 MONINO AF SEE 5570 NOGINSK", "5075 MOINESTI RUM SEE 1945
# DARMANESTI RUM"; names indented under an entry carry no number ("BELBEK AF").
XREF = re.compile(
    r"^(?:(?P<ref>\d{4,5}) )?(?P<name>.+?)(?: (?P<af>AF))?"
    r"(?: SEE (?P<see_ref>\d{4,5}) (?P<see_name>.+))?$"
)
# The Part I page lost from the scan lies between these two complexes (README, "Gaps").
LOST_AFTER, LOST_BEFORE = "ARTSIZ", "ATBASAR"
SOURCE_URL = (
    "https://nsarchive2.gwu.edu/nukevault/ebb538-Cold-War-Nuclear-Target-List-Declassified-"
    "First-Ever/documents/section7.pdf"
)


def write(name: str, rows: list[dict]) -> None:
    if rows:
        asm.write_csv(OUT / name, rows)


def crossref(lines: list[dict]) -> list[dict]:
    rows, entry = [], None
    for line in lines:
        if not line["page"].startswith("X") or line["kind"] != "data":
            continue
        for text in line["text"].split("||"):
            text = cmp.digits_for_letters(cmp.light(text))
            m = XREF.match(text)
            if not m:
                rows.append(
                    {
                        "id": line["id"],
                        "page": line["page"],
                        "level": "unparsed",
                        "ref": "",
                        "name": text,
                        "airfield": "",
                        "see_ref": "",
                        "see_name": "",
                        "entry_ref": "",
                        "entry_name": "",
                    }
                )
                continue
            if m["ref"]:
                entry = m
            name, country = asm.country_of(m["name"])
            rows.append(
                {
                    "id": line["id"],
                    "page": line["page"],
                    "level": "entry" if m["ref"] else "listed under",
                    "ref": m["ref"] or "",
                    "name": name,
                    "name_printed": m["name"],
                    "country": country,
                    "airfield": bool(m["af"]),
                    "see_ref": m["see_ref"] or "",
                    "see_name": m["see_name"] or "",
                    "entry_ref": "" if m["ref"] or entry is None else entry["ref"],
                    "entry_name": "" if m["ref"] or entry is None else entry["name"],
                }
            )
    return rows


def coord_key(row: dict) -> tuple:
    try:
        return (round(float(row["lat"]), 3), round(float(row["lon"]), 3))
    except (TypeError, ValueError):  # a coordinate with a "?" or none at all
        return ()


def line_key(line_id: str) -> tuple:
    page, label = line_id.split("-")
    return (page, int(label[1:].rstrip("+")), label.count("+"))


def page_breaks(part2: dict, part1: list[dict], dgz1: list[dict], inst1: list[dict]) -> dict:
    """Find where the excerpt skips pages, and which Part II complexes are seen whole.

    The R pages are a selection, so the lines at the top of a page may continue a complex that
    began on a page not published, and the last complex of a page may run on into one. Part II
    lists the same complexes in the same order as Part I, with the same installations, so Part I
    tells which complex the leading lines of a page belong to (by BE number or aim-point
    coordinates). Leading lines that belong to another complex than the one open at the end of
    the previous R page are detached (complex_id empty, `part1_owner` set), and the open
    complex is cut. A complex counts as whole when it is not cut and the next complex header in
    the excerpt is its successor in Part I. Returns {complex id: whole?}."""
    top1 = {c["id"]: (c["parent_id"] or c["id"]) for c in part1}
    ref1 = {c["id"]: c["ref"] for c in part1}
    owner = {}
    for i in inst1:
        owner.setdefault(
            ("i", i["category"], i["be_wac"], i["be_number"]), ref1[top1[i["complex_id"]]]
        )
    for d in dgz1:
        owner.setdefault(("d", *coord_key(d)), ref1[top1[d["complex_id"]]])
    for c in part1:
        if c["level"] == "subcomplex":
            owner.setdefault(("s", c["name"]), ref1[top1[c["id"]]])
    tops = [c["ref"] for c in part1 if c["level"] == "complex" and c["ref"]]
    successor = dict(itertools.pairwise(tops))
    items = [("c", c) for c in part2["complexes"]]
    items += [("d", d) for d in part2["dgzs"]] + [("i", i) for i in part2["installs"]]
    items.sort(key=lambda x: line_key(x[1]["id"]))
    current, cut, order = None, set(), []
    page, leading = None, []

    def key(kind: str, r: dict) -> tuple:
        if kind == "i":
            return ("i", r["category"], r["be_wac"], r["be_number"])
        return ("d", *coord_key(r)) if kind == "d" else ("s", r["name"])

    def settle() -> None:
        nonlocal current
        if not leading:
            return
        votes = Counter(owner[k] for k in (key(*x) for x in leading) if k in owner)
        if votes and current is not None and votes.most_common(1)[0][0] != current["ref"]:
            cut.add(current["id"])
            ref = votes.most_common(1)[0][0]
            subs = {r["id"] for k, r in leading if k == "s"}
            for k, r in leading:
                r["part1_owner"] = ref
                if k == "s":
                    r["parent_id"] = ""  # a sub-complex of a complex begun on a skipped page
                elif r["complex_id"] not in subs:
                    r["complex_id"] = ""
            current = None
        leading.clear()

    for kind, r in items:
        if r["page"] != page:
            settle()
            page = r["page"]
            at_top = True
        if kind == "c" and r["level"] == "complex":
            at_top = False
            settle()
            current = r
            order.append(r)
        elif at_top:
            leading.append(("s" if kind == "c" else kind, r))
    settle()
    whole = {}
    for a, b in itertools.pairwise([*order, None]):
        whole[a["id"]] = (
            a["id"] not in cut and b is not None and successor.get(a["ref"]) == b["ref"]
        )
    for r in part2["complexes"] + part2["dgzs"] + part2["installs"]:
        r.setdefault("part1_owner", "")
    return whole


def compare_complexes(
    part2: dict, part1: list[dict], dgz1: list[dict], inst1: list[dict], whole: dict
):
    """Each Part II complex (top level) beside the Part I complex with the same reference."""
    by_ref = {c["ref"]: c for c in part1 if c["level"] == "complex" and c["ref"]}
    subs1, aims1, insts1 = defaultdict(list), defaultdict(list), defaultdict(list)
    for c in part1:
        if c["parent_id"]:
            subs1[c["parent_id"]].append(c)
    top1 = {c["id"]: (c["parent_id"] or c["id"]) for c in part1}
    for d in dgz1:
        aims1[top1[d["complex_id"]]].append(d)
    for i in inst1:
        insts1[top1[i["complex_id"]]].append(i)
    top2 = {c["id"]: (c["parent_id"] or c["id"]) for c in part2["complexes"]}
    aims2, insts2, subs2 = defaultdict(list), defaultdict(list), defaultdict(list)
    for d in part2["dgzs"]:
        if d["complex_id"]:
            aims2[top2[d["complex_id"]]].append(d)
    for i in part2["installs"]:
        if i["complex_id"]:
            insts2[top2[i["complex_id"]]].append(i)
    for c in part2["complexes"]:
        if c["parent_id"]:
            subs2[c["parent_id"]].append(c)
    rows = []
    for c in part2["complexes"]:
        if c["level"] != "complex":
            continue
        p = by_ref.get(c["ref"])
        a2, i2 = aims2[c["id"]], insts2[c["id"]]
        row = {
            "part2_id": c["id"],
            "ref": c["ref"],
            "name": c["name"],
            "part2_priority": c["priority"],
            "seen_whole": whole.get(c["id"], False),
            "part2_dgz": len(a2),
            "part2_installations": len(i2),
            "part2_subcomplexes": len(subs2[c["id"]]),
            "part1_id": p["id"] if p else "",
            "part1_name": p["name"] if p else "",
            "part1_priority": p["priority"] if p else "",
            "part1_dgz": len(aims1[p["id"]]) if p else "",
            "part1_installations": len(insts1[p["id"]]) if p else "",
            "part1_subcomplexes": len(subs1[p["id"]]) if p else "",
        }
        if p:
            k1 = {coord_key(d) for d in aims1[p["id"]]}
            k2 = {coord_key(d) for d in a2}
            b1 = {(i["category"], i["be_wac"], i["be_number"]) for i in insts1[p["id"]]}
            b2 = {(i["category"], i["be_wac"], i["be_number"]) for i in i2}
            row |= {
                "same_header_coords": coord_key(p) == coord_key(c),
                "dgz_kept": len(k1 & k2),
                "dgz_dropped": len(k1 - k2),
                "dgz_added": len(k2 - k1),
                "installations_kept": len(b1 & b2),
                "installations_dropped": len(b1 - b2),
                "installations_added": len(b2 - b1),
            }
        rows.append(row)
    return rows


def compare_airfields(part1_af: list[dict], part2_af: list[dict]) -> list[dict]:
    by_be = defaultdict(list)
    for a in part2_af:
        by_be[a["be"]].append(a)
    rows = []
    for a in part1_af:
        match = by_be.get(a["be"], []) if not a["be"].endswith("-") else []
        if not match:  # fall back on the name and reference (and for BE numbers left blank)
            match = [b for b in part2_af if b["name"] == a["name"] and b["ref"] == a["ref"]]
        b = match[0] if match else None
        rows.append(
            {
                "part1_id": a["id"],
                "name": a["name"],
                "ref": a["ref"],
                "be": a["be"],
                "part1_priority": a["priority"],
                "part2_id": b["id"] if b else "",
                "part2_priority": b["priority"] if b else "",
                "same_coords": (coord_key(a) == coord_key(b)) if b else "",
                "same_code": (a["code"] == b["code"]) if b else "",
            }
        )
    return rows


def crossdoc_verdicts(af_versus: list[dict]) -> None:
    """Attach the verdicts of the cross-document check (crossdoc/decisions.tsv): for each
    airfield row whose two printings were transcribed differently, whether one transcription
    was a misread (since corrected) or the printings themselves differ."""
    pairs_path, decisions_path = (
        ROOT / "crossdoc" / "pairs.json",
        ROOT / "crossdoc" / "decisions.tsv",
    )
    verdict = {}
    if pairs_path.exists() and decisions_path.exists():
        pairs = json.loads(pairs_path.read_text())
        for pair, raw in zip(
            pairs, decisions_path.read_text(encoding="utf-8").splitlines(), strict=True
        ):
            f = raw.split("\t")
            verdict[pair["part1_id"]] = (f[5], f[6])
    for a in af_versus:
        a["cross_document_verdict"], a["cross_document_note"] = verdict.get(a["part1_id"], ("", ""))


def lost_page(xref: list[dict], part1: list[dict]) -> tuple[list[dict], dict]:
    top = [c for c in part1 if c["level"] == "complex" and c["ref"]]
    after = next(c for c in top if c["name"] == LOST_AFTER)
    before = next(c for c in top if c["name"] == LOST_BEFORE)
    lo, hi = asm.ref_value(after["ref"]), asm.ref_value(before["ref"])
    known = {c["ref"] for c in top}
    rows = []
    for x in xref:
        if x["level"] != "entry" or not lo < asm.ref_value(x["ref"]) < hi:
            continue
        rows.append(
            {
                **{
                    k: x[k]
                    for k in ("id", "ref", "name", "country", "airfield", "see_ref", "see_name")
                },
                "in_part1_table": x["ref"] in known,
                "listed_under": "; ".join(
                    y["name_printed"] + (" AF" if y["airfield"] else "")
                    for y in xref
                    if y["entry_ref"] == x["ref"]
                ),
            }
        )
    span = {"after": f"{after['ref']} {LOST_AFTER}", "before": f"{before['ref']} {LOST_BEFORE}"}
    return rows, span


def link_part1_rows(part2: dict, part1: list[dict], whole: dict) -> None:
    """Give each Part II complex and sub-complex row the id of the Part I row it repeats, and
    `top_seen_whole` from page_breaks (in place). A complex is matched by its reference; a
    sub-complex by name among the sub-complexes of the same Part I complex, allowing for a
    letter read differently in the two printings (BELCOSTROV, BELOOSTROV)."""
    top1 = {c["ref"]: c["id"] for c in part1 if c["level"] == "complex" and c["ref"]}
    subs1 = defaultdict(dict)
    for c in part1:
        if c["parent_id"]:
            subs1[c["parent_id"]][c["name"]] = c["id"]
    tops2 = {c["id"]: c for c in part2["complexes"] if c["level"] == "complex"}
    for c in part2["complexes"]:
        top = tops2.get(c["parent_id"] or c["id"])
        top_id1 = top1.get(c["part1_owner"] or (top["ref"] if top else ""))
        if c["level"] == "complex":
            c["part1_id"] = top_id1 or ""
        else:
            names = subs1.get(top_id1, {})
            best = difflib.get_close_matches(c["name"], list(names), n=1, cutoff=0.75)
            c["part1_id"] = names[best[0]] if best else ""
        c["top_seen_whole"] = whole.get(top["id"], False) if top else False


def write_part2_labels(part2: dict, versus: list[dict], lines: list[dict]) -> None:
    """The Part II complexes in the shared label schema (data/curated/labels/SCHEMA.md)."""
    text = {r["id"]: r["text"] for r in lines}
    by_id = {v["part2_id"]: v for v in versus}
    doc = "SAC, Atomic Weapons Requirements Study for 1959 (SM 129-56, June 1956)"
    rows = []
    for c in part2["complexes"]:
        if c["level"] != "complex" or c["lat"] == "":
            continue
        v = by_id[c["id"]]
        whole = "" if v["seen_whole"] else " (a floor: the complex runs onto a page not published)"
        country = asm.LABEL_COUNTRY.get(c["country"], c["country"])
        rows.append(
            {
                "plan_id": "us_1956_sac_part2_complexes",
                "planner": "US (SAC)",
                "target_country": asm.LABEL_COUNTRY_BY_NAME.get(c["name"], country),
                "plan_year": 1956,
                "provenance": "study",
                "seq": len(rows) + 1,
                "name_source": c["name_printed"],
                "name_modern": "",
                "target_class": "urban-industrial complex",
                "selected": 1 if v["part2_dgz"] else 0,
                "priority": c["priority"],
                "weapons": "",
                "yield_kt": "",
                "lat": c["lat"],
                "lon": c["lon"],
                "source_doc": f"{doc}, Part II complex list with weapons, excerpt "
                "(NSA EBB 538, section 7)",
                "source_url": SOURCE_URL,
                "source_page": f"PDF p.{int(c['page'][1:])} ({c['id']})",
                "quote": text[c["id"]][:200],
                "notes": f"DGZs={v['part2_dgz']}{whole}; Part I DGZs={v['part1_dgz']}; "
                f"installation lines={v['part2_installations']}; selected=1 if the complex has an "
                "aim point in Part II; excerpt only, complexes outside it are unknown",
            }
        )
    asm.write_csv(Path("data/curated/labels/us_1956_sac_part2_complexes.csv"), rows)


def main() -> None:
    t = asm.parse(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    is_r = lambda r: r["page"].startswith("R")  # noqa: E731
    part2 = {
        "complexes": [c for c in t["complexes"] if is_r(c)],
        "dgzs": [d for d in t["dgzs"] if is_r(d)],
        "installs": [i for i in t["installs"] if is_r(i)],
    }
    for c in part2["complexes"]:  # Part I's priority tiers mean nothing for an excerpt
        c.pop("priority_tier", None)
        c.pop("tier_size", None)
    part1_af = [a for a in t["airfields"] if a["page"].startswith("F")]
    xref = crossref(t["lines"])

    def read(name: str) -> list[dict]:
        return list(csv.DictReader(open(asm.OUT / name, encoding="utf-8")))

    part1, dgz1, inst1, af2 = (
        read(n) for n in ("complexes.csv", "dgz.csv", "installations.csv", "airfields.csv")
    )
    whole = page_breaks(part2, part1, dgz1, inst1)
    versus = compare_complexes(part2, part1, dgz1, inst1, whole)
    link_part1_rows(part2, part1, whole)
    af_versus = compare_airfields(part1_af, af2)
    crossdoc_verdicts(af_versus)
    lost, span = lost_page(xref, part1)

    write("lines.csv", t["lines"])
    write("part2_complexes.csv", part2["complexes"])
    write("part2_dgz.csv", part2["dgzs"])
    write("part2_installations.csv", part2["installs"])
    write("part1_airfields.csv", part1_af)
    write("crossref.csv", xref)
    write("part2_vs_part1.csv", versus)
    write("part1_vs_part2_airfields.csv", af_versus)
    write("lost_page.csv", lost)
    write("anomalies.csv", t["anomalies"])
    write_part2_labels(part2, versus, t["lines"])
    report(t, part2, part1_af, xref, versus, af_versus, lost, span, part1)


def report(t, part2, part1_af, xref, versus, af_versus, lost, span, part1) -> None:
    n = lambda rows, **kw: sum(all(r[k] == v for k, v in kw.items()) for r in rows)  # noqa: E731
    pages = sorted({line["page"] for line in t["lines"]})
    entries = [x for x in xref if x["level"] == "entry"]
    refs1 = {c["ref"] for c in part1 if c["level"] == "complex"}
    names1 = {c["name"] for c in part1}
    matched = [v for v in versus if v["part1_id"] and v["seen_whole"]]
    out = [
        "# SAC 1956 excerpts: report",
        "",
        "Written by `scripts/sac1956_excerpts.py`.",
        "",
        "## Counts",
        "",
        f"- Pages: {len(pages)} (F {sum(p[0] == 'F' for p in pages)}, R "
        f"{sum(p[0] == 'R' for p in pages)}, X {sum(p[0] == 'X' for p in pages)}); lines "
        f"{len(t['lines'])}, of them data {n(t['lines'], kind='data')}; agreed "
        f"{n(t['lines'], source='agreed')}, adjudicated {n(t['lines'], source='adjudicated')}; "
        f"gaps {len(t['gaps'])}",
        f"- Part II complexes {n(part2['complexes'], level='complex')}, sub-complexes "
        f"{n(part2['complexes'], level='subcomplex')}, DGZs {len(part2['dgzs'])}, installation "
        f"lines {len(part2['installs'])}",
        f"- Part I airfield rows: {len(part1_af)}",
        f"- Cross-reference rows: {len(xref)}; entries {len(entries)} (airfield entries "
        f"{sum(bool(x['airfield']) for x in entries)}, pointing elsewhere with SEE "
        f"{sum(bool(x['see_ref']) for x in entries)}); names listed under entries "
        f"{n(xref, level='listed under')}; unparsed {n(xref, level='unparsed')}",
        f"- Lines still carrying `?` or failing a rule: {len(t['anomalies'])} (`anomalies.csv`)",
        "",
        "## Part II complexes against Part I",
        "",
        f"- {sum(bool(v['part1_id']) for v in versus)} of {len(versus)} Part II complexes carry the "
        "reference number of a Part I complex, and all have the same priority: "
        f"{all(v['part1_priority'] == v['part2_priority'] for v in versus if v['part1_id'])}.",
        f"- Seen whole (not cut by a page the excerpt skips): {len(matched)}. The figures below "
        "are for these.",
        f"- Lines at the top of a page that belong to a complex begun on an unpublished page: "
        f"{sum(bool(r['part1_owner']) for r in part2['dgzs'] + part2['installs'])}",
    ]
    if matched:
        same_name = sum(v["name"] == v["part1_name"] for v in matched)
        out += [
            f"- Same name: {same_name}; same header coordinates: "
            f"{sum(bool(v['same_header_coords']) for v in matched)}",
            f"- DGZs: Part I {sum(v['part1_dgz'] for v in matched)}, Part II "
            f"{sum(v['part2_dgz'] for v in matched)}; kept (same coordinates) "
            f"{sum(v['dgz_kept'] for v in matched)}, dropped {sum(v['dgz_dropped'] for v in matched)}"
            f", added {sum(v['dgz_added'] for v in matched)}",
            f"- Installation lines: Part I {sum(v['part1_installations'] for v in matched)}, "
            f"Part II {sum(v['part2_installations'] for v in matched)}; kept "
            f"{sum(v['installations_kept'] for v in matched)}, dropped "
            f"{sum(v['installations_dropped'] for v in matched)}, added "
            f"{sum(v['installations_added'] for v in matched)}",
            f"- Complexes identical in DGZs and installations: "
            f"{sum(v['dgz_dropped'] == v['dgz_added'] == v['installations_dropped'] == v['installations_added'] == 0 for v in matched)}",
        ]
    unmatched = [v for v in versus if not v["part1_id"]]
    if unmatched:
        out.append(
            "- Without a Part I complex of the same reference: "
            + ", ".join(f"{v['ref']} {v['name']}" for v in unmatched)
        )
    aimed = sorted(
        (v for v in versus if v["part1_id"] and v["part1_dgz"]),
        key=lambda v: int(v["part1_priority"].rstrip("A")),
    )
    kept = [v["part2_dgz"] > 0 for v in aimed]
    run = next((i for i, k in enumerate(kept) if not k), len(kept))
    if aimed:
        out += [
            "",
            "## Aim points kept, by Part I priority",
            "",
            f"Of the {len(aimed)} excerpted complexes with an aim point in Part I, the {run} "
            f"ranked best (priority {aimed[0]['part1_priority']} to "
            f"{aimed[run - 1]['part1_priority'] if run else '-'}) all keep at least one in Part II; "
            f"of the {len(aimed) - run} ranked below, {sum(kept[run:])} do. A Part II count for a "
            "complex not seen whole is a floor.",
            "",
            "| Part I priority | complex | seen whole | aim points, Part I | Part II |",
            "|---|---|---|---|---|",
            *(
                f"| {v['part1_priority']} | {v['name']} | {'yes' if v['seen_whole'] else 'no'} | "
                f"{v['part1_dgz']} | {v['part2_dgz']} |"
                for v in aimed
            ),
        ]
    out += [
        "",
        "## Part I airfields against Part II",
        "",
        f"- {sum(bool(a['part2_id']) for a in af_versus)} of {len(af_versus)} Part I airfield rows "
        "have a Part II row of the same BE number (or name and reference).",
        f"- Of those, same coordinates {sum(a['same_coords'] is True for a in af_versus)}, same "
        f"trailing letter {sum(a['same_code'] is True for a in af_versus)}",
    ]
    judged = Counter(a["cross_document_verdict"] for a in af_versus if a["cross_document_verdict"])
    if judged:
        out.append(
            "- Rows transcribed differently from the two printings, judged on both scans "
            "(`crossdoc/`): " + ", ".join(f"{k} {v}" for k, v in judged.most_common())
        )
    missing = [a for a in af_versus if not a["part2_id"]]
    if missing:
        out.append("- Not in Part II: " + ", ".join(f"{a['name']} ({a['be']})" for a in missing))
    out += [
        "",
        "## Cross-reference list against Part I",
        "",
        f"- Entries whose reference number is a Part I complex: "
        f"{sum(x['ref'] in refs1 for x in entries)} of {len(entries)}",
        "- Entries with neither SEE nor AF and no Part I complex of that reference: "
        + ", ".join(
            f"{x['ref']} {x['name_printed']}"
            for x in entries
            if x["ref"] not in refs1 and not x["see_ref"] and not x["airfield"]
        ),
        f"- SEE targets that are Part I complexes: "
        f"{sum(x['see_ref'] in refs1 for x in entries if x['see_ref'])} of "
        f"{sum(bool(x['see_ref']) for x in entries)}",
        f"- Names listed under an entry that are Part I sub-complex or complex names: "
        f"{sum(x['name'] in names1 for x in xref if x['level'] == 'listed under')} of "
        f"{n(xref, level='listed under')}",
        "",
        "## The lost Part I page",
        "",
        f"The page between {span['after']} and {span['before']} is missing from the scan. "
        f"Cross-reference entries in that range of reference numbers: {len(lost)}.",
        "",
    ]
    if lost:
        out += [
            "| ref | name | AF | SEE | in Part I table | listed under it |",
            "|---|---|---|---|---|---|",
        ]
        out += [
            f"| {r['ref']} | {r['name']} | {'AF' if r['airfield'] else ''} | "
            f"{(r['see_ref'] + ' ' + r['see_name']).strip()} | {r['in_part1_table']} | "
            f"{r['listed_under']} |"
            for r in lost
        ]
    (OUT / "REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
