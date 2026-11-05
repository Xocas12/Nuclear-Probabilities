"""Checks for the review of fac1986: README's reading on lists other than SAC's says what its positives are and that
its gain follows an amendment written after a rescoring was seen; every protocol file parses as YAML, and the twelfth
amendment's syntax repair kept every word of the file as committed at ae1bbb6."""

import subprocess

import pandas as pd
import pytest
import yaml

from nucprob.classifier import report
from nucprob.paths import ROOT

CONFIGS = ROOT / "configs"


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_every_protocol_file_is_valid_yaml():
    files = sorted(CONFIGS.glob("protocol*.yaml"))
    assert len(files) >= 13
    for f in files:
        assert isinstance(yaml.safe_load(f.read_text(encoding="utf-8")), dict), f


def _words(obj) -> list[str]:
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out += [str(k), *_words(v)]
        return out
    return str(obj).split()


def test_the_twelfth_amendment_keeps_its_committed_words():
    committed = subprocess.run(
        ["git", "show", "ae1bbb6:configs/protocol_amendment_12.yaml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # a colon ends a key in the parsed file and is text in the committed one, so both sides drop trailing colons
    body = " ".join(line.strip() for line in committed.splitlines() if not line.startswith("#"))
    was = [w.rstrip(":") for w in body.split()]
    now = yaml.safe_load((CONFIGS / "protocol_amendment_12.yaml").read_text(encoding="utf-8"))
    assert [w.rstrip(":") for w in _words(now)] == was


def test_readme_says_what_the_other_lists_gain_rests_on():
    lists = pd.read_csv(report.OUT / "lists.csv")
    rows = lists[
        (lists["scope"] == report.GLOBAL_ALL)
        & (lists["holdout"] == "spatial blocks")
        & (lists["model"] == report.RULE)
        & (lists["plan_id"] != "us_1956_sac_complexes")
    ]
    by_type = rows.groupby("doc_type")["positives"].sum()
    not_plan = int(by_type[by_type.index.isin(list(report.NOT_PLAN_TYPES))].sum())
    readme = _flat(ROOT / "README.md")
    start = readme.index("**On lists other than SAC's**")
    bullet = readme[start : readme.index("**On a document the model has not seen**")]
    assert (
        f"Of its {int(by_type.sum())} positives, {not_plan} come from Warsaw Pact exercises"
        in bullet
    )
    assert (
        f"{int(by_type.get('war_plan', 0))} come from documents registered as war plans" in bullet
    )
    assert "(exercises included)" in bullet
    # every non-plan type that has positives is named with its count
    for t, words in report.NOT_PLAN_TYPES.items():
        if by_type.get(t, 0):
            assert f"{words} ({int(by_type[t])})" in bullet


def test_a_verdict_moved_by_the_seventeenth_amendment_is_flagged_as_after_the_fact():
    sel = pd.read_csv(report.OUT / "selection.csv")
    model = report._best(sel, report.GLOBAL_ALL)
    args = (report.GLOBAL_ALL, "spatial blocks", model, report.PLUS, "lists other than SAC")
    now = report._row(pd.read_csv(report.OUT / "comparison.csv"), *args)
    was = report._row(pd.read_csv(report.BEFORE_17 / "comparison.csv"), *args)
    readme = _flat(ROOT / "README.md")
    flagged = "so the change is not of a reading fixed before its result was seen" in readme
    assert flagged == (report.verdict(now) != report.verdict(was))
    assert "a verdict it moves is not of a reading fixed before its result was seen" in _flat(
        ROOT / "REPORT.md"
    )


@pytest.mark.skipif(
    not (ROOT / "data" / "processed" / "classifier_table.parquet").exists(),
    reason="classifier table not built (make test-full builds it)",
)
def test_lato67_row_46_is_placed_at_its_printed_offset():
    """Row 46 prints "south of Store Heddinge" (no distance) and "20 km SE of Køge": the point is the latter."""
    from nucprob.geo import haversine_km

    links = pd.read_csv(ROOT / "data" / "curated" / "gazetteer" / "transfer_target_links.csv")
    row = links[(links["plan_id"] == "wp_1967_lato67") & (links["seq"] == 46)].iloc[0]
    assert row["located_as"] == "20 km SE of Køge"
    table = pd.read_parquet(
        ROOT / "data" / "processed" / "classifier_table.parquet", columns=["name", "lat", "lon"]
    )
    koge = table[table["name"] == "Køge"].iloc[0]
    assert abs(float(haversine_km(row["lat"], row["lon"], koge["lat"], koge["lon"])) - 20) < 0.05
    assert row["lat"] < koge["lat"] and row["lon"] > koge["lon"]  # south-east


def test_the_row_48_boundary_case_touches_only_a_column_no_model_reads():
    card = _flat(ROOT / "data" / "curated" / "gazetteer" / "README.md")
    assert "Lato-67 row 48" in card and "15.0024 km" in card
    for path in [
        *(ROOT / "nucprob" / "classifier").glob("*.py"),
        *(ROOT / "nucprob" / "probmap").glob("*.py"),
    ]:
        if path.name != "table.py":
            assert "n_targets" not in path.read_text(encoding="utf-8"), path
    assert "n_targets" not in (CONFIGS / "protocol.yaml").read_text(encoding="utf-8")


def test_late_population_inputs_are_disclosed():
    readme, rep = _flat(ROOT / "README.md"), _flat(ROOT / "REPORT.md")
    for text in (readme, rep):
        assert "end-1956" in text and "1958" in text
    assert "chosen by later size" in rep
    assert "towns chosen by their size today" in readme
    assert "scripts/us_military_1985_spec.py" in readme
