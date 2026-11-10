"""The robots table judges a source on the host its bytes came from, not on a resolver in front of it: a card that
says a file was saved from a URL names a host its source entry records (url or obtained_from)."""

import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from nucprob.paths import CURATED, RUNS
from nucprob.sources import fetch

SAVED = re.compile(r"(https?://\S+?),? saved as `([^`]+)`")


def test_every_saved_as_url_is_on_a_host_its_source_records():
    sources = fetch.load_manifest()["sources"]
    by_file = {Path(s["path"]).name: s for s in sources if s.get("path")}
    for card in CURATED.rglob("*.md"):
        for url, path in SAVED.findall(card.read_text(encoding="utf-8")):
            s = by_file.get(Path(path).name)
            if s is None:
                continue
            hosts = {urlparse(str(s.get(k) or "")).netloc for k in ("url", "obtained_from")}
            assert urlparse(url).netloc in hosts, (card.name, url, s["id"])


def test_the_dutch_census_is_judged_on_the_host_it_came_from_and_withdrawn():
    audit = pd.read_csv(RUNS / "qa" / "robots.csv", dtype=str, keep_default_na=False).set_index(
        "id"
    )
    row = audit.loc["census_nl_1960"]
    assert row["host"] == "ssh.datastations.nl" and row["checked"] == "obtained_from"
    assert row["allowed"] == "False" and row["held_locally"] == "False"
    entry = next(s for s in fetch.load_manifest()["sources"] if s["id"] == "census_nl_1960")
    assert entry.get("withdrawn")
    assert not (CURATED / "gazetteer" / "towns_nl_1960.csv").exists()
