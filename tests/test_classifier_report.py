"""The classifier report is what its outputs say, its outputs are what the scores say, and the run
is of the committed inputs."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from nucprob.classifier import evaluate as ev
from nucprob.classifier import report
from nucprob.classifier.run import input_hashes
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

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
def test_the_run_is_of_the_committed_protocol_and_labels():
    """Changing the protocol, a label file, the registry or sources.yaml after a run fails here."""
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["protocol_sha256"] == sha256(ROOT / "configs" / "protocol.yaml")
    assert m["inputs_sha256"] == input_hashes()


@needs_run
@pytest.mark.skipif(
    not (PROCESSED / "classifier_table.parquet").exists(), reason="table not built here"
)
def test_the_run_is_of_this_table():
    """A permuted label in the table fails here, where the table exists."""
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["table_sha256"] == sha256(PROCESSED / "classifier_table.parquet")


@needs_run
def test_every_comparison_row_recomputes_from_the_held_out_scores():
    """A changed number in comparison.csv fails here, without any table or raw data."""
    comp = pd.read_csv(OUT / "comparison.csv")
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz")
    assert len(comp) > 0
    for (scope, holdout), part in comp.groupby(["scope", "holdout"]):
        s = scores[(scores["scope"] == scope) & (scores["holdout"] == holdout)]
        assert len(s), (scope, holdout)
        for _, r in part.iterrows():
            k = s if r["lists"] == "all lists" else s[s["plan_id"] != report.SAC]
            y, doc = k["listed"].to_numpy(int), k["plan_id"].to_numpy()
            a = ev.weighted_pr_auc(y, k[r["model"]].to_numpy(), doc)
            b = ev.weighted_pr_auc(y, k[r["against"]].to_numpy(), doc)
            assert a == pytest.approx(r["a_pr_auc"], abs=2e-3), (scope, holdout)
            assert b == pytest.approx(r["b_pr_auc"], abs=2e-3), (scope, holdout)
            assert int(y.sum()) == r["positives"]
            assert a - b == pytest.approx(r["delta"], abs=2e-3)


@needs_run
def test_verdicts_come_from_unrounded_bounds_and_need_both_intervals():
    row = {
        "low": -0.18,
        "high": -0.0004,
        "block_low": -0.2,
        "block_high": -0.001,
        "train_positives_min": 100,
        "constant_score": False,
    }
    assert report.verdict(row) == "loss"
    assert report.verdict(row | {"block_high": 0.01}) == "neither"
    assert report.verdict(row | {"train_positives_min": 8}) == "not a reading"
    assert report.verdict(row | {"constant_score": True}) == "not a reading"
    assert report.verdict(
        row | {"low": 0.01, "high": 0.2, "block_low": 0.0, "block_high": 0.2}
    ) == ("neither")


@needs_run
def test_failures_are_in_the_report_and_gains_are_not_claimed_where_an_interval_holds_zero():
    comp = pd.read_csv(OUT / "comparison.csv")
    assert ((comp["low"] <= comp["delta"]) & (comp["delta"] <= comp["high"])).all()
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    counts = primary["Verdict"].value_counts().to_dict()
    assert sum(counts.values()) == len(primary)
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    for name in ("gain", "loss", "neither", "not a reading"):
        assert f"{counts.get(name, 0)} {report.WORDS[name]}" in text
    for _, r in comp.iterrows():
        if report.verdict(r) == "gain":
            assert r["low"] > 0 and r["block_low"] > 0


@needs_run
def test_no_constant_model_is_read_as_a_finding():
    comp = pd.read_csv(OUT / "comparison.csv")
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    constant = comp[comp["constant_score"].astype(bool)]
    for _, r in constant.iterrows():
        assert report.verdict(r) == "not a reading"
    assert "not a reading" in set(primary["Verdict"]) or constant.empty


@needs_run
def test_no_exercise_based_scope_is_called_a_war_plan_model_and_the_ussr_is_refused():
    scopes = pd.read_csv(OUT / "scopes.csv").set_index("scope")
    pooled = "Warsaw Pact, pooled, exercise-based"
    assert scopes.loc[pooled, "exercise_based"]
    assert not scopes.loc["global, plan documents only", "exercise_based"]
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    assert not gate.loc["USSR", "allowed"]
    assert "not a war-plan model" in report.SCOPES[pooled]


@needs_run
def test_no_sealed_place_is_in_any_committed_score():
    """The sealed list is fixed by block. Run with the table here; the block check runs everywhere."""
    sealed = set(pd.read_csv(ROOT / "data" / "curated" / "splits" / "sealed_blocks.csv")["block"])
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz", usecols=["plan_id", "block"])
    sac = scores[scores["plan_id"] == report.SAC]
    assert len(sac) > 0
    assert not set(sac["block"]) & sealed
    assert not (OUT / "sealed" / "metrics.csv").exists() or (OUT / "sealed" / "LOCK.json").exists()


@needs_run
def test_the_readme_quotes_the_report_and_the_gate():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    for quoted in report.headline_quotes():
        assert quoted in readme and quoted in text, quoted
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    us = gate.loc["US"]
    assert f"{int(us['positives_outside_largest'])} outside" in readme


@needs_run
def test_tables_hold_no_row_for_a_list_absent_from_the_scope():
    tables = (OUT / "TABLES.md").read_text(encoding="utf-8")
    lists = pd.read_csv(OUT / "lists.csv")
    assert tables.count("\n") < 12 * len(lists) ** 0.5 + len(lists)
    assert not np.isnan(pd.read_csv(OUT / "comparison.csv")["delta"]).any()
