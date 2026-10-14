"""The cross-document check of the SAC 1956 airfields and the pilot comparison (issue #5)."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import sac1956_assemble as asm
import sac1956_pilot as pilot

REPO = Path(__file__).parents[1]
CROSSDOC = REPO / "data/interim/sac1956_excerpts/crossdoc"
CURATED = REPO / "data/curated/sac1956"


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verdicts() -> dict[str, str]:
    rows = (CROSSDOC / "decisions.tsv").read_text(encoding="utf-8").splitlines()
    return {r.split("\t")[1].split()[2]: r.split("\t")[5] for r in rows if r.strip()}


def test_low_confidence_part2_glyphs_are_not_printing_differences():
    v = verdicts()
    for name in ("AKTYUBINSK", "BREST", "BRIYENI", "BUZAU,"):
        assert v[name] in ("unresolved", "part2 misread"), name
    assert v["BRODY"] == "part1 misread"
    assert v["ONEGA."] == "punctuation only"
    assert sum(x == "printings differ" for x in v.values()) == 6


def test_brody_part1_longitude_corrected():
    row = next(r for r in read(CURATED / "excerpts/part1_airfields.csv") if r["id"] == "F005-L24")
    assert row["lon"] == "25.1833" and "5005-02511" in row["text"]


def test_label_rows_carry_cross_document_and_low_confidence_notes():
    notes = asm.crossdoc_notes(CROSSDOC)
    assert len(notes) == 19
    labels = {
        r["source_page"].split("(")[1].rstrip(")"): r
        for r in read(REPO / "data/curated/labels/us_1956_sac_airfields.csv")
    }
    for line_id in notes:
        assert "cross-document check" in labels[line_id]["notes"], line_id
    # the known Part II slips and the low-confidence Part II readings, named in the issue
    for line_id, word in (
        ("A002-L19", "typing slip"),  # AMDERMA
        ("A004-L29", "typing slip"),  # BIROBIDZHAN
        ("A005-L17", "typing slip"),  # BRATISLAVA/IVANKA
        ("A002-L07", "low confidence"),  # AKTYURINSK
        ("A005-L19", "low confidence"),  # BREST
        ("A005-L22", "low confidence"),  # BRIYENI
        ("A006-L09", "low confidence"),  # BUZAU
    ):
        assert word in labels[line_id]["notes"], line_id
    assert "6945-06140" in labels["A002-L19"]["notes"]


def test_reading_note_flags_low_confidence_adjudication():
    final = {"A1": {"source": "adjudicated", "confidence": "low", "note": "3 or 5"}}
    assert "low confidence" in asm.reading_note("A1", final, {})
    final["A1"]["confidence"] = "high"
    assert asm.reading_note("A1", final, {}) == ""
    assert asm.reading_note("A1", final, {"A1": "cross-document check: x"}).endswith("x")


def test_pilot_comparison_detects_a_digit_and_skips_unreadable_ones():
    lines = [
        {"id": "F005-L01", "page": "F005", "kind": "header", "text": "TOP SECRET"},
        {
            "id": "F005-L02",
            "page": "F005",
            "kind": "data",
            "text": "474 4131 BRODY 0233-8006 5005-02911 S",
        },
        {"id": "C002-L01", "page": "C002", "kind": "data", "text": "366 0169-0314"},
        {"id": "C002-L02", "page": "C002", "kind": "data", "text": "5340-5339E B"},
    ]
    airfield = {
        "row": "1", "priority": "474", "ref_no": "4131", "complex_or_city": "BRODY",
        "be_number": "0233-8006", "coord_raw": "5005-02511", "letter_code": "S", "legibility": "ok",
    }  # fmt: skip
    urban = [
        {"page": "1st_city_list_complete.pdf p.2", "row": "1", "row_type": "installation",
         "category_code": "366", "be_number": "016?-0314", "legibility": "partial"},
        {"page": "1st_city_list_complete.pdf p.2", "row": "2", "row_type": "dgz",
         "coord_raw": "5340- 5339E", "dgz_letter": "B", "legibility": "ok"},
    ]  # fmt: skip
    rows = pilot.compare(urban, [airfield], lines)
    assert [r["agrees"] for r in rows] == [True, True, False]
    assert rows[2]["differing_fields"] == "5005-02511" and rows[2]["final_id"] == "F005-L02"


def test_pilot_matches_the_committed_final_reading():
    lines = read(CURATED / "lines.csv") + read(CURATED / "excerpts/lines.csv")
    urban = read(REPO / "data/curated/labels/sac1956_pilot_urban.csv")
    airfields = read(REPO / "data/curated/labels/sac1956_pilot_airfields.csv")
    rows = pilot.compare(urban, airfields, lines)
    assert len(rows) == 156
    assert [r["final_id"] for r in rows if not r["agrees"]] == []


def test_data_card_quotes_the_corrected_counts():
    card = (CURATED / "README.md").read_text(encoding="utf-8")
    assert "216" in card and "about 1 in 90" not in card
    assert "156 lines" in card and "152 lines" not in card
    assert "12 are real" not in card
