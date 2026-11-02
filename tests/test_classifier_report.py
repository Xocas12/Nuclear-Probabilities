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
    """A sealed place is in a sealed block and unread by earlier runs. Eleven towns of those blocks were
    read by the M2 check before the seal and stay scored, so the block check allows only those."""
    sealed = set(pd.read_csv(ROOT / "data" / "curated" / "splits" / "sealed_blocks.csv")["block"])
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz", usecols=["plan_id", "place_id", "block"])
    sac = scores[scores["plan_id"] == report.SAC]
    assert len(sac) > 0
    assert sac.loc[sac["block"].isin(sealed), "place_id"].nunique() <= 11
    table = PROCESSED / "classifier_table.parquet"
    if table.exists():
        t = pd.read_parquet(table, columns=["place_id", "sealed"])
        assert not set(t.loc[t["sealed"].astype(bool), "place_id"]) & set(scores["place_id"])
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
def test_each_scope_lists_only_documents_of_that_scope():
    lists = pd.read_csv(OUT / "lists.csv")
    table = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    expected = lists["holdout"].str.startswith("expectation")
    pact = lists[lists["scope"].str.startswith("Warsaw Pact")]
    # Rows the pooled model is fitted and held out on are Warsaw Pact documents; the other side's
    # expectations of a Soviet strike are scored only as expectation lists, never as plans.
    assert pact.loc[~expected, "plan_id"].str.startswith("wp_").all()
    roles = table.groupby("plan_id")["role"].first()
    assert (roles.reindex(lists.loc[expected, "plan_id"]) == "test-expectation").all()
    assert not lists.loc[expected, "plan_id"].str.startswith("wp_").any()
    train = set(table.loc[table["role"] == "train", "plan_id"])
    assert set(lists.loc[~expected, "plan_id"]) <= train
    assert not np.isnan(pd.read_csv(OUT / "comparison.csv")["delta"]).any()


@needs_run
def test_the_report_states_what_earlier_reviews_found_it_withholding():
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    assert "no measured error rate" not in text
    assert "743 lines, found 0 errors" in text and "3 in 216" in text
    # Terms a newcomer needs, and the grades.
    for term in (
        "Strategic Air Command",
        "Correlates of War",
        '"All permitted"',
        "C, a scholar's table",
    ):
        assert term in text, term
    # War plans: what was read at source, in numbers from the outputs.
    assert "Only one was read at source" in text
    assert "A further 1 document" not in text
    # The map's unsourced shares and its scaling are printed, not left to the config.
    assert "The theatre shares have no source" in text
    assert "share of people living in scored towns" in text
    assert "unit_sensitivity.csv" in text
    assert "The temporal rows also change attacker" in text
    # A gain named in prose is one in the table, whatever the data say.
    assert "Those gains are over LightGBM" not in text


@needs_run
def test_the_transcription_figures_in_the_report_are_those_of_the_card():
    card = (ROOT / "data" / "curated" / "sac1956" / "README.md").read_text(encoding="utf-8")
    card = " ".join(card.split())
    assert "(743 lines, seed 1956)" in card and "0 of 743, 95% interval 0 to 0.51%" in card
    assert "error rate was 1.3%" in card and "is 3 in 216" in card


@needs_run
def test_a_row_under_the_training_floor_is_counted_over_every_grid():
    """The primary table's training count is the fewest positives of any fit, not an estimate."""
    table = PROCESSED / "classifier_table.parquet"
    if not table.exists():
        pytest.skip("no built tables")
    t = pd.read_parquet(table)
    t = t[~t["sealed"].astype(bool) & (t["role"] == "train") & t["plan_id"].str.startswith("wp_")]
    comp = pd.read_csv(OUT / "comparison.csv")
    row = comp[
        (comp["scope"] == "Warsaw Pact, pooled, exercise-based")
        & (comp["holdout"] == "spatial blocks")
    ].iloc[0]
    assert row["train_positives_min"] == ev.spatial_train_positives(t.reset_index(drop=True))
