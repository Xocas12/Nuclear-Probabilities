"""Compare the two transcriptions of the NAPB-90 county tables, and check them.

    python scripts/napb90_compare.py

Inputs: data/interim/napb90/pass1/ and pass2/ (one TSV per page, see INSTRUCTIONS.md). Rows are
aligned page by page on (kind, name, occurrence); split lines on their order on the page. A cell
the passes read differently, or a row only one pass has, is a dispute
(data/interim/napb90/compare/disputes.csv); cells they read the same are agreed.

The checks run on the agreed reading, filling disputed cells from pass 1 so that sums can be
formed (compare/checks.csv):
- column sums of every state's county rows against its total row, and the two split lines
  against the LOW/NO total;
- each county's population (the one band it is printed in) against the Census Bureau's
  estimate for 1985 (nucprob.sources.census_us), matched by state and county name. NAPB-90
  prints an "Estimated 1985 Population", so a county far from the census estimate is either a
  misread or a different estimate; both are listed.
"""

import csv
import difflib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from nucprob.sources import census_us

ROOT = Path("data/interim/napb90")
FIELDS = ["vh_pop", "vh_area", "h_pop", "h_area", "m_pop", "m_area", "l_pop", "l_area", "star"]
BANDS = ["vh", "h", "m", "l"]


def load(pass_dir: Path) -> dict[str, dict]:
    pages = {}
    for tsv in sorted(pass_dir.glob("A*.tsv")):
        page = {"type": "", "title": "", "printed": "", "header": None, "rows": []}
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            f = raw.split("\t")
            if f[0] == "#page":
                page["type"], page["title"], page["printed"] = ([*f[1:], "", ""])[:3]
            elif f[0] == "#header":
                page["header"] = f[1:3]
            else:
                f = ([*f, *[""] * 11])[:11]
                page["rows"].append(
                    {"kind": f[0].strip(), "name": f[1].strip()}
                    | {k: v.strip().replace(" ", "") for k, v in zip(FIELDS, f[2:], strict=True)}
                )
        pages[tsv.stem] = page
    return pages


def keyed(rows: list[dict]) -> dict[tuple, dict]:
    seen: Counter = Counter()
    out = {}
    for r in rows:
        k = (r["kind"], r["name"].lower())
        seen[k] += 1
        out[(*k, seen[k])] = r
    return out


def num(v: str) -> int | None:
    return int(v) if v and v.isdigit() else None


def state_of(title: str) -> str:
    """The state of a state page: "STATE OF ALABAMA (Continued)" and "STATE OF NEBRASKA--DIRECT
    EFFECTS RISK" both give ALABAMA / NEBRASKA."""
    t = re.sub(r"\s+", " ", title.upper())
    t = re.sub(r"^STATE OF\W*", "", t)
    t = re.split(r"\s*(?:--|\(CONTINUED\)|DIRECTS? EF+ECTS)", t)[0]
    return t.strip(" -")


def compare(a: dict, b: dict) -> tuple[dict, list[dict]]:
    final, disputes = {}, []
    for page in sorted(set(a) | set(b)):
        pa, pb = a.get(page), b.get(page)
        if pa is None or pb is None:
            disputes.append(
                {"page": page, "row": "", "field": "page", "a": bool(pa), "b": bool(pb)}
            )
            final[page] = pa or pb
            continue
        ka, kb = keyed(pa["rows"]), keyed(pb["rows"])
        rows = []
        for k in list(ka) + [k for k in kb if k not in ka]:
            ra, rb = ka.get(k), kb.get(k)
            if ra is None or rb is None:
                disputes.append(
                    {
                        "page": page,
                        "row": f"{k[0]} {k[1]} #{k[2]}",
                        "field": "row",
                        "a": "present" if ra else "absent",
                        "b": "present" if rb else "absent",
                    }
                )
                if (
                    ra is not None
                ):  # the final reading is pass 1's; pass 2's extra rows stay disputes
                    rows.append(ra)
                continue
            for f in FIELDS:
                va, vb = ra[f], rb[f]
                if f == "star":
                    va, vb = va or "0", vb or "0"
                if va != vb:
                    disputes.append(
                        {
                            "page": page,
                            "row": f"{k[0]} {ra['name']} #{k[2]}",
                            "field": f,
                            "a": ra[f],
                            "b": rb[f],
                        }
                    )
            rows.append(ra)
        final[page] = pa | {"rows": rows}
        if pa["header"] != pb["header"]:
            disputes.append(
                {
                    "page": page,
                    "row": "#header",
                    "field": "header",
                    "a": pa["header"],
                    "b": pb["header"],
                }
            )
    return final, disputes


def norm_county(name: str) -> str:
    n = name.lower().replace("st.", "saint").replace("ste.", "sainte")
    n = re.sub(r"^st\b", "saint", n).replace("&", "and")
    n = re.sub(r"\b(co|county|par|parish|bor|borough|c\.a|census area)\b\.?", "", n)
    return re.sub(r"[^a-z]", "", n)


