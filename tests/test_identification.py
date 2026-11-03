"""The document identification intervals (configs/protocol_amendment_13.yaml): the resampling keeps a
place's rows together, the verdicts follow the bounds, the capacity call follows its stated rule, and the
committed figures are the ones REPORT states."""

import json

import numpy as np
import pandas as pd
import pytest

from nucprob.classifier import identification as ident
from nucprob.paths import ROOT

OUT = ident.OUT
needs_run = pytest.mark.skipif(not (OUT / "manifest.json").exists(), reason="no identification run")


def test_resamples_draw_whole_places():
    places = np.array(["a", "a", "b", "c", "c", "c"])
    for r in ident.place_resamples(places, n=50, seed=3):
        drawn = pd.Series(places[r]).value_counts()
        sizes = {"a": 2, "b": 1, "c": 3}
        for p, k in drawn.items():
            assert k % sizes[p] == 0
        assert len(r) >= 1


def test_verdict_needs_the_whole_interval_on_one_side():
    assert ident.verdict(0.001, 0.2) == "above"
    assert ident.verdict(-0.2, -0.001) == "below"
    assert ident.verdict(-0.01, 0.2) == "cannot be told apart"


def test_intervals_find_a_real_gap_and_not_a_null_one():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 600)
    good = np.where(rng.random(600) < 0.8, y, (y + 1) % 3)
    preds = {"all permitted": good, "noise": rng.integers(0, 3, 600), "same": good.copy()}
    res = ident.place_resamples(np.arange(600), n=300, seed=1)
    out = ident.intervals(y, preds, res).set_index("columns")
    assert out.at["all permitted", "over_largest_verdict"] == "above"
    assert out.at["noise", "over_reference_verdict"] == "below"
    assert out.at["same", "over_reference_verdict"] == "cannot be told apart"
    assert out.at["all permitted", "over_reference_verdict"] == ""
    lo, hi = out.at["all permitted", "accuracy_lo"], out.at["all permitted", "accuracy_hi"]
    assert lo <= out.at["all permitted", "accuracy"] <= hi


def _probe(y, at_60, at_300):
    res = ident.place_resamples(np.arange(len(y)), n=300, seed=2)
    return ident.capacity(y, {60: at_60, 300: at_300}, res).set_index("max_iter")


def test_capacity_is_called_only_when_the_gap_closes():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 4, 800)
    right = y.copy()
    half = np.where(rng.random(800) < 0.5, y, (y + 1) % 4)
    closed = _probe(
        y,
        {"no source markers": right, "all permitted": half},
        {"no source markers": right, "all permitted": right},
    )
    assert (closed["call"] == "explained by capacity").all()
    kept = _probe(
        y,
        {"no source markers": right, "all permitted": half},
        {"no source markers": right, "all permitted": half},
    )
    assert (kept["call"] == "not explained").all()


@needs_run
def test_the_run_reproduced_the_committed_check_and_names_its_amendment():
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["amendment"] == "configs/protocol_amendment_13.yaml"
    assert (m["resamples"], m["seed"]) == (ident.N_BOOT, ident.SEED)
    committed = pd.read_csv(ident.RUNS / "classifier" / "document_identification.csv").set_index(
        "columns"
    )
    got = pd.read_csv(OUT / "intervals.csv").set_index("columns")
    for name in ident.SETS:
        assert got.at[name, "accuracy"] == pytest.approx(committed.at[name, "accuracy"], abs=1e-4)


@needs_run
def test_every_step_is_clean_and_the_pending_list_matches_the_outputs():
    m = json.loads((OUT / "manifest.json").read_text())
    assert set(m["steps"]) | set(m["pending"]) == set(ident.STEPS)
    assert not set(m["steps"]) & set(m["pending"])
    assert all(r["git_dirty"] is False for r in m["steps"].values())
    assert ("capacity probe" in m["steps"]) == (OUT / "capacity.csv").exists()
    seeds = [s for s in m["steps"] if s.startswith("split ")]
    assert bool(seeds) == (OUT / "splits.csv").exists()
    if seeds:
        assert (pd.read_csv(OUT / "splits.csv")["splits"] == len(seeds)).all()


@needs_run
def test_report_states_the_intervals_and_the_probe_call():
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    got = pd.read_csv(OUT / "intervals.csv").set_index("columns")
    for name in ident.SETS:
        lo, hi = got.at[name, "accuracy_lo"], got.at[name, "accuracy_hi"]
        assert f"[{lo:.1%}, {hi:.1%}]" in text, name
    if (OUT / "capacity.csv").exists():
        call = pd.read_csv(OUT / "capacity.csv")["call"].iloc[0]
        assert f"capacity probe: {call}" in text
    else:
        assert "capacity probe: pending" in text
    pending = json.loads((OUT / "manifest.json").read_text())["pending"]
    if pending:
        said = text[text.index("Steps of the amendment not yet run") :][:400]
        assert ("the capacity probe" in said) == ("capacity probe" in pending)
        splits_left = sum(p.startswith("split ") for p in pending)
        if splits_left:
            assert f"{splits_left} of the 10 split repeats" in said
    else:
        assert "Steps of the amendment not yet run" not in text
    assert "No interval was computed for any of these accuracies" not in text


def test_a_checkpoint_is_reused_only_under_the_same_key(tmp_path, monkeypatch):
    monkeypatch.setattr(ident, "WORK", tmp_path)
    calls = []

    def compute():
        calls.append(1)
        return {"all permitted": np.array([1, 2, 3])}

    first, _ = ident.checkpoint("s", {"k": 1}, compute, {"git_commit": "c", "git_dirty": False})
    again, _ = ident.checkpoint("s", {"k": 1}, compute, {"git_commit": "c", "git_dirty": False})
    assert len(calls) == 1
    assert (again["all permitted"] == first["all permitted"]).all()
    ident.checkpoint("s", {"k": 2}, compute, {"git_commit": "c", "git_dirty": False})
    assert len(calls) == 2
