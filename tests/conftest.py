"""Suite-wide settings.

Some tests check committed outputs against tables built from data/raw/ (data/processed/ is git-ignored), and skip
when those tables are absent, so a plain `make test` on a fresh checkout is a partial run. `make test-full` builds
the tables first and sets NUCPROB_NO_SKIP=1, under which any skip is reported as a failure.
"""

import os

import pytest

NO_SKIP = os.environ.get("NUCPROB_NO_SKIP") == "1"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if NO_SKIP and rep.skipped and not hasattr(rep, "wasxfail"):
        rep.outcome = "failed"
        rep.longrepr = f"skipped under NUCPROB_NO_SKIP=1 (make test-full): {rep.longrepr}"
