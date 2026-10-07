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
and data/curated/labels/us_1956_sac_complexes.csv and us_1956_sac_airfields.csv in the shared
label schema.

Lines flagged by checks() that no check batch has re-read yet are also written to
data/interim/sac1956/compare/flags.csv, in the format of disputes.csv, so that
`sac1956_adjudicate_prep.py 40 flags` can batch them for a second look at the scan.
"""

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import itertools

import sac1956_compare as cmp

ROOT = Path("data/interim/sac1956")
OUT = Path("data/curated/sac1956")
SOURCE_URL = {
    "C": "https://nsarchive.gwu.edu/document/15800-09-urban-industrial-target-list-part-i",
    "A": "https://nsarchive2.gwu.edu/nukevault/ebb538-Cold-War-Nuclear-Target-List-Declassified-First-Ever/documents/section6.pdf",
}
# Country suffixes as printed after a complex name; no suffix means the USSR.
SUFFIXES = [
    ("N KOREA", "North Korea"),
    ("N. KOREA", "North Korea"),
    ("KOREA", "North Korea"),
    ("N VIETNAM", "North Vietnam"),
    ("VIETNAM", "North Vietnam"),
    ("GER SOVZONE", "East Germany"),
    ("E GER", "East Germany"),
    ("E. GER", "East Germany"),
    ("E.GER", "East Germany"),
    ("E GE", "East Germany"),
    ("CZECH", "Czechoslovakia"),
    ("CZEC", "Czechoslovakia"),
    ("CZE", "Czechoslovakia"),
    ("CZ", "Czechoslovakia"),
    ("POL", "Poland"),
    ("HUNG", "Hungary"),
    ("HUN", "Hungary"),
    ("RUM", "Romania"),
    ("BULG", "Bulgaria"),
    ("BUL", "Bulgaria"),
    ("ALB", "Albania"),
    ("AL8", "Albania"),
    ("MANCH", "China (Manchuria)"),
    ("CHINA", "China"),
    ("CHIN", "China"),
]

# Pages scanned twice: the duplicate's lines stay in lines.csv but do not enter the tables.
# PDF page 46 repeats page 45 line for line (CHERNIGOV .. CHIA MU SSU); page 47 continues 45.
DUPLICATE_PAGES = {"C046": "C045"}
# Lines whose complex header is not in the scan; a placeholder complex without name or
# coordinates holds them. The scan of PDF page 64 cuts off the foot of the page after SAMBOR;
# page 65 opens inside a complex (chart 0322, sub-complex GORNA ORYAKHOVITSA BULG) whose header,
# alphabetically between DROGOBYCH and DUBNICE NAD VAHOM, was on the lost strip.
LOST_HEADERS = {
    "C065-L04": ("Bulgaria", "header not in the scan: PDF page 64 is cut off at the foot"),
    # A printed page is missing between PDF pages 9 and 10 (the scan duplicates page 45 in its
    # place). It held the rest of ARTSIZ and the complexes from ARTSIZ to ATBASAR: the airfield
    # list names ARZAMAS (0310), ASHKHABAD (0330) and ASTRAKHAN (0340) there. Page 10 opens
    # inside a complex on chart 0248 with the sub-complex ILINKA, beside Astrakhan.
    "C010-L04": ("USSR", "header not in the scan: the printed page after PDF page 9 is missing"),
}
BARE_COORDS = re.compile(r"^\d{4}-\d{5}[EW]?$")
DIRECTIONS = {
    "N",
    "S",
    "E",
    "W",
    "NE",
    "NW",
    "SE",
    "SW",
    "NNE",
    "NNW",
    "SSE",
    "SSW",
    "ENE",
    "ESE",
    "WNW",
    "WSW",
}

# Thresholds of the consistency checks, in degrees of latitude (longitude allows twice as much).
MAX_DGZ_OFFSET = 0.5
MAX_SUB_OFFSET = 1.0
MAX_AIRFIELD_OFFSET = 1.5
MAX_WAC_SPREAD = (4.0, 8.0)  # (lat, lon) from the median header of the chart
MIN_TIER = 6  # consecutive priorities in alphabetical order that make a tier


def degrees(dm: str, hem: str | None = None) -> float | str:
    """'5545' -> 55.75; '03737' -> 37.6167; W hemisphere -> negative. Blank when a digit is
    unreadable or the minutes are 60 or more (a slip in the source)."""
    if "?" in dm or int(dm[-2:]) >= 60:
        return ""
    value = int(dm[:-2]) + int(dm[-2:]) / 60
    return round(-value if hem == "W" else value, 4)


def airfield_with_gaps(text: str) -> dict | None:
    """An airfield row that keeps a '?': parse it with the gaps read as zeros, then give each
    field its printed characters back, so the '?' stays where it is (and blanks a coordinate)."""
    raw = cmp.digits_for_letters(cmp.light(text))
    m = cmp.AIRFIELD.match(raw.replace("?", "0"))
    if not m:
        return None
    return {k: (raw[m.start(k) : m.end(k)] if m.start(k) >= 0 else None) for k in m.groupdict()}


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
    return all(k < kp for k, kp in zip(sort_keys(name), sort_keys(previous), strict=False))


def ref_value(ref: str) -> float:
    """Reference numbers are four digits; a fifth digit inserts a complex between two numbers
    ("00255" lies between 0025 and 0030)."""
    return int(ref[:4]) + (int(ref[4:]) / 10 if len(ref) > 4 else 0)


def load_final(manifest: dict) -> tuple[dict, list]:
    final = {}
    for raw in (ROOT / "compare" / "agreed.tsv").read_text(encoding="utf-8").splitlines():
        if raw.strip():
            line_id, kind, text = ([*raw.split("\t"), "", ""])[:3]
            final[line_id] = {
                "kind": kind,
                "text": text,
                "source": "agreed",
                "confidence": "high",
                "note": "",
            }
    for tsv in sorted((ROOT / "adjudicate" / "decisions").glob("*.tsv")):
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                parts = (raw.split("\t") + [""] * 6)[:6]
                final[parts[0].strip()] = {
                    "kind": parts[1].strip().lower(),
                    "text": parts[2].strip(),
                    "source": "adjudicated",
                    "choice": parts[3].strip(),
                    "confidence": parts[4].strip(),
                    "note": parts[5].strip(),
                }
    gaps = [
        line["id"]
        for page in manifest.values()
        for line in page["lines"]
        if line["id"] not in final
    ]
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
    code_rows = list(
        csv.DictReader(open("data/curated/labels/sac1956_category_codes.csv", encoding="utf-8"))
    )
    codes = {r["code"]: r["description"] for r in code_rows}
    # Regional codes (power grids, railroad repair plants and yards) sit under a printed
    # sub-heading: 392 POLAND is a railroad yard in Poland.
    groups = {
        r["code"]: m[1].strip()
        for r in code_rows
        if (m := re.search(r"under printed sub-heading: ([^;]+)", r["notes"]))
    }
    current = None  # the complex or sub-complex that following lines belong to
    parent = None  # the enclosing complex (for sub-complexes)

    def handle(line_id: str, page: str, text: str, typ: str, f: dict) -> None:
        nonlocal current, parent
        if typ == "airfield":
            name, country = country_of(f["name"])
            airfields.append(
                {
                    "id": line_id,
                    "page": page,
                    "priority": f["prio"],
                    "ref": f["ref"],
                    "name": name,
                    "name_printed": f["name"],
                    "country": country,
                    "be": f"{f['wac']}-{f['num'] or ''}",
                    "lat": degrees(f["lat"]),
                    "lon": degrees(f["lon"], f.get("hem")),
                    "code": f["code"],
                    "text": text,
                }
            )
        elif typ in ("complex", "subcomplex"):
            name, country = country_of(f["name"])
            row = {
                "id": line_id,
                "page": page,
                "level": typ,
                "priority": f.get("prio", ""),
                "ref": f.get("ref", ""),
                "name": name,
                "name_printed": f["name"],
                "country": country,
                "lat": degrees(f["lat"]),
                "lon": degrees(f["lon"], f.get("hem")),
                "parent_id": parent["id"] if typ == "subcomplex" and parent else "",
                "n_dgz": 0,
                "n_installations": 0,
                "n_population": 0,
                "n_msites": 0,
                "last_page": page,
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
            msites.append(
                {
                    "id": line_id,
                    "page": page,
                    "complex_id": "" if own else current["id"],
                    "top_complex_id": "" if own else (parent or current)["id"],
                    "ref": f.get("ref") or "",
                    "name": f["name"],
                    "m_number": f["mnum"],
                    "lat": degrees(f["lat"]),
                    "lon": degrees(f["lon"]),
                    "label": f["label"],
                    "text": text,
                }
            )
            if own:
                current = parent = None  # lines after it, before the next header, are anomalies
            else:
                current["n_msites"] += 1
        elif current is None:
            anomalies.append(
                {"id": line_id, "text": text, "problem": "line before any complex header"}
            )
        elif typ == "dgz":
            dgzs.append(
                {
                    "id": line_id,
                    "page": page,
                    "complex_id": current["id"],
                    "label": f["label"],
                    "lat": degrees(f["lat"]),
                    "lon": degrees(f["lon"].zfill(5), f.get("hem")),
                    "text": text,
                }
            )
            current["n_dgz"] += 1
            current["last_page"] = page
        elif typ == "installation":
            installs.append(
                {
                    "id": line_id,
                    "page": page,
                    "complex_id": current["id"],
                    "category": f["cat"],
                    "category_name": codes.get(f["cat"], ""),
                    "category_group": groups.get(f["cat"], ""),
                    "be_wac": f["wac"],
                    "be_number": f["num"] or "",
                    "text": text,
                }
            )
            current["n_installations"] += 1
            current["n_population"] += f["cat"] == "275"
            current["last_page"] = page

    # On skewed pages a header's coordinates can sit in the band of the next line ("23 6830 RIGA"
    # then "5659-02409"); such pairs are read as one header.
    seq = [(i, final[i]) for i in ordered_ids(manifest, final) if i in final]
    joined = {}  # first line id -> second line id
    for (id1, r1), (id2, r2) in itertools.pairwise(seq):
        page = id1.split("-")[0]
        if r1["kind"] == r2["kind"] == "data" and BARE_COORDS.match(cmp.norm(r2["text"])):
            both = r1["text"] + " " + r2["text"]
            if cmp.classify(page, cmp.norm(r1["text"]), cmp.light(r1["text"]))[
                0
            ] == "unparsed" and cmp.classify(page, cmp.norm(both), cmp.light(both))[0] in (
                "complex",
                "subcomplex",
            ):
                joined[id1] = id2
    continuation = {v: k for k, v in joined.items()}

    for line_id, rec in seq:
        page = line_id.split("-")[0]
        text = rec["text"]
        if line_id in continuation:
            lines.append(
                {
                    "id": line_id,
                    "page": page,
                    "kind": "data",
                    "text": text,
                    "source": rec["source"],
                    "type": f"coordinates of {continuation[line_id]}",
                }
            )
            continue
        if line_id in joined:
            text = text + " " + final[joined[line_id]]["text"]
        if line_id in LOST_HEADERS:
            country, why = LOST_HEADERS[line_id]
            current = parent = {
                "id": f"{line_id}-lost",
                "page": page,
                "level": "complex",
                "priority": "",
                "ref": "",
                "name": "",
                "name_printed": f"({why})",
                "country": country,
                "lat": "",
                "lon": "",
                "parent_id": "",
                "n_dgz": 0,
                "n_installations": 0,
                "n_population": 0,
                "n_msites": 0,
                "last_page": page,
            }
            complexes.append(current)
        if page in DUPLICATE_PAGES:
            lines.append(
                {
                    "id": line_id,
                    "page": page,
                    "kind": rec["kind"],
                    "text": text,
                    "source": rec["source"],
                    "type": f"duplicate of page {DUPLICATE_PAGES[page]}",
                }
            )
            continue
        if rec["kind"] != "data":
            lines.append(
                {
                    "id": line_id,
                    "page": page,
                    "kind": rec["kind"],
                    "text": text,
                    "source": rec["source"],
                    "type": "",
                }
            )
            continue
        typ, f, problems = cmp.classify(page, cmp.norm(text), cmp.light(text))
        if (
            typ == "unparsed"
            and "?" in text
            and page.startswith("A")
            and (parsed := airfield_with_gaps(text))
        ):
            typ, f = "airfield", parsed
        lines.append(
            {
                "id": line_id,
                "page": page,
                "kind": "data",
                "text": text,
                "source": rec["source"],
                "type": typ,
            }
        )
        if "?" in text or problems:
            anomalies.append(
                {"id": line_id, "text": text, "problem": "; ".join(problems) or "contains ?"}
            )
        if typ == "merged":
            for part_typ, part_f, _ in f["parts"]:
                handle(line_id, page, text, part_typ, part_f)
        elif typ != "unparsed":
            handle(line_id, page, text, typ, f)

    add_priority_tiers(complexes)

    def write(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    for name, rows in [
        ("lines.csv", lines),
        ("complexes.csv", complexes),
        ("dgz.csv", dgzs),
        ("installations.csv", installs),
        ("msites.csv", msites),
        ("airfields.csv", airfields),
        ("anomalies.csv", anomalies),
    ]:
        write(name, rows)

    write_labels(complexes, airfields, lines)

    flags = checks(complexes, dgzs, installs, msites, airfields)
    flags += [{"check": a["problem"], "id": a["id"], "detail": a["text"]} for a in anomalies]
    second = {}  # outcome of the second look (check batches) at each flagged line
    for tsv in sorted((ROOT / "adjudicate" / "decisions").glob("check*.tsv")):
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            parts = (raw.split("\t") + [""] * 6)[:6]
            if raw.strip():
                second[parts[0].strip()] = (
                    "corrected" if parts[3].strip() == "new" else "confirmed as printed",
                    parts[5].strip(),
                )
    for f in flags:
        f["second_look"], f["second_look_note"] = second.get(f["id"], ("not re-read", ""))
    write("checks.csv", flags)
    write_flags(flags, final)
    report(complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final, flags)


# Country names in the shared label schema (the country containing the target in 1956), where
# they differ from the printed suffix.
LABEL_COUNTRY = {"East Germany": "GDR", "China": "PRC", "China (Manchuria)": "PRC"}
# Places whose printed suffix names another state than the one containing them.
LABEL_COUNTRY_BY_NAME = {"ULAAN BAATAR": "Mongolia"}


def write_labels(complexes: list[dict], airfields: list[dict], lines: list[dict]) -> None:
    """The shared-schema label files (data/curated/labels/SCHEMA.md): one row per top-level
    complex, and one per airfield. Rows without coordinates (the lost header) are left out."""
    text = {r["id"]: r["text"] for r in lines}
    kids = defaultdict(list)
    for c in complexes:
        if c["parent_id"]:
            kids[c["parent_id"]].append(c)
    doc = "SAC, Atomic Weapons Requirements Study for 1959 (SM 129-56, June 1956)"

    def country(name: str, printed_country: str) -> tuple[str, str]:
        if name in LABEL_COUNTRY_BY_NAME:
            return LABEL_COUNTRY_BY_NAME[name], f"printed suffix says {printed_country}; "
        region = "Manchuria; " if printed_country == "China (Manchuria)" else ""
        return LABEL_COUNTRY.get(printed_country, printed_country), region

    rows = []
    for c in complexes:
        if c["level"] != "complex" or c["lat"] == "":
            continue
        n_dgz = c["n_dgz"] + sum(k["n_dgz"] for k in kids[c["id"]])
        n_inst = c["n_installations"] + sum(k["n_installations"] for k in kids[c["id"]])
        target_country, note = country(c["name"], c["country"])
        tier = (
            f"priority tier {c['priority_tier']} of size {c['tier_size']}; "
            if c["tier_size"] not in ("", 1)
            else ""
        )
        rows.append(
            {
                "plan_id": "us_1956_sac_complexes",
                "planner": "US (SAC)",
                "target_country": target_country,
                "plan_year": 1956,
                "provenance": "study",
                "seq": len(rows) + 1,
                "name_source": c["name_printed"],
                "name_modern": "",
                "target_class": "urban-industrial complex",
                "selected": 1,
                "priority": c["priority"],
                "weapons": "",
                "yield_kt": "",
                "lat": c["lat"],
                "lon": c["lon"],
                "source_doc": f"{doc}, Part I complex list (NSA EBB 538, doc. 09)",
                "source_url": SOURCE_URL["C"],
                "source_page": f"PDF p.{int(c['page'][1:])} ({c['id']})",
                "quote": text[c["id"]][:200],
                "notes": f"{note}{tier}DGZs={n_dgz}{' (no aim point in this study)' if n_dgz == 0 else ''}; "
                f"installation lines={n_inst}; sub-complexes={len(kids[c['id']])}",
            }
        )
    write_csv(Path("data/curated/labels/us_1956_sac_complexes.csv"), rows)

    rows = []
    for a in airfields:
        target_country, note = country(a["name"], a["country"])
        rows.append(
            {
                "plan_id": "us_1956_sac_airfields",
                "planner": "US (SAC)",
                "target_country": target_country,
                "plan_year": 1956,
                "provenance": "study",
                "seq": len(rows) + 1,
                "name_source": a["name_printed"],
                "name_modern": "",
                "target_class": "airfield",
                "selected": 1,
                "priority": a["priority"],
                "weapons": "",
                "yield_kt": "",
                "lat": a["lat"],
                "lon": a["lon"],
                "source_doc": f"{doc}, Part II airfield list (NSA EBB 538, doc. 06)",
                "source_url": SOURCE_URL["A"],
                "source_page": f"PDF p.{int(a['page'][1:])} ({a['id']})",
                "quote": text[a["id"]][:200],
                "notes": f"{note}reference number {a['ref']}; BE {a['be']}; code {a['code']}"
                + (
                    "; coordinate not legible or printed with minutes >= 60"
                    if "" in (a["lat"], a["lon"])
                    else ""
                ),
            }
        )
    write_csv(Path("data/curated/labels/us_1956_sac_airfields.csv"), rows)


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def add_priority_tiers(complexes: list[dict]) -> None:
    """Group priority numbers into tiers. From about priority 300 down, the numbers run through
    the alphabet in long stretches (701 ABDULINO ... 732 YERSHOVO, then 739 APOSTOLOVO ...): the
    study ranked complexes in tiers and numbered each tier alphabetically. A stretch of at least
    MIN_TIER consecutive priorities in alphabetical order is one tier (by chance, six names fall
    in order once in 720 tries); every other complex is a tier of its own.

    Adds priority_tier (1 = most important, numbered in priority order) and tier_size."""
    top = [
        c for c in complexes if c["level"] == "complex" and re.fullmatch(r"\d+A?", c["priority"])
    ]
    top.sort(key=lambda c: (int(c["priority"].rstrip("A")), c["priority"]))
    runs, start = [], 0
    for k in range(1, len(top) + 1):
        if k == len(top) or not (
            int(top[k]["priority"].rstrip("A")) - int(top[k - 1]["priority"].rstrip("A")) <= 3
            and sort_keys(top[k]["name"])[0] >= sort_keys(top[k - 1]["name"])[0]
        ):
            runs.append((start, k))
            start = k
    tier = 0
    for a, b in runs:
        groups = [range(a, b)] if b - a >= MIN_TIER else [range(i, i + 1) for i in range(a, b)]
        for g in groups:
            tier += 1
            for i in g:
                top[i]["priority_tier"], top[i]["tier_size"] = tier, len(g)
    for c in complexes:
        c.setdefault("priority_tier", "")
        c.setdefault("tier_size", "")


def lon_gap(lon1: float, lon2: float, lat: float) -> float:
    """Longitude difference across the date line (Chukotka), in 'equator degrees': a degree of
    longitude shrinks with latitude, and charts in the far north span more of them."""
    d = abs(lon1 - lon2) % 360
    return min(d, 360 - d) * max(math.cos(math.radians(lat)), 0.3)


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
    rows += [
        (m, m["top_complex_id"], MAX_SUB_OFFSET, "M-site") for m in msites if m["top_complex_id"]
    ]
    for row, cid, limit, what in rows:
        c = by_id[cid]
        if "" in (c["lat"], c["lon"], row["lat"], row["lon"]):
            continue
        dlat, dlon = abs(row["lat"] - c["lat"]), abs(row["lon"] - c["lon"])
        if dlat > limit or dlon > limit * 2:
            flag(
                f"{what} far from its header",
                row["id"],
                f"{dlat:.2f} deg lat / {dlon:.2f} deg lon from {c['name_printed']} ({c['id']} {c['lat']}, {c['lon']})",
            )
    for c in complexes:
        if c["parent_id"] and "" not in (
            by_id[c["parent_id"]]["lat"],
            by_id[c["parent_id"]]["lon"],
            c["lat"],
            c["lon"],
        ):
            p = by_id[c["parent_id"]]
            dlat, dlon = abs(c["lat"] - p["lat"]), abs(c["lon"] - p["lon"])
            if dlat > MAX_SUB_OFFSET or dlon > MAX_SUB_OFFSET * 2:
                flag(
                    "sub-complex far from its complex",
                    c["id"],
                    f"{dlat:.2f} deg lat / {dlon:.2f} deg lon from {p['name_printed']} ({p['id']})",
                )
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
                    flag(
                        "WAC prefix differs from its block",
                        r["id"],
                        f"{r['be_wac']} in a block where {n} of {len(rows)} lines use {modal}",
                    )
        if "" not in (by_id[cid]["lat"], by_id[cid]["lon"]):
            wac_points[modal].append(by_id[cid])
    # A chart covers a fixed area, so headers whose installations sit on one chart lie close
    # together; a header far from the others on its chart has a misread coordinate or prefix.
    for wac, cs in wac_points.items():
        if len(cs) < 3:
            continue
        lat_med = sorted(c["lat"] for c in cs)[len(cs) // 2]
        lon_med = sorted(c["lon"] % 360 for c in cs)[len(cs) // 2]
        for c in cs:
            if (
                abs(c["lat"] - lat_med) > MAX_WAC_SPREAD[0]
                or lon_gap(c["lon"], lon_med, lat_med) > MAX_WAC_SPREAD[1]
            ):
                flag(
                    "header far from the other headers on its chart",
                    c["id"],
                    f"WAC {wac}: {c['lat']}, {c['lon']} vs median {lat_med}, {lon_med} of {len(cs)} headers",
                )
    # Airfields on one chart lie together too; the chart prefix of an airfield's BE number is
    # printed apart from its coordinates, so a misread coordinate digit shows up as distance
    # (a 2 that lost its base bar reads as 7: five degrees).
    af_points = defaultdict(list)
    for a in airfields:
        if "" not in (a["lat"], a["lon"]):
            af_points[a["be"].split("-")[0]].append(a)
    for wac, group in af_points.items():
        pts = group + wac_points.get(wac, [])
        if len(pts) < 3:
            continue
        lat_med = sorted(x["lat"] for x in pts)[len(pts) // 2]
        lon_med = sorted(x["lon"] % 360 for x in pts)[len(pts) // 2]
        for a in group:
            if (
                abs(a["lat"] - lat_med) > MAX_WAC_SPREAD[0]
                or lon_gap(a["lon"], lon_med, lat_med) > MAX_WAC_SPREAD[1]
            ):
                flag(
                    "airfield far from the other targets on its chart",
                    a["id"],
                    f"chart {wac}: {a['lat']}, {a['lon']} vs median {lat_med}, {lon_med} of {len(pts)}",
                )
    # Population lines carry 9xxx numbers (a rule in the comparison); each block normally has one.
    for c in complexes:
        n = c["n_population"]
        if n > 1:
            flag(
                "block with more than one population line",
                c["id"],
                f"{n} lines of category 275 under {c['name_printed']}",
            )
    # Top-level complexes run alphabetically, and so do their reference numbers.
    top = [c for c in complexes if c["level"] == "complex" and c["name"]]
    for prev, c in itertools.pairwise(top):
        if out_of_order(c["name"], prev["name"]):
            flag(
                "complex out of alphabetical order",
                c["id"],
                f"{c['name_printed']} follows {prev['name_printed']} ({prev['id']})",
            )
        if (
            c["ref"].isdigit()
            and prev["ref"].isdigit()
            and ref_value(c["ref"]) <= ref_value(prev["ref"])
        ):
            flag(
                "reference number not above the previous complex",
                c["id"],
                f"{c['ref']} after {prev['ref']} ({prev['id']})",
            )
    # Priority numbers are unique within each list.
    for rows, what in ((top, "complex"), (airfields, "airfield")):
        seen = defaultdict(list)
        for r in rows:
            seen[r["priority"]].append(r["id"])
        for prio, ids in seen.items():
            if len(ids) > 1:
                for line_id in ids:
                    flag(
                        f"duplicate {what} priority",
                        line_id,
                        f"priority {prio} also on {', '.join(i for i in ids if i != line_id)}",
                    )
    # Airfields: alphabetical; BE numbers 8xxx; the reference number is the parent complex's.
    refs = {c["ref"]: c for c in top}
    for prev, a in itertools.pairwise(airfields):
        if out_of_order(a["name"], prev["name"]):
            flag(
                "airfield out of alphabetical order",
                a["id"],
                f"{a['name']} follows {prev['name']} ({prev['id']})",
            )
    for a in airfields:
        num = a["be"].split("-")[1]
        if num and not num.startswith("8"):
            flag("airfield BE number not 8xxx", a["id"], a["be"])
        c = refs.get(a["ref"])  # many airfields name a complex that is not in Part I: not checked
        if (
            c
            and "" not in (a["lat"], a["lon"], c["lat"], c["lon"])
            and (
                abs(a["lat"] - c["lat"]) > MAX_AIRFIELD_OFFSET
                or abs(a["lon"] - c["lon"]) > MAX_AIRFIELD_OFFSET * 2
            )
        ):
            flag(
                "airfield far from its reference complex",
                a["id"],
                f"{a['lat']}, {a['lon']} vs {c['name_printed']} ({c['id']}) {c['lat']}, {c['lon']}",
            )
    # The same place can be printed twice: as a complex and in an airfield's name, or in both
    # lists. Two names a letter apart, a short distance apart, are probably one name, misread
    # once ("SUOYAKVI" for SUOYARVI).
    places = [(c["id"], c["name"], c["lat"], c["lon"]) for c in complexes]
    places += [(m["id"], m["name"], m["lat"], m["lon"]) for m in msites]
    for a in airfields:
        for part in re.split(r"/", a["name"]):
            places.append((a["id"], sort_keys(part)[4], a["lat"], a["lon"]))
    by_len = defaultdict(list)
    for place in places:
        if len(place[1]) >= 4 and "" not in (place[2], place[3]):
            by_len[len(place[1])].append(place)
    seen = set()
    for group in by_len.values():
        for i, (id1, n1, lat1, lon1) in enumerate(group):
            for id2, n2, lat2, lon2 in group[i + 1 :]:
                if (
                    id1 != id2
                    and n1 != n2
                    and abs(lat1 - lat2) < 1
                    and abs(lon1 - lon2) < 2
                    and sum(x != y for x, y in zip(n1, n2, strict=False)) == 1
                    and (n1, n2) not in seen
                ):
                    seen.add((n1, n2))
                    flag("name a letter away from a nearby name", id1, f"{n1} vs {n2} ({id2})")
                    flag("name a letter away from a nearby name", id2, f"{n2} vs {n1} ({id1})")
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
            w.writerow(
                [
                    line_id,
                    line_id.split("-")[0],
                    rec["kind"],
                    rec["kind"],
                    rec["text"],
                    rec["text"],
                    "; ".join(why),
                ]
            )


def quality(final: dict) -> list[str]:
    """How often each pass matched the final reading, and what adjudication decided."""
    passes = {name: cmp.load(name) for name in ("passA", "passB")}
    data = [i for i, r in final.items() if r["kind"] == "data"]
    wrong = {
        name: {
            i for i in data if i not in rows or cmp.norm(rows[i][1]) != cmp.norm(final[i]["text"])
        }
        for name, rows in passes.items()
    }
    both = wrong["passA"] & wrong["passB"]
    same = {
        i
        for i in both
        if i in passes["passA"]
        and i in passes["passB"]
        and "?" not in passes["passA"][i][1]
        and cmp.norm(passes["passA"][i][1]) == cmp.norm(passes["passB"][i][1])
    }
    adjudicated = [r for r in final.values() if r["source"] == "adjudicated"]
    out = [
        "## Transcription quality",
        "",
        f"- Data lines: {len(data)}. Pass A differs from the final reading on {len(wrong['passA'])} "
        f"({len(wrong['passA']) / len(data):.2%}), pass B on {len(wrong['passB'])} ({len(wrong['passB']) / len(data):.2%}); "
        f"both on {len(both)}. On {len(same)} of these the two passes wrote the same legible text: errors the "
        f"comparison cannot see, found by the consistency checks or by an adjudicator looking at the line for "
        f"another reason ({', '.join(sorted(same))}).",
        f"- Adjudicated lines: {len(adjudicated)}; choice "
        + ", ".join(
            f"{k} {v}" for k, v in sorted(Counter(r["choice"] for r in adjudicated).items())
        )
        + "; confidence "
        + ", ".join(
            f"{k} {v}" for k, v in sorted(Counter(r["confidence"] for r in adjudicated).items())
        ),
        "",
    ]
    return out


def nsa_check(complexes, installs) -> list[str]:
    """Compare installation lines by category with the NSA city sheets (an independent count)."""
    path = Path("data/curated/validation_sac1956_nsa_city_sheets.csv")
    if not path.exists():
        return []
    sheets = list(csv.DictReader(open(path, encoding="utf-8")))
    main = {
        r["sheet"]: r["block"]
        for r in sheets
        if "/" in r["location"] or r["location"] == r["sheet"]
    }
    by_id = {c["id"]: c for c in complexes}
    cats = defaultdict(Counter)
    for r in installs:
        cats[r["complex_id"]][r["category"]] += 1
    out = [
        "",
        "## External check: NSA city sheets",
        "",
        "Installation lines by category against the National Security Archive's city sheets "
        "(validation_sac1956_nsa_city_sheets.csv).",
        "",
        "| Sheet | Location | Block in the list | Lines here | Lines on the sheet | Categories that differ (here/sheet) |",
        "|---|---|---|---|---|---|",
    ]
    for (sheet, location), group in groupby_keys(sheets, ("sheet", "location")):
        block = group[0]["block"]
        top = main[sheet]
        match = [
            c
            for c in complexes
            if c["name"] == block
            and (c["name"] == top or (c["parent_id"] and by_id[c["parent_id"]]["name"] == top))
        ]
        theirs = Counter({r["category_code"]: int(r["count"]) for r in group})
        ours = cats[match[0]["id"]] if match else Counter()
        diff = [
            f"{code}: {ours[code]}/{theirs[code]}"
            for code in sorted(set(ours) | set(theirs))
            if ours[code] != theirs[code]
        ]
        out.append(
            f"| {sheet} | {location} | {match[0]['id'] + ' ' + match[0]['name_printed'] if match else 'not a block'} | "
            f"{sum(ours.values())} | {sum(theirs.values())} | {', '.join(diff) or '-'} |"
        )
    return out


def groupby_keys(rows: list[dict], keys: tuple[str, ...]) -> list[tuple[tuple, list[dict]]]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    return list(groups.items())


def report(
    complexes, dgzs, installs, msites, airfields, anomalies, lines, gaps, final, flags
) -> None:
    top = [c for c in complexes if c["level"] == "complex"]
    {c["id"]: c for c in complexes}

    def totals(c):  # a complex plus its sub-complexes
        kids = [k for k in complexes if k["parent_id"] == c["id"]]
        return c["n_dgz"] + sum(k["n_dgz"] for k in kids), c["n_installations"] + sum(
            k["n_installations"] for k in kids
        )

    out = ["# SAC 1956 list: assembly report", ""]
    src = Counter(r["source"] for r in final.values())
    out += [
        f"- Lines with a final reading: {len(final)} ({src['agreed']} agreed by both passes, "
        f"{src['adjudicated']} adjudicated); lines with no reading yet: {len(gaps)}",
        f"- Complexes: {len(top)}; sub-complexes: {len(complexes) - len(top)}; DGZs: {len(dgzs)}; "
        f"installation lines: {len(installs)}; M-n rows: {len(msites)}; airfields: {len(airfields)}",
        f"- Lines still carrying '?' or failing a rule: {len(anomalies)}",
        "",
    ]
    out += quality(final)
    out += [
        "## Anchors",
        "",
        "| Complex | Priority | DGZs | Installations (with sub-complexes) |",
        "|---|---|---|---|",
    ]
    for name in ["MOSCOW", "LENINGRAD", "BERLIN"]:
        for c in top:
            if c["name"].startswith(name):
                d, i = totals(c)
                out.append(f"| {c['name_printed']} | {c['priority']} | {d} | {i} |")
    prios = [c["priority"] for c in top if c["priority"]]
    nums = sorted(int(re.sub(r"\D", "", p)) for p in prios if re.sub(r"\D", "", p))
    dup = [p for p, n in Counter(prios).items() if n > 1]
    missing = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
    out += [
        "",
        "## Priority numbers",
        "",
        f"- {len(prios)} complexes carry a priority; highest {max(nums) if nums else '-'}; "
        f"duplicates: {len(dup)} {dup[:20]}; numbers missing from 1..max: {len(missing)} {missing[:30]}",
    ]
    aprios = [a["priority"] for a in airfields]
    anums = sorted(int(x.rstrip("A")) for x in aprios if x.rstrip("A").isdigit())
    adup = [x for x, n in Counter(aprios).items() if n > 1]
    amissing = sorted(set(range(1, max(anums) + 1)) - set(anums)) if anums else []
    out += [
        f"- Airfields: {len(aprios)} priorities, highest {max(anums) if anums else '-'}, "
        f"{sum(x.endswith('A') for x in aprios)} with an A suffix (typed in later); duplicates: {len(adup)} {adup}; "
        f"numbers missing from 1..max: {len(amissing)} {amissing}"
    ]
    refs = [ref_value(c["ref"]) for c in top if c["ref"].isdigit()]
    drops = sum(1 for x, y in itertools.pairwise(refs) if y <= x)
    out += [
        f"- Reference numbers that drop below the previous complex (alphabetical order check): {drops}"
    ]
    out += [
        "",
        "## Complexes by country",
        "",
        "| Country | Complexes | DGZs | Installations |",
        "|---|---|---|---|",
    ]
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
    label = {
        r["category"]: " / ".join(x for x in (r["category_group"], r["category_name"]) if x)
        for r in installs
    }
    out += [f"- {code} {label[code]}: {n}" for code, n in cats.most_common(15)]
    unknown = sorted({r["category"] for r in installs if not r["category_name"]})
    out += ["", f"- Category codes not in the code list: {unknown}"]
    in_part1 = {c["ref"] for c in top}
    out += [
        "",
        f"- Airfields whose reference number is a Part I complex: "
        f"{sum(a['ref'] in in_part1 for a in airfields)} of {len(airfields)}",
    ]
    out += [
        "- Duplicate scans left out of the tables: "
        + ", ".join(
            f"PDF page {int(d[1:])} (= page {int(o[1:])})" for d, o in DUPLICATE_PAGES.items()
        )
    ]
    out += [
        "- Missing from the scan: "
        + "; ".join(
            f"{line_id} opens without its header ({why})"
            for line_id, (_, why) in LOST_HEADERS.items()
        )
    ]
    out += nsa_check(complexes, installs)
    out += [
        "",
        "## Consistency checks across lines",
        "",
        "Lines that the checks still flag after the second look, with its outcome (checks.csv has the notes). "
        "Lines that the second look corrected no longer break a check and are not listed. In all, "
        f"{sum(1 for r in final.values() if r.get('choice') == 'new')} lines ended with a reading that neither "
        "pass had (adjudication or second look, choice `new`).",
        "",
        "| Check | Lines | Confirmed as printed | Not re-read |",
        "|---|---|---|---|",
    ]
    for check, n in Counter(f["check"] for f in flags).most_common():
        rows = [f for f in flags if f["check"] == check]
        out.append(
            f"| {check} | {n} | {sum(f['second_look'] == 'confirmed as printed' for f in rows)} | "
            f"{sum(f['second_look'] == 'not re-read' for f in rows)} |"
        )
    (OUT / "REPORT.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
