"""The US county check's rerun sits beside its pinned record and states how far it moved."""

import json

import pandas as pd
import pytest

from nucprob.paths import RUNS
from nucprob.us1985 import check

PINNED = RUNS / "m4-us-check"
RERUN = RUNS / "m4-us-check-rerun"


def test_the_committed_comparison_is_the_two_metric_tables():
    got = pd.read_csv(RERUN / "comparison.csv")
    want = check.compare(pd.read_csv(PINNED / "metrics.csv"), pd.read_csv(RERUN / "metrics.csv"))
    pd.testing.assert_frame_equal(got, want, check_exact=False, atol=1e-4)


def test_the_rerun_does_not_touch_the_pinned_record():
    pins = json.loads((RUNS / "milestone_hashes.json").read_text(encoding="utf-8"))
    assert any(k.startswith("runs/m4-us-check/") for k in pins)
    assert not any(k.startswith("runs/m4-us-check-rerun/") for k in pins)
    assert check.RERUN != check.OUT


def test_the_rerun_records_the_live_inputs_it_read():
    inputs = json.loads((RERUN / "manifest.json").read_text(encoding="utf-8"))["inputs"]
    assert set(inputs) == {
        "ourairports/airports.csv",
        "data/curated/features/us_military_sites_1985.csv",
    }


def test_a_rerun_with_a_missing_row_is_refused():
    m = pd.read_csv(PINNED / "metrics.csv")
    with pytest.raises(AssertionError, match="not the pinned record"):
        check.compare(m, m.iloc[1:])


def test_the_difference_is_rerun_minus_pinned():
    m = pd.read_csv(PINNED / "metrics.csv")
    r = m.copy()
    r.loc[0, "pr_auc_mean"] += 0.01
    d = check.compare(m, r)["pr_auc_mean_diff"]
    assert d.iloc[0] == pytest.approx(0.01) and (d.iloc[1:] == 0).all()


def test_the_readme_states_the_comparison_as_committed():
    from nucprob.paths import ROOT

    c = pd.read_csv(RERUN / "comparison.csv")
    d = c["pr_auc_mean_diff"].abs()
    text = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert f"{int((d == 0).sum())} of the {len(c)} rows match" in text
    assert f"largest PR-AUC difference is {d.max():.4f}" in text
    # Every row that moved has the airfield count among its features.
    moved = c.loc[d > 0, "model"]
    models = json.loads((RERUN / "manifest.json").read_text(encoding="utf-8"))["models"]
    assert all("log_airports_county" in models[m] for m in moved)
