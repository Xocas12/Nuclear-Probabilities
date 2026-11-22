"""Dated facilities worldwide from Wikidata (CC0): military, economic, political and
administrative sites with coordinates, opening and closing dates, country and capacity.

    python -m nucprob.sources.wikidata_facilities [fetch|build|all]

`fetch()` queries query.wikidata.org and saves every raw SPARQL response (gzipped JSON, with the
query text) under data/raw/wikidata/, then writes data/sources.d/wikidata_facilities.yaml.
`build()` reads only those raw files and writes data/processed/wikidata_facilities.parquet,
one row per item and class (an item can sit in two classes, e.g. a naval base and a port), or,
for capitals, one row per city, polity and stint. `active(year, classes)` returns the rows open
in a year.

How classes are found. Each class is a set of root classes; its members are items whose P31
(instance of) is a root or, for most classes, any subclass of one (P279*), minus excluded
subtrees (gendarmerie barracks, quarries, marinas, breweries...). Only items with coordinates
(P625) are kept. The class specs are in CLASSES.

Dates. `start_year` is the year of service entry / official opening (P729) when present, else
inception (P571); `end_year` is the earliest of dissolved/abolished (P576), service retirement
(P730) and official closure (P3999). An item is active in `year` when start_year <= year and
(end_year is missing or end_year > year). Items with no start date are kept with
`undated = True`. Capitals take their dates from the P580/P582 qualifiers of P36 (or P1376);
where a qualifier is missing they fall back on the polity's inception / dissolution
(`start_source`, `end_source` say which).

Caveats: Wikidata coverage is uneven (Western Europe and North America are dense, the Soviet
bloc sparse) and its dates are what editors entered, at varying precision (`start_precision`:
9 = year, 8 = decade, 7 = century). The modern catalogue under-represents sites that closed
before the Internet era (survivorship bias), so absence is not evidence of absence.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pandas as pd
import requests

from nucprob.paths import DATA, PROCESSED, RAW

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = (
    "nuclear-probabilities historical research dataset/0.1 "
    "(facility features from Wikidata; python-requests)"
)
RAW_DIR = RAW / "wikidata"
OUT = PROCESSED / "wikidata_facilities.parquet"
FRAGMENT = DATA / "sources.d" / "wikidata_facilities.yaml"
BATCH = 400  # items per detail query
WORKERS = 3  # parallel queries (WDQS allows up to 5 per client)


@dataclass(frozen=True)
class ClassSpec:
    name: str
    family: str
    roots: tuple[str, ...]
    exclude: tuple[str, ...] = ()
    deep: bool = True  # follow P279* below the roots


CLASSES = (
    # military
    ClassSpec(
        "military_base",
        "military",
        ("Q245016", "Q88556", "Q1198413"),  # military base, garrison, military camp
        # gendarmerie barracks, airbase, naval base, military radar station (own classes)
        ("Q83554028", "Q695850", "Q1324633", "Q133288241"),
    ),
    ClassSpec("air_base", "military", ("Q695850",)),
    ClassSpec("naval_base", "military", ("Q1324633", "Q11637431")),  # + military port
    ClassSpec("missile_site", "military", ("Q853409", "Q21193688")),  # launch facility, base
    ClassSpec("launch_site", "military", ("Q1933026", "Q194188")),  # launch site, spaceport
    ClassSpec("weapons_storage", "military", ("Q7978061",)),  # weapon storage area
    ClassSpec(
        "radar_station",
        "military",
        ("Q89578131", "Q16905219", "Q133288241", "Q332548"),
    ),
    ClassSpec("military_hq", "military", ("Q47272186", "Q575259")),  # HQ unit, Fuehrer HQ
    ClassSpec("military_academy", "military", ("Q917182", "Q1935049")),
    ClassSpec("arsenal", "military", ("Q81669", "Q124638970", "Q60983064")),
    ClassSpec("shipyard", "military", ("Q190928",)),  # all shipyards; subclass marks naval
    ClassSpec("nuclear_test_site", "military", ("Q53732481",)),
    ClassSpec(
        "bunker",
        "military",
        ("Q91122", "Q1772543", "Q1346923"),  # bunker, command center, command post
        # infantry/artillery casemates, turrets and tobruks (Second World War field works)
        ("Q61826171", "Q61826172", "Q11863092", "Q11863088", "Q12022155", "Q471359"),
    ),
    # economic
    ClassSpec("power_station", "economic", ("Q159719",), ("Q134447", "Q15911738")),
    ClassSpec("nuclear_power_plant", "economic", ("Q134447",)),
    ClassSpec("hydroelectric", "economic", ("Q15911738", "Q56697283")),
    ClassSpec("oil_refinery", "economic", ("Q12353044",)),
    ClassSpec("steelworks", "economic", ("Q2069494", "Q181485", "Q10832530")),
    ClassSpec("chemical_plant", "economic", ("Q905286",)),
    ClassSpec("aluminium_smelter", "economic", ("Q44396585", "Q65515162")),
    ClassSpec(
        "mine",
        "economic",
        ("Q820477",),
        # quarry, gravel pit, show mine, mining park, solfara, underground quarry
        ("Q188040", "Q504874", "Q1506469", "Q116193487", "Q16607162", "Q140463560"),
    ),
    ClassSpec(
        "port",
        "economic",
        ("Q44782", "Q15310171"),
        # marina, fishing port, landing, ferry stop, guest harbour, naval base (own class)
        ("Q721207", "Q1420027", "Q16938673", "Q133867301", "Q10512405", "Q1324633"),
    ),
    ClassSpec("rail_junction", "economic", ("Q336764", "Q519608")),  # junction, classif. yard
    ClassSpec("airport", "economic", ("Q1248784",), ("Q695850",)),
    ClassSpec(
        "factory",
        "economic",
        ("Q83405", "Q557685"),  # factory, industrial plant
        # breweries, distilleries, armouries, and plants that have their own class
        (
            "Q131734",
            "Q1251750",
            "Q10373548",
            "Q1967269",
            "Q190928",
            "Q10832530",
            "Q12353044",
            "Q2069494",
            "Q905286",
            "Q159719",
            "Q124638970",
        ),
    ),
    ClassSpec(
        "research_institute",
        "economic",
        ("Q31855",),
        # botanical garden, arboretum, rose garden, academic department, seminary,
        # think tank, graduate school
        ("Q167346", "Q272231", "Q291177", "Q2467461", "Q14911880", "Q155271", "Q20820271"),
    ),
    ClassSpec(
        "nuclear_facility",
        "economic",
        ("Q1739545", "Q109909183"),  # nuclear facility, nuclear research institute
        ("Q134447", "Q53732481"),  # power plants and test sites have their own classes
    ),
    # political
    ClassSpec("parliament", "political", ("Q7138926", "Q30124446")),
    ClassSpec(
        "government_seat",
        "political",
        ("Q1901835", "Q113557679", "Q2114972"),  # seat of government (exact), presidential palace
        deep=False,
    ),
)
CAPITAL_CLASSES = ("capital_national", "capital_first_level")
NATIONAL_ROOTS = ("Q6256", "Q3624078", "Q3024240", "Q7275")  # country, sovereign/hist., state
FIRST_LEVEL_ROOTS = ("Q10864048",)  # first-level administrative country subdivision

DATE_PROPS = ("P571", "P729", "P576", "P730", "P3999")
FUEL_WORDS = (
    ("nuclear", ("nuclear",)),
    ("hydro", ("hydro", "pumped", "run-of-river", "tidal")),
    ("coal", ("coal", "lignite", "anthracite")),
    ("gas", ("gas", "combined cycle")),
    ("oil", ("oil", "diesel", "fuel oil", "petroleum", "mazut")),
    ("solar", ("solar", "photovoltaic")),
    ("wind", ("wind",)),
    ("geothermal", ("geothermal",)),
    ("biomass", ("biomass", "biogas", "wood", "waste", "peat")),
    ("storage", ("battery", "storage")),
)


# --------------------------------------------------------------------------- querying


def sparql(query: str, tries: int = 6) -> list[dict]:
    """Run a query, retrying on rate limits and server errors with backoff."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    for attempt in range(tries):
        try:
            r = requests.post(ENDPOINT, data={"query": query}, headers=headers, timeout=180)
            if r.status_code in (429, 500, 502, 503, 504):
                wait = int(r.headers.get("Retry-After", 0) or 0) or 5 * 2**attempt
                raise requests.HTTPError(f"{r.status_code}; waiting {wait}s")
            r.raise_for_status()
            return r.json()["results"]["bindings"]
        except (requests.RequestException, ValueError) as err:
            if attempt == tries - 1:
                raise
            wait = 5 * 2**attempt
            print(f"  {err}; retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    return []


def save_raw(name: str, queries: list[str], results: list[list[dict]]) -> None:
    path = RAW_DIR / f"{name}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "endpoint": ENDPOINT,
        "retrieved": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "licence": "CC0 1.0 (Wikidata)",
        "queries": queries,
        "results": results,
    }
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)


