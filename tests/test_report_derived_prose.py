"""Sentences of REPORT and README that review 23 found typed are now read from the outputs (findings 7-9)."""

import pandas as pd

from nucprob.classifier import report
from nucprob.paths import ROOT


def test_the_seed_sentence_gives_the_tail_not_a_cap():
    text = report.seed_movement()
    assert "up to" not in text and "the largest by" in text
    spans = report._seed_spans()
    assert f"the largest by {spans.max():.3f}" in text


def test_a_selection_closer_than_seed_noise_is_called_a_tie():
    sel = pd.DataFrame(
        {
            "scope": ["s", "s"],
            "model": ["logistic, all permitted", "LightGBM, all permitted"],
            "weighted_pr_auc": [0.8449, 0.8450],
            "selected": [False, True],
        }
    )
    assert "so the two are tied" in report.tie_note(sel, "s")
    sel.loc[0, "weighted_pr_auc"] = 0.70
    assert report.tie_note(sel, "s") == ""


def test_the_sealed_gain_size_follows_the_rows():
    prim = pd.DataFrame(
        {"verdict": ["gain", "neither"], "delta": [0.031, 0.2], "base_rate": [0.56, 0.56]}
    )
    assert (
        report._sealed_gain_size(prim) == "The gains are +0.03 of PR-AUC, on a base rate of 0.56. "
    )
    assert report._sealed_gain_size(prim.assign(verdict="neither")) == ""


def test_card_figures_once_typed_are_read():
    xd = report._crossdoc()
    assert (xd["rows"], xd["coarse"]) == (270, 216)
    wr = report._weurope_resolution()
    assert wr["kept"] + wr["dropped"] == 29
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())
    assert f"was {xd['misread']} in {xd['coarse']}" in flat
    assert f"{wr['rows']} rows remain" in flat
    assert "Six fed features" not in flat and "a few hundredths" not in flat
