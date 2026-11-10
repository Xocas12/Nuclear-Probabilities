"""The README's opening counts of lists and documents follow PLANS.yaml (review 23, finding 4: lists were
counted as documents)."""

import re

import yaml

from nucprob.paths import ROOT


def test_readme_counts_lists_and_documents_from_the_register():
    plans = yaml.safe_load((ROOT / "data/curated/labels/PLANS.yaml").read_text(encoding="utf-8"))[
        "plans"
    ]
    attacker = [p for p in plans if p["attacker"]]
    none = [p for p in plans if not p["attacker"]]
    intro = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split("## ")[0].split())
    assert f"the {len(plans)} target lists" in intro
    assert f"come from {len({p['group'] for p in plans})} documents or exercises" in intro
    assert (
        f"{len(attacker)} lists, from {len({p['group'] for p in attacker})} documents, have"
        in intro
    )
    assert (
        f"{len(none)} lists, from {len({p['group'] for p in none})} documents, have no attacker"
        in intro
    )
    shared = {p["group"] for p in attacker} & {p["group"] for p in none}
    assert len(shared) == 1 and re.search(r"One exercise, .* is counted in both groups", intro)
    wars = [p for p in plans if p["doc_type"] == "war_plan"]
    assert len(wars) == 3 and "Three lists are war plans" in intro


def test_the_flagged_columns_are_named_in_full_where_the_repeat_is_described():
    """Review 23, finding 5: the text named railways, ports and airfields while the repeat also dropped
    power-station capacity and the distance to nuclear-complex sites."""
    from nucprob.classifier.report import FLAGGED_WORDS, flagged_phrase

    phrase = flagged_phrase()
    assert set(phrase.replace(" and ", ", ").split(", ")) <= set(FLAGGED_WORDS.values())
    for path in ("README.md", "data/FEATURES_CLASSIFIER.md"):
        text = " ".join((ROOT / path).read_text(encoding="utf-8").split())
        for word in phrase.replace(" and ", ", ").split(", "):
            assert word in text, (path, word)
