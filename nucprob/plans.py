"""The evidence registry (data/curated/labels/PLANS.yaml) and the state-model gate.

    python -m nucprob.plans

`plans()` loads the registry. `gate()` decides, by the rule frozen in configs/protocol.yaml, which
attacker states get their own model; a refusal is an output with its reason. Counts of plans are
counts of independence groups (several lists from one document are one plan).

Writes runs/evidence/evidence_by_attacker.csv (documents and rows by attacker, document type and
grade) and, if the labels are built, runs/evidence/state_model_gate.csv.
"""

from collections.abc import Mapping

import pandas as pd
import yaml

from nucprob.paths import CURATED, PROCESSED, ROOT, RUNS

REGISTRY = CURATED / "labels" / "PLANS.yaml"
PROTOCOL = ROOT / "configs" / "protocol.yaml"
OUT = RUNS / "evidence"
DOC_TYPES = {
    "war_plan",
    "target_selection",
    "requirements_study",
    "policy_study",
    "exercise",
    "wargame",
    "training",
    "mirror",
    "civil_defence",
    "reconstruction",
}
GRADES = {"A", "B", "C", "D"}
ROLES = {"train", "test-expectation", "excluded"}


def plans() -> pd.DataFrame:
    return pd.DataFrame(yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["plans"])


def protocol() -> dict:
    return yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))


def rows_in(plan_id: str) -> int:
    path = CURATED / "labels" / f"{plan_id}.csv"
    return sum(1 for _ in pd.read_csv(path, dtype=str, keep_default_na=False).itertuples())


def evidence_table(reg: pd.DataFrame | None = None) -> pd.DataFrame:
    reg = plans() if reg is None else reg
    reg = reg.assign(
        attacker=reg["attacker"].fillna("(none: expectation of a defender)"),
        rows=[rows_in(p) for p in reg["plan_id"]],
    )
    grouped = reg.groupby(["attacker", "doc_type", "grade", "role"], sort=True)
    return grouped.agg(
        documents=("group", "nunique"), lists=("plan_id", "size"), rows=("rows", "sum")
    ).reset_index()


def gate(positives: Mapping[str, int], reg: pd.DataFrame, rule: Mapping) -> pd.DataFrame:
    """One row per attacker: `allowed`, and the reason. `positives` maps plan_id to linked
    positive places in its universe. Only lists with role `train` and a counted document type
    count as plans; the positives of exercises count only where the rule says so."""
    rows = []
    usable = reg[reg["role"].eq("train") & reg["attacker"].notna()]
    for attacker, g in usable.groupby("attacker", sort=True):
        counted = g[g["doc_type"].isin(rule["plan_doc_types"])]
        counted = counted[counted["grade"].isin(rule["grades"])]
        by_group = counted.assign(pos=counted["plan_id"].map(positives).fillna(0)).groupby("group")
        pos = by_group["pos"].sum().sort_values(ascending=False)
        n_plans = int((pos > 0).sum())
        total, rest = int(pos.sum()), int(pos.iloc[1:].sum())
        reasons = []
        if n_plans < rule["min_independent_plans"]:
            reasons.append(f"{n_plans} independent plans, needs {rule['min_independent_plans']}")
        if total < rule["min_positives"]:
            reasons.append(f"{total} linked positives, needs {rule['min_positives']}")
        if rest < rule["min_positives_outside_largest"]:
            reasons.append(
                f"{rest} positives outside its largest plan, "
                f"needs {rule['min_positives_outside_largest']}"
            )
        rows.append(
            {
                "attacker": attacker,
                "documents_any_type": g["group"].nunique(),
                "independent_plans": n_plans,
                "linked_positives": total,
                "positives_outside_largest": rest,
                "allowed": not reasons,
                "reason": "; ".join(reasons) or "meets the rule",
            }
        )
    return pd.DataFrame(rows)


def exercise_gate(positives: Mapping[str, int], reg: pd.DataFrame, rule: Mapping) -> dict:
    """The one pooled model the protocol allows on Warsaw Pact documents including exercises:
    every attacker of the Pact, every document type with role train. Always exercise-based."""
    pact = reg[reg["plan_id"].str.startswith("wp_") & reg["role"].eq("train")]
    pos = pact.assign(pos=pact["plan_id"].map(positives).fillna(0))
    linked = pos.groupby("group")["pos"].sum()
    documents, total = int((linked > 0).sum()), int(linked.sum())
    reasons = []
    if total < rule["min_positives"]:
        reasons.append(f"{total} linked positives, needs {rule['min_positives']}")
    if documents < rule["min_documents"]:
        reasons.append(f"{documents} documents with a linked target, needs {rule['min_documents']}")
    return {
        "attacker": "Warsaw Pact, pooled, exercise-based",
        "documents_any_type": int(pact["group"].nunique()),
        "independent_plans": 0,
        "linked_positives": total,
        "positives_outside_largest": int(linked.sum() - linked.max()),
        "allowed": not reasons,
        "reason": "; ".join(reasons) or "meets the rule; never a war-plan model",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    evidence_table().to_csv(OUT / "evidence_by_attacker.csv", index=False)
    labels = PROCESSED / "labels_transfer.parquet"
    dataset = PROCESSED / "dataset_sac1956.parquet"
    if not (labels.exists() and dataset.exists()):
        print("labels not built: gate not written")
        return
    t = pd.read_parquet(labels)
    positives = t.groupby("plan_id")["listed"].sum().astype(int).to_dict()
    d = pd.read_parquet(dataset)
    positives["us_1956_sac_complexes"] = int(d["listed"].sum())
    rule = protocol()["state_models"]
    table = gate(positives, plans(), rule)
    pooled = exercise_gate(positives, plans(), rule["warsaw_pact_exercise_model"])
    table = pd.concat([table, pd.DataFrame([pooled])], ignore_index=True)
    table.to_csv(OUT / "state_model_gate.csv", index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
