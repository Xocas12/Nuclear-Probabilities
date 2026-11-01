"""Whether documents name defences as targets in themselves: counts by document, from what the
documents print. Never sequencing, never which aim point served what.

    python -m nucprob.classifier.defence_targets

Target-list rows count if their stated class names an air or missile defence. In SAC 1956, whose
complexes hold coded installations, the count is of category 284 (radar installations) and 210
(guided missiles), with the share of complexes that hold one. Category 210 also covers missile production,
so it is an upper bound on defences. Writes runs/classifier/defence_targets.csv.
"""

import json
import re

import pandas as pd

from nucprob.outputs import hashes, start_record
from nucprob.paths import CURATED, RUNS
from nucprob.plans import plans

OUT = RUNS / "classifier" / "defence_targets.csv"
DEFENCE_CLASS = re.compile(
    r"\bsam\b|nike|hawk|air defen[cs]e|anti-?aircraft|\bradar\b|surface-to-air|bloodhound|\bpvo\b|control and warning",
    re.I,
)
LISTS = ["wp_", "us_1945", "us_1958", "us_1963", "us_1964"]


def by_list() -> pd.DataFrame:
    reg = plans()
    reg = reg[(reg["role"] == "train") & reg["plan_id"].str.startswith(tuple(LISTS))]
    rows = []
    for _, doc in reg.iterrows():
        d = pd.read_csv(
            CURATED / "labels" / f"{doc['plan_id']}.csv", dtype=str, keep_default_na=False
        )
        d = d[d["selected"] == "1"]
        rows.append(
            {
                "document": doc["plan_id"],
                "doc_type": doc["doc_type"],
                "attacker": doc["attacker"],
                "counted": "designated rows",
                "total": len(d),
                "naming_defences": int(d["target_class"].str.contains(DEFENCE_CLASS).sum()),
            }
        )
    return pd.DataFrame(rows)


def sac() -> pd.DataFrame:
    i = pd.read_csv(CURATED / "sac1956" / "installations.csv", dtype=str, keep_default_na=False)
    n = i["complex_id"].nunique()
    rows = []
    for code, name in (("284", "radar installations"), ("210", "guided missiles, upper bound")):
        rows.append(
            {
                "document": f"us_1956_sac_complexes, category {code}: {name}",
                "doc_type": "requirements_study",
                "attacker": "US",
                "counted": "complexes holding one",
                "total": n,
                "naming_defences": int(i.loc[i["category"] == code, "complex_id"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def table() -> pd.DataFrame:
    t = pd.concat([sac(), by_list()], ignore_index=True)
    t["share"] = (t["naming_defences"] / t["total"].where(t["total"] > 0)).round(3)
    return t


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    started = start_record()
    table().to_csv(OUT, index=False)
    print(table().to_string(index=False))
    (OUT.parent / "defence_targets_manifest.json").write_text(
        json.dumps({**started, "outputs": hashes([OUT])}, indent=2)
    )


if __name__ == "__main__":
    main()
