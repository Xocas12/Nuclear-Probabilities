"""Committed results are what the runs wrote. A figure edited by hand, in a table or in a document,
fails here: tables through the hash each run recorded, documents through their regeneration."""

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from nucprob.classifier import report
from nucprob.paths import CURATED, PROCESSED, ROOT, RUNS
from nucprob.plans import protocol
from nucprob.probmap import viewer
from nucprob.sources import history
from nucprob.sources.fetch import sha256

CLASSIFIER = RUNS / "classifier"
MAP = RUNS / "probmap"
MANIFESTS = [
    CLASSIFIER / "manifest.json",
    CLASSIFIER / "sensitivity_manifest.json",
    CLASSIFIER / "extended_manifest.json",
    CLASSIFIER / "defence_targets_manifest.json",
    CLASSIFIER / "link_audit_manifest.json",
    CLASSIFIER / "seed_check_manifest.json",
    RUNS / "evidence" / "manifest.json",
    MAP / "manifest.json",
    CLASSIFIER / "sealed" / "blind" / "manifest.json",
    CLASSIFIER / "identification" / "manifest.json",
    CLASSIFIER / "identification" / "fit_manifest.json",
]
needs_run = pytest.mark.skipif(not (MAP / "manifest.json").exists(), reason="no committed run")


@needs_run
@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.name)
def test_every_output_is_the_file_its_run_wrote(path):
    outputs = json.loads(path.read_text())["outputs"]
    assert outputs
    for name, digest in outputs.items():
        assert sha256(ROOT / name) == digest, name


@needs_run
def test_no_table_stands_outside_a_manifest():
    listed = set()
    for path in MANIFESTS:
        listed |= set(json.loads(path.read_text())["outputs"])
    for folder in (
        CLASSIFIER,
        MAP,
        MAP / "cells",
        RUNS / "evidence",
        CLASSIFIER / "sealed" / "blind",
        CLASSIFIER / "identification",
    ):
        for f in [*folder.glob("*.csv"), *folder.glob("*.csv.gz")]:
            assert str(f.relative_to(ROOT)) in listed, f


@needs_run
@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.name)
def test_each_run_names_a_clean_commit_in_this_history(path):
    m = json.loads(path.read_text())
    assert m["git_dirty"] is False
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", m["git_commit"], "HEAD"], cwd=ROOT
    )
    if ancestor.returncode == 128:
        pytest.skip("this clone does not hold the commit (a shallow clone or no git)")
    assert ancestor.returncode == 0, m["git_commit"]


@needs_run
def test_the_viewer_is_a_regeneration_of_the_committed_map():
    page = MAP / "viewer" / "index.html"
    assert page.read_text(encoding="utf-8") == viewer.render()


@needs_run
def test_the_readme_results_are_a_regeneration_of_the_outputs():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text == report.with_readme_results(text)


@needs_run
def test_the_state_gate_still_refuses_what_it_refused():
    """What the classifier run committed: refusals, each with the counts the rule reads put through the rule
    again (tests/test_holdouts_bite.py does the same for runs/evidence/), and the same rows as the evidence run."""
    g = pd.read_csv(CLASSIFIER / "state_gate.csv").set_index("attacker")
    assert not g.loc[["US", "USSR", "Poland", "Czechoslovakia"], "allowed"].any()
    rule = protocol()["state_models"]
    for attacker, row in g.iterrows():
        if attacker.startswith("Warsaw Pact"):
            continue
        assert row["allowed"] == (
            row["independent_plans"] >= rule["min_independent_plans"]
            and row["linked_positives"] >= rule["min_positives"]
            and row["positives_outside_largest"] >= rule["min_positives_outside_largest"]
        ), attacker
    evidence = pd.read_csv(RUNS / "evidence" / "state_model_gate.csv").set_index("attacker")
    shared = g.index.intersection(evidence.index)
    assert len(shared) >= 4
    pd.testing.assert_frame_equal(g.loc[shared], evidence.loc[shared], check_dtype=False)


@pytest.mark.parametrize(
    "card, table",
    [
        ("bloc_air_defence_1956.md", "bloc_air_defence_1956.csv"),
        ("us_military_sites_1985.md", "us_military_sites_1985.csv"),
        ("weurope_military_sites_1965.md", "weurope_military_sites_1965.csv"),
        ("README.md", "military_sites_1956.csv"),
    ],
)
def test_each_site_table_card_gives_the_table_hash_and_points_to_its_licences(card, table):
    folder = ROOT / "data" / "curated" / "features"
    text = (folder / card).read_text(encoding="utf-8")
    pinned = {Path(p.path).name: p for p in history.PINNED}
    path = history.restore(pinned[table]) if table in pinned else folder / table
    assert sha256(path) in text
    assert "cited_pages.csv" in text
    pages = pd.read_csv(folder / "cited_pages.csv", dtype=str, keep_default_na=False)
    assert pages["licence"].str.len().min() > 0


def test_the_sealed_sizes_in_the_report_are_those_of_the_table():
    path = PROCESSED / "dataset_sac1956.parquet"
    if not path.exists():
        pytest.skip("no built tables")
    d = pd.read_parquet(path, columns=["place_id", "sealed", "never_scored"])
    assert (int(d["sealed"].sum()), int(d["never_scored"].sum())) == (467, 273)
    # The review of c27c1b8: the report's hard-coded sealed counts are checked here.
    assert int(d["sealed"].sum()) == report.SEALED_PLACES
    assert int(d["never_scored"].sum()) == report.AMENDMENT_11_SET
    # The early check's places are matched by name and country, not id (Kirovsk), so one of the 194
    # has no id of its own in scored_before_freeze.csv: the count is of sealed places not in the set.
    assert int((d["sealed"] & ~d["never_scored"]).sum()) == report.EARLY_SCORED
    early = set(pd.read_csv(CURATED / "splits" / "scored_before_freeze.csv")["place_id"])
    assert int(d.loc[d["sealed"], "place_id"].isin(early).sum()) == report.EARLY_SCORED - 1


def test_the_report_figures_from_data_cards_are_those_of_the_cards():
    """The review of c27c1b8 (trivia 15): figures the report takes from a card or a curated table, not from a
    run, are computed from that file or checked against its text here."""
    aud = report._audit()
    card = " ".join((CURATED / "sac1956" / "README.md").read_text(encoding="utf-8").split())
    assert f"{aud['wrong']} of {aud['lines']}, 95% interval 0 to {100 * aud['upper']:.2f}%" in card
    audit = pd.read_csv(CURATED / "sac1956" / "audit.csv")
    auditors = 100 * (audit["outcome"] == "curated right").sum() / len(audit)
    verdicts = pd.read_csv(
        ROOT / "data" / "interim" / "sac1956_excerpts" / "crossdoc" / "decisions.tsv",
        sep="\t",
        header=None,
    )[5]
    part2 = int((verdicts == "part2 misread").sum())
    assert f"own error rate was {auditors:.1f}%" in card
    assert f"{part2} in 216" in card and "216 of the 270 rows" in card
    assert f"The two transcriptions differ on {len(verdicts)} rows" in card
    nrdc, owid = report._stockpile_1950_us()
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    assert f"{nrdc} loaded, more than the {owid} Our World in Data (OWID) gives" in text
    assert f"{aud['lines']} lines, found {aud['wrong']} errors" in text
    assert f"auditors whose own error rate was {auditors:.1f}%" in text
    assert f"rate was {part2} in 216" in text
