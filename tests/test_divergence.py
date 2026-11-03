"""The primary-fit divergence check (configs/protocol_amendment_15.yaml): its bags are fit_bagged's, its
evaluation set leaves the trees alone, its rules catch a fit that runs away, and REPORT states its counts."""

import json

import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression

from nucprob.classifier import divergence as dv
from nucprob.classifier import fit as cfit
from nucprob.paths import ROOT
from tests.test_classifier import toy

needs_run = pytest.mark.skipif(not (dv.OUT / "manifest.json").exists(), reason="no divergence run")


def table(n: int = 400) -> pd.DataFrame:
    d = toy(n, seed=4)
    rng = np.random.default_rng(5)
    for c in cfit.ALL_FEATURES:
        if c not in d:
            d[c] = rng.normal(size=n)
    d.loc[rng.random(n) < 0.1, cfit.ALL_FEATURES[3]] = np.nan
    return d


@pytest.mark.parametrize("spec", cfit.specs(), ids=lambda s: s.name)
def test_the_refitted_bags_score_exactly_as_fit_bagged(spec):
    d = table()
    models, records = dv.fit_all(spec, d, n_bags=4)
    ours = cfit.Fitted(models, spec.columns).score(d)
    theirs = cfit.fit_bagged(spec, d, n_bags=4).score(d)
    np.testing.assert_array_equal(ours, theirs)
    assert len(records) == 4
    assert all(
        r["kind"] == ("lightgbm" if "LightGBM" in spec.name else "logistic") for r in records
    )


def test_a_complete_scope_is_one_plain_fit_as_in_fit_bagged():
    d = table().assign(complete=True)
    spec = cfit.specs()[3]
    models, _ = dv.fit_all(spec, d, n_bags=4)
    assert len(models) == 1
    np.testing.assert_array_equal(
        cfit.Fitted(models, spec.columns).score(d), cfit.fit_bagged(spec, d, n_bags=4).score(d)
    )


def test_a_smooth_fit_is_not_called_diverged():
    d = table()
    spec = cfit.specs()[3]
    _, records = dv.fit_all(spec, d, n_bags=2)
    for r in records:
        assert not r["diverged"]
        assert r["loss_final"] <= r["loss_min"] + dv.LOSS_RISE
        assert r["max_abs_raw"] < dv.MAX_RAW


def test_the_rules_catch_an_unconverged_logistic_and_a_runaway_boosting_fit():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"log_pop": rng.normal(size=200), "b": rng.normal(size=200)})
    y = (X["log_pop"] + rng.normal(0, 0.5, 200) > 0).astype(int).to_numpy()
    _, r = dv.diagnose(LogisticRegression(max_iter=2), X, y)
    assert r["solver_hit_max_iter"] and r["diverged"]
    _, r = dv.diagnose(LogisticRegression(max_iter=5000), X, y)
    assert not r["solver_hit_max_iter"] and not r["diverged"]
    # Random labels against a feature the trees can split forever, at a learning rate far past the
    # protocol's 0.03: the training loss rises and the raw scores run away.
    _, r = dv.diagnose(
        LGBMClassifier(
            n_estimators=60, learning_rate=40.0, num_leaves=4, min_child_samples=1, verbose=-1
        ),
        pd.DataFrame({"a": rng.normal(size=200)}),
        rng.integers(0, 2, 200),
    )
    assert r["diverged"]
    assert r["loss_final"] - r["loss_min"] > dv.LOSS_RISE and r["max_abs_raw"] > dv.MAX_RAW


def test_the_holdouts_are_the_evaluations_own():
    d = table()
    kinds = [(h, f, len(t)) for h, f, t in dv.trainings(d)]
    assert kinds[0] == ("whole scope", "all rows", len(d))
    assert sum(h == "spatial blocks, first grid" for h, *_ in kinds) == 5
    lopo = [(f, n) for h, f, n in kinds if h == "leave one document out"]
    for group, n in lopo:
        held = d[d["group"] == group]
        assert n == (~d["place_id"].isin(held["place_id"])).sum()
    assert [f for h, f, _ in kinds if h == "temporal"] == ["fit up to cut", "fit after cut"]


@needs_run
def test_the_run_names_its_amendment_and_its_summary_follows_the_fits():
    m = json.loads((dv.OUT / "manifest.json").read_text())
    assert m["amendment"] == "configs/protocol_amendment_15.yaml"
    assert m["git_dirty"] is False
    assert (m["bags"], m["seed"]) == (cfit.N_BAGS, dv.SEED)
    fits = pd.read_csv(dv.OUT / "fits.csv")
    pd.testing.assert_frame_equal(
        dv.summarise(fits).reset_index(drop=True),
        pd.read_csv(dv.OUT / "summary.csv"),
        check_dtype=False,
        atol=1e-5,
    )
    rule = (fits["loss_final"] - fits["loss_min"] > dv.LOSS_RISE) | (
        fits["max_abs_raw"] > dv.MAX_RAW
    )
    rule |= fits["solver_hit_max_iter"].astype(bool)
    assert (fits["diverged"].astype(bool) == rule).all()
    assert set(fits["model"]) == {s.name for s in cfit.specs()}


@needs_run
def test_report_states_the_divergence_counts():
    fits = pd.read_csv(dv.OUT / "fits.csv")
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    n, bad = len(fits), int(fits["diverged"].sum())
    assert f"{n:,} bag fits" in text
    assert f"{bad:,} were called diverged" in text


@needs_run
def test_report_states_the_largest_scores_from_the_fits():
    fits = pd.read_csv(dv.OUT / "fits.csv")
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    lgb, lr = fits[fits["kind"] == "lightgbm"], fits[fits["kind"] == "logistic"]
    assert f"its largest raw score was {lgb['max_abs_raw'].max():.1f}" in text
    assert f"largest decision value was {lr['max_abs_raw'].max():.1f}" in text
    if not fits["diverged"].any():
        assert "Some primary fits diverged" not in text
    else:
        assert "Some primary fits diverged" in text
