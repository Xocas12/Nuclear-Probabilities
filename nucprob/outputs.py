"""What a run records about itself: the commit, whether the code it ran had uncommitted changes, and
the hash of every file it wrote. tests/test_committed_outputs.py compares those hashes with the
committed files, so a figure edited by hand, or left over from an earlier run, fails a test.
"""

import hashlib
import json
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


# Earlier checks whose manifests record no hashes. runs/milestone_hashes.json holds them instead, so
# that a figure edited by hand fails tests/test_holdouts_bite.py.
MILESTONES = ("m1-slice", "m2-check", "m4-transfer-check", "m4-us-check")


# Written by a run about when and from which commit it ran. A rebuild by the README's commands changes
# them and nothing else, so the pin reads every other field of a manifest.
RUN_STAMPS = ("created", "git_commit", "git_dirty")


def manifest_hash(path: Path) -> str:
    """sha256 of a manifest's JSON with its run stamps removed, keys sorted."""
    record = json.loads(Path(path).read_text())
    kept = {k: v for k, v in record.items() if k not in RUN_STAMPS}
    return hashlib.sha256(json.dumps(kept, sort_keys=True).encode()).hexdigest()


def milestone_hashes() -> dict[str, str]:
    """Data files by their bytes; manifests by `manifest_hash`."""
    files = [
        f
        for folder in MILESTONES
        for f in sorted((ROOT / "runs" / folder).iterdir())
        if f.suffix in (".csv", ".json")
    ]
    out = hashes(f for f in files if f.name != "manifest.json")
    for f in files:
        if f.name == "manifest.json":
            out[str(f.resolve().relative_to(ROOT.resolve()))] = manifest_hash(f)
    return dict(sorted(out.items()))
