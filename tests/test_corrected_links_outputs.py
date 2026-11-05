"""The refit on the corrected Warsaw Pact links (configs/protocol_amendment_17.yaml): the outputs are of the corrected
table, README and REPORT no longer say the refit is pending, the "Changed by" paragraph lists every moved row, and the
transfer card's link counts are those of the rebuilt links."""

import json
import re

import pandas as pd
import pytest

from nucprob.classifier import report
from nucprob.paths import CURATED, PROCESSED, ROOT

LINKS = PROCESSED / "transfer_links.csv"


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_committed_outputs_are_of_the_corrected_links():
    for manifest in (
        report.OUT / "manifest.json",
        ROOT / "runs" / "probmap" / "manifest.json",
    ):
        assert json.loads(manifest.read_text())["table_sha256"] != report.TABLE_BEFORE_17, manifest
    readme, rep = _flat(ROOT / "README.md"), _flat(ROOT / "REPORT.md")
    assert "not yet committed" not in readme
    assert "Known link errors in these results." not in rep
    history = (ROOT / "configs" / "HISTORY.md").read_text(encoding="utf-8").splitlines()
    row = [line for line in history if line.startswith("| 17 |")]
    assert len(row) == 1 and "pending" not in row[0]


def test_the_corrections_section_lists_every_row_the_seventeenth_amendment_moved():
    # The run after the seventeenth amendment: kept in before_amendment_19/ once the nineteenth refits.
    after = report.BEFORE_19 if (report.BEFORE_19 / "comparison.csv").exists() else report.OUT
    sel_now = pd.read_csv(after / "selection.csv")
    sel_was = pd.read_csv(report.BEFORE_17 / "selection.csv")
    now = report.primary_table(pd.read_csv(after / "comparison.csv"), sel_now)
    was = report.primary_table(pd.read_csv(report.BEFORE_17 / "comparison.csv"), sel_was)
    both = now.merge(was, on=["Scope", "Holdout", "Lists"], suffixes=("", "_was"))
    moved = both[both["Verdict"] != both["Verdict_was"]]
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    section = text[text.index("### Corrections made after results were read") :]
    section = section[: section.index("\n### ", 5)]
    # each bullet of the seventeenth amendment with its wrapped continuation lines
    bullets = [
        " ".join(part.split("\n\n")[0].split())
        for part in re.split(r"\n(?=- )", section)
        if part.startswith("- Amendment 17:")
    ]
    assert len(bullets) == len(moved)
    flat = " ".join(section.split())
    assert re.search(rf"\| 17 \|[^|]*\| {len(moved)} of {len(both)} \|", flat)
    for _, r in moved.iterrows():
        assert any(
            r["Scope"] in b
            and r["Lists"] in b
            and f"{r['Verdict']} after ({r['Difference, country']}, by blocks {r['By blocks']})"
            in b
            for b in bullets
        ), (r["Scope"], r["Holdout"], r["Lists"])


def test_readme_reports_the_spatial_reading_on_lists_other_than_sac():
    comp = pd.read_csv(report.OUT / "comparison.csv")
    best = report._best(pd.read_csv(report.OUT / "selection.csv"), report.GLOBAL_ALL)
    r = report._row(
        comp, report.GLOBAL_ALL, "spatial blocks", best, report.PLUS, "lists other than SAC"
    )
    readme = _flat(ROOT / "README.md")
    want = (
        f"against population plus country is {report.interval(r)}, by blocks {report.block_interval(r)}: "
        f"{report.claim(r)}."
    )
    assert want in readme
    assert "this is not a reading on an unseen document" in readme


def test_the_transfer_cards_link_table_counts_the_rebuilt_links():
    """Targets, located and linked columns of TRANSFER.md's link table against transfer_links.csv."""
    if not LINKS.exists():
        pytest.skip("data/processed/transfer_links.csv not built (make test-full builds it)")
    from tests.test_transfer_paired import CARD_LISTS

    links = pd.read_csv(LINKS)
    counts = links.groupby("plan_id").agg(
        n=("seq", "size"), located=("lat", "count"), linked=("place_id", "count")
    )
    card = (CURATED / "gazetteer" / "TRANSFER.md").read_text(encoding="utf-8")
    for label, plan in CARD_LISTS.items():
        row = re.search(rf"^\| {re.escape(label)} \| (\d+) \| (\d+) \| (\d+) \|", card, re.M)
        assert row, label
        got = tuple(int(row.group(i)) for i in (1, 2, 3))
        assert got == tuple(int(x) for x in counts.loc[plan]), label
