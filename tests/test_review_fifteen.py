"""Checks for the review of fac1986: README's reading on lists other than SAC's says what its positives are and that
its gain follows an amendment written after a rescoring was seen; every protocol file parses as YAML, and the twelfth
amendment's syntax repair kept every word of the file as committed at ae1bbb6."""

import subprocess

import pandas as pd
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
