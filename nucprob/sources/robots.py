"""Obey each source host's robots.txt, and record what it says about every registered source.

    python -m nucprob.sources.robots     # writes runs/qa/robots.csv

`check` answers for one URL and `nucprob.sources.fetch.download` asks it before every download. A URL
is fetched only if the host allows all of AGENTS: this project's own User-Agent, the general `*`
rule, and the two names that the project's automated agents answer to. Unavailability follows RFC
9309, section 2.3.1: a 4xx answer for robots.txt sets no rule, while a 5xx answer or no answer means
that nothing may be assumed, so nothing is fetched.

Files already in data/raw/ are not touched here. Each row is judged on the URL the held bytes came
from: `obtained_from` in data/sources_obtained.yaml where it has one (a licensed mirror or an archived capture), else
its `url`. The publisher's own answer is kept beside it (`publisher_status`, `publisher_allowed`), so
a source obtained from a mirror because its publisher refuses stays visible. The table says which
files came from a URL that disallows them, so that the decision about them is visible.
"""

import csv
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from nucprob.paths import RAW, RUNS

USER_AGENT = "nuclear-probabilities research project (historical data; contact via GitHub)"
AGENTS = (USER_AGENT, "*", "ClaudeBot", "anthropic-ai")
OUT = RUNS / "qa" / "robots.csv"
# Fetches made by record-keeping scripts, not registered as sources: one URL for each kind of path.
SCRIPT_URLS = {
    "script:weurope_military_1965_fetch": "https://en.wikipedia.org/wiki/Nike?action=raw",
}
# Routes that earlier work used and its cards record, one URL for each kind of path. They are listed so
# that their refusal stays visible; no code uses them now. The pages behind the tables they fed are
# registered through allowed paths in data/curated/features/cited_pages.csv; their copies are not held.
PAST_ROUTES = {
    # weurope_military_sites_1965 and us_military_sites_1985 (their cards)
    "past:wikipedia_index_raw": "https://en.wikipedia.org/w/index.php?title=Thor&action=raw",
    # uk_districts_1981_seats, a table of 1981 district seats removed from the tree with the Nomis district
    # names it was built on (tenth amendment; git history before this change holds its card, Method 1)
    "past:wikipedia_special_export": "https://en.wikipedia.org/wiki/Special:Export/Bolsover",
    # uk_districts_1981_seats (Method 3 of the removed card), gazetteer TOWNS_INSTRUCTIONS.md before 2026-11-02, and
    # one wargame page in data/notes/warsaw_pact.md
    "past:wikipedia_api": "https://en.wikipedia.org/w/api.php?action=parse&page=Thor&prop=wikitext",
}


class RobotsRefused(RuntimeError):
    """The host's robots.txt does not allow this download, or could not be read."""


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    status: str  # rules, no_rule_http_<code>, unavailable_http_<code>, unreachable
    denied_agents: tuple[str, ...] = ()


def read_rules(host_url: str, get=requests.get) -> tuple[str, list[str] | None]:
    """A host's status and robots.txt lines. None means that no rule could be read."""
    try:
        r = get(f"{host_url}/robots.txt", timeout=30, headers={"User-Agent": USER_AGENT})
    except requests.RequestException:
        return "unreachable", None
    if r.status_code == 200:
        return "rules", r.text.splitlines()
    if 400 <= r.status_code < 500:
        return f"no_rule_http_{r.status_code}", []
    return f"unavailable_http_{r.status_code}", None


def judge(url: str, status: str, lines: list[str] | None) -> Verdict:
    if lines is None:
        return Verdict(False, status, AGENTS)
    parser = RobotFileParser()
    parser.parse(lines)
    denied = tuple(a for a in AGENTS if not parser.can_fetch(a, url))
    return Verdict(not denied, status, denied)


_cache: dict[str, tuple[str, list[str] | None]] = {}


def check(url: str, get=requests.get) -> Verdict:
    parts = urlparse(url)
    host_url = f"{parts.scheme}://{parts.netloc}"
    if host_url not in _cache:
        _cache[host_url] = read_rules(host_url, get)
    return judge(url, *_cache[host_url])


def require(url: str, get=requests.get) -> None:
    v = check(url, get)
    if not v.allowed:
        raise RobotsRefused(f"{url}: {v.status}, denied to {', '.join(v.denied_agents)}")


def main() -> None:
    from nucprob.sources.fetch import load_manifest  # fetch imports this module

    sources = load_manifest()["sources"]
    entries = [
        (
            s["id"],
            str(s.get("obtained_from") or s.get("url") or ""),
            str(s.get("url") or ""),
            s.get("role", ""),
            s.get("retrieved", ""),
            s.get("path"),
        )
        for s in sources
    ] + [(k, u, u, "script", "", None) for k, u in SCRIPT_URLS.items()]
    entries += [(k, u, u, "past_route", "", None) for k, u in PAST_ROUTES.items()]
    rows = []
    for name, url, publisher, role, retrieved, path in entries:
        known = url.startswith("http")
        v = check(url) if known else None
        p = check(publisher) if publisher != url and publisher.startswith("http") else v
        rows.append(
            {
                "id": name,
                "host": urlparse(url).netloc if known else "",
                "status": v.status if known else "no_url",
                "allowed": v.allowed if known else "",
                "denied_agents": "; ".join(
                    "project" if a == USER_AGENT else a for a in (v.denied_agents if known else ())
                ),
                "role": role,
                "retrieved": retrieved,
                "held_locally": (RAW / path).exists() if path else False,
                "checked": "obtained_from" if url != publisher else ("url" if known else ""),
                "publisher_status": p.status if p else "",
                "publisher_allowed": p.allowed if p else "",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    refused = [r for r in rows if r["allowed"] is False]
    print(f"{len(rows)} sources; {len(refused)} on hosts that do not allow them; see {OUT}")


if __name__ == "__main__":
    main()
