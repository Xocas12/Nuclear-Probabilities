"""Fetch Wikipedia wikitext for the UK 1980 military-sites table.

Saves one JSON per requested page under data/raw/uk_military/wikipedia/ with the URL it came
from ({"parse": {"requested", "title", "url", "wikitext"}}). Uses index.php?action=raw (the API
is rate-limited) and follows #REDIRECTs.

Run: .venv/bin/python scripts/uk_military_1980_fetch.py "Page title" ...   (or no args = all spec pages)
"""

import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/uk_military/wikipedia"
UA = "nuclear-probabilities historical research (contact xocas75 via repo owner)"


def fname(page):
    return RAW / (page.replace(" ", "_").replace("/", "_") + ".json")


def raw(title):
    u = (
        "https://en.wikipedia.org/w/index.php?title="
        + urllib.parse.quote(title.replace(" ", "_"))
        + "&action=raw"
    )
    for k in range(5):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            return u, urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
        except Exception as e:
            if "404" in str(e):
                return u, None
            time.sleep(5 * (k + 1))
    raise RuntimeError(title)


def fetch(page):
    f = fname(page)
    if f.exists():
        return
    title, urls = page, []
    for _ in range(3):
        u, w = raw(title)
        urls.append(u)
        if w is None:
            print("MISSING", page, file=sys.stderr)
            return
        m = re.match(r"\s*#REDIRECT\s*:?\s*\[\[([^\]#|]+)", w, re.I)
        if not m:
            break
        title = m.group(1).strip()
        time.sleep(1)
    RAW.mkdir(parents=True, exist_ok=True)
    json.dump(
        {
            "parse": {
                "requested": page,
                "title": title,
                "url": urls[-1],
                "fetched_via": urls,
                "wikitext": w,
            }
        },
        open(f, "w"),
        ensure_ascii=False,
    )
    print("ok", page, "->", title, len(w), file=sys.stderr)
    time.sleep(1)


if __name__ == "__main__":
    pages = sys.argv[1:]
    if not pages:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        import uk_military_1980_spec as spec

        pages = list(
            dict.fromkeys(
                [
                    p
                    for s in spec.R
                    for p in [s["page"]]
                    + s["extra"]
                    + ([s["coord"]] if isinstance(s["coord"], str) else [])
                ]
            )
        )
    for p in pages:
        fetch(p)
