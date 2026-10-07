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
  checks.csv         lines that break a consistency check across lines (see checks())
  REPORT.md          counts and validation checks
and data/curated/labels/us_1956_sac_complexes.csv in the shared label schema.

Lines flagged by checks() that no check batch has re-read yet are also written to
data/interim/sac1956/compare/flags.csv, in the format of disputes.csv, so that
`sac1956_adjudicate_prep.py 40 flags` can batch them for a second look at the scan.
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
    ("GER SOVZONE", "East Germany"), ("E GER", "East Germany"), ("E. GER", "East Germany"), ("E.GER", "East Germany"), ("E GE", "East Germany"),
    ("CZECH", "Czechoslovakia"), ("CZEC", "Czechoslovakia"), ("CZE", "Czechoslovakia"), ("CZ", "Czechoslovakia"),
    ("POL", "Poland"), ("HUNG", "Hungary"), ("HUN", "Hungary"), ("RUM", "Romania"),
    ("BULG", "Bulgaria"), ("BUL", "Bulgaria"), ("ALB", "Albania"), ("AL8", "Albania"),
    ("MANCH", "China (Manchuria)"), ("CHINA", "China"), ("CHIN", "China"),
]

# Pages scanned twice: the duplicate's lines stay in lines.csv but do not enter the tables.
# PDF page 46 repeats page 45 line for line (CHERNIGOV .. CHIA MU SSU); page 47 continues 45.
DUPLICATE_PAGES = {"C046": "C045"}
DIRECTIONS = {"N", "S", "E", "W", "NE", "NW", "SE", "SW", "NNE", "NNW", "SSE", "SSW", "ENE", "ESE", "WNW", "WSW"}

# Thresholds of the consistency checks, in degrees of latitude (longitude allows twice as much).
MAX_DGZ_OFFSET = 0.5
MAX_SUB_OFFSET = 1.0
MAX_AIRFIELD_OFFSET = 1.5
MAX_WAC_SPREAD = (4.0, 8.0)  # (lat, lon) from the median header of the chart


def degrees(dm: str, hem: str | None = None) -> float:
    """'5545' -> 55.75; '03737' -> 37.6167; W hemisphere -> negative."""
    value = int(dm[:-2]) + int(dm[-2:]) / 60
    return round(-value if hem == "W" else value, 4)


# The name column holds 25 characters, which cuts some suffixes ("CZEC", "CHIN", "E GE"); these
# are in SUFFIXES. One is cut to a bare letter.
NAME_OVERRIDES = {"TURCIANSKY SVATY MARTIN C": ("TURCIANSKY SVATY MARTIN", "Czechoslovakia")}


def country_of(name: str) -> tuple[str, str]:
    if name.strip() in NAME_OVERRIDES:
        return NAME_OVERRIDES[name.strip()]
    clean = re.sub(r"[.,]", " ", name).strip()
    clean = re.sub(r"\s+", " ", clean)
    for suffix, country in SUFFIXES:
        if clean.endswith(" " + suffix) or clean == suffix:
            return clean[: -len(suffix)].strip(" -"), country
    return clean, "USSR"


def sort_keys(name: str) -> list[str]:
    """The lists run alphabetically, but not by one consistent rule: mostly letters only
    ("AN SHAN" after "ANGREN"), sometimes word by word ("USTI NAD LABEM" after "UST
    KAMENOGORSK"), with or without the part after '/' and compass points ("MINSK S.")."""
    name = country_of(name)[0].upper()
    keys = []
    for cut in (False, True):
        base = name.split("/")[0] if cut else name
        words = re.sub(r"[^A-Z ]", " ", base).split()
        bare = list(words)
        while len(bare) > 1 and bare[-1] in DIRECTIONS:
            bare.pop()
        keys += ["".join(words), "".join(bare), " ".join(bare)]
    return keys


def out_of_order(name: str, previous: str) -> bool:
    """Out of order under every plausible key, so probably a misread or a misprint."""
    return all(k < kp for k, kp in zip(sort_keys(name), sort_keys(previous)))


