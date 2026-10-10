"""Build data/curated/features/uk_military_sites_1980.csv (documented in
data/curated/features/uk_military_sites_1980.md).

Reads the Wikipedia wikitext saved under data/raw/uk_military/wikipedia/ (fetched by
scripts/uk_military_1980_fetch.py); the rows, years and decisions are in
scripts/uk_military_1980_spec.py. Coordinates come from each article's {{coord}} template
(the title/infobox one), rounded to 3 decimals. Each row's check regex must match its
article (or one of its extra pages); with -v the matching snippets are printed for review.

Run: .venv/bin/python scripts/uk_military_1980_build.py [-v]
"""

import csv
import json
import pathlib
import re
import sys
import urllib.parse
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uk_military_1980_spec as spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/uk_military/wikipedia"
HTML = ROOT / "data/raw/uk_military/html"
OUT = ROOT / "data/curated/features/uk_military_sites_1980.csv"
VERBOSE = "-v" in sys.argv


# coordinate parsing as in scripts/us_military_1985_build.py
def templates(w):
    out = []
    for m in re.finditer(r"\{\{\s*[Cc]oord\s*\|", w):
        i = m.end()
        depth = 1
        j = i
        while j < len(w) and depth:
            if w.startswith("{{", j):
                depth += 1
                j += 2
            elif w.startswith("}}", j):
                depth -= 1
                j += 2
            else:
                j += 1
        body = w[i : j - 2]
        # strip nested templates
        while re.search(r"\{\{[^{}]*\}\}", body):
            body = re.sub(r"\{\{[^{}]*\}\}", "", body)
        out.append(body.split("|"))
    return out


def dms(xs):
    return sum(float(x) / 60**n for n, x in enumerate(xs) if x)


def parse(parts):
    named = {p.split("=")[0].strip(): p.split("=", 1)[1].strip() for p in parts if "=" in p}
    pos = [p.strip() for p in parts if "=" not in p]
    for k, p in enumerate(pos):
        if p.upper() in ("N", "S"):
            for jj, q in enumerate(pos[k + 1 :]):
                if q.upper() in ("E", "W"):
                    return (
                        dms(pos[:k]) * (1 if p.upper() == "N" else -1),
                        dms(pos[k + 1 : k + 1 + jj]) * (1 if q.upper() == "E" else -1),
                        named,
                    )
            return None
    try:
        return float(pos[0]), float(pos[1]), named
    except Exception:
        return None


def get(w):
    """The title/infobox {{coord}} of a wikitext (display=title), else the first one."""
    best = None
    for parts in templates(w):
        res = parse(parts)
        if not res:
            if any(p.strip().startswith("display=") and "title" in p for p in parts):
                return None  # title coordinates filled from Wikidata: use the rendered page
            continue
        lat, lon, named = res
        if "title" in named.get("display", "") or named.get("display", "") == "t":
            return lat, lon
        if best is None:
            best = (lat, lon)
    return best


def load(page):
    return json.load(open(RAW / (page.replace(" ", "_").replace("/", "_") + ".json")))["parse"]


def html_coord(page):
    """Coordinates from the rendered page (infobox {{coord}} filled from Wikidata), saved in data/raw/uk_military/html/."""
    f = HTML / (load(page)["title"].replace(" ", "_") + ".html")
    if not f.exists():
        return None
    m = re.search(r'class="geo-dec"[^>]*>([\d.]+)°([NS]) ([\d.]+)°([EW])<', f.read_text())
    if not m:
        return None
    return float(m.group(1)) * (1 if m.group(2) == "N" else -1), float(m.group(3)) * (
        1 if m.group(4) == "E" else -1
    )


def url(page):
    t = load(page)["title"]
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
        t.replace(" ", "_"), safe="(),_-.'"
    )


rows, bad = [], 0
for s in spec.R:
    page = s["page"]
    cpage = s["coord"] if isinstance(s["coord"], str) else page
    if isinstance(s["coord"], tuple):
        lat, lon = s["coord"]
    else:
        res = get(load(cpage)["wikitext"])
        from_html = False
        if res is None:
            res = html_coord(cpage)
            from_html = res is not None
        if res is None:
            print("NO COORD", s["site"], cpage, file=sys.stderr)
            bad += 1
            continue
        lat, lon = res
    if not (49.8 < lat < 61 and -8.7 < lon < 2):
        print("OUTSIDE UK", s["site"], lat, lon, file=sys.stderr)
        bad += 1
    texts = [load(p)["wikitext"] for p in [page] + s["extra"]]
    hits = [m for t in texts for m in re.finditer(s["chk"], t)]
    if not hits:
        print("CHECK FAILED", s["site"], s["chk"], file=sys.stderr)
        bad += 1
    elif VERBOSE:
        m = hits[0]
        t = m.string
        print(
            f"{s['site']}: ...{t[max(0, m.start() - 120) : m.end() + 120]}...".replace("\n", " "),
            file=sys.stderr,
        )
    srcs = [url(page)] + ([url(cpage)] if cpage != page else []) + [url(e) for e in s["extra"]]
    if not isinstance(s["coord"], tuple) and from_html:
        k = srcs.index(url(cpage))
        srcs[k] += " (coordinates from the rendered page, filled from Wikidata)"
    rows.append(
        dict(
            site=s["site"],
            role=s["role"],
            unit=s["unit"],
            country=s["country"],
            town=s["town"],
            lat=f"{lat:.3f}",
            lon=f"{lon:.3f}",
            from_year=s["from_year"],
            until_year=s["until_year"],
            in_role_1980="true" if s["in_role_1980"] else "false",
            decision=s["decision"],
            note=s["note"],
            source="; ".join(dict.fromkeys(srcs)),
        )
    )

cols = [
    "site",
    "role",
    "unit",
    "country",
    "town",
    "lat",
    "lon",
    "from_year",
    "until_year",
    "in_role_1980",
    "decision",
    "note",
    "source",
]
with open(OUT, "w", newline="") as fh:
    wr = csv.DictWriter(fh, cols)
    wr.writeheader()
    wr.writerows(rows)
print(len(rows), "rows;", bad, "problems", file=sys.stderr)
c = Counter((r["role"], r["in_role_1980"]) for r in rows)
for role in dict.fromkeys(r["role"] for r in rows):
    print(
        f"  {role}: {c[(role, 'true')]} in / {c[(role, 'true')] + c[(role, 'false')]}",
        file=sys.stderr,
    )