def exists(name: str) -> bool:
    """A raw file already fetched is kept (delete data/raw/wikidata/ to refresh)."""
    return (RAW_DIR / f"{name}.json.gz").exists()


def load_raw(name: str) -> list[dict]:
    """All bindings of a raw file, concatenated across its queries."""
    with gzip.open(RAW_DIR / f"{name}.json.gz", "rt", encoding="utf-8") as fh:
        doc = json.load(fh)
    return [b for res in doc["results"] for b in res]


def run_batched(name: str, template: str, values: list[str], size: int = BATCH) -> None:
    """Fill `{values}` in template with chunks of VALUES rows, run them in parallel, save."""
    if exists(name):
        print(f"{name}: kept")
        return
    chunks = [values[i : i + size] for i in range(0, len(values), size)]
    queries = [template.replace("{values}", " ".join(c)) for c in chunks]
    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(sparql, queries))
    save_raw(name, queries, results)
    print(f"{name}: {len(queries)} queries, {sum(map(len, results))} rows")


def qid(binding: dict, key: str) -> str | None:
    v = binding.get(key, {}).get("value")
    return v.rsplit("/", 1)[-1] if v and v.startswith("http://www.wikidata.org/entity/") else None


def val(binding: dict, key: str) -> str | None:
    return binding.get(key, {}).get("value")


