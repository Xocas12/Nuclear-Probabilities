"""The build runs every step whose output REPORT reads; the feature registry names inputs later than the document
that are not flagged; README's population figures are the population rule's; the map's intervals are called what
they are; the viewer says what a cell's probability is of and who fires on whom; and the notes and cards speak of
their own sources, not of instructions held outside the repository."""

import re

import pandas as pd

from nucprob.classifier import report
from nucprob.features.registry import FEATURES
from nucprob.paths import ROOT
from nucprob.probmap.run import load_scenarios

MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _target(name: str) -> str:
    """The recipe lines of one Makefile target."""
    m = re.search(rf"^{name}:.*\n((?:\t.*\n)+)", MAKEFILE, re.M)
    assert m, name
    return m.group(1)


def test_make_classifier_runs_every_step_whose_output_report_reads():
    recipe = _target("classifier")
    for module in ("run", "seed_check", "sensitivity", "extended", "defence_targets"):
        assert f"-m nucprob.classifier.{module}\n" in recipe, module
    # the seed check reads the held-out scores the run writes
    assert recipe.index("classifier.run\n") < recipe.index("classifier.seed_check\n")


def test_census_columns_name_the_1959_census_as_later_and_are_not_flagged():
    for name in ("log_pop", "pop_rank_pct", "log_pop_within_50km"):
        f = FEATURES[name]
        assert "1959" in f.later and not f.anachronism, name
    # a column flagged as today's data is a different thing from a later census
    assert all(not f.later for f in FEATURES.values() if f.anachronism)
    catalogue = (ROOT / "data" / "FEATURES.md").read_text(encoding="utf-8")
    assert "| Anachronism | Later | Note |" in catalogue
    assert "USSR 1959 census; some other countries' censuses of 1958-1961" in catalogue


def test_readme_population_figures_are_the_population_rule_of_comparison_csv():
    comp = pd.read_csv(report.OUT / "comparison.csv")
    sac = comp[(comp["scope"] == report.SAC_SCOPE) & (comp["holdout"] == "spatial blocks")]
    rule = sac[sac["against"] == report.RULE]["b_pr_auc"].unique()
    assert len(rule) == 1  # one population rule, whatever model it is set against
    readme = _flat(ROOT / "README.md")
    assert f"(the population rule) gives a PR-AUC of {rule[0]:.2f}" in readme
    # the fitted LightGBM base of the family table is named as such, not as the population rule
    assert "That fit is not the population rule" in readme
    assert "Ranking towns by population alone gives a PR-AUC" not in readme


def test_the_map_intervals_are_called_5th_to_95th_percentiles_not_95_percent():
    readme = _flat(ROOT / "README.md")
    assert "Each interval is 95%" not in readme
    assert "The map's intervals are the 5th to 95th percentiles of its draws (90%)" in readme
    rep = _flat(ROOT / "REPORT.md")
    assert (
        'the map\'s (section "Probability map") are the 5th to 95th percentiles of its draws, so 90%'
        in rep
    )


def test_report_lines_are_wrapped():
    for line in (ROOT / "REPORT.md").read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            assert len(line) <= 130, line[:80]


def test_the_viewer_says_what_a_cells_probability_is_of():
    page = (ROOT / "runs" / "probmap" / "viewer" / "index.html").read_text(encoding="utf-8")
    assert "probability that at least one delivered warhead falls on a town in that cell" in page


def test_every_modern_label_says_who_fires_on_whom():
    for sc in load_scenarios():
        if sc["era"] != "modern" or sc["label"].startswith("2026: the same"):
            continue
        attackers = {a["state"] for a in sc["attackers"]}
        assert " on " in sc["label"], sc["id"]
        assert " with " not in sc["label"] and " and China" not in sc["label"], sc["id"]
        for state in attackers:
            assert state.split()[0] in sc["label"] or (state == "US" and "the US" in sc["label"]), (
                sc["id"],
                state,
            )


def test_a_zero_low_inventory_is_explained_beside_delivered_percentiles_above_zero():
    sc = next(s for s in load_scenarios() if s["id"] == "modern_india_pakistan")
    note = " ".join(sc["note"].split())
    assert "drawn from zero to its whole stockpile" in note
    assert "the 5th percentile of warheads delivered is therefore above zero" in note
    delivered = pd.read_csv(ROOT / "runs" / "probmap" / "delivered.csv")
    rows = delivered[delivered["scenario"] == "modern_india_pakistan"]
    assert (rows["delivered_low"] > 0).all()


def test_notes_and_cards_cite_no_instructions_outside_the_repository():
    for path in (ROOT / "data").rglob("*.md"):
        if "raw" in path.relative_to(ROOT / "data").parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert "owner's instructions" not in text, path
        assert "section E of the brief" not in text, path
    # data cards (not the dated search logs under data/notes/) are not in the first person
    for path in (ROOT / "data" / "curated").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        first_person = (
            r"\bI (?:classified|scanned|did|read|know|expect|found|think|checked|could)\b|\bmy\b"
        )
        assert not re.search(first_person, text), path


def test_the_issues_page_states_where_things_stand():
    text = _flat(ROOT / "data" / "ISSUES.md")
    assert "stay until the owner decides" not in text
    assert "not answered" not in text
    assert "a file held by the owner" not in text
    assert "No held file came from a disallowed path" in text
