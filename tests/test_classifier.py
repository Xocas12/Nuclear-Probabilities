"""The pre-committed classifier: as-of features, positive-unlabeled bags, holdouts, the seal."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score

from nucprob.classifier import evaluate as ev
from nucprob.classifier import features as cf
from nucprob.classifier import fit as cfit
from nucprob.classifier import run as crun
from nucprob.classifier import sealed as csealed
from nucprob.paths import PROCESSED
from nucprob.plans import exercise_gate


def nmc_table() -> pd.DataFrame:
    rows = [("USA", 1950, 1.0), ("USA", 1955, 2.0), ("USA", 1960, 3.0), ("RUS", 1950, 9.0)]
    d = pd.DataFrame(rows, columns=["stateabb", "year", "nmc_log_cinc"])
    for c in cf.NMC_FEATURES[1:]:
        d[c] = d["nmc_log_cinc"]
    return d


def test_national_power_never_reads_a_later_year():
    assert cf.nmc_as_of(nmc_table(), "USA", 1959)["nmc_log_cinc"] == 2.0
    assert cf.nmc_as_of(nmc_table(), "USA", 1960)["nmc_log_cinc"] == 3.0
    assert cf.nmc_as_of(nmc_table(), "USA", 1949).isna().all()


def sites() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site": list("abcd"),
            "role": ["nike_site", "nike_site", "hawk_site", "radar_station"],
            "lat": [50.0, 51.0, 52.0, 53.0],
            "lon": [8.0, 8.0, 8.0, 8.0],
            "from_year": [1958, 1962, np.nan, np.nan],
            "until_year": [1960, np.nan, np.nan, np.nan],
            "in_role_1965": [False, True, True, False],
        }
    )


def test_a_site_counts_only_while_in_being():
    assert cf.sites_as_of(sites(), 1959)["site"].tolist() == ["a", "c"]
    assert cf.sites_as_of(sites(), 1961)["site"].tolist() == ["c"]
    assert cf.sites_as_of(sites(), 1965)["site"].tolist() == ["b", "c"]


def test_defence_features_are_empty_with_no_table_and_measure_distance_with_one():
    none = cf.defence_features([50.0], [8.0], pd.DataFrame())
    assert none.isna().all(axis=None)
    near = cf.defence_features([50.0, 60.0], [8.0, 8.0], sites())
    assert near.loc[0, "log_km_to_sam"] < near.loc[1, "log_km_to_sam"]
    assert near.loc[0, "log_air_defence_sites_50km"] > 0
    assert near.loc[1, "log_air_defence_sites_50km"] == 0


def test_the_1956_table_covers_only_countries_it_documents_and_only_units_in_being():
    sites = cf.load_defence_sites("bloc_1956")
    if not (cf.CURATED / "features" / "bloc_air_defence_1956.csv").exists():
        pytest.skip("no table")
    assert "S-25 Berkut system, Moscow area" not in set(sites["site"])
    table = pd.read_csv(cf.CURATED / "features" / "bloc_air_defence_1956.csv")
    outside = table[table["in_june_1956"] != "yes"]["site"]
    assert not set(sites["site"]) & (
        set(outside) - set(table[table["in_june_1956"] == "yes"]["site"])
    )
    towns = pd.DataFrame(
        {
            "place_id": ["a", "b"],
            "country": ["USSR", "Hungary"],
            "lat": [55.7, 47.5],
            "lon": [37.6, 19.0],
        }
    )
    out = cf.add_defence(towns, cf.BLOC)
    assert out[cf.DEFENCE].iloc[0].notna().all()
    assert out[cf.DEFENCE].iloc[1].isna().all()  # Hungary has one radar in the table


def test_bags_keep_positives_and_complete_negatives_and_draw_only_from_incomplete_lists():
    y = np.array([1, 0, 0, 1, 0, 0, 0, 0])
    doc = np.array(["c", "c", "c", "p", "p", "p", "p", "p"])
    complete = np.array([True] * 3 + [False] * 5)
    # Place x is listed in the complete list and sits unlabeled in the incomplete one.
    place = np.array(["x", "a", "b", "d", "x", "e", "f", "g"])
    for seed in range(40):
        rows = cfit.bag_rows(y, doc, complete, place, np.random.default_rng(seed))
        assert {0, 1, 2, 3} <= set(rows)
        drawn = set(rows) - {0, 1, 2, 3}
        assert len(drawn) == 1  # as many unlabeled as the list has positives
        assert 4 not in drawn  # a listed place is never drawn as a negative


def toy(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    d = pd.DataFrame(
        {
            "place_id": [f"p{i}" for i in range(n)],
            "plan_id": rng.choice(["A", "B", "C"], n),
            "lat": rng.uniform(40, 60, n),
            "lon": rng.uniform(0, 40, n),
            "log_pop": rng.normal(4.5, 0.5, n),
            "country": rng.choice(["X", "Y"], n),
        }
    )
    d["group"] = d["plan_id"]
    d["block"] = "b"
    d["doc_type"] = "exercise"
    d["complete"] = d["plan_id"].ne("C")
    d["year"] = d["plan_id"].map({"A": 1950, "B": 1960, "C": 1970})
    d["listed"] = (d["log_pop"] + rng.normal(0, 0.3, n) > 4.9).astype(int)
    return d


class Spy:
    """Records what each fit saw, and scores nothing in particular."""

    def __init__(self, seen: list):
        self.seen = seen

    def __call__(self, seed: int = 0):
        seen = self.seen

        class M:
            def fit(self, x, y):
                seen.append(x.copy())
                return self

            def predict_proba(self, x):
                return np.tile([0.5, 0.5], (len(x), 1))

        return M()


def test_every_bag_fits_each_town_on_its_own_label():
    """A bag may drop unlabeled rows but never reorders or replaces the labels it fits on."""
    d = toy()
    d["row"] = np.arange(len(d))
    pairs: list = []

    class Pair:
        def __call__(self, seed: int = 0):
            class M:
                def fit(self, x, y):
                    pairs.append((x["row"].to_numpy(), np.asarray(y)))
                    return self

            return M()

    cfit.fit_bagged(cfit.Spec("pair", Pair(), ["log_pop", "row"]), d, n_bags=5)
    assert len(pairs) == 5
    listed = d["listed"].to_numpy()
    for rows, y in pairs:
        assert np.array_equal(y, listed[rows])
    # And the bagged logistic ranks the toy's listed towns, which follow population, above chance.
    fitted = cfit.fit_bagged(cfit.Spec("pop", cfit.population_rule, ["log_pop"]), d, n_bags=5)
    assert average_precision_score(listed, fitted.score(d)) > 2 * listed.mean()


def test_leave_one_document_out_never_trains_on_the_group_it_scores():
    d = toy()
    seen: list = []
    spec = cfit.Spec("spy", Spy(seen), ["log_pop", "group"])
    out, held = ev.leave_one_document_out(d, [spec], n_bags=2)
    assert len(held) == len(d)
    assert {r["holdout"] for r in out} == {f"leave-one-document-out ({g})" for g in "ABC"}
    trained_on = {frozenset(x["group"]) for x in seen}
    assert trained_on == {frozenset("AB"), frozenset("AC"), frozenset("BC")}


def test_leave_one_document_out_takes_the_left_out_towns_out_of_training():
    d = toy()
    d = pd.concat([d, d[d["group"] == "A"].assign(group="B", plan_id="B2")], ignore_index=True)
    seen: list = []
    spec = cfit.Spec("spy", Spy(seen), ["log_pop", "group", "place_id"])
    ev.leave_one_document_out(d, [spec], n_bags=2)
    places_a = set(d.loc[d["group"] == "A", "place_id"])
    # Fits that scored group A saw none of its towns, under any other document either.
    without_a = [x for x in seen if "A" not in set(x["group"])]
    assert any(not (set(x["place_id"]) & places_a) for x in without_a)
    seen.clear()
    ev.leave_one_document_out(d, [spec], n_bags=2, keep_places=True)
    assert any(set(x["place_id"]) & places_a for x in seen if "A" not in set(x["group"]))


def test_block_bootstrap_is_wider_than_rows_when_a_gap_lives_in_one_block():
    rng = np.random.default_rng(0)
    n = 400
    y = (rng.random(n) < 0.3).astype(int)
    block = np.repeat(np.arange(8), 50)
    a = rng.random(n)
    b = a.copy()
    # All of the difference is in one block.
    a[block == 0] = y[block == 0] + rng.random(50) * 0.1
    doc = np.array(["L"] * n)
    row = ev.paired_bootstrap(y, a, b, doc, n=200)
    clustered = ev.block_bootstrap(y, a, b, doc, block, n=200)
    assert clustered["block_high"] - clustered["block_low"] > row["high"] - row["low"]


def test_a_place_stays_on_one_side_of_a_spatial_split_in_every_document():
    one = toy().assign(complete=True)
    d = pd.concat([one, one.assign(plan_id="other", group="other")], ignore_index=True)
    seen: list = []
    ev.spatial_scores(d, [cfit.Spec("spy", Spy(seen), ["log_pop", "place_id"])], 1)
    assert len(seen) == ev.N_FOLDS * len(ev.GRID_OFFSETS)
    for x in seen:
        # Each place in a training set brings both of its documents: none is split.
        assert x["place_id"].value_counts().eq(2).all()
        assert x["place_id"].nunique() < one["place_id"].nunique()


def test_paired_bootstrap_sees_nothing_between_equal_models_and_finds_a_real_gap():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 400)
    doc = np.array(["a"] * 200 + ["b"] * 200)
    noise = rng.uniform(size=400)
    same = ev.paired_bootstrap(y, noise, noise, doc, n=100)
    assert same["delta"] == 0 and not same["excludes_zero"]
    gap = ev.paired_bootstrap(y, y + 0.1 * noise, noise, doc, n=100)
    assert gap["delta"] > 0.3 and gap["excludes_zero"]


def test_the_fast_pr_auc_is_scikit_learns_with_ties():
    rng = np.random.default_rng(3)
    for n in (5, 40, 700):
        y = rng.integers(0, 2, n)
        y[0] = 1
        for s in (rng.uniform(size=n), rng.integers(0, 4, n).astype(float)):
            assert ev.pr_auc(y, s) == pytest.approx(average_precision_score(y, s), abs=1e-12)


def test_weighted_pr_auc_leaves_out_lists_too_small_to_score():
    y = np.array([1, 0, 1, 1, 0, 0])
    s = np.array([0.9, 0.1, 0.1, 0.9, 0.8, 0.2])
    doc = np.array(["small", "small", "big", "big", "big", "big"])
    assert ev.weighted_pr_auc(y, s, doc) == pytest.approx(average_precision_score(y[2:], s[2:]))


def test_calibration_is_cross_fitted_and_preserves_order():
    rng = np.random.default_rng(1)
    p = rng.uniform(size=500)
    y = (rng.uniform(size=500) < p).astype(int)
    fold = rng.integers(0, 5, 500)
    cal = ev.cross_fit_isotonic(y, p**3, fold)
    # The miscalibrated score is brought close to the truth.
    assert np.mean((cal - p) ** 2) < np.mean((p**3 - p) ** 2)
    curve = ev.calibration_curve(y, p)
    assert len(curve) == 10 and curve["n"].sum() == 500


def test_the_seal_refuses_a_second_read(tmp_path):
    lock = tmp_path / "sealed" / "LOCK.json"
    csealed.claim(lock, {"scored": "now"})
    with pytest.raises(csealed.AlreadyScored):
        csealed.claim(lock, {"scored": "later"})


def test_no_sealed_row_reaches_a_model():
    d = toy().assign(sealed=False)
    d.loc[d.index[:10], "sealed"] = True
    assert not crun.usable(d)["sealed"].any()
    assert len(crun.usable(d)) == len(d) - 10


def test_the_exercise_gate_counts_documents_and_says_what_it_is():
    reg = pd.DataFrame(
        {
            "plan_id": ["wp_a", "wp_b", "wp_c", "us_a"],
            "group": ["a", "b", "c", "d"],
            "role": ["train"] * 4,
        }
    )
    rule = {"min_positives": 50, "min_documents": 3}
    no = exercise_gate({"wp_a": 60, "wp_b": 1}, reg, rule)
    assert not no["allowed"] and "2 documents" in no["reason"]
    yes = exercise_gate({"wp_a": 30, "wp_b": 15, "wp_c": 5, "us_a": 900}, reg, rule)
    assert yes["allowed"] and yes["linked_positives"] == 50
    assert "exercise-based" in yes["attacker"]


@pytest.mark.skipif(
    not (PROCESSED / "classifier_table.parquet").exists(), reason="classifier table not built"
)
def test_the_table_keeps_documents_apart_and_never_trains_on_a_mirror():
    t = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    assert t.duplicated(["plan_id", "place_id"]).sum() == 0
    groups, _ = crun.scopes(crun.usable(t), crun.positives_of(t))
    for name, rows in groups.items():
        assert set(rows["role"]) == {"train"}, name
        assert not rows["doc_type"].isin(["mirror", "civil_defence", "reconstruction"]).any()
        assert not rows["sealed"].astype(bool).any()
    plans_only = groups["global, plan documents only"]
    assert not plans_only["doc_type"].isin(["exercise", "wargame", "training"]).any()
    # Sites and plants as of the document: Burza (1961) cannot see a site built after 1961.
    west = t[t["plan_id"].isin(["wp_1961_burza", "wp_1967_lato67"])].dropna(
        subset=["log_km_to_sam"]
    )
    pivot = west.pivot_table(index="place_id", columns="plan_id", values="log_power_mw_25km")
    both = pivot.dropna()
    assert (both["wp_1961_burza"] <= both["wp_1967_lato67"] + 1e-9).all()
    assert (both["wp_1961_burza"] < both["wp_1967_lato67"]).any()


def test_the_sealed_reading_is_the_eleventh_amendments():
    """Selected candidate against population + country on never_scored places is the one primary row;
    a gain needs both intervals clear of zero; every model gets a row in each population."""
    rng = np.random.default_rng(0)
    n = 400
    y = (rng.uniform(size=n) < 0.3).astype(int)
    sealed = pd.DataFrame(
        {
            "listed": y,
            "plan_id": "sac",
            "block": rng.integers(0, 40, n),
            "never_scored": rng.uniform(size=n) < 0.6,
        }
    )
    good = y + rng.normal(0, 0.3, n)
    noise = rng.normal(0, 1, n)
    scores = {
        ("s", "LightGBM, all permitted"): good,
        ("s", "population + country"): noise,
        ("s", "population rule"): good,
    }
    met, comp = csealed.read(sealed, scores, {"s": "LightGBM, all permitted"}, n=200)
    assert len(met) == 3 * 2 and set(met["population"]) == set(csealed.POPULATIONS)
    assert (met["pr_auc_low"] <= met["pr_auc"]).all() and (
        met["pr_auc"] <= met["pr_auc_high"]
    ).all()
    assert comp["primary"].sum() == 1
    primary = comp[comp["primary"]].iloc[0]
    assert (primary["population"], primary["against"]) == ("never_scored", "population + country")
    assert primary["rows"] == sealed["never_scored"].sum()
    assert primary["verdict"] == "gain"
    same = comp[(comp["against"] == "population rule")]
    assert (same["delta"] == 0).all() and (same["verdict"] == "neither").all()