# --------------------------------------------------------------------------- fetch


def subclass_query(spec: ClassSpec) -> str:
    roots = " ".join(f"wd:{r}" for r in spec.roots + spec.exclude)
    path = "wdt:P279*" if spec.deep else "wdt:P279{0}"
    if not spec.deep:
        return f"SELECT ?root ?s ?sl WHERE {{ VALUES ?root {{ {roots} }} BIND(?root AS ?s) {label('s')} }}"
    return (
        f"SELECT ?root ?s ?sl WHERE {{ VALUES ?root {{ {roots} }} ?s {path} ?root . {label('s')} }}"
    )


def label(var: str) -> str:
    return f"OPTIONAL {{ ?{var} rdfs:label ?{var}l FILTER(lang(?{var}l) = 'en') }}"


def class_members(spec: ClassSpec) -> set[str]:
    rows = load_raw(f"classes/{spec.name}")
    keep = {qid(b, "s") for b in rows if qid(b, "root") in spec.roots}
    drop = {qid(b, "s") for b in rows if qid(b, "root") in spec.exclude}
    return keep - drop


def fetch_classes() -> dict[str, set[str]]:
    """Subclass trees of every class, then the items with coordinates in each."""
    members = {}
    for spec in CLASSES:
        q = subclass_query(spec)
        if not exists(f"classes/{spec.name}"):
            save_raw(f"classes/{spec.name}", [q], [sparql(q)])
        subs = sorted(class_members(spec))
        run_batched(
            f"members/{spec.name}",
            "SELECT ?i ?s WHERE { VALUES ?s { {values} } ?i wdt:P31 ?s . "
            "FILTER EXISTS { ?i wdt:P625 [] } }",
            [f"wd:{s}" for s in subs],
            size=150,
        )
        members[spec.name] = {qid(b, "i") for b in load_raw(f"members/{spec.name}")}
    return members


