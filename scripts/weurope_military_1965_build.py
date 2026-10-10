"""Build data/curated/features/weurope_military_sites_1965.csv (documented in
data/curated/features/weurope_military_sites_1965.md).

Reads the Wikipedia wikitext saved under data/raw/weurope_military/wikipedia/<lang>/ (fetched
by scripts/weurope_military_1965_fetch.py); the rows, years and decisions are in
scripts/weurope_military_1965_spec.py.

Coordinates:
  * 'page' / a page ref -> the article's title/infobox coordinate template, 3 decimals;
  * ('named', ref, regex) -> the coordinate template on the line of that article matching regex
    (e.g. one launch site in a list);
  * (lat, lon, ref, quote) -> a coordinate written in a list/table/location map of that article;
    the build checks that `quote` occurs verbatim in the saved wikitext.
Each row's `chk` regex must match the text of its cited pages; the build stops if one fails.

Run: .venv/bin/python -I scripts/weurope_military_1965_build.py
"""

import csv
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import weurope_military_1965_coords as C
import weurope_military_1965_spec as spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data/curated/features/weurope_military_sites_1965.csv"
COLS = [
    "site",
    "role",
    "unit",
    "country",
    "town",
    "lat",
    "lon",
    "from_year",
    "until_year",
    "in_role_1965",
    "decision",
    "note",
    "coord_source",
    "source",
]
BOX = {  # rough country boxes, to catch swapped or wrong coordinates
    "DE": (47.2, 55.1, 5.8, 13.9),
    "DK": (54.5, 57.8, 8.0, 15.2),
    "NL": (50.7, 53.6, 3.3, 7.3),
    "BE": (49.4, 51.6, 2.5, 6.5),
    "AT": (46.3, 49.1, 9.5, 17.2),
    "IT": (44.4, 47.1, 6.6, 13.9),
    "FR": (42.0, 51.2, -5.0, 8.3),
}


def url(ref):
    d = C.load(ref)
    return d["url"]


def text(ref):
    return C.load(ref)["wikitext"]


def plain(ref):
    """Wikitext with refs removed, links reduced to their labels, bold/italic quotes dropped."""
    w = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text(ref), flags=re.S)
    w = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", w)
    w = w.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", w)


fails = []
rows = []
for s in spec.R:
    missing = [
        x
        for x in s["src"]
        + [
            v
            for v in (s["coord"] if isinstance(s["coord"], tuple) else [s["coord"]])
            if isinstance(v, str) and ":" in v and not v.startswith(("{", "lat"))
        ]
        if not (C.RAW / x.split(":", 1)[0] / C.fname(x.split(":", 1)[1].replace("_", " "))).exists()
    ]
    if missing:
        fails.append(f"MISSING PAGE {s['site']}: {missing}")
        continue
    srcs = list(s["src"])
    c = s["coord"]
    how = ""
    if c == "page" or isinstance(c, str):
        ref = srcs[0] if c == "page" else c
        r = C.title_coord(ref)
        if r is None:
            fails.append(f"NO COORD {s['site']} in {ref}")
            continue
        lat, lon, kind = r
        how = f"{ref.split(':')[0]}wiki title/infobox coordinate ({C.load(ref)['title']})"
        if ref not in srcs:
            srcs.append(ref)
    elif c[0] == "named":
        _, ref, rx = c
        r = C.named_coord(ref, rx)
        if r is None:
            fails.append(f"NO NAMED COORD {s['site']} {rx} in {ref}")
            continue
        lat, lon, kind = r
        how = f"{ref.split(':')[0]}wiki coordinate in list ({C.load(ref)['title']}: {rx})"
        if ref not in srcs:
            srcs.append(ref)
    else:
        lat, lon, ref, quote = c
        if quote not in text(ref):
            fails.append(f"QUOTE NOT FOUND {s['site']}: {quote!r} in {ref}")
        how = f"{ref.split(':')[0]}wiki list/map entry ({C.load(ref)['title']}: {quote})"
        if ref not in srcs:
            srcs.append(ref)
    b = BOX[s["country"]]
    if not (b[0] <= lat <= b[1] and b[2] <= lon <= b[3]):
        fails.append(f"OUT OF BOX {s['site']} {s['country']} {lat:.3f},{lon:.3f}")
    if s["chk"]:
        blob = "\n".join(text(x) + "\n" + plain(x) for x in srcs)
        if not re.search(s["chk"], blob):
            fails.append(f"CHK FAILED {s['site']}: {s['chk']!r}")
    rows.append(
        dict(
            site=s["site"],
            role=s["role"],
            unit=s["unit"],
            country=s["country"],
            town=s["town"],
            lat=f"{lat:.3f}",
            lon=f"{lon:.3f}",
            from_year=s["fr"],
            until_year=s["un"],
            in_role_1965="true" if s["inr"] else "false",
            decision=s["dec"],
            note=s["note"],
            coord_source=how,
            source="; ".join(dict.fromkeys(url(x) for x in srcs)),
        )
    )

dup = [k for k, v in Counter((r["site"], r["role"]) for r in rows).items() if v > 1]
if dup:
    fails.append(f"DUPLICATE site/role {dup}")
if fails:
    print("\n".join(fails), file=sys.stderr)
    sys.exit(1)

with open(OUT, "w", newline="") as fh:
    wr = csv.DictWriter(fh, COLS)
    wr.writeheader()
    wr.writerows(rows)
print(len(rows), "rows", file=sys.stderr)
for k, v in sorted(Counter((r["role"], r["in_role_1965"]) for r in rows).items()):
    print(f"  {k[0]:22s} {k[1]:5s} {v}", file=sys.stderr)
print(Counter(r["country"] for r in rows), file=sys.stderr)
