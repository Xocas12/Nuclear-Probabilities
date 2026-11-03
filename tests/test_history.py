"""Tables kept out of the working tree under section E but read by a pinned run come back from git
history unchanged (nucprob.sources.history)."""

import dataclasses
import hashlib
import subprocess

import pandas as pd
import pytest

from nucprob.paths import ROOT
from nucprob.sources import history


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return [p for p in out.stdout.decode().split("\0") if p]


def have(commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", commit], cwd=ROOT).returncode == 0


@pytest.mark.parametrize("pinned", history.PINNED, ids=lambda p: p.path)
def test_a_pinned_table_is_not_in_the_tree_under_its_path_or_its_bytes(pinned):
    files = tracked()
    assert pinned.path not in files
    hashes = {
        hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
        for f in files
        if f.endswith(".csv") and (ROOT / f).is_file()
    }
    assert pinned.sha256 not in hashes


@pytest.mark.parametrize("pinned", history.PINNED, ids=lambda p: p.path)
def test_a_pinned_table_comes_back_with_the_hash_its_card_states(pinned):
    if not have(pinned.commit):
        pytest.skip("shallow clone without the pinned commit")
    path = history.restore(pinned)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == pinned.sha256
    ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=ROOT).returncode == 0
    assert ignored, "the restored copy must be ignored by git"


def test_the_us_site_table_is_the_one_the_check_was_run_on():
    p = history.US_MILITARY_SITES_1985
    if not have(p.commit):
        pytest.skip("shallow clone without the pinned commit")
    s = pd.read_csv(history.restore(p))
    assert len(s) == 196 and s["in_role_1985"].sum() == 184


def test_a_wrong_hash_is_refused_and_nothing_is_written(tmp_path, monkeypatch):
    p = history.US_MILITARY_SITES_1985
    if not have(p.commit):
        pytest.skip("shallow clone without the pinned commit")
    monkeypatch.setattr(history, "DATA", tmp_path)
    wrong = dataclasses.replace(p, sha256="0" * 64)
    with pytest.raises(history.HistoryError, match="expected"):
        history.restore(wrong)
    assert not wrong.local.exists()
