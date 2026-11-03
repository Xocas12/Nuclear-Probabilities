"""Tables that left the working tree but that a pinned run still reads, restored from git history.

    python -m nucprob.sources.history

`data/curated/features/us_military_sites_1985.csv` lists US military installations as of mid-1985
with coordinates; 125 of its 196 rows have no end year, so most are present-day facilities. The
brief's section E keeps such coordinates out of the committed tree. The table feeds only the
US county check (`runs/m4-us-check/`), whose outputs are pinned in `runs/milestone_hashes.json`,
and its Wikipedia copies are not held, so it cannot be rebuilt from its sources. It is therefore
read back from the commit that added it, checked against the sha256 its card states, and written
to `data/interim/` (ignored by git). A shallow clone without that commit cannot run the check.
"""

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from nucprob.paths import DATA, ROOT


@dataclass(frozen=True)
class Pinned:
    path: str  # path in the commit, from the repository root
    commit: str
    sha256: str

    @property
    def local(self) -> Path:
        return DATA / "interim" / "history" / Path(self.path).name


US_MILITARY_SITES_1985 = Pinned(
    "data/curated/features/us_military_sites_1985.csv",
    "a9ca394b4b67bf07a9bc4cc7d02b008c1ee576e5",
    "8cbca76f8243fc0b452b24a6275fcfe7a5488c5a215c90660780ef81a1740eab",
)
PINNED = (US_MILITARY_SITES_1985,)


class HistoryError(RuntimeError):
    pass


def restore(p: Pinned) -> Path:
    """The table's bytes at the pinned commit, written once to data/interim/history/ and checked."""
    if p.local.exists() and hashlib.sha256(p.local.read_bytes()).hexdigest() == p.sha256:
        return p.local
    try:
        blob = subprocess.run(
            ["git", "show", f"{p.commit}:{p.path}"], cwd=ROOT, capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise HistoryError(f"cannot read {p.path} at {p.commit[:7]} (shallow clone?)") from e
    got = hashlib.sha256(blob).hexdigest()
    if got != p.sha256:
        raise HistoryError(f"{p.path} at {p.commit[:7]} has sha256 {got}, expected {p.sha256}")
    p.local.parent.mkdir(parents=True, exist_ok=True)
    p.local.write_bytes(blob)
    return p.local


def main() -> None:
    for p in PINNED:
        print(f"{restore(p).relative_to(ROOT)}  {p.sha256}")


if __name__ == "__main__":
    main()
