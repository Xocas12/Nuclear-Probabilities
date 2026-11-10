"""The viewer's method text follows the outputs (review 23, finding 6): its claims about the score, the
left-out-document results and the countries missing from the 1965 map are read, not typed."""

from nucprob.classifier import report
from nucprob.probmap import viewer


def test_a_gain_on_a_left_out_document_changes_the_sentence(monkeypatch):
    assert viewer.unseen_document_sentence().startswith("no score has been shown")
    monkeypatch.setattr(report, "verdict", lambda r: "gain")
    assert viewer.unseen_document_sentence().startswith("on a document it has not seen, these beat")


def test_the_1965_sentence_names_only_countries_the_scenario_lacks(monkeypatch):
    sc = {"id": "ussr_1965_on_west", "attackers": [{"targets": ["Denmark", "United Kingdom"]}]}
    monkeypatch.setattr(viewer, "mapped_scenarios", lambda: [sc])
    text = viewer.withdrawn_1965()
    assert "no Netherlands" in text and "United Kingdom" not in text.split(":")[0]
    sc["attackers"][0]["targets"] += ["Netherlands"]
    assert viewer.withdrawn_1965() == ""


def test_the_method_text_reads_the_score_and_its_features(monkeypatch):
    text = viewer.method_text()
    assert "population and nothing else" in text
    real = viewer.json.loads

    def other_score(s):
        d = real(s)
        if isinstance(d, dict) and "features" in d:
            d = {**d, "score": "portable logistic", "features": ["log_pop", "military_thing"]}
        return d

    monkeypatch.setattr(viewer.json, "loads", other_score)
    text = viewer.method_text()
    assert "portable logistic" in text and "plays no part" not in text
