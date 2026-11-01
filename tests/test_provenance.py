"""The provenance manifest, data/sources.yaml: each source says when it was retrieved and what its
bytes hash to, or says why it cannot, and each target list cites registered documents. No network;
the hash checks need data/raw/, which is git-ignored, and skip without it."""

import csv
import hashlib
import re

import pandas as pd
import pytest
import yaml

from nucprob.paths import CURATED, RAW
from nucprob.sources import cited_pages
from nucprob.sources.fetch import load_manifest, sha256

LABELS = CURATED / "labels"
TILE_MANIFEST = CURATED / "features" / "terrain_tiles_manifest.sha256"
CHECKED_ROLES = {"train", "test-expectation"}
# A list with no source_url column, and the source that stands for it.
NO_URL_COLUMN = {"cd_1987_napb90_counties": "fema_napb90"}
DATE = r"\d{4}-\d{2}-\d{2}"


def sources() -> list[dict]:
    return load_manifest()["sources"]


def source(source_id: str) -> dict:
    return next(s for s in sources() if s["id"] == source_id)


def checked_lists() -> list[str]:
    plans = yaml.safe_load((LABELS / "PLANS.yaml").read_text(encoding="utf-8"))["plans"]
    return [p["plan_id"] for p in plans if p["role"] in CHECKED_ROLES]


def list_rows(plan_id: str) -> list[dict]:
    with open(LABELS / f"{plan_id}.csv", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_every_source_says_when_it_was_retrieved():
    for src in sources():
        retrieved = src.get("retrieved")
        name = src["id"]
        assert isinstance(retrieved, str), f"{name}: no retrieved date"
        if retrieved == "unknown":
            assert src.get("retrieved_note"), f"{name}: unknown date with no retrieved_note"
        elif retrieved.startswith("failed"):
            assert re.fullmatch(f"failed {DATE}", retrieved), f"{name}: {retrieved}"
            assert src.get("hash_note"), f"{name}: failure with no reason in hash_note"
        else:
            assert re.fullmatch(DATE, retrieved), f"{name}: {retrieved}"


def test_every_source_has_a_hash_or_says_why_not():
    for src in sources():
        name = src["id"]
        assert "sha256" in src, f"{name}: no sha256 key"
        if src["sha256"] is None:
            assert src.get("hash_note"), f"{name}: sha256 null with no hash_note"
        else:
            assert re.fullmatch("[0-9a-f]{64}", src["sha256"]), f"{name}: malformed sha256"


def test_every_source_of_a_scored_list_is_registered():
    registered = {s["url"] for s in sources()}
    missing = {}
    for plan_id in checked_lists():
        rows = list_rows(plan_id)
        if "source_url" not in rows[0]:
            assert NO_URL_COLUMN[plan_id] in {s["id"] for s in sources()}
            continue
        urls = {r["source_url"] for r in rows}
        assert "" not in urls and None not in urls, f"{plan_id}: a row with no source_url"
        if urls - registered:
            missing[plan_id] = sorted(urls - registered)
    assert not missing


def test_registered_documents_say_what_they_are():
    registered = {s["url"]: s for s in sources()}
    for plan_id in checked_lists():
        for url in {r.get("source_url") for r in list_rows(plan_id)} - {None}:
            src = registered[url]
            assert src["licence"] and src["use"], f"{src['id']}: no licence or use"
            assert src.get("title"), f"{src['id']}: no title"
            assert src["role"] == "labels", f"{src['id']}: cited by a list, role {src['role']}"


@pytest.mark.skipif(not RAW.exists(), reason="data/raw/ is absent")
def test_files_in_data_raw_match_their_recorded_hash():
    """`volatile: <why>` is the annotation that the file changes with no change in what is used."""
    differ = [
        src["id"]
        for src in sources()
        if src["sha256"]
        and not src.get("volatile")
        and (RAW / src["path"]).exists()
        and sha256(RAW / src["path"]) != src["sha256"]
    ]
    assert not differ, f"sha256 differs from data/sources.yaml: {differ}"


def test_tile_manifest_is_the_one_registered():
    tiles = source("aws_terrain_tiles")
    assert TILE_MANIFEST.name in tiles["manifest"]
    assert sha256(TILE_MANIFEST) == tiles["manifest_sha256"]


@pytest.mark.skipif(not (RAW / "terrain").exists(), reason="data/raw/terrain/ is absent")
def test_tiles_match_the_manifest():
    terrain = RAW / "terrain"
    listed = {}
    for line in TILE_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, tile = line.split("  ")
        listed[tile] = digest
    present = {p.relative_to(terrain).as_posix() for p in terrain.glob("*/*/*.png")}
    assert present == set(listed)
    for tile, digest in listed.items():
        assert hashlib.sha256((terrain / tile).read_bytes()).hexdigest() == digest, tile


def test_every_sector_box_cites_a_registered_document():
    urls = {s.get("url") for s in load_manifest()["sources"]}
    sectors = yaml.safe_load((CURATED / "labels" / "SECTORS.yaml").read_text(encoding="utf-8"))
    cited = [s["source_url"] for s in sectors["sectors"] if s.get("source_url")]
    assert cited
    assert not [u for u in cited if u not in urls]


def test_every_cited_page_has_a_registry_row_with_date_and_licence_or_a_stated_failure():
    pages = cited_pages.cited()
    rows = pd.read_csv(cited_pages.OUT, dtype=str, keep_default_na=False).set_index("url")
    assert set(pages) == set(rows.index)
    assert (rows["licence"] != "").all() and (rows["retrieved"] != "").all()
    fetched = rows["status"] == "ok"
    assert rows.loc[fetched, "sha256"].str.fullmatch("[0-9a-f]{64}").all()
    assert (rows.loc[~fetched, "status"] != "").all()


def test_urls_keep_their_brackets_and_lose_trailing_punctuation():
    got = cited_pages.urls_in("see https://a.org/x_(y), https://b.org/z; https://c.org/k.")
    assert got == {"https://a.org/x_(y)", "https://b.org/z", "https://c.org/k"}
    assert cited_pages.urls_in("(https://a.org/k)") == {"https://a.org/k"}
