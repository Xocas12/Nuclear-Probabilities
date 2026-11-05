"""`make test-full` must not pass a skipped test: tests/conftest.py turns skips into failures under NUCPROB_NO_SKIP=1."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFTEST = (ROOT / "tests" / "conftest.py").read_text()
SAMPLE = """
import pytest

def test_skips():
    pytest.skip("no built tables")

@pytest.mark.skipif(True, reason="absent")
def test_marked():
    pass

@pytest.mark.xfail(reason="known")
def test_xfail():
    assert False

def test_passes():
    pass
"""


def run(tmp_path: Path, no_skip: str | None) -> str:
    (tmp_path / "conftest.py").write_text(CONFTEST)
    (tmp_path / "test_sample.py").write_text(SAMPLE)
    env = {"PATH": "/usr/bin:/bin"}
    if no_skip is not None:
        env["NUCPROB_NO_SKIP"] = no_skip
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", str(tmp_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize("value", [None, "0"])
def test_a_plain_run_still_skips(tmp_path, value):
    assert run(tmp_path, value).startswith("1 passed, 2 skipped, 1 xfailed")


def test_a_full_run_fails_on_every_skip_but_not_on_xfail(tmp_path):
    # a skip inside the test fails it; a skipif mark skips in setup, which is then reported as an error
    assert run(tmp_path, "1").startswith("1 failed, 1 passed, 1 xfailed, 1 error")


def test_make_test_full_sets_the_flag_and_builds_the_tables():
    make = (ROOT / "Makefile").read_text()
    body = make.split("\ntest-full:")[1].split("\n\n")[0]
    assert "NUCPROB_NO_SKIP=1" in body
    for target in ("places", "labels", "features", "dataset", "transfer"):
        assert target in body.splitlines()[0]
    assert "nucprob.classifier.table" in body
