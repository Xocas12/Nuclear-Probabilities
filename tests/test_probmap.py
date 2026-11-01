"""The allocation step, the stockpile's effect, the intervals and the limits on what is written."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from nucprob.paths import ROOT, RUNS
from nucprob.probmap import allocate as al
from nucprob.probmap import run as rn
from nucprob.probmap import stockpile as st

OUT = RUNS / "probmap"
needs_run = pytest.mark.skipif(not (OUT / "scenarios.csv").exists(), reason="no map run")


def towns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lat": [50.1, 50.2, 55.5, 60.5, 41.5],
            "lon": [10.1, 10.2, 20.5, 30.5, 2.5],
            "country": ["A", "A", "A", "A", "B"],
        }
    )


def scores(draws: int = 4) -> np.ndarray:
    base = np.array([0.8, 0.4, 0.3, 0.1, 0.5])
    rng = np.random.default_rng(0)
    return np.column_stack([base * rng.uniform(0.8, 1.2, 5) for _ in range(draws)])


ATTACK = [{"state": "U", "targets": ["A"]}]


def probabilities(w: float, draws: int = 4) -> np.ndarray:
    _, p = rn.scenario_probabilities(
        towns(), scores(draws), ATTACK, {"U": np.full(draws, float(w))}, 1.0
    )
    return p


def test_formula_on_one_cell():
    # Two cells with shares 0.75 and 0.25, W = 2: P = 1 - 0.25^2 and 1 - 0.75^2.
    s = al.score_shares(np.array([[3.0], [1.0]]))
    q = al.area_shares(s, np.array([0, 1]), 2)
    assert 1 - al.survival(q, np.array([2.0]))[0, 0] == pytest.approx(1 - 0.25**2)
    assert 1 - al.survival(q, np.array([2.0]))[1, 0] == pytest.approx(1 - 0.75**2)


def test_stockpile_changes_the_output_and_more_warheads_never_lower_it():
    low, mid, high = probabilities(1), probabilities(10), probabilities(100)
    assert (mid > low).any() and (high > mid).any()
    assert (mid >= low - 1e-12).all() and (high >= mid - 1e-12).all()


def test_no_warheads_means_no_strike():
    assert (probabilities(0) == 0).all()


def test_the_stockpile_test_fails_if_allocation_is_disabled(monkeypatch):
    """Mutation check: with an allocation that ignores warheads, the output cannot respond."""
    monkeypatch.setattr(al, "survival", lambda q, w: np.broadcast_to(1 - q, q.shape))
    with pytest.raises(AssertionError):
        test_stockpile_changes_the_output_and_more_warheads_never_lower_it()


def test_an_area_keeps_its_rank_by_share_and_towns_of_another_country_are_not_reached():
    cells, p = rn.scenario_probabilities(towns(), scores(1), ATTACK, {"U": np.array([5.0])}, 1.0)
    row = dict(zip(cells["cell"], p[:, 0], strict=True))
    assert row["50.0_10.0"] > row["55.0_20.0"] > row["60.0_30.0"]
    assert row["41.0_2.0"] == 0.0  # country B is not a target of this attacker


def test_two_attackers_combine_as_independent():
    a = [{"state": "U", "targets": ["A"]}, {"state": "V", "targets": ["A"]}]
    _, both = rn.scenario_probabilities(
        towns(), scores(1), a, {"U": np.array([3.0]), "V": np.array([4.0])}, 1.0
    )
    _, one = rn.scenario_probabilities(towns(), scores(1), ATTACK, {"U": np.array([7.0])}, 1.0)
    assert both == pytest.approx(one)


def test_the_grid_cannot_go_below_half_a_degree():
    with pytest.raises(ValueError):
        al.cell_ids([50.0], [10.0], 0.25)
    assert al.cell_ids([50.7], [10.7], 0.5).iloc[0] == "50.5_10.5"
    assert al.cell_ids([-0.2], [-0.2], 1.0).iloc[0] == "-1.0_-1.0"


def test_stockpile_range_propagates_into_the_interval():
    draws = 200
    rng = np.random.default_rng(0)
    narrow = rng.uniform(49, 51, draws)
    wide = rng.uniform(5, 500, draws)
    s = np.tile(scores(1), (1, draws))
    _, a = rn.scenario_probabilities(towns(), s, ATTACK, {"U": narrow}, 1.0)
    _, b = rn.scenario_probabilities(towns(), s, ATTACK, {"U": wide}, 1.0)
    width = lambda x: np.percentile(x, 95, axis=1) - np.percentile(x, 5, axis=1)  # noqa: E731
    assert (width(b) >= width(a) - 1e-9).all() and (width(b) > width(a)).any()


def test_model_spread_propagates_into_the_interval():
    w = {"U": np.full(50, 20.0)}
    same = np.tile(scores(1), (1, 50))
    varied = scores(50)
    _, a = rn.scenario_probabilities(towns(), same, ATTACK, w, 1.0)
    _, b = rn.scenario_probabilities(towns(), varied, ATTACK, w, 1.0)
    assert np.ptp(a, axis=1).max() == pytest.approx(0)
    assert np.ptp(b, axis=1).max() > 0.01


def attacker(**over) -> dict:
    return {
        "state": "U",
        "stock_year": 2000,
        "inventory_low": ["deployed", "s"],
        "inventory_high": ["military_stockpile", "s"],
        "theatre_share": [0.5, 0.5, 0.5],
        "reliability": {"all": [0.8, 0.8, 0.8]},
        "fraction_lost_to_defences": [0.1, 0.1, 0.1],
    } | over


def inventory_table(low=100.0, high=100.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("deployed", low),
            ("military_stockpile", high),
        ],
        columns=["count_basis", "central"],
    ).assign(scenario_year=2000, state="U", delivery="unspecified", source_id="s")


NO_MIX = pd.DataFrame(columns=["year", "state", "delivery", "share"])


def test_delivered_warheads_follow_the_inventory_and_lose_to_each_assumption():
    rng = np.random.default_rng(0)
    out = st.draw_delivered(attacker(), 50, rng, inventory_table(), NO_MIX)
    assert out == pytest.approx(np.full(50, 100 * 0.5 * 0.8 * 0.9))
    half = st.draw_delivered(attacker(stock_multiplier=0.5), 50, rng, inventory_table(), NO_MIX)
    assert half == pytest.approx(out * 0.5)
    more = st.draw_delivered(attacker(), 50, rng, inventory_table(200.0, 200.0), NO_MIX)
    assert more == pytest.approx(out * 2)


def test_inventory_range_is_drawn_between_its_cited_ends():
    rng = np.random.default_rng(0)
    a = attacker(theatre_share=[1, 1, 1], reliability={"all": [1, 1, 1]})
    a["fraction_lost_to_defences"] = [0, 0, 0]
    out = st.draw_delivered(a, 2000, rng, inventory_table(100.0, 300.0), NO_MIX)
    assert out.min() >= 100 and out.max() <= 300 and np.ptp(out) > 100


def test_interceptors_take_off_at_most_one_warhead_each_and_never_go_below_zero():
    rng = np.random.default_rng(0)
    a = attacker(interceptors=10)
    out = st.draw_delivered(a, 500, rng, inventory_table(), NO_MIX)
    assert out.max() <= 36 and out.min() >= 26
    b = attacker(interceptors=1000)
    assert st.draw_delivered(b, 500, rng, inventory_table(), NO_MIX).min() == 0


def mix_table() -> pd.DataFrame:
    return pd.DataFrame(
        [(2000, "U", "icbm", 0.25), (2000, "U", "slbm", 0.75), (1990, "U", "bomber", 1.0)],
        columns=["year", "state", "delivery", "share"],
    )


def test_warheads_split_by_delivery_and_add_up_to_the_total():
    a = attacker(
        reliability={"by_delivery": {"icbm": [1, 1, 1], "slbm": [0.5, 0.5, 0.5]}},
        fraction_lost_to_defences=[0, 0, 0],
    )
    parts = st.draw_by_delivery(a, 20, np.random.default_rng(0), inventory_table(), mix_table())
    assert set(parts) == {"icbm", "slbm"}  # the 1990 row belongs to another year
    assert parts["icbm"]["available"] == pytest.approx(np.full(20, 25.0))
    assert parts["slbm"]["available"] == pytest.approx(np.full(20, 75.0))
    assert parts["icbm"]["delivered"] == pytest.approx(np.full(20, 25 * 0.5 * 1.0))
    assert parts["slbm"]["delivered"] == pytest.approx(np.full(20, 75 * 0.5 * 0.5))
    total = st.draw_delivered(a, 20, np.random.default_rng(0), inventory_table(), mix_table())
    assert total == pytest.approx(parts["icbm"]["delivered"] + parts["slbm"]["delivered"])


def test_a_change_of_mix_changes_what_is_delivered_when_reliability_differs():
    a = attacker(
        reliability={"by_delivery": {"icbm": [1, 1, 1], "slbm": [0.5, 0.5, 0.5]}},
        fraction_lost_to_defences=[0, 0, 0],
    )
    other = mix_table().assign(share=[0.75, 0.25, 1.0])
    rng = np.random.default_rng(0)
    one = st.draw_delivered(a, 5, rng, inventory_table(), mix_table())
    two = st.draw_delivered(a, 5, rng, inventory_table(), other)
    assert two[0] > one[0]


def test_interceptors_come_off_in_proportion_and_a_stock_without_a_mix_is_unspecified():
    a = attacker(interceptors=10)
    parts = st.draw_by_delivery(a, 50, np.random.default_rng(0), inventory_table(), NO_MIX)
    assert set(parts) == {"unspecified"}
    b = attacker(
        interceptors=10,
        reliability={"by_delivery": {"icbm": [1, 1, 1], "slbm": [1, 1, 1]}},
        fraction_lost_to_defences=[0, 0, 0],
    )
    parts = st.draw_by_delivery(b, 50, np.random.default_rng(0), inventory_table(), mix_table())
    assert parts["slbm"]["delivered"] == pytest.approx(3 * parts["icbm"]["delivered"])
    assert (parts["icbm"]["delivered"] + parts["slbm"]["delivered"]).max() <= 50
    assert (parts["icbm"]["available"] == 25).all()


def test_every_scenario_year_but_1950_has_a_delivery_split_and_shares_are_whole():
    mix = pd.read_csv(st.MIX)
    for sc in rn.load_scenarios():
        for a in sc["attackers"]:
            shares = st.mix_of(a, mix)
            if a["stock_year"] == 1950:
                assert shares.empty
                continue
            assert len(shares), (sc["id"], a["state"])
            raw = mix[(mix["state"] == a["state"]) & (mix["year"] == a["stock_year"])]["share"]
            assert raw.sum() == pytest.approx(1.0, abs=0.051), (sc["id"], a["state"])


def test_historical_shares_agree_with_the_cited_rows():
    table, mix = pd.read_csv(st.TABLE), pd.read_csv(st.MIX)
    for state, year in (("US", 1956), ("USSR", 1965)):
        rows = table[
            (table["scenario_year"] == year)
            & (table["state"] == state)
            & (table["count_basis"] == "strategic_force_loading")
            & (table["delivery"] != "unspecified")
        ].set_index("delivery")["central"]
        m = mix[(mix["state"] == state) & (mix["year"] == year)].set_index("delivery")["share"]
        assert (rows / rows.sum()).round(2).to_dict() == m.to_dict()


def test_a_missing_inventory_row_is_an_error_not_a_guess():
    with pytest.raises(ValueError):
        st.inventory(inventory_table(), 1999, "U", "deployed", "s")


def test_every_scenario_reads_its_inventories_from_the_cited_table():
    table = pd.read_csv(st.TABLE)
    rng = np.random.default_rng(0)
    for sc in rn.load_scenarios():
        assert sc["era"] in {"historical", "modern"}
        for a in sc["attackers"]:
            w = st.draw_delivered(a, 20, rng, table, pd.read_csv(st.MIX))
            assert np.isfinite(w).all() and (w >= 0).all()


def test_every_stockpile_row_cites_a_registered_source():
    d = pd.read_csv(ROOT / "data" / "curated" / "stockpiles" / "stockpiles.csv")
    assert d["source_id"].notna().all()
    ids = {s["id"] for s in yaml.safe_load((ROOT / "data" / "sources.yaml").read_text())["sources"]}
    assert set(d["source_id"]) <= ids


@needs_run
def test_the_map_is_of_the_committed_scenarios_and_protocol():
    from nucprob.sources.fetch import sha256

    m = json.loads((OUT / "manifest.json").read_text())
    assert m["draws"] == rn.N_DRAWS and not m["quick"]
    assert m["scenarios_sha256"] == sha256(rn.SCENARIOS)
    assert m["protocol_sha256"] == sha256(ROOT / "configs" / "protocol.yaml")


@needs_run
def test_committed_cells_obey_the_limits():
    """Grid only: no names, no counts of weapons, not ranked, nothing finer than the protocol's."""
    for sc in rn.load_scenarios():
        path = OUT / "cells" / f"{sc['id']}.csv.gz"
        c = pd.read_csv(path)
        assert sc["cell_deg"] >= (1.0 if sc["era"] == "modern" else 0.5)
        assert ((c["cell_lat"] / sc["cell_deg"]) % 1 == 0).all()
        assert ((c["cell_lon"] / sc["cell_deg"]) % 1 == 0).all()
        assert set(c.columns) == {
            "cell_lat",
            "cell_lon",
            "p_median",
            "p_low",
            "p_high",
            "p_low_model_only",
            "p_high_model_only",
            "p_low_stockpile_only",
            "p_high_stockpile_only",
            "holds_sealed_town",
        }
        order = c.sort_values(["cell_lat", "cell_lon"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(c, order)
        assert ((c["p_low"] <= c["p_median"]) & (c["p_median"] <= c["p_high"])).all()


@needs_run
def test_committed_scenarios_respond_to_their_stockpile():
    s = pd.read_csv(OUT / "scenarios.csv").set_index("scenario")
    for sc in rn.load_scenarios():
        other = sc.get("compare_with")
        if not other:
            continue
        a, b = (
            pd.read_csv(OUT / "cells" / f"{sc['id']}.csv.gz"),
            pd.read_csv(OUT / "cells" / f"{other}.csv.gz"),
        )
        joined = a.merge(b, on=["cell_lat", "cell_lon"], suffixes=("_a", "_b"))
        assert len(joined)
        assert (joined["p_median_a"] - joined["p_median_b"]).abs().max() > 0.01, sc["id"]
    assert (s["cells"] > 0).all()


@needs_run
def test_every_modern_scenario_is_labelled_as_extrapolation():
    text = (OUT / "viewer" / "index.html").read_text(encoding="utf-8")
    assert "EXTRAPOLATION" in text
    assert "http://" not in text and "https://" not in text
    for sc in rn.load_scenarios():
        if sc["era"] == "modern":
            assert "extrapolation" in sc["evidence"].lower()
    shift = pd.read_csv(OUT / "domain_shift.csv")
    assert (shift["measure"] == "two-sample ROC-AUC").sum() == 2


@needs_run
def test_by_delivery_output_holds_no_place_and_adds_up():
    d = pd.read_csv(OUT / "by_delivery.csv")
    assert set(d.columns) == {
        "scenario",
        "attacker",
        "stock_year",
        "delivery",
        "available_low",
        "available_median",
        "available_high",
        "delivered_low",
        "delivered_median",
        "delivered_high",
    }
    total = pd.read_csv(OUT / "delivered.csv").set_index(["scenario", "attacker"])
    summed = d.groupby(["scenario", "attacker"])["delivered_median"].sum()
    gap = (summed - total["delivered_median"]).abs() / total["delivered_median"].clip(lower=1)
    assert len(summed) == len(total) and gap.max() < 0.25
    assert set(d.loc[d["stock_year"] == 1950, "delivery"]) == {"unspecified"}
    assert not (set(d.loc[d["stock_year"] != 1950, "delivery"]) & {"unspecified"})


@needs_run
def test_the_map_was_run_on_the_committed_stockpile_tables():
    from nucprob.sources.fetch import sha256

    m = json.loads((OUT / "manifest.json").read_text())
    assert m["stockpiles_sha256"] == sha256(st.TABLE)
    assert m["delivery_mix_sha256"] == sha256(st.MIX)


@needs_run
def test_the_viewer_holds_no_town_name():
    text = (OUT / "viewer" / "index.html").read_text(encoding="utf-8").lower()
    for name in ("moscow", "washington", "beijing", "omaha", "severodvinsk"):
        assert name not in text
