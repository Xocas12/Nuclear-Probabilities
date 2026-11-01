"""Compare the pilot reading of the SAC 1956 lists with the final reading.

    python scripts/sac1956_pilot.py

Before the two-pass pipeline, four pages were read once by hand (the "pilot"):
data/curated/labels/sac1956_pilot_urban.csv (Part I complex list, PDF pages 2, 166 and 305) and
sac1956_pilot_airfields.csv (the Part I airfield list excerpt, section4.pdf page 5). Both are
Part I pages, so the pilot is a third read of the Part I scan; it says nothing about the Part II
airfield scan.

Each pilot row is set against the final line in the same position on its page (pages C002,
C166, C305 in data/curated/sac1956/lines.csv; F005 in excerpts/lines.csv). Every printed field
the pilot recorded (priority, reference, name, BE number, category, coordinates, letters) must
appear in the final text; a "?" in the pilot matches any character.

Writes data/curated/sac1956/pilot.csv (one row per pilot row). sac1956_excerpts.py quotes the
summary in excerpts/REPORT.md.
"""

import csv
import re
from pathlib import Path

LABELS = Path("data/curated/labels")
OUT = Path("data/curated/sac1956")
PILOT_PAGES = {
    "1st_city_list_complete.pdf p.2": "C002",
    "1st_city_list_complete.pdf p.166": "C166",
    "1st_city_list_complete.pdf p.305": "C305",
}
AIRFIELD_PAGE = "F005"
# The printed fields of each kind of pilot row, in the order they are printed.
FIELDS = {
    "complex_header": ("priority", "ref_no", "complex_or_city", "coord_raw"),
    "sub_complex_header": ("sub_complex", "coord_raw"),
    "site_with_dgz_code": ("sub_complex", "coord_raw", "dgz_letter"),
    "dgz": ("coord_raw", "dgz_letter"),
    "installation": ("category_code", "be_number"),
    "airfield": ("priority", "ref_no", "complex_or_city", "be_number", "coord_raw", "letter_code"),
}


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def field_pattern(value: str) -> re.Pattern:
    """A printed field as a regex: '?' matches any character, and the field must not run on
    into a neighbouring letter or digit."""
    body = "".join("." if ch == "?" else re.escape(ch) for ch in value)
    return re.compile(rf"(?<![A-Z0-9]){body}(?![A-Z0-9])")


def compare_row(pilot: dict, kind: str, final_text: str) -> dict:
    """Which of the pilot's printed fields appear in the final text of the line."""
    # the pilot wrote aim points as "5340- 5339E"; the final reading as "5340-5339E"
    text = re.sub(r"-\s+", "-", re.sub(r"\s+", " ", final_text))
    fields, differ, chars = [], [], 0
    for name in FIELDS[kind]:
        value = re.sub(r"\s+", "", pilot.get(name, "")) if name == "coord_raw" else pilot[name]
        value = value.strip()
        if not value:
            continue
        fields.append(value)
        chars += sum(ch != "?" for ch in value)
        if not field_pattern(value).search(text):
            differ.append(value)
    return {"fields": fields, "differ": differ, "chars": chars}


def compare(urban: list[dict], airfields: list[dict], lines: list[dict]) -> list[dict]:
    """One row per pilot row: the final line it is set against, and the pilot fields that do
    not appear in it."""
    by_page: dict[str, list[dict]] = {}
    for line in lines:
        if line["kind"] == "data":
            by_page.setdefault(line["page"], []).append(line)
    groups = [(PILOT_PAGES[r["page"]], r, r["row_type"]) for r in urban if r["page"] in PILOT_PAGES]
    groups += [(AIRFIELD_PAGE, r, "airfield") for r in airfields]
    out = []
    for page, pilot, kind in groups:
        k = int(pilot["row"]) - 1
        final = by_page.get(page, [])
        line = final[k] if k < len(final) else None
        result = compare_row(pilot, kind, line["text"] if line else "")
        out.append(
            {
                "pilot_file": "airfields" if kind == "airfield" else "urban",
                "page": page,
                "pilot_row": pilot["row"],
                "row_type": kind,
                "legibility": pilot["legibility"],
                "final_id": line["id"] if line else "",
                "final_text": line["text"] if line else "",
                "pilot_fields": " | ".join(result["fields"]),
                "pilot_characters": result["chars"],
                "differing_fields": " | ".join(result["differ"]),
                "agrees": not result["differ"],
            }
        )
    return out


def summary(rows: list[dict]) -> list[str]:
    """Report lines (Markdown) for the comparison."""
    files = {f: sum(r["pilot_file"] == f for r in rows) for f in ("urban", "airfields")}
    differ = [r for r in rows if not r["agrees"]]
    out = [
        f"- Pilot rows: {len(rows)} ({files['urban']} from the complex list, pages C002, C166 and "
        f"C305; {files['airfields']} from the Part I airfield list, page {AIRFIELD_PAGE}), "
        f"each set against the final line in the same place; "
        f"{sum(r['pilot_characters'] for r in rows)} characters the pilot could read.",
        f"- Rows where every field the pilot read appears in the final reading: "
        f"{len(rows) - len(differ)} of {len(rows)}.",
    ]
    if differ:
        out.append(
            "- Rows that differ: "
            + "; ".join(
                f"{r['final_id'] or r['page'] + ' row ' + r['pilot_row']} (pilot "
                f"{r['differing_fields']}, {r['legibility']}; final `{r['final_text']}`)"
                for r in differ
            )
        )
    out.append(
        "- All four pilot pages are Part I pages, so the pilot is a third read of the Part I "
        "scan; it says nothing about the Part II airfield scan."
    )
    return out


def run(
    labels: Path = LABELS, out: Path = OUT, lines: list[dict] | None = None
) -> tuple[list[dict], list[str]]:
    urban = read(labels / "sac1956_pilot_urban.csv")
    airfields = read(labels / "sac1956_pilot_airfields.csv")
    if lines is None:
        lines = read(out / "lines.csv") + read(out / "excerpts" / "lines.csv")
    rows = compare(urban, airfields, lines)
    with open(out / "pilot.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows, summary(rows)


if __name__ == "__main__":
    print("\n".join(run()[1]))
