"""Build data/curated/features/us_military_sites_1985.csv (documented in
data/curated/features/us_military_sites_1985.md).

Reads the Wikipedia wikitext saved under data/raw/us_military/wikipedia/ and the 1990 county
boundaries (data/raw/census/co99_d90); the rows, years and decisions are in
scripts/us_military_1985_spec.py. Coordinates come from each article's {{coord}} template
(the title/infobox one), rounded to 3 decimals; missile-field centres are the mean of the
launch facilities listed with coordinates on Wikipedia.

Run: .venv/bin/python scripts/us_military_1985_build.py
"""

import csv
import json
import math
import pathlib
import re
import sys
import urllib.parse
from collections import Counter
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import shapefile
import us_military_1985_spec as spec
from shapely.geometry import Point, shape

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/us_military/wikipedia"
OUT = ROOT / "data/curated/features/us_military_sites_1985.csv"
STUDY = date(1985, 6, 30)
ST = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}

sf = shapefile.Reader(str(ROOT / "data/raw/census/co99_d90/co99_d90.shp"))
geoms = {}
for sr in sf.iterShapeRecords():
    rec = sr.record.as_dict()
    fips = rec["ST"] + rec["CO"]
    g = shape(sr.shape.__geo_interface__)
    geoms[fips] = (
        geoms[fips][0].union(g) if fips in geoms else g,
        rec["NAME"],
        ST.get(rec["ST"], rec["ST"]),
    )


def county(lat, lon):
    p = Point(lon, lat)
    for f, (g, n, s) in geoms.items():
        if g.contains(p):
            return f, n, s, 0.0
    # in water: nearest county (distance in degrees -> km approx)
    best = min(geoms.items(), key=lambda kv: kv[1][0].distance(p))
    d = best[1][0].distance(p) * 111 * math.cos(math.radians(lat)) if best else None
    return best[0], best[1][1], best[1][2], d


def load(page):
    return json.load(open(RAW / (page.replace(" ", "_").replace("/", "_") + ".json")))["parse"]


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


def get(page):
    j = load(page)
    best = None
    for parts in templates(j["wikitext"]):
        r = parse(parts)
        if not r:
            continue
        lat, lon, named = r
        if "title" in named.get("display", "") or "t" == named.get("display", ""):
            return j, (lat, lon), "title"
        if best is None:
            best = ((lat, lon), "first")
    if best:
        return (j, *best)
    return j, None, "none"


def url(page):
    t = load(page)["title"]
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
        t.replace(" ", "_"), safe="(),_-.'"
    )


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * 6371 * math.asin(math.sqrt(h))


def named_coords(w):
    out = []
    for m in re.finditer(r"([^\n]*?)\{\{\s*[Cc]oord\|([^{}]*)\}\}", w):
        parts = m.group(2).split("|")
        nm = dict(p.split("=", 1) for p in parts if "=" in p).get("name", "").strip()
        r = parse(parts)
        if r:
            out.append((nm, r[0], r[1], m.group(1)))
    return out


MON = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}


def pdate(s):
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", s.strip())
    return date(int(m.group(3)), MON[m.group(2).lower()], int(m.group(1))) if m else None


rows = []
for s in spec.R:
    page = s["page"]
    cpage = s["coord"] if isinstance(s["coord"], str) else page
    if isinstance(s["coord"], tuple):
        lat, lon = s["coord"]
    else:
        j, r, how = get(cpage)
        lat, lon = r
    srcs = [url(page)] + ([url(cpage)] if cpage != page else []) + [url(e) for e in s["extra"]]
    if isinstance(s["coord"], tuple):
        srcs[0] += " (coordinates from the rendered page)"
    f, cn, cst, d = county(lat, lon)
    note = s["note"]
    if d and d > 0:
        note = (
            note + " " if note else ""
        ) + f"Point is in water; nearest county assigned ({d:.1f} km)."
    rows.append(
        dict(
            site=s["site"],
            role=s["role"],
            unit=s["unit"],
            state=s["state"],
            town=s["town"],
            lat=f"{lat:.3f}",
            lon=f"{lon:.3f}",
            county_fips=f,
            county=cn,
            from_year=s["from_year"],
            until_year=s["until_year"],
            in_role_1985="true" if s["in_role_1985"] else "false",
            decision=s["decision"],
            note=note,
            source="; ".join(dict.fromkeys(srcs)),
        )
    )
    if cst != s["state"]:
        print("STATE MISMATCH", s["site"], s["state"], cst, cn, file=sys.stderr)

