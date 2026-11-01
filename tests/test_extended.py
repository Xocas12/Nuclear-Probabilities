"""The economic and political readings: as-of values, no borrowed state, the verdict's rule."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from nucprob.classifier import extended as ex
from nucprob.classifier import state_features as sf
from nucprob.classifier.features import COW
from nucprob.paths import PROCESSED, ROOT, RUNS, SOURCES, SOURCES_AMENDMENT_5
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "extended.csv"
needs_run = pytest.mark.skipif(not OUT.exists(), reason="no extended run")
needs_data = pytest.mark.skipif(
    not sf.REGIME.exists() or not (PROCESSED / "classifier_table.parquet").exists(),
    reason="no raw data or no built table",
)


def series(entity: str, pairs: list[tuple[int, float]], column: str) -> pd.DataFrame:
    return pd.DataFrame([(entity, y, v) for y, v in pairs], columns=["Entity", "Year", column])


def test_a_later_year_is_never_read():
    d = series("A", [(1950, 1.0), (1960, 2.0), (1970, 3.0)], "x")
    assert sf.last_at_or_before(d, "A", "x", 1965) == 2.0
    assert sf.last_at_or_before(d, "A", "x", 1960) == 2.0
    assert np.isnan(sf.last_at_or_before(d, "A", "x", 1949))


def test_a_state_its_source_does_not_hold_stays_missing():
    d = series("Germany", [(1950, 3000.0)], "GDP per capita")
    assert "East Germany" not in sf.GDP_ENTITY and "North Vietnam" not in sf.GDP_ENTITY
    assert np.isnan(
        sf.last_at_or_before(d, sf.GDP_ENTITY.get("East Germany"), "GDP per capita", 1956)
    )


def test_every_country_of_the_table_is_named_for_regime():
    for country in COW:
        assert country in sf.REGIME_ENTITY, country


def test_pacts_count_only_the_documents_year_and_a_superpower_counts_as_its_own_side():
    pacts = pd.DataFrame({"ccode1": [200, 200], "ccode2": [2, 2], "year": [1949, 1950]})
    uk = sf.pact_columns(pacts, 200, 1949)
    assert uk["pol_defence_pact_usa"] == 1 and uk["pol_defence_pact_ussr"] == 0
    assert sf.pact_columns(pacts, 200, 1948)["pol_defence_pact_usa"] == 0
    assert sf.pact_columns(pacts, sf.USA, 1940)["pol_defence_pact_usa"] == 1
    assert sf.pact_columns(pacts, sf.USSR, 1940)["pol_defence_pact_ussr"] == 1


def test_the_verdict_needs_both_intervals_and_enough_training():
    row = {"train_positives": 100, "constant": False}
    assert (
        ex.verdict(row | {"low": 0.1, "high": 0.2, "block_low": 0.01, "block_high": 0.3}) == "gain"
    )
    assert (
        ex.verdict(row | {"low": 0.1, "high": 0.2, "block_low": -0.01, "block_high": 0.3})
        == "neither"
    )
    assert (
        ex.verdict(row | {"low": -0.2, "high": -0.1, "block_low": -0.3, "block_high": -0.01})
        == "loss"
    )
    few = {"train_positives": 29, "constant": False, "low": 0.1, "high": 0.2}
    assert ex.verdict(few | {"block_low": 0.1, "block_high": 0.2}) == "not a reading"


def test_the_amendment_names_every_new_column_and_changes_no_primary_rule():
    a = yaml.safe_load(ex.AMENDMENT.read_text(encoding="utf-8"))
    for c in sf.POLITICAL:
        assert c in a["columns"]["political"]
    for c in sf.ECONOMIC:
        assert c in a["columns"]["economic"]
    assert "Primary comparisons" in a["unchanged"]
    protocol = (ROOT / "configs" / "protocol.yaml").read_text(encoding="utf-8")
    assert "pol_regime" not in protocol


def test_the_new_sources_are_registered_with_a_date_and_hash_and_the_primary_registry_is_untouched():
    extra = yaml.safe_load(SOURCES_AMENDMENT_5.read_text(encoding="utf-8"))["sources"]
    assert {s["id"] for s in extra} == {
        "cow_alliances_v41",
        "owid_political_regime",
        "owid_maddison_gdp_pc",
    }
    assert all(s["retrieved"] and s["sha256"] and s["licence"] for s in extra)
    primary = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]
    assert not {s["id"] for s in extra} & {s["id"] for s in primary}


@needs_data
def test_known_values_of_the_state_year_table():
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = sf.state_year_table(
        full[["country", "year"]].dropna(),
        pd.read_csv(sf.REGIME),
        pd.read_csv(sf.GDP),
        sf.read_pacts(),
        sf.state_codes(),
    ).set_index(["country", "year"])
    poland = table.loc[("Poland", 1962)]
    assert poland["pol_defence_pact_ussr"] == 1 and poland["pol_defence_pact_usa"] == 0
    denmark = table.loc[("Denmark", 1967)]
    assert denmark["pol_defence_pact_usa"] == 1 and denmark["pol_defence_pact_ussr"] == 0
    assert np.isnan(table.loc[("East Germany", 1956), "econ_log_gdp_pc"])
    assert table.loc[("USSR", 1956), "pol_regime"] == 0
    assert table.loc[("Denmark", 1967), "pol_regime"] >= 2
    assert table["pol_regime"].notna().all()


@needs_run
def test_committed_extended_run_is_of_this_amendment_and_table_and_holds_every_reading():
    m = json.loads((RUNS / "classifier" / "extended_manifest.json").read_text())
    assert m["amendment_sha256"] == sha256(ex.AMENDMENT)
    d = pd.read_csv(OUT)
    assert set(d["holdout"]) == {"spatial blocks", "leave one document out"}
    assert set(ex.comparisons()) <= set(d["comparison"])
    assert "defence industry over population" in set(d["comparison"])
    assert set(d["verdict"]) <= {"gain", "loss", "neither", "not a reading"}
    assert d.apply(lambda r: ex.verdict(r) == r["verdict"], axis=1).all()
    if (PROCESSED / "classifier_table.parquet").exists():
        assert m["table_sha256"] == sha256(PROCESSED / "classifier_table.parquet")


@needs_run
def test_the_readme_states_what_the_extended_run_and_the_primary_run_hold():
    d = pd.read_csv(OUT)
    glob = d[(d["scope"] == ex.SCOPES[0]) & (d["holdout"] == "leave one document out")]
    assert not (glob.loc[glob["lists"] == "other than SAC", "verdict"] == "gain").any()
    best = glob.loc[glob["lists"] == "all lists", "a_pr_auc"].max()
    comp = pd.read_csv(RUNS / "classifier" / "comparison.csv")
    rule = comp[
        (comp["scope"] == ex.SCOPES[0])
        & (comp["holdout"] == "leave one document out")
        & (comp["against"] == "population rule")
        & (comp["lists"] == "all lists")
    ]["b_pr_auc"].iloc[0]
    plants = d[d["comparison"] == "defence industry over population"].iloc[0]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"scores {best:.2f} against {rule:.2f}" in " ".join(readme.split())
    assert f"[{plants['low']:+.3f}, {plants['high']:+.3f}]" in readme
