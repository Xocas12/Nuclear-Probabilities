"""The eighteenth amendment's bootstrap seed check (nucprob.classifier.seed_check): its resampling is the
protocol's, draw for draw; the committed summary covers every comparison of the primary table and is of the
committed scores; one of its seeds reproduces from those scores; REPORT and README say what it found."""

import json

import numpy as np
import pandas as pd

from nucprob.classifier import evaluate as ev
from nucprob.classifier import report
from nucprob.classifier import seed_check as sc
from nucprob.paths import ROOT
from nucprob.sources.fetch import sha256

OUT = report.OUT


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _synthetic(seed: int = 0, n: int = 600):
    rng = np.random.default_rng(seed)
    doc = rng.choice(np.array(["a", "b", "c", "d"]), size=n)
    y = rng.random(n) < np.where(doc == "a", 0.4, 0.1)
    y[doc == "d"] = False  # a list with no positives is not scored
    # Rounded scores, so that ties occur within lists.
    a = np.round(rng.random(n) + y * 0.3, 1)
    b = np.round(rng.random(n) + y * 0.2, 2)
    block = rng.integers(0, 12, size=n)
    return y.astype(int), a, b, doc, block


def test_the_fast_pr_auc_is_evaluate_s_with_ties_and_unscored_lists():
    for seed in range(5):
        y, a, b, doc, _ = _synthetic(seed)
        names, code = np.unique(doc, return_inverse=True)
        for s in (a, b):
            assert np.isclose(
                sc.fast_weighted_pr_auc(y, s, code, len(names)),
                ev.weighted_pr_auc(y, s, doc),
                rtol=0,
                atol=1e-12,
            )


def test_the_seed_check_draws_what_evaluate_draws():
    y, a, b, doc, block = _synthetic(7)
    for seed in (1956, 3):
        got = sc.bootstraps(y, a, b, doc, block, seed, n=200)
        town = ev.paired_bootstrap(y, a, b, doc, n=200, seed=seed)
        blocks = ev.block_bootstrap(y, a, b, doc, block, n=200, seed=seed)
        for k in ("low", "high"):
            assert np.isclose(got[k], town[k], rtol=0, atol=1e-12)
        for k in ("block_low", "block_high"):
            assert np.isclose(got[k], blocks[k], rtol=0, atol=1e-12)


def test_the_summary_covers_the_primary_table_and_is_of_the_committed_scores():
    manifest = json.loads((OUT / "seed_check_manifest.json").read_text())
    assert manifest["amendment"] == "configs/protocol_amendment_18.yaml"
    assert manifest["seeds"] == list(range(1, 21)) and manifest["bootstrap"] == ev.N_BOOT
    for path, digest in {**manifest["inputs"], **manifest["outputs"]}.items():
        assert sha256(ROOT / path) == digest, path
    comp = pd.read_csv(OUT / "comparison.csv")
    rows = sc.primary(comp, pd.read_csv(OUT / "selection.csv"))
    summary = pd.read_csv(OUT / "seed_check_summary.csv")
    per_seed = pd.read_csv(OUT / "seed_check.csv")
    assert len(summary) == len(rows) and len(per_seed) == 20 * len(rows)
    merged = rows.merge(summary, on=report.SEED_KEY, validate="one_to_one")
    assert len(merged) == len(rows)
    for _, r in merged.iterrows():
        assert r["verdict_seed_1956"] == report.verdict(r)
        counts = sum(int(r[f"seeds_{v.replace(' ', '_')}"]) for v in report.SEED_VERDICTS)
        assert counts == 20
        assert bool(r["seed_stable"]) == (
            int(r[f"seeds_{r['verdict_seed_1956'].replace(' ', '_')}"]) == 20
        )
    # Every comparison of REPORT's primary table, against both baselines, is in it.
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    assert len(summary) >= 2 * len(primary)


def test_one_seed_reproduces_from_the_held_out_scores():
    """The review's case: the pooled Warsaw Pact gain under spatial blocks, seed 6."""
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz")
    key = ("Warsaw Pact, pooled, exercise-based", "spatial blocks", "all lists")
    part = sc.part_of(scores, *key)
    got = sc.one(part, "LightGBM, all permitted", report.PLUS, 6)
    per_seed = pd.read_csv(OUT / "seed_check.csv")
    row = per_seed[
        (per_seed["scope"] == key[0])
        & (per_seed["holdout"] == key[1])
        & (per_seed["lists"] == key[2])
        & (per_seed["against"] == report.PLUS)
        & (per_seed["seed"] == 6)
    ].iloc[0]
    for k in ("low", "high", "block_low", "block_high"):
        assert abs(got[k] - row[k]) < 6e-5, k
    assert got["block_low"] < 0 and row["verdict"] == "neither"


def test_report_and_readme_say_what_the_check_found():
    rep, readme = _flat(ROOT / "REPORT.md"), _flat(ROOT / "README.md")
    assert " ".join(report.seed_section().split()) in rep
    summary = pd.read_csv(OUT / "seed_check_summary.csv")
    moved = summary[~summary["seed_stable"].astype(bool)]
    for r in moved.itertuples():
        counts = report.seed_counts(r._asdict())
        assert (
            f"| {report.SCOPES[r.scope]} | {report.HOLDOUTS[r.holdout]} | {r.lists} | {r.against} | "
            f"{r.verdict_seed_1956} | {counts} |" in rep
        )
        assert counts in readme
        # README groups the moved rows by scope and holdout; each row's list set and baseline is named.
        assert f"{r.lists} against {r.against}" in readme
    assert (
        f"{len(summary) - len(moved)} of {len(summary)} keep their verdict under all 20" in readme
    )
    assert "Seeds 1-20" in rep


def test_readme_answers_what_made_a_place_a_target():
    """The review of 736fdb5: README's first question had no feature-family answer."""
    readme = _flat(ROOT / "README.md")
    assert " ".join(report._readme_families().split()) in readme
    fam = report._families()
    for f, words in report.FAMILY_WORDS.items():
        cells = [
            report.family_cell(fam[(fam["rows"] == rows) & (fam["family"] == f)].iloc[0])
            for rows in ("all countries", "USSR")
        ]
        assert f"| {words} | {cells[0]} | {cells[1]} |" in readme, f
    for r in fam[fam["verdict"] == "gain"].itertuples():
        assert report.interval(r._asdict()) in readme
