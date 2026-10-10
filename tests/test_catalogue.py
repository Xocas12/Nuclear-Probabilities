"""Every label file has a data card and a provenance tag (milestone M4)."""

import pandas as pd
import yaml

from nucprob.paths import CURATED, ROOT

LABELS = CURATED / "labels"
PROVENANCE = {"plan", "study", "exercise", "defender", "reconstruction", "reference"}
SELECTION = {"judgment", "rule", "mixed", "unknown", "n/a"}
USE = {"training", "transfer-test", "validation", "audit", "reference"}
KEYS = {
    "file",
    "title",
    "planner",
    "targets",
    "year",
    "provenance",
    "selection",
    "use",
    "completeness",
    "card",
    "caveats",
}


def catalogue() -> dict[str, dict]:
    entries = yaml.safe_load((LABELS / "CATALOGUE.yaml").read_text(encoding="utf-8"))["lists"]
    return {e["file"]: e for e in entries}


def test_every_label_file_has_a_card():
    cards = catalogue()
    files = {p.name for p in LABELS.glob("*.csv")}
    assert files == set(cards), f"no card: {files - set(cards)}; no file: {set(cards) - files}"


def test_cards_use_the_vocabularies():
    for name, e in catalogue().items():
        assert set(e) == KEYS, f"{name}: {set(e) ^ KEYS}"
        assert e["provenance"] in PROVENANCE, name
        assert e["selection"] in SELECTION, name
        assert e["use"] in USE, name
        card_path = ROOT / str(e["card"]).split(" (")[0]
        assert card_path.exists(), f"{name}: card {card_path} missing"


def test_provenance_matches_the_file():
    for name, e in catalogue().items():
        if e["provenance"] == "reference":
            continue
        df = pd.read_csv(LABELS / name, low_memory=False)
        assert "provenance" in df.columns, name
        tags = set(df["provenance"].dropna().astype(str))
        # A list may mix approved plans and staff studies (the 1945 and 1958 files).
        allowed = {e["provenance"]} | (
            {"plan", "study"} if e["provenance"] in {"plan", "study"} else set()
        )
        assert tags and tags <= allowed, (name, tags)
