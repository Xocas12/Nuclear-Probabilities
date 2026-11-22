"""The protocol is frozen: its file matches the recorded hash (milestone M5)."""

from nucprob.protocol import load, protocol_hash, recorded_hash


def test_protocol_matches_recorded_hash():
    assert protocol_hash() == recorded_hash(), (
        "configs/protocol.yaml changed: bump its version, note the change, and run "
        "python -m nucprob.protocol --record"
    )


def test_protocol_fixes_the_splits():
    p = load()
    assert p["splits"]["sealed_seed"] == 1956
    assert p["splits"]["block_km"] == 300
    assert p["metrics"]["primary"].startswith("PR-AUC")
