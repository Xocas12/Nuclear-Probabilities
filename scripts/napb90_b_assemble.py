"""Assemble the NAPB-90 county table of fallout risk (Annex B).

    python scripts/napb90_b_assemble.py

Reads the single transcription data/interim/napb90_b/pass1/ (one TSV per page, same format as
Annex A, see data/interim/napb90_b/INSTRUCTIONS.md) through napb90_compare. There is no second
pass: Annex B prints each county's whole 1985 population and area again, so the checks are
- the column sums of every state against its printed total (as for Annex A), and
- each county's printed population and area against the same county in Annex A
  (data/curated/napb90/counties.csv, matched by FIPS), which was read twice.

Writes data/curated/napb90/:
  fallout_counties.csv  one row per county: its fallout band, printed population and area, FIPS,
                        and its Annex A blast band
  fallout_checks.csv    failed checks
  FALLOUT_REPORT.md     counts
"""

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import napb90_compare as cmp

from nucprob.sources import census_us

ROOT = Path("data/interim/napb90_b")
OUT = Path("data/curated/napb90")
BAND_NAMES = {
    "vh": "very high (>15000 R)",
    "h": "high (6000-15000 R)",
    "m": "medium (3000-6000 R)",
    "l": "low (<3000 R)",
}
RANK = {"vh": 3, "h": 2, "m": 1, "l": 0}


def band_of(row: dict) -> tuple[str, int | None, int | None]:
    filled = [b for b in cmp.BANDS if row[f"{b}_pop"] not in ("", "---") or row[f"{b}_area"]]
    filled = [b for b in filled if row[f"{b}_area"] != "---"]
    if len(filled) != 1:
        return ("?" if filled else ""), None, None
    b = filled[0]
    return b, cmp.num(row[f"{b}_pop"]), cmp.num(row[f"{b}_area"])


def main() -> None:
    final = cmp.load(ROOT / "pass1", "B*.tsv")
    checks = [
        c for c in cmp.checks(final) if c["check"] != "census 1985 differs by a third or more"
    ]
    est = census_us.estimates()
    states = {r["name"].upper(): r["fips"][:2] for _, r in est[est["level"] == "state"].iterrows()}
    pools: dict = {}
    for _, r in est[est["level"] == "county"].iterrows():
        pools.setdefault(r["fips"][:2], {})[cmp.norm_county(r["name"])] = r
    with open(OUT / "counties.csv", encoding="utf-8") as fh:
        annex_a = {r["fips"]: r for r in csv.DictReader(fh) if r["fips"]}

    by_state: dict[str, list] = {}
    pages: dict[str, list] = {}
    for page, p in sorted(final.items()):
        if p["type"] != "state":
            continue
        st = cmp.state_of(p["title"])
        for r in p["rows"]:
            if r["kind"] == "county":
                by_state.setdefault(st, []).append(r)
                pages.setdefault(st, []).append((page, p["printed"]))
    rows = []
    for st, county_rows in by_state.items():
        matches = cmp.match_counties(st, county_rows, states, pools)
        for r, c, (page, printed) in zip(county_rows, matches, pages[st], strict=True):
            band, pop, area = band_of(r)
            fips = c["fips"] if c is not None else ""
            a = annex_a.get(fips, {})
            row = {
                "state": st.title(),
                "county_printed": r["name"],
                "fips": fips,
                "fallout_band": BAND_NAMES.get(band, band),
                "fallout_rank": RANK.get(band, ""),
                "pop_1985_napb": pop if pop is not None else "",
                "area_sqmi": area if area is not None else "",
                "blast_band": a.get("band", ""),
                "blast_rank": a.get("band_rank", ""),
                "page": page,
                "printed_page": printed,
            }
            rows.append(row)
            if band == "?" or band == "":
                checks.append(
                    {
                        "check": "no single band",
                        "state": st,
                        "page": page,
                        "field": r["name"],
                        "sum": "",
                        "printed": "",
                        "diff": "",
                    }
                )
            if not a:
                checks.append(
                    {
                        "check": "not in Annex A",
                        "state": st,
                        "page": page,
                        "field": r["name"],
                        "sum": pop,
                        "printed": "",
                        "diff": "",
                    }
                )
                continue
            for f, v in (("pop_1985_napb", pop), ("area_sqmi", area)):
                ref = cmp.num(a[f])
                if v != ref:
                    checks.append(
                        {
                            "check": f"Annex A {f}",
                            "state": st,
                            "page": page,
                            "field": f"{r['name']} ({fips})",
                            "sum": v,
                            "printed": ref,
                            "diff": (v - ref) if v is not None and ref is not None else "",
                        }
                    )
    seen = Counter(r["fips"] for r in rows if r["fips"])
    for f, n in seen.items():
        if n > 1:
            checks.append(
                {
                    "check": "FIPS twice",
                    "state": "",
                    "page": "",
                    "field": f,
                    "sum": n,
                    "printed": "",
                    "diff": "",
                }
            )
    missing = sorted(set(annex_a) - set(seen))
    for f in missing:
        checks.append(
            {
                "check": "Annex A county missing",
                "state": annex_a[f]["state"],
                "page": "",
                "field": f"{annex_a[f]['county_printed']} ({f})",
                "sum": "",
                "printed": "",
                "diff": "",
            }
        )
    cmp.write(OUT / "fallout_counties.csv", rows)
    cmp.write(OUT / "fallout_checks.csv", checks)
    report(rows, checks, final)


def report(rows, checks, final) -> None:
    pop = Counter()
    n = Counter()
    for r in rows:
        n[r["fallout_band"]] += 1
        pop[r["fallout_band"]] += r["pop_1985_napb"] or 0
    total = sum(pop.values())
    cross = Counter((r["blast_band"], r["fallout_band"]) for r in rows)
    lines = [
        "# NAPB-90 Annex B (fallout risk by county): report",
        "",
        f"Pages transcribed: {len(final)} ({sum(p['type'] == 'state' for p in final.values())}"
        f" state pages). County rows: {len(rows)}; with a FIPS match: "
        f"{sum(bool(r['fips']) for r in rows)}.",
        "",
        "| Fallout band | Counties | 1985 population (NAPB) | Share |",
        "|---|---|---|---|",
    ]
    for b in BAND_NAMES.values():
        lines.append(f"| {b} | {n[b]:,} | {pop[b] / 1e6:.1f} m | {pop[b] / total:.1%} |")
    lines += ["", "## Failed checks", "", "| Check | Count |", "|---|---|"]
    for k, v in Counter(c["check"] for c in checks).most_common():
        lines.append(f"| {k} | {v} |")
    lines += ["", "## Blast band (Annex A) by fallout band (counties)", ""]
    fb = list(BAND_NAMES.values())
    lines += ["| blast \\ fallout | " + " | ".join(fb) + " |", "|---" * (len(fb) + 1) + "|"]
    for bb in sorted({r["blast_band"] for r in rows}):
        lines.append(f"| {bb or '(none)'} | " + " | ".join(str(cross[(bb, f)]) for f in fb) + " |")
    (OUT / "FALLOUT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
