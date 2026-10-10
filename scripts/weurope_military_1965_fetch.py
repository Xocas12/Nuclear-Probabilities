"""Fetch Wikipedia wikitext for data/curated/features/weurope_military_sites_1965.csv.

Saves one JSON file per page under data/raw/weurope_military/wikipedia/<lang>/ with the
URL it was fetched from ({"lang", "requested", "title", "url", "fetched", "wikitext"}).
The action API was rate-limited (HTTP 429), so pages come through index.php?action=raw;
redirects are followed by hand.

Usage: .venv/bin/python -I scripts/weurope_military_1965_fetch.py de:Fliegerhorst_Büchel en:Ramstein_Air_Base ...
       .venv/bin/python -I scripts/weurope_military_1965_fetch.py --search de "Nike-Stellung"
"""

import html
import json
import pathlib
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/weurope_military/wikipedia"
UA = "nuclear-probabilities-research/1.0 (historical dataset; contact via repository owner)"
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")


def fname(title):
    return re.sub(r'[/\\:*?"<>|]', "_", title.replace(" ", "_")) + ".json"


def path(lang, title):
    return RAW / lang / fname(title)


def get(url, tries=8):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 503, 502):
                time.sleep(5 * (k + 1))
                continue
            raise
        except Exception:
            time.sleep(3 * (k + 1))
    raise RuntimeError("failed " + url)


def fetch(lang, title, force=False):
    title = title.replace("_", " ")
    p = path(lang, title)
    if p.exists() and not force:
        return json.load(open(p))
    t = title
    for _ in range(4):
        url = f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(t.replace(' ', '_'))}&action=raw"
        w = get(url)
        if w is None:
            print("MISSING", lang, title, file=sys.stderr)
            return None
        m = re.match(
            r"\s*#(?:REDIRECT|WEITERLEITUNG|DOORVERWIJZING|OMDIRIGERING|RINVIA)\s*\[\[([^\]|#]+)",
            w,
            re.I,
        )
        if m:
            t = m.group(1).strip()
            continue
        break
    d = dict(
        lang=lang,
        requested=title,
        title=t,
        url=f"https://{lang}.wikipedia.org/wiki/"
        + urllib.parse.quote(t.replace(" ", "_"), safe="(),_-.'"),
        raw_url=url,
        fetched=datetime.now(UTC).isoformat(timespec="seconds"),
        wikitext=w,
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(p, "w"), ensure_ascii=False)
    time.sleep(0.7)
    return d


def search(lang, q, n=20):
    sp = {
        "de": "Spezial:Suche",
        "nl": "Speciaal:Zoeken",
        "da": "Speciel:Søgning",
        "it": "Speciale:Ricerca",
    }.get(lang, "Special:Search")
    url = f"https://{lang}.wikipedia.org/w/index.php?search={urllib.parse.quote(q)}&title={urllib.parse.quote(sp)}&ns0=1&fulltext=1&limit={n}"
    h = get(url) or ""
    return [
        html.unescape(t)
        for t in re.findall(r'mw-search-result-heading"><a href="[^"]*" title="([^"]*)"', h)
    ]


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--search":
        for t in search(a[1], " ".join(a[2:])):
            print(t)
    else:
        for x in a:
            lang, t = x.split(":", 1)
            d = fetch(lang, t)
            if d:
                print(lang, d["title"], len(d["wikitext"]))
