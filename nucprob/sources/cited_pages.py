"""A registry of the web pages cited row by row in the curated site tables.

    python -m nucprob.sources.cited_pages          # fetch what is not yet recorded, one request a second
    python -m nucprob.sources.cited_pages --check  # say what is missing, fetch nothing

The site tables (one read back from git history, `nucprob.sources.history`), and the gazetteer tables built
from Wikipedia, cite their pages row by row. This registry gives each page the host's
licence, the date it was retrieved here and the hash of the bytes received, with Wikipedia's revision id when
the page states one. These are the pages as they stood on that date, not as they stood when the row was
written: where a table was made from an earlier copy, nothing here shows that the two agree. A page that
robots.txt refuses, or that gives an error, is recorded with that status and no hash. Pages are not kept:
only their hashes are committed.

Writes data/curated/features/cited_pages.csv.
"""

import argparse
import csv
import datetime as dt
import hashlib
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from nucprob.paths import CURATED
from nucprob.sources import history, robots

FEATURES = CURATED / "features"
GAZETTEER = CURATED / "gazetteer"
TABLES = {
    "bloc_air_defence_1956": FEATURES,
    "military_sites_1956": FEATURES,
    "weurope_military_sites_1965": FEATURES,
    # Gazetteer tables read from Wikipedia, some through paths robots.txt disallows (README, "Robots"):
    # their pages are registered here through paths it allows.
    "frg_1961_wikipedia": GAZETTEER,
    "closed_cities_1956": GAZETTEER,
}
OUT = FEATURES / "cited_pages.csv"
COLUMNS = ["url", "host", "tables", "rows", "licence", "retrieved", "status", "sha256", "revision"]
URL = re.compile(r"https?://[^\s;|\]\"]+")
REVISION = re.compile(rb'"wgRevisionId":(\d+)')
LICENCE = {
    "wikipedia.org": "CC BY-SA 4.0 (Wikipedia); facts cited, page not kept",
    "www.ww2.dk": "No open licence stated (Michael Holm); facts cited, page not kept",
}
OTHER_LICENCE = "None read for this page; facts cited, page not kept"


def licence_of(host: str) -> str:
    return next((v for k, v in LICENCE.items() if host.endswith(k)), OTHER_LICENCE)


def urls_in(text: str) -> set[str]:
    """URLs in a cell. Wikipedia titles may hold commas and brackets, so only a trailing comma, full
    stop or unmatched bracket is the text's and not the URL's."""
    out = set()
    for u in URL.findall(text):
        u = u.rstrip(",.")
        while u.endswith(")") and u.count(")") > u.count("("):
            u = u[:-1].rstrip(",.")
        out.add(u)
    return out


def cited() -> dict[str, dict]:
    """Each URL in the tables, with the tables and the number of rows that cite it."""
    pages: dict[str, dict] = {}
    paths = {name: folder / f"{name}.csv" for name, folder in TABLES.items()}
    for p in history.PINNED:
        paths[Path(p.path).stem] = history.restore(p)
    for name, path in paths.items():
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                urls = {u for v in row.values() if v for u in urls_in(v)}
                for u in urls:
                    p = pages.setdefault(u, {"tables": set(), "rows": 0})
                    p["tables"].add(name)
                    p["rows"] += 1
    return pages


def recorded() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    with open(OUT, encoding="utf-8", newline="") as fh:
        return {r["url"]: r for r in csv.DictReader(fh)}


def retrieve(url: str) -> dict:
    today = dt.datetime.now(dt.UTC).date().isoformat()
    verdict = robots.check(url)
    if not verdict.allowed:
        return {"retrieved": today, "status": f"refused by robots.txt ({verdict.status})"}
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": robots.USER_AGENT})
    except requests.RequestException as err:
        return {"retrieved": today, "status": f"not obtained: {type(err).__name__}"}
    if r.status_code != 200:
        return {"retrieved": today, "status": f"not obtained: HTTP {r.status_code}"}
    rev = REVISION.search(r.content)
    return {
        "retrieved": today,
        "status": "ok",
        "sha256": hashlib.sha256(r.content).hexdigest(),
        "revision": rev.group(1).decode() if rev else "",
    }


def write(pages: dict[str, dict], results: dict[str, dict]) -> None:
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, COLUMNS, lineterminator="\n")
        w.writeheader()
        for url in sorted(pages):
            host = urlparse(url).netloc
            w.writerow(
                {
                    "url": url,
                    "host": host,
                    "tables": " ".join(sorted(pages[url]["tables"])),
                    "rows": pages[url]["rows"],
                    "licence": licence_of(host),
                    "retrieved": "",
                    "status": "",
                    "sha256": "",
                    "revision": "",
                }
                | {k: v for k, v in results.get(url, {}).items() if k in COLUMNS[5:]}
            )


def main(argv: list[str] | None = None) -> int:
    args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    args.add_argument("--check", action="store_true")
    check = args.parse_args(argv).check
    pages, results = cited(), recorded()
    todo = [u for u in sorted(pages) if not results.get(u, {}).get("retrieved")]
    print(f"{len(pages)} pages cited, {len(todo)} not yet recorded")
    if check:
        return 1 if todo else 0
    for i, url in enumerate(todo):
        results[url] = retrieve(url)
        if i % 25 == 0:
            write(pages, results)
            print(i, url, results[url]["status"], flush=True)
        time.sleep(1.0)
    write(pages, results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
