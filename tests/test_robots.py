"""The fetcher obeys robots.txt, and every registered source has a recorded answer."""

import pandas as pd
import pytest
import requests
import yaml

from nucprob.paths import ROOT, RUNS, SOURCES
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
    ids = {s["id"] for s in yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]}
    assert ids <= set(audit["id"])
    refused = audit.loc[audit["status"].eq("rules") & audit["allowed"].eq("False"), "host"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for host in refused.unique():
        assert host in readme, host
