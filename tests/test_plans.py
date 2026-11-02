"""The evidence registry keeps plan, side, date and grade apart, and the state gate refuses."""

import pandas as pd
import yaml

from nucprob.paths import CURATED
from nucprob.plans import DOC_TYPES, GRADES, ROLES, gate, plans, protocol

RULE = {
    "plan_doc_types": ["war_plan", "requirements_study"],
    "grades": ["A", "B", "C"],
    "min_independent_plans": 2,
    "min_positives": 10,
    "min_positives_outside_largest": 3,
}


def catalogue() -> pd.DataFrame:
    cat = yaml.safe_load((CURATED / "labels" / "CATALOGUE.yaml").read_text(encoding="utf-8"))
    return pd.DataFrame(cat["lists"]).assign(plan_id=lambda d: d["file"].str.removesuffix(".csv"))


def test_vocabularies():
    reg = plans()
    assert reg["plan_id"].is_unique
    assert set(reg["doc_type"]) <= DOC_TYPES
    assert set(reg["grade"]) <= GRADES
    assert set(reg["role"]) <= ROLES


def test_every_target_list_is_registered():
    cat = catalogue()
    targets = cat[cat["provenance"] != "reference"]
    assert set(targets["plan_id"]) == set(plans()["plan_id"])


def test_a_document_is_only_a_war_plan_if_the_catalogue_calls_it_a_plan():
    merged = plans().merge(catalogue()[["plan_id", "provenance"]], on="plan_id")
    war = merged[merged["doc_type"].eq("war_plan")]
    assert set(war["provenance"]) == {"plan"}
    for doc_type in ("exercise", "wargame", "training", "mirror", "civil_defence"):
        assert not merged.loc[merged["doc_type"].eq(doc_type), "provenance"].eq("plan").any()


def test_no_attacker_is_recorded_for_a_defenders_expectation():
    reg = plans()
    expect = reg[reg["doc_type"].isin(["mirror", "civil_defence"])]
    assert expect["attacker"].isna().all()
    assert not expect["role"].eq("train").any()


def test_journalism_and_encyclopedias_give_no_labels():
    reg = plans()
    assert reg.loc[reg["grade"].eq("D"), "role"].eq("excluded").all()
    assert reg.loc[reg["doc_type"].eq("reconstruction"), "role"].eq("excluded").all()


def registry(rows: list[tuple]) -> pd.DataFrame:
    cols = ["plan_id", "attacker", "doc_type", "grade", "group", "role"]
    return pd.DataFrame(rows, columns=cols)


def test_gate_counts_a_document_once_and_refuses_thin_states():
    reg = registry(
        [
            ("a1", "A", "war_plan", "A", "doc-a", "train"),
            ("a2", "A", "war_plan", "A", "doc-a", "train"),
            ("a3", "A", "requirements_study", "A", "doc-b", "train"),
            ("b1", "B", "war_plan", "A", "doc-c", "train"),
            ("b2", "B", "exercise", "A", "doc-d", "train"),
            ("c1", "C", "war_plan", "D", "doc-e", "train"),
            ("c2", "C", "war_plan", "D", "doc-f", "train"),
        ]
    )
    out = gate(
        {"a1": 50, "a2": 50, "a3": 4, "b1": 100, "b2": 100, "c1": 40, "c2": 40}, reg, RULE
    ).set_index("attacker")
    assert out.at["A", "independent_plans"] == 2
    assert out.at["A", "positives_outside_largest"] == 4
    assert out.at["A", "allowed"]
    # an exercise is not a plan, so B has one plan however many exercise positives it has
    assert not out.at["B", "allowed"] and "1 independent plans" in out.at["B", "reason"]
    # grade D does not count
    assert not out.at["C", "allowed"]


def test_a_disputed_document_never_counts_as_a_plan():
    reg = plans().set_index("plan_id")
    assert reg.at["wp_1970_coastal_front_map", "doc_type"] == "disputed_plan_or_exercise"
    assert "disputed_plan_or_exercise" not in protocol()["state_models"]["plan_doc_types"]
    # Through the gate itself: a disputed document's positives, however many, make no plan.
    out = gate({"wp_1970_coastal_front_map": 1000}, plans(), protocol()["state_models"])
    poland = out.set_index("attacker").loc["Poland"]
    assert poland["independent_plans"] == 0 and poland["linked_positives"] == 0
    assert not poland["allowed"]


def test_protocol_rule_has_the_declared_fields():
    rule = protocol()["state_models"]
    assert set(RULE) <= set(rule)
    assert rule["min_independent_plans"] >= 2
    assert "exercise" not in rule["plan_doc_types"]
    assert "mirror" not in rule["plan_doc_types"]
