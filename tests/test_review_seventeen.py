"""Checks for the review of 4e8c648: the historical scenario notes, which the viewer prints, date the FRUS
figures as the source does (central reliability 1953, losses mid-1953 to mid-1955) and call the +/- 0.07
spread on reliability this study's assumption, matching README."""

import yaml

from nucprob.paths import ROOT


def _scenarios() -> dict:
    return yaml.safe_load((ROOT / "configs" / "scenarios.yaml").read_text(encoding="utf-8"))


def test_historical_notes_date_the_frus_figures_as_the_source_does():
    historical = [s for s in _scenarios()["scenarios"] if s["era"] == "historical"]
    assert historical
    for s in historical:
        note = s["note"]
        for stale in ("1953 US government estimates", "1953 US estimates", "1953 FRUS"):
            assert stale not in note, (s["id"], stale)
        assert "FRUS" in note and "1952-54 vol. II, doc. 66" in note, s["id"]
        assert "mid-1953 to mid-1955" in note or "1953-55" in note, s["id"]


def test_reliability_spread_is_called_an_assumption():
    d = _scenarios()
    assert "this study's assumption" in d["assumptions"]["reliability_historical"]
    for s in d["scenarios"]:
        if s["era"] == "historical" and "central 0.65" in s["note"]:
            assert "this study's assumption" in s["note"], s["id"]
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "1953-55" in readme