# ---- missile fields ----
for name, src, kind, fr, un, inr, dec in spec.FIELDS:
    pts = []
    pages = [src] if isinstance(src, str) else src
    active = 0
    for p in pages:
        w = load(p)["wikitext"]
        for nm, la, lo, pre in named_coords(w):
            if kind == "list" and re.fullmatch(r"[A-T]-\d{1,2}", nm):
                pts.append((la, lo))
            elif kind == "titan" and re.fullmatch(r"\d{3}-\d", nm):
                pts.append((la, lo))
                m = re.search(r"\(([^()]*?)\s*[–-]\s*([^()]*?)\)", pre)
                end = pdate(m.group(2)) if m else None
                if end is None:
                    m2 = re.search(r"[–-]\s*(\d{1,2}\s+\w+\s+\d{4})", pre)
                    end = pdate(m2.group(1)) if m2 else None
                if end and end > STUDY:
                    active += 1
                if end is None:
                    print("NO END DATE", nm, pre[-80:], file=sys.stderr)
    pts = list(dict.fromkeys(pts))
    clat = sum(p[0] for p in pts) / len(pts)
    clon = sum(p[1] for p in pts) / len(pts)
    radius = max(hav((clat, clon), p) for p in pts)
    cnt = {}
    for la, lo in pts:
        f, cn, cst, d = county(la, lo)
        cnt[(cst, cn, f)] = cnt.get((cst, cn, f), 0) + 1
    states = "/".join(
        sorted({k[0] for k in cnt}, key=lambda x: -sum(v for k, v in cnt.items() if k[0] == x))
    )
    clist = ", ".join(
        f"{cn} {cst} ({f}) {v}" for (cst, cn, f), v in sorted(cnt.items(), key=lambda kv: -kv[1])
    )
    if kind == "list":
        what = (
            f"{len(pts)} launch and alert facilities (named A-T) from the wing's launch-site list"
        )
    else:
        what = f"{len(pts)} Titan II launch complexes from the squadron articles; {active} still in service on 30 Jun 1985 by the listed off-alert dates"
    f0, cn0, cst0, _ = county(clat, clon)
    note = f"Centre = mean of {what}; all sites within {radius:.0f} km of it. Counties (sites per county, 1990 FIPS): {clist}."
    rows.append(
        dict(
            site=name,
            role="missile_field",
            unit=name.replace(" missile field", ""),
            state=states,
            town="",
            lat=f"{clat:.3f}",
            lon=f"{clon:.3f}",
            county_fips=f0,
            county=cn0,
            from_year=fr,
            until_year=un,
            in_role_1985="true" if inr else "false",
            decision=dec,
            note=note,
            source="; ".join(url(p) for p in pages),
        )
    )
    print(
        name,
        len(pts),
        "active85=",
        active if kind == "titan" else "-",
        f"{radius:.0f}km",
        states,
        file=sys.stderr,
    )

cols = [
    "site",
    "role",
    "unit",
    "state",
    "town",
    "lat",
    "lon",
    "county_fips",
    "county",
    "from_year",
    "until_year",
    "in_role_1985",
    "decision",
    "note",
    "source",
]
with open(OUT, "w", newline="") as fh:
    wr = csv.DictWriter(fh, cols)
    wr.writeheader()
    wr.writerows(rows)
print(len(rows), Counter(r["role"] for r in rows), file=sys.stderr)
