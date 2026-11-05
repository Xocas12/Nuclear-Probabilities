"""Checks for the eleventh review's findings (review of 7ef717e): each reads the data or outputs a
statement rests on, so a wrong figure or a stale run fails, not only a changed word."""

import json

import pandas as pd
import pytest
import yaml

from nucprob.classifier import report
from nucprob.paths import CURATED, ROOT, RUNS
from nucprob.places import CLOSED, UNIVERSE
from nucprob.probmap.counts import count

OUT = RUNS / "classifier"
MAP = RUNS / "probmap"
needs_run = pytest.mark.skipif(not (OUT / "comparison.csv").exists(), reason="no classifier run")
needs_map = pytest.mark.skipif(not (MAP / "manifest.json").exists(), reason="no map run")


def _text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def test_count_rounds_simulated_counts_to_tens_from_one_hundred():
    assert [count(x) for x in (6, 99.4, 100, 1377, 1128.4, 597, 2088)] == [
        "6",
        "99",
        "100",
        "1380",
        "1130",
        "600",
        "2090",
    ]


@needs_map
def test_the_map_ran_on_the_classifier_table_of_record():
    """Finding 4: the map's manifest must name the same feature table as the classifier's."""
    probmap = json.loads((MAP / "manifest.json").read_text())
    classifier = json.loads((OUT / "manifest.json").read_text())
    assert probmap["table_sha256"] == classifier["table_sha256"]


@needs_map
def test_every_historical_scenario_states_the_frus_stand_in_in_the_viewer():
    """Findings 5 and 6: reliability and losses of every historical scenario are the 1953 FRUS figures,
    and the viewer, README and stockpile card say so."""
    scenarios = yaml.safe_load((ROOT / "configs" / "scenarios.yaml").read_text())["scenarios"]
    page = (MAP / "viewer" / "index.html").read_text(encoding="utf-8")
    historical = [s for s in scenarios if s["era"] == "historical"]
    assert historical
    for s in historical:
        losses = {tuple(a["fraction_lost_to_defences"]) for a in s["attackers"]}
        assert losses == {(0.07, 0.17, 0.27)}, s["id"]
        assert "FRUS" in s["note"] and "Soviet bombers attacking the US" in s["note"], s["id"]
        assert json.dumps(s["note"])[1:-1] in page, s["id"]
    assert "FRUS" in _text(ROOT / "README.md")
    card = _text(CURATED / "stockpiles" / "README.md")
    assert "would be an extrapolation" not in card and "nevertheless apply them" in card


@needs_map
def test_the_viewer_uses_no_internal_shorthand_and_claims_no_sealed_town():
    """Findings 7 and 8."""
    page = (MAP / "viewer" / "index.html").read_text(encoding="utf-8")
    assert "amendment" not in page
    assert "all bloc towns" not in page


def test_readme_does_not_say_every_late_input_is_removed():
    """Finding 2: README must not say late features are flagged and dropped while the population
    columns keep later censuses; it names each closed town in the universe whose only figure is late."""
    readme = _text(ROOT / "README.md")
    assert "it is flagged and the results are repeated without it" not in readme
    assert "not flagged and stay in those repeats" in readme
    closed = pd.read_csv(CLOSED)
    late = closed[(closed["pop_year"] > 1959) & (closed["pop_estimate"] >= UNIVERSE)]
    for r in late.itertuples():
        assert f"{r.name}'s {r.pop_year:.0f} figure" in readme, r.name


@needs_run
def test_the_report_counts_the_scored_places_inside_sealed_blocks():
    """Finding 3: sealed blocks do hold scored places; REPORT gives their count from the outputs."""
    sealed = set(pd.read_csv(ROOT / "data" / "curated" / "splits" / "sealed_blocks.csv")["block"])
    h = pd.read_csv(OUT / "held_out_scores.csv.gz", usecols=["plan_id", "place_id", "block"])
    inside = h[h["block"].isin(sealed)]
    total = inside["place_id"].nunique()
    sac = inside.loc[inside["plan_id"] == report.SAC, "place_id"].nunique()
    text = _text(ROOT / "REPORT.md")
    assert "holds no training place" not in text
    assert f"{total} scored places lie in sealed blocks, {sac} of them SAC 1956 towns" in text


@needs_run
def test_sac_positives_split_into_scope_and_sealed():
    """Finding 10: SAC's linked positives are the SAC scope's positives plus the sealed listed places,
    and REPORT connects the two counts."""
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker").loc["US"]
    sac_linked = int(gate["linked_positives"] - gate["positives_outside_largest"])
    sealed = pd.read_csv(OUT / "sealed" / "comparison.csv")
    sealed_pos = int(sealed.loc[sealed["population"].eq("all sealed"), "positives"].iloc[0])
    comp = pd.read_csv(OUT / "comparison.csv")
    scope = int(
        comp.loc[comp["scope"].str.startswith("single document: SAC 1956"), "positives"].iloc[0]
    )
    assert sac_linked == scope + sealed_pos
    text = _text(ROOT / "REPORT.md")
    assert f"Of SAC's, {sealed_pos} lie in the sealed blocks" in text
    assert f"leaves the {scope} positives" in text


def test_terms_are_defined_where_first_used():
    """Finding 9."""
    text = _text(ROOT / "REPORT.md")
    first = text.index("the early check")
    assert text[first : first + 80].startswith("the early check (the two test models")
    assert "M1 slice (USSR towns only" in text
    assert "Control and Reporting Centre (CRC) at Glons" in text
    assert "plans of Zealand" not in text


@needs_map
def test_report_rounds_the_map_counts():
    """Finding 13: delivered warheads and cells over one half are printed as count() gives them."""
    text = _text(ROOT / "REPORT.md")
    d = pd.read_csv(MAP / "delivered.csv")
    bloc = d[d["scenario"] == "us_1956_on_bloc"].iloc[0]
    assert f"{count(bloc['delivered_median'])} delivered at the median" in text
    s = pd.read_csv(MAP / "scenarios.csv")
    for r in s.itertuples():
        cell = f"{count(r.cells_over_half_median)} [{count(r.cells_over_half_low)}, {count(r.cells_over_half_high)}]"
        assert f"| {r.scenario} |" in text and cell in text, cell


def test_the_second_read_note_does_not_say_the_gate_moved():
    """Finding 11: lessons are not plans, so the USSR's gate row cannot move with them."""
    note = _text(ROOT / "data" / "notes" / "second_read_2026-11b.md")
    assert "moves only in positives" not in note
    gate = OUT / "state_gate.csv"
    if gate.exists():
        ussr = pd.read_csv(gate).set_index("attacker").loc["USSR"]
        assert int(ussr["linked_positives"]) == 0 and int(ussr["independent_plans"]) == 0
