"""The frozen analysis protocol (configs/protocol.yaml, PLAN section 5.1).

    python -m nucprob.protocol            # print the protocol hash and whether it is recorded
    python -m nucprob.protocol --record   # record a new version's hash (deliberate changes only)

Runs import `protocol_hash()` and write it into their manifest.
"""

import hashlib
import sys

import yaml

from nucprob.paths import ROOT

PROTOCOL = ROOT / "configs" / "protocol.yaml"
RECORDED = ROOT / "configs" / "protocol.sha256"


def protocol_hash() -> str:
    return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()


def recorded_hash() -> str:
    return RECORDED.read_text().split()[0] if RECORDED.exists() else ""


def load() -> dict:
    return yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    h = protocol_hash()
    if "--record" in argv:
        RECORDED.write_text(f"{h}  configs/protocol.yaml (version {load()['version']})\n")
        print(f"recorded {h}")
        return
    print(h, "recorded" if h == recorded_hash() else "NOT the recorded hash")


if __name__ == "__main__":
    main()
