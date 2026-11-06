"""The fetcher obeys robots.txt, and every registered source has a recorded answer."""

import ast

import pandas as pd
import pytest
import requests

from nucprob.paths import ROOT, RUNS
from nucprob.sources import fetch, robots


class Answer:
    def __init__(self, code: int, text: str = ""):
        self.status_code, self.text = code, text


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    monkeypatch.setattr(robots, "_cache", {})


def answering(code: int, text: str = ""):
    return lambda *a, **k: Answer(code, text)


def test_a_path_disallowed_to_all_is_refused_and_other_paths_pass():
    get = answering(200, "User-agent: *\nDisallow: /private/\n")
    assert not robots.check("https://a.example/private/x.csv", get).allowed
    assert robots.check("https://a.example/open/x.csv", get).allowed


def test_a_rule_for_one_automated_agent_is_enough_to_refuse():
    get = answering(200, "User-agent: ClaudeBot\nDisallow: /\n")
    v = robots.check("https://b.example/x.csv", get)
    assert not v.allowed and v.denied_agents == ("ClaudeBot",)


def test_unavailable_rules_follow_the_rfc():
    assert robots.check("https://c.example/x", answering(404)).allowed
    assert robots.check("https://d.example/x", answering(403)).allowed
    assert not robots.check("https://e.example/x", answering(503)).allowed

    def down(*a, **k):
        raise requests.ConnectionError

    assert not robots.check("https://f.example/x", down).allowed


def test_download_requests_nothing_when_refused(monkeypatch, tmp_path):
    robots._cache["https://g.example"] = ("rules", ["User-agent: *", "Disallow: /"])

    def fail(*a, **k):
        raise AssertionError("a request was made")

    monkeypatch.setattr(fetch.requests, "get", fail)
    with pytest.raises(robots.RobotsRefused):
        fetch.download("https://g.example/x.zip", tmp_path / "x.zip")
    assert not (tmp_path / "x.zip").exists()


def test_a_refused_source_and_its_mirror_are_reported_not_obtained(monkeypatch, tmp_path, capsys):
    robots._cache["https://g.example"] = ("rules", ["User-agent: *", "Disallow: /"])
    entry = {"id": "s", "url": "https://g.example/x.zip", "path": "x.zip"}
    monkeypatch.setattr(fetch, "load_manifest", lambda: {"sources": [entry]})
    monkeypatch.setattr(fetch, "RAW", tmp_path)
    assert fetch.main([]) == 1
    assert "not obtained" in capsys.readouterr().out
    assert not (tmp_path / "x.zip").exists()


