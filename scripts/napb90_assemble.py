"""Assemble the NAPB-90 county table of direct-effects risk.

    python scripts/napb90_assemble.py

Reads the two transcriptions (data/interim/napb90/pass1, pass2) through napb90_compare. The
passes agree on every figure; they differ on two county names (pass 1 keeps the printed
misspellings "Schuykill" and "East Carrol", checked on the scan) and on the star of summary and
total rows (not used). The final reading is pass 1.

Writes data/curated/napb90/:
  counties.csv      one row per county (or independent city, parish, borough, census area,
                    territory): its band, the printed 1985 population and land area, its FIPS
                    code and the Census Bureau's 1985 estimate
  state_totals.csv  the printed TOTAL STATE rows and page headers
  checks.csv        column sums that differ from the printed totals, and counties whose printed
                    population is a third or more off the census estimate
  REPORT.md         counts
and data/curated/labels/cd_1987_napb90_counties.csv, the county table for the label inventory.
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import napb90_compare as cmp

from nucprob.sources import census_us

OUT = Path("data/curated/napb90")
BAND_NAMES = {
    "vh": "very high (>=10 psi)",
    "h": "high (5-10 psi)",
    "m": "medium (2-5 psi)",
    "l": "low (0.5-2 psi)",
    "no": "no (<0.5 psi)",
}
SOURCE = (
    "FEMA, Nuclear Attack Planning Base - 1990 (NAPB-90), Final Project Report, April 1987, "
    "Annex A Part 2, Highest Direct Effects Risk by County (FOIA release 2005)"
)


def band_of(row: dict) -> tuple[str, int | None, int | None]:
    filled = [b for b in cmp.BANDS if row[f"{b}_pop"] or row[f"{b}_area"]]
    if len(filled) != 1:
        return ("?" if filled else ""), None, None
    b = filled[0]
    band = "no" if b == "l" and row["star"] == "1" else b
    return band, cmp.num(row[f"{b}_pop"]), cmp.num(row[f"{b}_area"])


def main() -> None:
    final, disputes = cmp.compare(cmp.load(cmp.ROOT / "pass1"), cmp.load(cmp.ROOT / "pass2"))
    checks = cmp.checks(final)
    est = census_us.estimates()
    states = {r["name"].upper(): r["fips"][:2] for _, r in est[est["level"] == "state"].iterrows()}
    pools: dict = {}
    for _, r in est[est["level"] == "county"].iterrows():
        pools.setdefault(r["fips"][:2], {})[cmp.norm_county(r["name"])] = r
    by_state: dict[str, list] = {}
    pages: dict[str, list] = {}
    totals, headers = [], {}
    for page, p in sorted(final.items()):
        if p["type"] != "state" and not p["title"].upper().startswith(("TERRITORY", "U.S.")):
            continue
        st = cmp.state_of(p["title"])
        if p["header"] and st not in headers:
            headers[st] = p["header"]
        for r in p["rows"]:
            if r["kind"] == "county":
                by_state.setdefault(st, []).append(r)
                pages.setdefault(st, []).append((page, p["printed"]))
            elif r["kind"] == "total":
                totals.append(
                    {"state": st, "page": page, "printed_page": p["printed"]}
                    | {f: r[f] for f in cmp.FIELDS[:-1]}
                )
    rows = []
    for st, county_rows in by_state.items():
        matches = cmp.match_counties(st, county_rows, states, pools)
        for r, c, (page, printed) in zip(county_rows, matches, pages[st], strict=True):
            band, pop, area = band_of(r)
            ref = c["pop_1985"] if c is not None else None
            rows.append(
                {
                    "state": st.title(),
                    "county_printed": r["name"],
                    "fips": c["fips"] if c is not None else "",
                    "census_name": c["name"] if c is not None else "",
                    "band": BAND_NAMES.get(band, band),
                    "band_rank": {"vh": 4, "h": 3, "m": 2, "l": 1, "no": 0}.get(band, ""),
                    "pop_1985_napb": pop if pop is not None else "",
                    "area_sqmi": area if area is not None else "",
                    "census_pop_1985": int(ref) if ref == ref and ref is not None else "",
                    "pop_ratio": round(pop / ref, 3) if pop and ref == ref and ref else "",
                    "page": page,
                    "printed_page": printed,
                }
            )
    OUT.mkdir(parents=True, exist_ok=True)
    cmp.write(OUT / "counties.csv", rows)
    for t in totals:
        h = headers.get(t["state"])
        t["header_pop"], t["header_area"] = (h if h else ["", ""])[:2]
    cmp.write(OUT / "state_totals.csv", totals)
    cmp.write(OUT / "checks.csv", checks)
    write_label(rows)
    report(rows, checks, disputes, final)


def write_label(rows: list[dict]) -> None:
    """The county table in the label folder, one row per county, own columns (the shared
    schema is for lists of named targets; a county's band is a modelled exposure, not a
    designation)."""
    out = [
        {
            "plan_id": "cd_1987_napb90_counties",
            "planner": "FEMA (defender), modelled on Soviet doctrine",
            "target_country": "USA",
            "plan_year": 1987,
            "provenance": "defender",
        }
        | {
            k: r[k]
            for k in (
                "state",
                "county_printed",
                "fips",
                "band",
                "band_rank",
                "pop_1985_napb",
                "area_sqmi",
                "page",
                "printed_page",
            )
        }
        | {"source_doc": SOURCE}
        for r in rows
    ]
    cmp.write(Path("data/curated/labels/cd_1987_napb90_counties.csv"), out)


def report(rows, checks, disputes, final) -> None:
    bands = Counter(r["band"] for r in rows)
    matched = sum(bool(r["fips"]) for r in rows)
    pop_bands: Counter = Counter()
    for r in rows:
        pop_bands[r["band"]] += r["pop_1985_napb"] or 0
    total_pop = sum(pop_bands.values())
    lines = [
        "# NAPB-90 county table: report",
        "",
        "Written by `scripts/napb90_assemble.py`.",
        "",
        f"- Pages: {len(final)} (PDF pp. 135-292); county rows: {len(rows)}; matched to a "
        f"FIPS code: {matched}",
        f"- Cells where the two passes differ: {len(disputes)} (none of them a figure)",
        "",
        "| Highest risk band | Counties | 1985 population (NAPB) | Share |",
        "|---|---|---|---|",
        *(
            f"| {b} | {bands[b]} | {pop_bands[b]:,} | {pop_bands[b] / total_pop:.1%} |"
            for b in BAND_NAMES.values()
        ),
        "",
        "## Checks",
        "",
        *(f"- {k}: {v}" for k, v in Counter(c["check"] for c in checks).items()),
        "",
        "Column sums that differ from a printed total, and the counties far from the census "
        "estimate, were read again by both passes on enlarged images: the figures are printed as "
        "transcribed, so they are slips in FEMA's tables (`checks.csv`).",
    ]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