def fetch_capitals() -> set[str]:
    """Polities of national and first-level rank, their capitals (P36) and the cities that
    name them as their capital (P1376), with start and end qualifiers."""
    # one query per root and direction: a single query over all instances times out
    queries = [
        f"SELECT DISTINCT ?p ?root WHERE {{ BIND(wd:{root} AS ?root) "
        f"?s wdt:P279* ?root . ?p wdt:P31 ?s . {link} }}"
        for root in NATIONAL_ROOTS + FIRST_LEVEL_ROOTS
        for link in ("?p p:P36 [] .", "?city wdt:P1376 ?p .")
    ]
    if not exists("capitals/polities"):
        save_raw("capitals/polities", queries, [sparql(q) for q in queries])
    polities = sorted({qid(b, "p") for b in load_raw("capitals/polities")})
    tail = (
        "OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end } "
        "?st wikibase:rank ?rank . FILTER(?rank != wikibase:DeprecatedRank) "
        "FILTER EXISTS { ?city wdt:P625 [] } }"
    )
    values = [f"wd:{p}" for p in polities]
    run_batched(
        "capitals/p36",
        "SELECT ?pol ?city ?start ?end ?rank WHERE { VALUES ?pol { {values} } "
        "?pol p:P36 ?st . ?st ps:P36 ?city . " + tail,
        values,
    )
    run_batched(
        "capitals/p1376",
        "SELECT ?pol ?city ?start ?end ?rank WHERE { VALUES ?pol { {values} } "
        "?city p:P1376 ?st . ?st ps:P1376 ?pol . " + tail,
        values,
    )
    run_batched("capitals/polity_details", POLITY_TEMPLATE, values)
    cities = {qid(b, "city") for f in ("p36", "p1376") for b in load_raw(f"capitals/{f}")}
    return {c for c in cities if c}


POLITY_TEMPLATE = (
    "SELECT ?pol ?pl ?inc ?dis ?country WHERE { VALUES ?pol { {values} } "
    "OPTIONAL { ?pol rdfs:label ?pl FILTER(lang(?pl) = 'en') } "
    "OPTIONAL { ?pol wdt:P571 ?inc } OPTIONAL { ?pol wdt:P576 ?dis } "
    "OPTIONAL { ?pol wdt:P17 ?country } }"
)
LABEL_TEMPLATE = (
    "SELECT ?i ?en ?mul ?native ?official ?coord WHERE { VALUES ?i { {values} } "
    "OPTIONAL { ?i rdfs:label ?en FILTER(lang(?en) = 'en') } "
    "OPTIONAL { ?i rdfs:label ?mul FILTER(lang(?mul) = 'mul') } "
    "OPTIONAL { ?i wdt:P1705 ?native } OPTIONAL { ?i wdt:P1448 ?official } "
    "OPTIONAL { ?i wdt:P625 ?coord } }"
)
DATE_TEMPLATE = (
    "SELECT ?i ?prop ?t ?prec WHERE { VALUES ?i { {values} } "
    "VALUES (?prop ?p ?psv) { "
    + " ".join(f'("{p}" p:{p} psv:{p})' for p in DATE_PROPS)
    + " } ?i ?p ?st . ?st ?psv ?v . ?v wikibase:timeValue ?t ; wikibase:timePrecision ?prec . "
    "?st wikibase:rank ?rank . FILTER(?rank != wikibase:DeprecatedRank) }"
)
COUNTRY_TEMPLATE = (
    "SELECT ?i ?c ?cl ?start ?end ?rank WHERE { VALUES ?i { {values} } "
    "?i p:P17 ?st . ?st ps:P17 ?c ; wikibase:rank ?rank . "
    "FILTER(?rank != wikibase:DeprecatedRank) "
    "OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end } "
    "OPTIONAL { ?c rdfs:label ?cl FILTER(lang(?cl) = 'en') } }"
)
ATTR_TEMPLATE = (
    # the label lookup sits inside each branch: an OPTIONAL on an unbound ?v would match
    # every English label in Wikidata
    "SELECT ?i ?prop ?v ?vl ?amount WHERE { VALUES ?i { {values} } { "
    + " } UNION { ".join(
        f"?i wdt:{p} ?v . BIND('{p}' AS ?prop) "
        "OPTIONAL { ?v rdfs:label ?vl FILTER(lang(?vl) = 'en') }"
        for p in ("P31", "P516", "P1056")
    )
    + " } UNION { ?i p:P2109/psn:P2109/wikibase:quantityAmount ?amount . "
    "BIND('P2109' AS ?prop) } }"
)
LANG_QUERY = (
    "SELECT ?c ?code WHERE { ?c wdt:P31/wdt:P279* wd:Q6256 . ?c wdt:P37 ?l . ?l wdt:P424 ?code . }"
)
LOCAL_TEMPLATE = (
    "SELECT ?i ?lang ?l WHERE { VALUES (?i ?lang) { {values} } "
    "?i rdfs:label ?l FILTER(lang(?l) = ?lang) }"
)


