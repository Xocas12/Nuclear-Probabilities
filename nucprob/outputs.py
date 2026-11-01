"""What a run records about itself: the commit, whether the code it ran had uncommitted changes, and
the hash of every file it wrote. tests/test_committed_outputs.py compares those hashes with the
committed files, so a figure edited by hand, or left over from an earlier run, fails a test.
"""

import subprocess
from collections.abc import Iterable
from pathlib import Path

from nucprob.model.cv import git_commit
from nucprob.paths import ROOT
from nucprob.sources.fetch import sha256

# Code and inputs whose uncommitted change would make a run's commit a false statement. Outputs under
# runs/ are not here: a chain of runs writes them as it goes.
TRACKED = ["nucprob", "configs", "data/curated", "data/sources.yaml", "pyproject.toml", "uv.lock"]


def git_dirty() -> bool:
    """True if the code or inputs differ from the commit, or if git cannot say."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", *TRACKED],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return True
    return bool(out.strip())


def start_record() -> dict:
    """Taken when a run starts: modules are read then, so the commit at the end may not be the code."""
    return {"git_commit": git_commit(), "git_dirty": git_dirty()}


def hashes(files: Iterable[Path]) -> dict[str, str]:
    return {str(Path(f).resolve().relative_to(ROOT.resolve())): sha256(f) for f in sorted(files)}
