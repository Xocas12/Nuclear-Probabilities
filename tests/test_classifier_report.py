"""The classifier report is what its outputs say, and they obey the protocol."""

import json

import pandas as pd
import pytest
import yaml

from nucprob.classifier import report
from nucprob.paths import ROOT, RUNS

OUT = RUNS / "classifier"
needs_run = pytest.mark.skipif(not (OUT / "comparison.csv").exists(), reason="no classifier run")


@needs_run
def test_report_is_a_regeneration_of_the_committed_outputs():
    assert (ROOT / "REPORT.md").read_text(encoding="utf-8") == report.report()
    assert (OUT / "TABLES.md").read_text(encoding="utf-8") == report.tables()


@needs_run
def test_the_run_used_the_protocol_settings_and_the_full_analysis():
    m = json.loads((OUT / "manifest.json").read_text())
    proto = yaml.safe_load((ROOT / "configs" / "protocol.yaml").read_text(encoding="utf-8"))
    assert m["bags"] == 50
    assert m["bootstrap"] == proto["evaluation"]["bootstrap"]["resamples"]
    assert not m["quick"]
    assert m["sealed_rows_excluded"] > 0


@needs_run
def test_failures_are_in_the_report_and_gains_are_not_claimed_where_an_interval_holds_zero():
    comp = pd.read_csv(OUT / "comparison.csv")
    assert ((comp["low"] <= comp["delta"]) & (comp["delta"] <= comp["high"])).all()
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    assert report.verdicts(primary).get("loss", 0) > 0
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    assert "do not carry over" in text
    # The claim of the main result: gains on population + country come only from spatial blocks.
    won = primary[
        primary["Difference"].map(lambda s: float(s[s.index("[") + 1 :].split(",")[0]) > 0)
    ]
    assert set(won["Holdout"]) <= {"Spatial blocks"}


@needs_run
def test_no_exercise_based_scope_is_called_a_war_plan_model_and_the_ussr_is_refused():
    scopes = pd.read_csv(OUT / "scopes.csv").set_index("scope")
    pooled = "Warsaw Pact, pooled, exercise-based"
    assert scopes.loc[pooled, "exercise_based"]
    assert not scopes.loc["global, plan documents only", "exercise_based"]
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    assert not gate.loc["USSR", "allowed"]
    assert "not a war-plan model" in report.SCOPES[pooled]


def test_the_sealed_set_has_not_been_read_unless_its_lock_says_so():
    sealed = OUT / "sealed"
    if (sealed / "metrics.csv").exists():
        assert (sealed / "LOCK.json").exists()


@needs_run
def test_the_readme_quotes_the_report():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    for quoted in ("+0.02 [+0.01, +0.04]", "-0.15 [-0.17, -0.13]"):
        assert quoted in readme and quoted in text
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    assert int(gate.loc["US", "linked_positives"]) == 1314
    assert int(gate.loc["US", "positives_outside_largest"]) == 25
    assert "1289 of its 1314" in readme
