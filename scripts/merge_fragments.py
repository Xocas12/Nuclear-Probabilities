"""Merge collectors' fragments into the shared manifests.

    python scripts/merge_fragments.py [topic ...]

- data/curated/labels/catalogue.d/*.yaml (one card each) are appended to
  data/curated/labels/CATALOGUE.yaml, unless a card for that file already exists, which is an
  error.
- data/sources.d/<topic>.yaml (a list of source entries) are appended to data/sources.yaml,
  skipping ids already present.

Merged fragments are deleted. With topics given, only data/sources.d/<topic>.yaml and the
cards whose `card` path mentions the topic are merged.
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "curated" / "labels"
CARDS = LABELS / "catalogue.d"
SOURCES_D = ROOT / "data" / "sources.d"
SOURCES = ROOT / "data" / "sources.yaml"
KEYS = [
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
]


def dump_card(card: dict) -> str:
    body = yaml.safe_dump(
        [{k: card[k] for k in KEYS}], sort_keys=False, allow_unicode=True, width=100
    )
    return "\n" + "\n".join("  " + line if line else line for line in body.splitlines()) + "\n"


def merge_cards(topics: list[str]) -> int:
    text = (LABELS / "CATALOGUE.yaml").read_text(encoding="utf-8")
    have = {e["file"] for e in yaml.safe_load(text)["lists"]}
    n = 0
    for path in sorted(CARDS.glob("*.yaml")):
        card = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(card, list):
            card = card[0]
        if topics and not any(t in str(card.get("card", "")) for t in topics):
            continue
        missing = set(KEYS) - set(card)
        if missing:
            raise ValueError(f"{path.name}: missing keys {missing}")
        if card["file"] in have:
            raise ValueError(f"{path.name}: a card for {card['file']} already exists")
        if not (LABELS / card["file"]).exists():
            raise FileNotFoundError(f"{path.name}: {card['file']} not in data/curated/labels")
        text = text.rstrip("\n") + "\n" + dump_card(card)
        have.add(card["file"])
        path.unlink()
        n += 1
    (LABELS / "CATALOGUE.yaml").write_text(text, encoding="utf-8")
    return n


def merge_sources(topics: list[str]) -> int:
    text = SOURCES.read_text(encoding="utf-8")
    have = {s["id"] for s in yaml.safe_load(text)["sources"]}
    n = 0
    for path in sorted(SOURCES_D.glob("*.yaml")):
        if topics and path.stem not in topics:
            continue
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        new = [e for e in entries if e["id"] not in have]
        for e in new:
            for k in ("id", "url", "path", "role"):
                if k not in e:
                    raise ValueError(f"{path.name}: entry {e.get('id')} lacks {k}")
        if new:
            body = yaml.safe_dump(new, sort_keys=False, allow_unicode=True, width=100)
            text = text.rstrip("\n") + "\n" + body
            have |= {e["id"] for e in new}
            n += len(new)
        path.unlink()
    SOURCES.write_text(text, encoding="utf-8")
    return n


def main() -> None:
    topics = sys.argv[1:]
    print(f"cards merged: {merge_cards(topics)}; sources merged: {merge_sources(topics)}")


if __name__ == "__main__":
    main()