# Printed names that differ from the Census Bureau's beyond what the fuzzy match allows.
# Alaska's census areas of the 1980s were later split and renamed (the Census Bureau's
# estimates use the 1990 areas): Kobuk is Northwest Arctic (renamed 1986); the Aleutian Islands
# area was split into Aleutians East and West in 1987, so it has no single counterpart.
ALIASES = {
    ("DISTRICT OF COLUMBIA", "dist. of columbia"): "11001",
    ("MAINE", "knos"): "23013",
    ("ALASKA", "kobuk"): "02188",
    ("ALASKA", "prince of wales"): "02201",
    ("ALASKA", "se fairbanks"): "02240",
}
STATE_NAMES = {"DISTRICT OF COLUMBIA": "D.C."}


def match_counties(st: str, rows: list[dict], states: dict, counties: dict) -> list:
    """The census row of each county row of a state, in order. An independent city (Virginia,
    Baltimore, St. Louis, Carson City) shares its name with a county: a row marked "(City)", or a
    second row of the same name, is matched to the city. Then a close fuzzy match (typos such
    as Osford, Schuykill)."""
    sf = states.get(STATE_NAMES.get(st, st))
    pool = counties.get(sf, {})
    by_fips = {c["fips"]: c for c in pool.values()}
    out, used = [], set()
    for r in rows:
        name = r["name"]
        key = norm_county(re.sub(r"\(city\)", "", name, flags=re.I))
        candidates = []
        if (st, name.lower()) in ALIASES:
            candidates.append(by_fips.get(ALIASES[(st, name.lower())]))
        county, city = pool.get(key), pool.get(key + "city")
        if "(city)" in name.lower() or (county is not None and county["fips"] in used):
            candidates += [city, county]
        else:
            candidates += [county, city]
        if not any(c is not None for c in candidates):
            close = difflib.get_close_matches(key, list(pool), n=1, cutoff=0.8)
            candidates.append(pool[close[0]] if close else None)
        c = next((c for c in candidates if c is not None), None)
        if c is not None:
            used.add(c["fips"])
        out.append(c)
    return out


def checks(final: dict) -> list[dict]:
    out = []
    # Column sums per state.
    by_state = defaultdict(list)
    totals = {}
    for page, p in final.items():
        if p["type"] != "state":
            continue
        st = state_of(p["title"])
        for r in p["rows"]:
            if r["kind"] == "county":
                by_state[st].append(r)
            elif r["kind"] == "total":
                totals[st] = (page, r, [x for x in p["rows"] if x["kind"] == "split"])
    for st, (page, tot, splits) in totals.items():
        for f in FIELDS[:-1]:
            s = sum(num(r[f]) or 0 for r in by_state[st])
            t = num(tot[f]) or 0
            if s != t:
                out.append(
                    {
                        "check": "column sum",
                        "state": st,
                        "page": page,
                        "field": f,
                        "sum": s,
                        "printed": t,
                        "diff": s - t,
                    }
                )
        if len(splits) == 2:
            for f in ("l_pop", "l_area"):
                s = sum(num(x[f]) or 0 for x in splits)
                t = num(tot[f]) or 0
                if s != t:
                    out.append(
                        {
                            "check": "split lines",
                            "state": st,
                            "page": page,
                            "field": f,
                            "sum": s,
                            "printed": t,
                            "diff": s - t,
                        }
                    )
    # Census 1985.
    est = census_us.estimates()
    states = {r["name"].upper(): r["fips"][:2] for _, r in est[est["level"] == "state"].iterrows()}
    counties = defaultdict(dict)
    for _, r in est[est["level"] == "county"].iterrows():
        counties[r["fips"][:2]][norm_county(r["name"])] = r
    for st, rows in by_state.items():
        for r, c in zip(rows, match_counties(st, rows, states, counties), strict=True):
            pop = sum(num(r[f"{b}_pop"]) or 0 for b in BANDS)
            if c is None:
                out.append(
                    {
                        "check": "no census match",
                        "state": st,
                        "page": "",
                        "field": r["name"],
                        "sum": pop,
                        "printed": "",
                        "diff": "",
                    }
                )
                continue
            ref = c["pop_1985"]
            if ref == ref and ref and not 0.67 < pop / ref < 1.5:  # ref == ref: not NaN
                out.append(
                    {
                        "check": "census 1985 differs by a third or more",
                        "state": st,
                        "page": "",
                        "field": f"{r['name']} ({c['fips']})",
                        "sum": pop,
                        "printed": int(ref),
                        "diff": pop - int(ref),
                    }
                )
    return out


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["empty"])
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    a, b = load(ROOT / "pass1"), load(ROOT / "pass2")
    final, disputes = compare(a, b)
    write(ROOT / "compare" / "disputes.csv", disputes)
    chk = checks(final)
    write(ROOT / "compare" / "checks.csv", chk)
    n_cells = sum(len(p["rows"]) for p in final.values()) * len(FIELDS)
    print(
        f"pages: pass1 {len(a)}, pass2 {len(b)}; rows {sum(len(p['rows']) for p in final.values())}"
    )
    print(f"disputes: {len(disputes)} ({len(disputes) / n_cells:.2%} of cells)")
    print(Counter(c["check"] for c in chk))


if __name__ == "__main__":
    main()
