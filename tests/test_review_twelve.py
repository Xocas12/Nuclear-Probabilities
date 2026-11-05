"""Checks for the twelfth review's findings (partial review of 9177bae): each reads the output a sentence
rests on, so a wrong count or a misstated rule fails, not only a changed word."""

import pandas as pd
import pytest
import yaml

from nucprob.classifier.divergence import MAX_RAW
from nucprob.classifier.identification_fit import DIVERGED_DROP
from nucprob.paths import CURATED, ROOT, RUNS
from nucprob.probmap.run import load_scenarios
from nucprob.probmap.viewer import shift_label

IDENT = RUNS / "classifier" / "identification" / "divergence.csv"
MAP = RUNS / "probmap"
needs_ident = pytest.mark.skipif(not IDENT.exists(), reason="no identification fit run")
needs_map = pytest.mark.skipif(not (MAP / "domain_shift.csv").exists(), reason="no map run")


def _text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_identification_divergence_flag_is_the_fourteenth_amendments_rule():
    """configs/protocol_amendment_14.yaml: diverged = final training accuracy more than 0.05 below its best."""
    amendment = yaml.safe_load((ROOT / "configs" / "protocol_amendment_14.yaml").read_text())
    assert "more than 0.05 below its best" in " ".join(str(amendment).split())
    assert DIVERGED_DROP == 0.05


@needs_ident
def test_the_identification_flags_in_the_file_follow_that_rule():
    fits = pd.read_csv(IDENT)
    recomputed = fits["train_accuracy_best"] - fits["train_accuracy_final"] > DIVERGED_DROP
    assert (recomputed == fits["diverged"].astype(bool)).all()


@needs_ident
def test_report_states_the_identification_rule_and_both_counts():
    """REPORT gave 8 of 16 without saying which rule; under the primary models' raw-score rule it is 9."""
    fits = pd.read_csv(IDENT)
    as_run = fits[fits["l2_regularization"] == 0]
    by_drop = int(as_run["diverged"].sum())
    by_raw = int((as_run["max_abs_raw_score"] > MAX_RAW).sum())
    text = _text(ROOT / "REPORT.md")
    assert f"{by_drop} of its {len(as_run)} fits (four column sets, four folds) diverged" in text
    assert f"{100 * DIVERGED_DROP:.0f} points below its best" in text
    if by_raw != by_drop:
        assert (
            f"raw score above {MAX_RAW:.0f}, {by_raw} of the {len(as_run)} would be called diverged"
            in text
        )
        extra = as_run[(as_run["max_abs_raw_score"] > MAX_RAW) & ~as_run["diverged"].astype(bool)]
        for r in extra.itertuples():
            assert f'"{r.columns}" fold {r.fold} (raw score {r.max_abs_raw_score:,.0f}' in text


@needs_map
def test_report_gives_the_domain_shift_town_counts_of_the_file():
    """The 6,091 kept modern towns and the 2,276 the shift is measured on were never reconciled."""
    shift = pd.read_csv(MAP / "domain_shift.csv")
    two = shift[shift["measure"] == "two-sample ROC-AUC"].iloc[0]
    kept = int(pd.read_csv(MAP / "modern_universe.csv")["places"].iloc[-1])
    assert int(two["towns_b"]) < kept
    text = _text(ROOT / "REPORT.md")
    assert (
        f"the {int(two['towns_a']):,} training towns from the {int(two['towns_b']):,} modern towns in the "
        f"countries the modern scenarios target (of the {kept:,} kept worldwide)"
    ) in text


def test_only_a_scenario_whose_attacker_has_a_list_of_its_year_is_called_historical():
    """viewer.py claimed "Historical" meant a score fitted on the attacker's own list; it means the stockpile
    and a training list of the attacker are of that year. The score is fitted on all documents."""
    plans = yaml.safe_load((CURATED / "labels" / "PLANS.yaml").read_text())["plans"]
    lists = {(p["attacker"], int(str(p["date"])[:4])) for p in plans if p.get("role") == "train"}
    for sc in load_scenarios():
        if shift_label(sc) != "Historical":
            continue
        for a in sc["attackers"]:
            assert a["stock_year"] == sc["year"]
            assert (a["state"], sc["year"]) in lists, sc["id"]


def test_the_viewer_says_the_score_is_fitted_on_all_documents():
    page = _text(MAP / "viewer" / "index.html")
    assert "fitted on all attacker documents together, exercises included" in page
    assert "fitted on all attacker documents, exercises included" in _text(ROOT / "REPORT.md")
