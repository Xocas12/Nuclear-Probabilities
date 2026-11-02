"""Committed results are what the runs wrote. A figure edited by hand, in a table or in a document,
fails here: tables through the hash each run recorded, documents through their regeneration."""

import json
import subprocess

import pandas as pd
import pytest

from nucprob.classifier import report
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.plans import protocol
from nucprob.probmap import viewer
from nucprob.sources.fetch import sha256

CLASSIFIER = RUNS / "classifier"
MAP = RUNS / "probmap"
MANIFESTS = [
    CLASSIFIER / "manifest.json",
    CLASSIFIER / "sensitivity_manifest.json",
    CLASSIFIER / "extended_manifest.json",
    CLASSIFIER / "defence_targets_manifest.json",
    CLASSIFIER / "link_audit_manifest.json",
    RUNS / "evidence" / "manifest.json",
    MAP / "manifest.json",
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
    for folder in (CLASSIFIER, MAP, MAP / "cells", RUNS / "evidence"):
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
        ("uk_military_sites_1980.md", "uk_military_sites_1980.csv"),
        ("us_military_sites_1985.md", "us_military_sites_1985.csv"),
        ("weurope_military_sites_1965.md", "weurope_military_sites_1965.csv"),
        ("README.md", "military_sites_1956.csv"),
    ],
)
def test_each_site_table_card_gives_the_table_hash_and_points_to_its_licences(card, table):
    folder = ROOT / "data" / "curated" / "features"
    text = (folder / card).read_text(encoding="utf-8")
    assert sha256(folder / table) in text
    assert "cited_pages.csv" in text
    pages = pd.read_csv(folder / "cited_pages.csv", dtype=str, keep_default_na=False)
    assert pages["licence"].str.len().min() > 0


def test_the_sealed_sizes_in_the_report_are_those_of_the_table():
    path = PROCESSED / "dataset_sac1956.parquet"
    if not path.exists():
        pytest.skip("no built tables")
    d = pd.read_parquet(path, columns=["sealed", "never_scored"])
    assert (int(d["sealed"].sum()), int(d["never_scored"].sum())) == (467, 273)
