"""The transfer check's paired bootstrap, and the claims TRANSFER.md and PLAN.md make from it."""

import re

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from nucprob.model.evaluate import precision_at_k
from nucprob.paths import CURATED, ROOT, RUNS
from nucprob.transfer.paired import compare, paired_bootstrap, score_rows

RUN = RUNS / "m4-transfer-check"
MODEL = "LightGBM, common"
NUM = r"([+-]?\d\.\d\d)"
INTERVAL = re.compile(rf"{NUM} \[{NUM}, {NUM}\]")


def _signed(x: float) -> str:
    s = f"{x:+.2f}"
    return "0.00" if s in ("+0.00", "-0.00") else s


def test_scores_match_sklearn_with_ties():
    rng = np.random.default_rng(1)
    for n, rate in [(40, 0.1), (300, 0.03), (55, 0.3)]:
        y = (rng.random(n) < rate).astype(int)
        y[:2] = [1, 0]
        p = np.round(rng.random(n), 1)  # many ties
        got = score_rows(y, p)
        assert got["pr_auc"][0] == pytest.approx(average_precision_score(y, p))
        assert got["roc_auc"][0] == pytest.approx(roc_auc_score(y, p))
        assert got["precision_at_k"][0] == pytest.approx(precision_at_k(y, p))


def test_same_scores_give_a_zero_interval():
    rng = np.random.default_rng(2)
    y = np.r_[np.ones(5), np.zeros(95)]
    p = rng.random(100)
    for r in paired_bootstrap(y, p, p, n_boot=200).values():
        assert r["diff"] == r["lo"] == r["hi"] == 0


def test_interval_separates_a_clear_gain_from_noise():
    rng = np.random.default_rng(3)
    y = np.r_[np.ones(20), np.zeros(380)]
    noise = rng.random(400)
    perfect = y + 0.01 * rng.random(400)
    res = paired_bootstrap(y, noise, perfect, n_boot=500)
    assert all(r["lo"] > 0 for r in res.values())
    # Two independent random scorers: the interval covers zero.
    res = paired_bootstrap(y, noise, rng.random(400), n_boot=500)
    assert res["pr_auc"]["lo"] < 0 < res["pr_auc"]["hi"]


def test_paired_csv_is_what_the_scores_give():
    paired = pd.read_csv(RUN / "paired.csv")
    scores = pd.read_csv(RUN / "scores.csv")
    some = scores[scores["plan_id"].isin(["cd_1956_canada_target_areas", "wp_1967_lato67"])]
    again = compare(some, ["population rule", MODEL], min_positives=2)
    keys = ["plan_id", "model", "metric"]
    merged = again.merge(paired, on=keys, suffixes=("", "_csv"))
    assert len(merged) == len(again) == 6
    for col in ["rule_value", "model_value", "diff", "lo", "hi"]:
        assert np.allclose(merged[col], merged[f"{col}_csv"], atol=1e-4), col
    lists = scores.groupby("plan_id")["listed"].sum()
    assert set(paired["plan_id"]) == set(lists[lists >= 2].index)


def test_transfer_card_quotes_pr_auc_and_precision_with_intervals():
    """Every row of TRANSFER.md's check table matches paired.csv, for PR-AUC, precision@k
    and ROC-AUC."""
    text = (CURATED / "gazetteer" / "TRANSFER.md").read_text(encoding="utf-8")
    section = text[text.index("## Check run") : text.index("## Caveats")]
    assert "PR-AUC difference [95% CI]" in section
    assert "Precision@k difference [95% CI]" in section
    paired = pd.read_csv(RUN / "paired.csv")
    paired = paired[paired["model"] == MODEL].set_index(["plan_id", "metric"])
    names = {
        "Canada target areas 1956": "cd_1956_canada_target_areas",
        "Operation Alert 1955 (full)": "cd_1955_operation_alert_full",
        "Target Committee 1945": "us_1945_target_committee",
        "Square Leg 1980": "cd_1980_square_leg",
        "Lato-67": "wp_1967_lato67",
        "NATO mirror, Poland 1962": "nato_1962_pl_exercise_mirror",
    }
    rows = {r.split("|")[1].strip(): r for r in section.splitlines() if r.startswith("| ")}
    for name, plan in names.items():
        cells = [c.strip() for c in rows[name].strip("|").split("|")]
        for i, metric in enumerate(["pr_auc", "precision_at_k", "roc_auc"]):
            r = paired.loc[(plan, metric)]
            assert cells[2 + 2 * i] == f"{r.rule_value:.2f} / {r.model_value:.2f}", (name, metric)
            want = f"{_signed(r['diff'])} [{_signed(r.lo)}, {_signed(r.hi)}]"
            assert cells[3 + 2 * i] == want, (name, metric)


def test_plan_claims_no_gain_the_intervals_do_not_show():
    text = (ROOT / "PLAN.md").read_text(encoding="utf-8")
    note = text[text.index("- **Transfer check**") :]
    note = note[: note.index("This is a check, not a result.")]
    assert "gain a little" not in note
    assert "adds nothing" not in note
    assert "PR-AUC" in note and "precision@k" in note
    paired = pd.read_csv(RUN / "paired.csv")
    paired = paired[paired["model"] == MODEL]
    quoted = {
        f"{_signed(d)} [{_signed(lo)}, {_signed(hi)}]"
        for d, lo, hi in zip(paired["diff"], paired["lo"], paired["hi"], strict=True)
    }
    found = INTERVAL.findall(note)
    assert len(found) >= 8
    for d, lo, hi in found:
        assert f"{d} [{lo}, {hi}]" in quoted
    # "No gain is detectable" on the mixed lists: every interval quoted there includes zero.
    mixed = note[note.index("mixed civil and military lists") :]
    assert "no gain is detectable" in mixed
    for _, lo, hi in INTERVAL.findall(mixed):
        assert float(lo) <= 0 <= float(hi)


def test_mixed_lists_show_no_detectable_gain():
    """TRANSFER.md says no gain is detectable on the mixed lists; paired.csv must agree."""
    text = (CURATED / "gazetteer" / "TRANSFER.md").read_text(encoding="utf-8")
    assert "No gain is detectable" in " ".join(text.split())
    paired = pd.read_csv(RUN / "paired.csv")
    mixed = [
        "cd_1980_square_leg",
        "wp_1967_lato67",
        "nato_1962_pl_exercise_mirror",
        "nato_1965_hu_wargame_mirror",
        "wp_1965_hu_wargame",
    ]
    rows = paired[(paired["model"] == MODEL) & paired["plan_id"].isin(mixed)]
    assert len(rows) == 15
    assert not rows["excludes_zero"].any()
