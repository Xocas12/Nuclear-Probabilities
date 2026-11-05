"""Checks for the in-build review of c39684a: what README, REPORT, the cards and the viewer say against the data."""

import re

import pandas as pd
import yaml

from nucprob.paths import CURATED, ROOT
from nucprob.probmap.run import load_scenarios
from nucprob.probmap.viewer import shift_label


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_readme_says_the_blind_places_were_set_apart_after_the_sealed_reading():
    readme = _flat(ROOT / "README.md")
    report = _flat(ROOT / "REPORT.md")
    for text in (readme, report):
        assert (
            "The blind places were set apart after the reading of all sealed places had been seen"
            in text
        )
        assert (
            "the sealed scores are of the fit made before the corrected West European site table"
            in text
        )
    assert "That subset was defined after the reading of all sealed places had been seen" in readme


def test_readme_describes_the_temporal_holdout_as_up_to_1956():
    readme = _flat(ROOT / "README.md")
    assert "fitting before 1956" not in readme
    assert "fitting on documents up to 1956 to score later ones" in readme


def test_readme_names_every_document_type_of_the_registry():
    plans = yaml.safe_load((CURATED / "labels" / "PLANS.yaml").read_text(encoding="utf-8"))
    plans = plans["plans"] if isinstance(plans, dict) else plans
    named = {
        "war_plan": "war plan",
        "target_selection": "target selection",
        "requirements_study": "requirements study",
        "policy_study": "policy study",
        "exercise": "exercise",
        "wargame": "war game",
        "training": "staff-academy lesson",
        "civil_defence": "civil-defence list",
        "mirror": "a mirror",
        "disputed_plan_or_exercise": "disputed between plan and exercise",
        "reconstruction": "a reconstruction",
    }
    readme = _flat(ROOT / "README.md")
    for doc_type in {p["doc_type"] for p in plans}:
        assert named[doc_type] in readme, doc_type


def test_report_scenario_table_carries_the_viewer_label():
    report = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    seen = {}
    for line in (row for row in report.splitlines() if row.startswith("| ")):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) > 3 and cells[1] in ("historical", "modern"):
            seen[cells[0]] = cells[2]
    scenarios = load_scenarios()
    assert set(seen) == {sc["id"] for sc in scenarios}
    for sc in scenarios:
        assert seen[sc["id"]] == shift_label(sc)


def test_the_sealed_cut_is_described_as_a_population_share_everywhere():
    report = _flat(ROOT / "REPORT.md")
    assert (
        "That is a population share, not the share of score the sealed towns would hold" in report
    )
    viewer = (ROOT / "nucprob" / "probmap" / "viewer.py").read_text(encoding="utf-8")
    assert "falling on towns outside the sealed set" not in viewer
    assert "share of people living in the scored towns" in viewer


def test_misread_rate_names_its_denominator():
    report = _flat(ROOT / "REPORT.md")
    assert (
        "Of the 270 airfield rows that can be compared with a second printing, 216 lie on the low-resolution"
        in report
    )


def test_no_text_cites_an_amendment_that_does_not_exist():
    files = sorted((ROOT / "configs").glob("protocol_amendment_*.yaml"))
    last = max(int(re.search(r"_(\d+)\.yaml", f.name).group(1)) for f in files)
    ordinals = {17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth"}
    later = [word for n, word in ordinals.items() if n > last]
    for path in [
        ROOT / "README.md",
        ROOT / "REPORT.md",
        *CURATED.rglob("*.csv"),
        *CURATED.rglob("*.md"),
    ]:
        text = path.read_text(encoding="utf-8").lower()
        for word in later:
            assert f"{word} amendment" not in text, (path, word)


def test_cards_cite_no_review_round():
    for path in [ROOT / "data" / "FEATURES_CLASSIFIER.md", *CURATED.rglob("README.md")]:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"review of [0-9a-f]{7}, finding", text), path
        assert "milestone runs" not in text


def test_modern_reliability_range_is_named_modern():
    card = _flat(CURATED / "stockpiles" / "README.md")
    assert "Modern reliability values are analysts' assumptions of 80 to 90 percent" in card
    scenarios = load_scenarios()
    assert any(sc["era"] == "modern" for sc in scenarios)
    assert "agreed alternative" not in card


def test_extended_sentence_says_the_best_is_taken_per_list_set():
    report = _flat(ROOT / "REPORT.md")
    assert "picked after the fact for each list set" in report
    ext = pd.read_csv(ROOT / "runs" / "classifier" / "extended.csv")
    glob = ext[ext["scope"] == "global, all attacker documents"]
    assert glob["comparison"].nunique() == 6