def fetch_details(items: set[str]) -> None:
    values = [f"wd:{i}" for i in sorted(items)]
    for name, template in (
        ("labels", LABEL_TEMPLATE),
        ("dates", DATE_TEMPLATE),
        ("country", COUNTRY_TEMPLATE),
        ("attributes", ATTR_TEMPLATE),
    ):
        run_batched(f"details/{name}", template, values)


def fetch_local_labels() -> None:
    """Labels in the official language of each item's present country (the 'original' label
    where no P1705 native label or P1448 official name exists)."""
    if not exists("details/languages"):
        save_raw("details/languages", [LANG_QUERY], [sparql(LANG_QUERY)])
    langs: dict[str, str] = {}
    for b in load_raw("details/languages"):
        code = val(b, "code")
        if code and code != "en" and "-" not in code:
            langs.setdefault(qid(b, "c"), code)
    country = current_country(load_raw("details/country"))
    pairs = sorted(f'(wd:{i} "{langs[c]}")' for i, (c, _) in country.items() if c in langs)
    run_batched("details/local_labels", LOCAL_TEMPLATE, pairs)


def fetch() -> None:
    members = fetch_classes()
    cities = fetch_capitals()
    items = set().union(*members.values()) | cities
    items.discard(None)
    print(f"{len(items)} distinct items")
    fetch_details(items)
    fetch_local_labels()
    write_fragment()


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_fragment() -> None:
    """One sources entry per raw file (the SPARQL text is stored inside each file)."""
    import yaml

    entries = []
    for path in sorted(RAW_DIR.rglob("*.json.gz")):
        rel = path.relative_to(RAW)
        stem = str(path.relative_to(RAW_DIR)).removesuffix(".json.gz")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            retrieved = json.load(fh)["retrieved"][:10]
        entries.append(
            {
                "id": "wikidata_facilities_" + re.sub(r"\W", "_", stem),
                "url": ENDPOINT,
                "path": str(rel),
                "licence": "CC0 1.0 (Wikidata)",
                "use": f"Wikidata SPARQL results ({stem}); queries stored in the file",
                "role": "features",
                "fetch": "nucprob.sources.wikidata_facilities",
                "retrieved": retrieved,
                "sha256": sha256(path),
            }
        )
    FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Wikidata facilities (nucprob/sources/wikidata_facilities.py). Every file holds the\n"
        "# SPARQL queries sent to the endpoint and their JSON results; rebuilt by fetch().\n"
    )
    FRAGMENT.write_text(
        header + yaml.safe_dump(entries, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- build


def year_of(t: str | None) -> int | None:
    """Year of a Wikidata time literal ('1956-03-01T00:00:00Z', '-0500-...')."""
    if not t:
        return None
    m = re.match(r"^([+-]?)(\d+)-", t)
    if not m:
        return None
    y = int(m.group(2))
    return -y if m.group(1) == "-" else y


def parse_point(wkt: str | None) -> tuple[float, float] | tuple[None, None]:
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", wkt or "")
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def current_country(rows: list[dict]) -> dict[str, tuple[str, str]]:
    """Each item's present country: a preferred statement, else one with no end date."""
    best: dict[str, tuple[int, str, str]] = {}
    for b in rows:
        i, c = qid(b, "i"), qid(b, "c")
        if not c:
            continue
        score = ("Preferred" in val(b, "rank")) * 2 + (val(b, "end") is None)
        if i not in best or score > best[i][0]:
            best[i] = (score, c, val(b, "cl") or c)
    return {i: (c, label) for i, (_, c, label) in best.items()}


def country_history(rows: list[dict]) -> dict[str, str]:
    """JSON list of [qid, label, start_year, end_year] per item, oldest first."""
    hist: dict[str, set] = {}
    for b in rows:
        c = qid(b, "c")
        if c:
            hist.setdefault(qid(b, "i"), set()).add(
                (c, val(b, "cl") or c, year_of(val(b, "start")), year_of(val(b, "end")))
            )
    return {
        i: json.dumps(sorted(h, key=lambda r: (r[2] is not None, r[2] or 0)), ensure_ascii=False)
        for i, h in hist.items()
    }


def fuel_of(text: str) -> str | None:
    text = text.lower()
    for fuel, words in FUEL_WORDS:
        if any(w in text for w in words):
            return fuel
    return None


def item_table() -> pd.DataFrame:
    """One row per item: labels, coordinates, dates, country, capacity, fuel, product."""
    items: dict[str, dict] = {}
    for b in load_raw("details/labels"):
        r = items.setdefault(qid(b, "i"), {"qid": qid(b, "i")})
        r.setdefault("label_en", val(b, "en") or val(b, "mul"))
        for key in ("native", "official"):
            if val(b, key) and not r.get("label_orig"):
                r["label_orig"] = val(b, key)
                r["label_orig_lang"] = b[key].get("xml:lang")
        if "lat" not in r:
            r["lat"], r["lon"] = parse_point(val(b, "coord"))
    for b in load_raw("details/local_labels"):
        r = items.get(qid(b, "i"))
        if r is not None and not r.get("label_orig"):
            r["label_orig"], r["label_orig_lang"] = val(b, "l"), val(b, "lang")

    dates: dict[tuple[str, str], tuple[int, int]] = {}
    for b in load_raw("details/dates"):
        key, y, prec = (qid(b, "i"), val(b, "prop")), year_of(val(b, "t")), int(val(b, "prec"))
        if y is not None and (key not in dates or y < dates[key][0]):
            dates[key] = (y, prec)
    for (i, prop), (y, prec) in dates.items():
        if i in items:
            items[i][f"{prop}_year"], items[i][f"{prop}_precision"] = y, prec

    rows = load_raw("details/country")
    for i, (c, label) in current_country(rows).items():
        if i in items:
            items[i]["country_qid"], items[i]["country"] = c, label
    for i, h in country_history(rows).items():
        if i in items:
            items[i]["country_history"] = h

    attrs: dict[str, dict[str, set]] = {}
    for b in load_raw("details/attributes"):
        a = attrs.setdefault(qid(b, "i"), {})
        if val(b, "prop") == "P2109":
            a.setdefault("capacity", set()).add(float(val(b, "amount")))
        else:
            a.setdefault(val(b, "prop"), set()).add(val(b, "vl") or qid(b, "v") or "")
    for i, a in attrs.items():
        if i not in items:
            continue
        r = items[i]
        if a.get("capacity"):
            r["capacity_mw"] = max(a["capacity"]) / 1e6  # normalised to watts
        r["types"] = "; ".join(sorted(a.get("P31", ())))
        r["powered_by"] = "; ".join(sorted(a.get("P516", ()))) or None
        r["product"] = "; ".join(sorted(a.get("P1056", ()))) or None
    t = pd.DataFrame(list(items.values()))
    for p in DATE_PROPS:
        for suffix in ("_year", "_precision"):
            if p + suffix not in t:
                t[p + suffix] = pd.NA
    return t


def class_rows() -> pd.DataFrame:
    rows = []
    for spec in CLASSES:
        subs = {qid(b, "s"): val(b, "sl") for b in load_raw(f"classes/{spec.name}")}
        for b in load_raw(f"members/{spec.name}"):
            s = qid(b, "s")
            rows.append(
                {
                    "qid": qid(b, "i"),
                    "class": spec.name,
                    "family": spec.family,
                    "subclass_qid": s,
                    "subclass": subs.get(s) or s,
                }
            )
    df = pd.DataFrame(rows)
    # an item typed with two subclasses of one class keeps one row, subclass names joined
    return df.groupby(["qid", "class", "family"], as_index=False).agg(
        {
            "subclass_qid": lambda s: "; ".join(sorted(set(s))),
            "subclass": lambda s: "; ".join(sorted(set(s))),
        }
    )


def capital_rows(city_inception: dict[str, int]) -> pd.DataFrame:
    polities = {}
    for b in load_raw("capitals/polity_details"):
        p = qid(b, "pol")
        r = polities.setdefault(
            p, {"label": val(b, "pl") or p, "inc": None, "dis": None, "country": None}
        )
        for key in ("inc", "dis"):
            y = year_of(val(b, key))
            if y is not None and (r[key] is None or y < r[key]):
                r[key] = y
        r["country"] = r["country"] or qid(b, "country")
    level: dict[str, str] = {}
    for b in load_raw("capitals/polities"):
        p, root = qid(b, "pol") or qid(b, "p"), qid(b, "root")
        if root in FIRST_LEVEL_ROOTS:
            level[p] = "capital_first_level"
        else:
            level.setdefault(p, "capital_national")
    rows = {}
    for source in ("p36", "p1376"):
        for b in load_raw(f"capitals/{source}"):
            p, city = qid(b, "pol"), qid(b, "city")
            if not city or not p:
                continue
            start, end = year_of(val(b, "start")), year_of(val(b, "end"))
            key = (city, p, start, end)
            if key in rows:
                continue
            pol = polities.get(p, {})
            rows[key] = {
                "qid": city,
                "class": level.get(p, "capital_national"),
                "family": "political",
                "polity_qid": p,
                "polity": pol.get("label", p),
                "capital_source": source.upper(),
                "start_year": start,
                "end_year": end,
                "polity_inc": pol.get("inc"),
                "polity_dis": pol.get("dis"),
            }
    return date_capitals(pd.DataFrame(list(rows.values())), city_inception)


def date_capitals(df: pd.DataFrame, city_inception: dict[str, int]) -> pd.DataFrame:
    """Fill missing stint dates. A statement with no qualifiers is dropped when the same city
    and polity have a qualified one. A missing end falls back on the polity's dissolution. A
    missing start falls back on the polity's inception (or the city's, if later) only when the
    polity has a single capital in Wikidata; otherwise the stint stays undated, since an
    unqualified statement is usually the present capital (Islamabad, not Karachi, for
    Pakistan in 1947)."""
    bare = df["start_year"].isna() & df["end_year"].isna()
    qualified = set(map(tuple, df.loc[~bare, ["qid", "polity_qid"]].to_numpy()))
    keys = list(zip(df["qid"], df["polity_qid"], strict=True))
    df = df[~(bare & pd.Series([k in qualified for k in keys], index=df.index))].copy()
    n_cities = df.groupby("polity_qid")["qid"].nunique()
    df["start_source"] = df["start_year"].notna().map({True: "P580", False: None})
    df["end_source"] = df["end_year"].notna().map({True: "P582", False: None})
    fill = df["start_year"].isna() & df["polity_qid"].map(n_cities).eq(1) & df["polity_inc"].notna()
    city_inc = df["qid"].map(city_inception)
    df.loc[fill, "start_year"] = pd.concat(
        [df.loc[fill, "polity_inc"], city_inc[fill]], axis=1
    ).max(axis=1)
    df.loc[fill, "start_source"] = "polity_inception"
    fill = df["end_year"].isna() & df["polity_dis"].notna()
    df.loc[fill, "end_year"] = df.loc[fill, "polity_dis"]
    df.loc[fill, "end_source"] = "polity_dissolution"
    return df.drop(columns=["polity_inc", "polity_dis"]).drop_duplicates(
        ["qid", "polity_qid", "start_year", "end_year"]
    )


def build() -> pd.DataFrame:
    items = item_table()
    facilities = class_rows().merge(items, on="qid", how="left")
    opening = facilities["P729_year"]
    facilities["start_year"] = opening.fillna(facilities["P571_year"])
    facilities["start_source"] = (
        opening.notna().map({True: "P729", False: "P571"}).where(facilities["start_year"].notna())
    )
    facilities["start_precision"] = facilities["P729_precision"].where(
        opening.notna(), facilities["P571_precision"]
    )
    ends = facilities[["P576_year", "P730_year", "P3999_year"]]
    facilities["end_year"] = ends.min(axis=1)
    facilities["end_source"] = (
        ends.astype(float)
        .fillna(float("inf"))
        .idxmin(axis=1)
        .str.removesuffix("_year")
        .where(facilities["end_year"].notna())
    )
    inception = items.set_index("qid")["P571_year"].dropna().astype(int).to_dict()
    capitals = capital_rows(inception).merge(items, on="qid", how="left")
    capitals["subclass"] = "capital city"
    df = pd.concat([facilities, capitals], ignore_index=True)
    is_power = df["class"].isin(["power_station", "nuclear_power_plant", "hydroelectric"])
    text = (
        df["subclass"].fillna("") + " " + df["powered_by"].fillna("") + " " + df["types"].fillna("")
    )
    df["fuel"] = text.map(fuel_of).where(is_power)
    df.loc[df["class"] == "nuclear_power_plant", "fuel"] = "nuclear"
    df.loc[df["class"] == "hydroelectric", "fuel"] = "hydro"
    df["undated"] = df["start_year"].isna()
    df["wikidata_url"] = "https://www.wikidata.org/wiki/" + df["qid"]
    for col in ("start_year", "end_year", "start_precision", *[f"{p}_year" for p in DATE_PROPS]):
        df[col] = df[col].astype("Int64")
    cols = [
        "qid",
        "class",
        "family",
        "subclass",
        "subclass_qid",
        "label_en",
        "label_orig",
        "label_orig_lang",
        "country_qid",
        "country",
        "country_history",
        "lat",
        "lon",
        "start_year",
        "start_source",
        "start_precision",
        "end_year",
        "end_source",
        "undated",
        *[f"{p}_year" for p in DATE_PROPS],
        "capacity_mw",
        "fuel",
        "powered_by",
        "product",
        "polity_qid",
        "polity",
        "capital_source",
        "types",
        "wikidata_url",
    ]
    df = df[cols].dropna(subset=["lat", "lon"]).sort_values(["class", "qid"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"{OUT}: {len(df)} rows, {df['qid'].nunique()} items")
    return df


# --------------------------------------------------------------------------- use


def load() -> pd.DataFrame:
    return pd.read_parquet(OUT)


def active(
    year: int, classes=None, include_undated: bool = True, df: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Rows open in `year`: start_year <= year and (no end or end_year > year). Undated rows
    (no start year) are kept, with `undated` True, unless include_undated is False; their end
    date still applies. Adds `country_asof`, the item's country in that year where its P17
    history has dates, else its present country."""
    df = load() if df is None else df
    if classes is not None:
        df = df[df["class"].isin([classes] if isinstance(classes, str) else list(classes))]
    started = df["start_year"].le(year).fillna(False)
    if include_undated:
        started |= df["start_year"].isna()
    open_ = df["end_year"].isna() | df["end_year"].gt(year).fillna(False)
    out = df[started & open_].copy()
    out["country_asof"] = [
        country_asof(h, c, year)
        for h, c in zip(out["country_history"], out["country"], strict=True)
    ]
    return out


def country_asof(history: str | None, present: str | None, year: int) -> str | None:
    if not isinstance(history, str):
        return present
    for _, label, start, end in json.loads(history):
        if start is not None and start <= year and (end is None or end > year):
            return label
    return present


def card_tables(df: pd.DataFrame | None = None) -> str:
    """Markdown tables for the card: rows by class and start decade, share undated, and rows
    active in selected years."""
    df = load() if df is None else df
    bins = [-10_000, 1800, 1900, 1920, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 3000]
    names = [
        "<1800",
        "1800s",
        "1900-19",
        "1920-39",
        "1940s",
        "1950s",
        "1960s",
        "1970s",
        "1980s",
        "1990s",
        "2000s",
        "2010+",
    ]
    period = pd.cut(df["start_year"].astype(float), bins, right=False, labels=names)
    t = pd.crosstab(df["class"], period.cat.add_categories("undated").fillna("undated"))
    t["rows"] = t.sum(axis=1)
    t["% undated"] = (100 * t["undated"] / t["rows"]).round(0).astype(int)
    t["with end"] = df.groupby("class")["end_year"].count()
    years = (1945, 1956, 1962, 1985, 2000)
    for y in years:
        dated = active(y, df=df, include_undated=False)
        t[f"open {y}"] = dated.groupby("class").size()
    t = t.fillna(0).astype(int)
    fam = df.drop_duplicates("class").set_index("class")["family"]
    t = t.loc[sorted(t.index, key=lambda c: (fam[c], c))]
    total = t.sum()
    total["% undated"] = round(100 * total["undated"] / total["rows"])
    t.loc["**all**"] = total
    return markdown(t)


def markdown(t: pd.DataFrame) -> str:
    head = "| class | " + " | ".join(map(str, t.columns)) + " |"
    rule = "|---|" + "---:|" * len(t.columns)
    body = [
        "| " + " | ".join([str(i), *map(str, r)]) + " |"
        for i, r in zip(t.index, t.values, strict=True)
    ]
    return "\n".join([head, rule, *body])


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    step = args[0] if args else "all"
    if step in ("fetch", "all"):
        fetch()
    if step in ("build", "all"):
        build()
    if step == "card":
        print(card_tables())
    if step == "fragment":
        write_fragment()
    return 0


if __name__ == "__main__":
    sys.exit(main())
