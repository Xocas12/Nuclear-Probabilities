"""The document identification intervals (configs/protocol_amendment_13.yaml): the resampling keeps a
place's rows together, the verdicts follow the bounds, the capacity call follows its stated rule, and the
committed figures are the ones REPORT states."""

import json

import numpy as np
import pandas as pd
import pytest

from nucprob.classifier import identification as ident
from nucprob.classifier import identification_fit as fit
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
def test_report_states_the_regularised_intervals_and_what_was_not_run():
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    reg = pd.read_csv(OUT / "regularised.csv").set_index("columns")
    for name in ident.SETS:
        lo, hi = reg.at[name, "accuracy_lo"], reg.at[name, "accuracy_hi"]
        assert f"[{lo:.1%}, {hi:.1%}]" in text, name
    iv = pd.read_csv(OUT / "intervals.csv").set_index("columns")
    lo, hi = iv.at["all permitted", "accuracy_lo"], iv.at["all permitted", "accuracy_hi"]
    assert f"{lo:.1%} to {hi:.1%} on all columns" in text
    # The capacity probe's call was quoted without a definition, inside the
    # account of the withdrawn fit. REPORT now states that fit's divergence count instead.
    div = pd.read_csv(OUT / "divergence.csv")
    as_run = div[div["l2_regularization"] == 0]
    assert f"{int(as_run['diverged'].sum())} of its {len(as_run)} fits" in text
    assert "(capacity probe:" not in text
    pending = json.loads((OUT / "manifest.json").read_text())["pending"]
    splits_left = sum(p.startswith("split ") for p in pending)
    if splits_left:
        assert f"{splits_left} of the 10 split repeats" in text
    if not pending:
        assert "were not run; they would describe the diverged fit" not in text
    assert "No interval was computed for any of these accuracies" not in text


@needs_run
def test_divergence_record_follows_its_rule_and_report_counts_it():
    div = pd.read_csv(OUT / "divergence.csv")
    assert len(div) == len(ident.SETS) * 4 * len(fit.L2)
    rule = div["train_accuracy_best"] - div["train_accuracy_final"] > fit.DIVERGED_DROP
    assert (div["diverged"] == rule).all()
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    as_run = div[div["l2_regularization"] == 0]
    assert (
        f"{int(as_run['diverged'].sum())} of its {len(as_run)} fits (four column sets, four folds) diverged"
        in text
    )
    m = json.loads((OUT / "fit_manifest.json").read_text())
    assert m["amendment"] == "configs/protocol_amendment_14.yaml"
    assert m["l2_regularization"] == fit.REGULARISED


def test_a_fit_on_separable_documents_does_not_diverge():
    rng = np.random.default_rng(0)
    y = np.repeat(np.arange(3), 60)
    X = pd.DataFrame({"a": y + rng.normal(0, 0.1, len(y)), "b": rng.normal(size=len(y))})
    train, test = np.arange(0, len(y), 2), np.arange(1, len(y), 2)
    record, held = fit.fit_fold(X, y, train, test, 1.0)
    assert not record["diverged"]
    assert record["test_accuracy"] > 0.9
    assert len(held) == len(test)


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