def ref_value(ref: str) -> float:
    """Reference numbers are four digits; a fifth digit inserts a complex between two numbers
    ("00255" lies between 0025 and 0030)."""
    return int(ref[:4]) + (int(ref[4:]) / 10 if len(ref) > 4 else 0)


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
            name, country = country_of(f["name"])
            airfields.append({
                "id": line_id, "page": page, "priority": f["prio"], "ref": f["ref"], "name": name,
                "name_printed": f["name"], "country": country,
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
        elif typ == "msite":
            # "M-n" rows (all near Moscow). With a reference number a row stands on its own in the
            # alphabetical order, like a complex without a priority; without one it is listed
            # under the complex it follows (e.g. DEDENEVO M-29 under DMITROV).
            own = bool(f.get("ref")) or current is None
            msites.append({
                "id": line_id, "page": page, "complex_id": "" if own else current["id"],
                "top_complex_id": "" if own else (parent or current)["id"], "ref": f.get("ref") or "",
                "name": f["name"], "m_number": f["mnum"], "lat": degrees(f["lat"]), "lon": degrees(f["lon"]),
                "label": f["label"], "text": text,
            })
            if own:
                current = parent = None  # lines after it, before the next header, are anomalies
            else:
                current["n_msites"] += 1
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

    for line_id in ordered_ids(manifest, final):
        rec = final.get(line_id)
        if rec is None:
            continue
        page = line_id.split("-")[0]
        text = rec["text"]
        if page in DUPLICATE_PAGES:
            lines.append({"id": line_id, "page": page, "kind": rec["kind"], "text": text, "source": rec["source"],
                          "type": f"duplicate of page {DUPLICATE_PAGES[page]}"})
            continue
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

    flags = checks(complexes, dgzs, installs, msites, airfields)
    write("checks.csv", flags)
    write_flags(flags, final)
    report(complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final, flags)


def checks(complexes, dgzs, installs, msites, airfields) -> list[dict]:
    """Consistency checks across lines. Both passes can misread a glyph the same way (3/5/8,
    6/0/9); such a line agrees and parses, but it disagrees with the lines around it."""
    flags = []

    def flag(check: str, line_id: str, detail: str) -> None:
        flags.append({"check": check, "id": line_id, "detail": detail})

    by_id = {c["id"]: c for c in complexes}
    # Aim points lie near the header they follow; M-n sites listed under a complex lie around it
    # (as far as the outer Moscow ring); sub-complexes lie near their complex.
    rows = [(d, d["complex_id"], MAX_DGZ_OFFSET, "DGZ") for d in dgzs]
    rows += [(m, m["top_complex_id"], MAX_SUB_OFFSET, "M-site") for m in msites if m["top_complex_id"]]
    for row, cid, limit, what in rows:
        c = by_id[cid]
        dlat, dlon = abs(row["lat"] - c["lat"]), abs(row["lon"] - c["lon"])
        if dlat > limit or dlon > limit * 2:
            flag(f"{what} far from its header", row["id"],
                 f"{dlat:.2f} deg lat / {dlon:.2f} deg lon from {c['name_printed']} ({c['id']} {c['lat']}, {c['lon']})")
    for c in complexes:
        if c["parent_id"]:
            p = by_id[c["parent_id"]]
            dlat, dlon = abs(c["lat"] - p["lat"]), abs(c["lon"] - p["lon"])
            if dlat > MAX_SUB_OFFSET or dlon > MAX_SUB_OFFSET * 2:
                flag("sub-complex far from its complex", c["id"],
                     f"{dlat:.2f} deg lat / {dlon:.2f} deg lon from {p['name_printed']} ({p['id']})")
    # The installations of one block mostly share a chart (WAC) prefix; a lone different prefix
    # is either a real chart edge or a misread.
    blocks = defaultdict(list)
    for r in installs:
        blocks[r["complex_id"]].append(r)
    wac_points = defaultdict(list)
    for cid, rows in blocks.items():
        counts = Counter(r["be_wac"] for r in rows)
        modal, n = counts.most_common(1)[0]
        if len(rows) >= 3:
            for r in rows:
                if counts[r["be_wac"]] == 1 and n >= 2:
                    flag("WAC prefix differs from its block", r["id"], f"{r['be_wac']} in a block where {n} of {len(rows)} lines use {modal}")
        wac_points[modal].append(by_id[cid])
    # A chart covers a fixed area, so headers whose installations sit on one chart lie close
    # together; a header far from the others on its chart has a misread coordinate or prefix.
    for wac, cs in wac_points.items():
        if len(cs) < 3:
            continue
        lat_med = sorted(c["lat"] for c in cs)[len(cs) // 2]
        lon_med = sorted(c["lon"] for c in cs)[len(cs) // 2]
        for c in cs:
            if abs(c["lat"] - lat_med) > MAX_WAC_SPREAD[0] or abs(c["lon"] - lon_med) > MAX_WAC_SPREAD[1]:
                flag("header far from the other headers on its chart", c["id"],
                     f"WAC {wac}: {c['lat']}, {c['lon']} vs median {lat_med}, {lon_med} of {len(cs)} headers")
    # Population lines carry 9xxx numbers (a rule in the comparison); each block normally has one.
    for c in complexes:
        n = c["n_population"]
        if n > 1:
            flag("block with more than one population line", c["id"], f"{n} lines of category 275 under {c['name_printed']}")
    # Top-level complexes run alphabetically, and so do their reference numbers.
    top = [c for c in complexes if c["level"] == "complex"]
    for prev, c in zip(top, top[1:]):
        if out_of_order(c["name"], prev["name"]):
            flag("complex out of alphabetical order", c["id"], f"{c['name_printed']} follows {prev['name_printed']} ({prev['id']})")
        if c["ref"].isdigit() and prev["ref"].isdigit() and ref_value(c["ref"]) <= ref_value(prev["ref"]):
            flag("reference number not above the previous complex", c["id"], f"{c['ref']} after {prev['ref']} ({prev['id']})")
    # Priority numbers are unique within each list.
    for rows, what in ((top, "complex"), (airfields, "airfield")):
        seen = defaultdict(list)
        for r in rows:
            seen[r["priority"]].append(r["id"])
        for prio, ids in seen.items():
            if len(ids) > 1:
                for line_id in ids:
                    flag(f"duplicate {what} priority", line_id, f"priority {prio} also on {', '.join(i for i in ids if i != line_id)}")
    # Airfields: alphabetical; BE numbers 8xxx; the reference number is the parent complex's.
    refs = {c["ref"]: c for c in top}
    for prev, a in zip(airfields, airfields[1:]):
        if out_of_order(a["name"], prev["name"]):
            flag("airfield out of alphabetical order", a["id"], f"{a['name']} follows {prev['name']} ({prev['id']})")
    for a in airfields:
        num = a["be"].split("-")[1]
        if num and not num.startswith("8"):
            flag("airfield BE number not 8xxx", a["id"], a["be"])
        c = refs.get(a["ref"])  # many airfields name a complex that is not in Part I: not checked
        if c and (abs(a["lat"] - c["lat"]) > MAX_AIRFIELD_OFFSET or abs(a["lon"] - c["lon"]) > MAX_AIRFIELD_OFFSET * 2):
            flag("airfield far from its reference complex", a["id"],
                 f"{a['lat']}, {a['lon']} vs {c['name_printed']} ({c['id']}) {c['lat']}, {c['lon']}")
    return flags


def write_flags(flags: list[dict], final: dict) -> None:
    """Flagged lines in the disputes.csv format, for a second look at the scan."""
    reasons = defaultdict(list)
    for f in flags:
        reasons[f["id"]].append(f"check: {f['check']} ({f['detail']})")
    with open(ROOT / "compare" / "flags.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "page", "kind_a", "kind_b", "text_a", "text_b", "reasons"])
        for line_id, why in reasons.items():
            rec = final[line_id]
            w.writerow([line_id, line_id.split("-")[0], rec["kind"], rec["kind"], rec["text"], rec["text"], "; ".join(why)])


def nsa_check(complexes, installs) -> list[str]:
    """Compare installation lines by category with the NSA city sheets (an independent count)."""
    path = Path("data/curated/validation_sac1956_nsa_city_sheets.csv")
    if not path.exists():
        return []
    sheets = list(csv.DictReader(open(path, encoding="utf-8")))
    main = {r["sheet"]: r["block"] for r in sheets if "/" in r["location"] or r["location"] == r["sheet"]}
    by_id = {c["id"]: c for c in complexes}
    cats = defaultdict(Counter)
    for r in installs:
        cats[r["complex_id"]][r["category"]] += 1
    out = ["", "## External check: NSA city sheets", "",
           "Installation lines by category against the National Security Archive's city sheets "
           "(validation_sac1956_nsa_city_sheets.csv).", "",
           "| Sheet | Location | Block in the list | Lines here | Lines on the sheet | Categories that differ (here/sheet) |",
           "|---|---|---|---|---|---|"]
    for (sheet, location), group in groupby_keys(sheets, ("sheet", "location")):
        block = group[0]["block"]
        top = main[sheet]
        match = [c for c in complexes if c["name"] == block
                 and (c["name"] == top or (c["parent_id"] and by_id[c["parent_id"]]["name"] == top))]
        theirs = Counter({r["category_code"]: int(r["count"]) for r in group})
        ours = cats[match[0]["id"]] if match else Counter()
        diff = [f"{code}: {ours[code]}/{theirs[code]}" for code in sorted(set(ours) | set(theirs)) if ours[code] != theirs[code]]
        out.append(f"| {sheet} | {location} | {match[0]['id'] + ' ' + match[0]['name_printed'] if match else 'not a block'} | "
                   f"{sum(ours.values())} | {sum(theirs.values())} | {', '.join(diff) or '-'} |")
    return out


def groupby_keys(rows: list[dict], keys: tuple[str, ...]) -> list[tuple[tuple, list[dict]]]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    return list(groups.items())


def report(complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final, flags) -> None:
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
    in_part1 = {c["ref"] for c in top}
    out += ["", f"- Airfields whose reference number is a Part I complex: "
            f"{sum(a['ref'] in in_part1 for a in airfields)} of {len(airfields)}"]
    out += [f"- Duplicate scans left out of the tables: " + ", ".join(f"PDF page {int(d[1:])} (= page {int(o[1:])})" for d, o in DUPLICATE_PAGES.items())]
    out += nsa_check(complexes, installs)
    out += ["", "## Consistency checks across lines", "", "Lines listed in checks.csv; each was re-read on the scan "
            "unless noted below.", "", "| Check | Lines |", "|---|---|"]
    out += [f"| {check} | {n} |" for check, n in Counter(f["check"] for f in flags).most_common()]
    (OUT / "REPORT.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