def test_the_audit_covers_every_source_and_names_each_refusal_in_the_readme():
    audit = pd.read_csv(RUNS / "qa" / "robots.csv", dtype={"allowed": "string"})
    ids = {s["id"] for s in fetch.load_manifest()["sources"]}
    assert ids <= set(audit["id"])
    refused = audit.loc[audit["status"].eq("rules") & audit["allowed"].eq("False"), "host"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for host in refused.unique():
        assert host in readme, host


def test_every_held_file_came_from_a_url_robots_allows():
    audit = pd.read_csv(RUNS / "qa" / "robots.csv", dtype=str, keep_default_na=False)
    held = audit[audit["held_locally"].eq("True")]
    refused = set(held.loc[held["allowed"].ne("True"), "id"])
    assert refused == set()


def test_a_withdrawn_source_is_neither_held_nor_read():
    """The tenth amendment withdrew Great Britain's 1981 district totals (Nomis, refused by robots), and the
    nineteenth the Dutch census of 1960 (fetched from ssh.datastations.nl, refused by robots): no raw copy, no
    curated row and no region may come back without a source robots allows."""
    from nucprob.paths import CURATED, RAW
    from nucprob.transfer.regions import REGIONS

    withdrawn = [s for s in fetch.load_manifest()["sources"] if s.get("withdrawn")]
    assert {s["id"] for s in withdrawn} == {"census_uk_1981_nomis", "census_nl_1960"}
    assert not (CURATED / "gazetteer" / "towns_nl_1960.csv").exists()
    for s in withdrawn:
        assert not (RAW / s["path"]).exists(), s["id"]
    uk = pd.read_csv(CURATED / "gazetteer" / "towns_uk_1981.csv", dtype=str)
    assert not uk["source"].str.contains("Nomis").any()
    tables = {stem for r in REGIONS.values() for _, _, stem in r.countries}
    assert "towns_uk_1981" not in tables and "towns_nl_1960" not in tables


def test_scripts_use_allowed_routes_and_past_routes_stay_listed_as_refused():
    audit = pd.read_csv(RUNS / "qa" / "robots.csv", dtype=str, keep_default_na=False)
    scripts = audit[audit["role"].eq("script")]
    assert set(scripts["id"]) == set(robots.SCRIPT_URLS) and scripts["allowed"].eq("True").all()
    past = audit[audit["role"].eq("past_route")]
    assert set(past["id"]) == set(robots.PAST_ROUTES) and past["allowed"].eq("False").all()
    for path in sorted((ROOT / "scripts").glob("*fetch*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        tree.body = tree.body[1:] if ast.get_docstring(tree) else tree.body
        code = ast.unparse(tree)
        assert "/w/index.php" not in code and "/w/api.php" not in code, path.name
        assert "/wiki/" in code, path.name


def test_obtained_from_entries_give_a_url_date_and_note_and_cover_geonames():
    routes = fetch.obtained()
    assert routes, "no source in data/sources.yaml gives obtained_from"
    for sid, entry in routes.items():
        assert entry["obtained_from"].startswith("https://"), sid
        assert entry["obtained_from"] != entry.get("url"), sid
        assert str(entry["obtained"])[:2] == "20" and entry["obtained_note"], sid
        assert entry["sha256"], sid  # the held bytes' hash is the one the source records
    registry = {s["id"] for s in fetch.load_manifest()["sources"]}
    geonames = {s for s in registry if s.startswith("geonames_")}
    assert geonames <= set(routes)
    assert not (ROOT / "data" / "sources_obtained.yaml").exists()  # folded into sources.yaml


def test_held_copies_have_the_hash_of_their_obtained_from_entry():
    from nucprob.paths import RAW

    checked = 0
    for sid, entry in fetch.obtained().items():
        path = RAW / entry["path"]
        if path.exists():
            assert fetch.sha256(path) == entry["sha256"], sid
            checked += 1
    if not checked:
        pytest.skip("no raw files here")


def test_the_fetcher_downloads_obtained_from_in_place_of_the_publisher_url(monkeypatch, tmp_path):
    entry = {
        "id": "s",
        "url": "https://pub.example/x.zip",
        "path": "x.zip",
        "obtained_from": "https://m.example/x",
    }
    monkeypatch.setattr(fetch, "_read", lambda path: [dict(entry)])
    monkeypatch.setattr(fetch, "REGISTRIES", (tmp_path / "r.yaml",))
    monkeypatch.setattr(fetch, "RAW", tmp_path)
    monkeypatch.setattr(fetch, "save_manifest", lambda m: None)
    asked = []

    def download(url, dest):
        asked.append(url)
        dest.write_bytes(b"x")

    monkeypatch.setattr(fetch, "download", download)
    fetch.main([])
    assert asked == ["https://m.example/x"]


def test_saving_the_registry_keeps_obtained_from_and_records_the_hash(monkeypatch, tmp_path):
    reg = tmp_path / "sources.yaml"
    reg.write_text(
        "# a\n# b\n# c\n# d\nsources:\n- id: s\n  url: https://pub.example/x\n"
        "  obtained_from: https://m.example/x\n"
    )
    monkeypatch.setattr(fetch, "REGISTRIES", (reg,))
    manifest = fetch.load_manifest()
    assert manifest["sources"][0]["obtained_from"] == "https://m.example/x"
    manifest["sources"][0]["sha256"] = "0" * 64
    fetch.save_manifest(manifest)
    text = reg.read_text()
    assert "obtained_from: https://m.example/x" in text and "0" * 64 in text
    assert text.startswith("# a\n# b\n# c\n# d\n")
