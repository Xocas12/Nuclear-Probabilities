"""Each holdout, on a table small enough to see what it did. A test here fails if the branch it names
is changed: the committed outputs cannot catch that, because their hashes do not read the code."""

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from nucprob.classifier import evaluate as ev
from nucprob.classifier import fit as cfit
from nucprob.classifier.fit import Spec, logistic_all
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.outputs import MILESTONES, milestone_hashes
from nucprob.paths import CURATED, ROOT, RUNS
from nucprob.plans import gate, plans, protocol
from nucprob.sources.fetch import sha256

SPLITS = CURATED / "splits"


def small_table(n: int = 240, seed: int = 0) -> pd.DataFrame:
    """Positives are the large towns, on a spread of points, so that any working fit ranks them first."""
    rng = np.random.default_rng(seed)
    pop = rng.uniform(4, 6, n)
    return pd.DataFrame(
        {
            "plan_id": np.where(np.arange(n) % 2, "early", "late"),
            "group": np.where(np.arange(n) % 2, "g1", "g2"),
            "place_id": [f"p{i}" for i in range(n)],
            "year": np.where(np.arange(n) % 2, 1950, 1970),
            "lat": rng.uniform(40, 60, n),
            "lon": rng.uniform(0, 40, n),
            "log_pop": pop,
            "listed": (pop > 5).astype(int),
            "complete": False,
            "doc_type": "exercise",
            "block": "b",
        }
    )


class Spy:
    """Stands in for fit_bagged, keeps what each fit was given, and scores by log_pop."""

    def __init__(self):
        self.trained = []

    def __call__(self, spec, train, n_bags=1, seed=0):
        self.trained.append(train.copy())

        class Fitted:
            def score(self, x):
                return x["log_pop"].to_numpy()

        return Fitted()


SPEC = Spec("m", logistic_all, ["log_pop"])


def test_isotonic_calibration_of_a_town_never_reads_that_towns_label():
    rng = np.random.default_rng(3)
    p = rng.uniform(size=200)
    y = (rng.uniform(size=200) < p).astype(int)
    fold = rng.integers(0, 5, 200)
    base = ev.cross_fit_isotonic(y, p, fold)
    flipped = y.copy()
    flipped[17] = 1 - flipped[17]
    moved = ev.cross_fit_isotonic(flipped, p, fold)
    assert moved[17] == base[17]
    others = fold != fold[17]
    assert (moved[others] != base[others]).any()  # the label does reach the other folds


def test_the_temporal_holdout_never_fits_on_the_period_it_scores(monkeypatch):
    spy = Spy()
    monkeypatch.setattr(ev, "fit_bagged", spy)
    t = small_table()
    rows, kept = ev.temporal(t, [SPEC], 1)
    assert len(kept) == 2 and len(spy.trained) == 2
    assert spy.trained[0]["year"].max() <= ev.TEMPORAL_CUT
    assert spy.trained[1]["year"].min() > ev.TEMPORAL_CUT
    forward, backward = kept.values()
    assert set(forward["plan_id"]) == {"late"} and set(backward["plan_id"]) == {"early"}
    assert rows


def test_leave_one_document_out_removes_the_documents_towns_from_training(monkeypatch):
    spy = Spy()
    monkeypatch.setattr(ev, "fit_bagged", spy)
    t = small_table()
    shared = t.iloc[0].copy()
    shared["plan_id"], shared["group"] = "early", "g1"
    t = pd.concat([t, shared.to_frame().T], ignore_index=True).infer_objects()
    ev.leave_one_document_out(t, [SPEC], 1)
    for train, held_group in zip(spy.trained, sorted(t["group"].unique()), strict=True):
        held = set(t.loc[t["group"] == held_group, "place_id"])
        assert not held & set(train["place_id"])


def test_spatial_folds_score_no_row_a_fit_trained_on(monkeypatch):
    spy = Spy()
    monkeypatch.setattr(ev, "fit_bagged", spy)
    t = small_table()
    ev.spatial_scores(t, [SPEC], 1)
    assert len(spy.trained) == len(ev.GRID_OFFSETS) * ev.N_FOLDS
    lat, lon = t["lat"].to_numpy(), t["lon"].to_numpy()
    fits = iter(spy.trained)
    for offset in ev.GRID_OFFSETS:
        blocks = pd.Series(assign_blocks(lat, lon, BLOCK_KM, offset))
        fold = folds(blocks, t["listed"], ev.N_FOLDS, seed=int(offset))
        for f in range(ev.N_FOLDS):
            train = next(fits)
            assert not set(train["place_id"]) & set(t.loc[fold == f, "place_id"])
            assert not set(blocks[train.index]) & set(blocks[fold == f])


def test_blocks_are_the_protocols_300_km_and_read_lat_as_north():
    assert BLOCK_KM == 300.0
    assert "5 folds of 300 km blocks" in (ROOT / "configs" / "protocol.yaml").read_text()
    # One degree of latitude is about 111 km: 3 degrees north crosses a block edge, 2 does not.
    assert assign_blocks([0.5], [0.5])[0] == "0_0"
    assert assign_blocks([2.5], [0.5])[0] == "0_0"
    assert assign_blocks([3.5], [0.5])[0] == "0_1"
    assert assign_blocks([0.5], [3.5])[0] == "1_0"
    # East-west blocks follow the shrinking of longitude: at 60 north, 3.5 degrees is 195 km.
    assert assign_blocks([60.5], [3.5])[0].split("_")[0] == "0"


def test_a_bagged_fit_learns_the_labels_it_is_given():
    t = small_table()
    spec = Spec("m", logistic_all, ["log_pop"])
    scores = cfit.fit_bagged(spec, t, 5).score(t)
    assert roc_auc_score(t["listed"], scores) > 0.95
    upended = t.assign(listed=1 - t["listed"])
    assert roc_auc_score(t["listed"], cfit.fit_bagged(spec, upended, 5).score(t)) < 0.05


def test_the_committed_gate_is_what_the_rule_gives():
    table = pd.read_csv(RUNS / "evidence" / "state_model_gate.csv").set_index("attacker")
    rule = protocol()["state_models"]
    reg = plans()
    for attacker, row in table.iterrows():
        if attacker.startswith("Warsaw Pact"):
            continue
        # The committed counts put through the rule again: no state may read as allowed by hand.
        assert row["allowed"] == (
            row["independent_plans"] >= rule["min_independent_plans"]
            and row["linked_positives"] >= rule["min_positives"]
            and row["positives_outside_largest"] >= rule["min_positives_outside_largest"]
        ), attacker
    assert not gate({}, reg, rule)["allowed"].any()


def test_the_sealed_set_is_the_one_frozen_on_1_november():
    assert sha256(SPLITS / "sealed_blocks.csv") == (
        "0fbd8055c0ff4bdd27f462f6460be36b93edd4c6cd1eb24e3ab3d6b0e424e01a"
    )
    assert len(pd.read_csv(SPLITS / "sealed_blocks.csv")) == 50


@pytest.mark.parametrize("folder", MILESTONES)
def test_milestone_outputs_are_the_files_their_runs_wrote(folder):
    recorded = json.loads((RUNS / "milestone_hashes.json").read_text())
    current = milestone_hashes()
    names = [n for n in recorded if n.startswith(f"runs/{folder}/")]
    assert names, folder
    for name in names:
        assert current[name] == recorded[name], name
        assert (ROOT / name).exists()


def test_a_manifest_pin_ignores_run_stamps_and_reads_everything_else(tmp_path):
    from nucprob.outputs import manifest_hash

    path = RUNS / "m4-transfer-check" / "manifest.json"
    record = json.loads(path.read_text())
    copy = tmp_path / "manifest.json"
    copy.write_text(json.dumps(record | {"created": "2030-01-01", "git_commit": "0" * 40}))
    assert manifest_hash(copy) == manifest_hash(path)
    copy.write_text(json.dumps(record | {"train": {"rows": 1, "positives": 1}}))
    assert manifest_hash(copy) != manifest_hash(path)


def _protocol_holdouts() -> dict:
    return protocol()["evaluation"]["holdouts"]


def test_the_holdout_constants_are_the_protocols():
    """The settings themselves, read from configs/protocol.yaml: the toy tables above would pass
    with another cut year, grid or fold count."""
    h = _protocol_holdouts()
    assert f"documents dated up to {ev.TEMPORAL_CUT}," in h["temporal"]
    offsets = ", ".join(f"{o:g}" for o in ev.GRID_OFFSETS)
    assert (
        f"{ev.N_FOLDS} folds of {BLOCK_KM:g} km blocks on three shifted grids ({offsets} km)"
        in (h["spatial_blocks"])
    )
    assert len(ev.GRID_OFFSETS) == 3 and len(set(ev.GRID_OFFSETS)) == 3
    assert "groups, not lists" in h["leave_one_plan_out"]


def test_the_temporal_cut_puts_the_protocol_year_in_training_and_the_next_in_scoring(monkeypatch):
    spy = Spy()
    monkeypatch.setattr(ev, "fit_bagged", spy)
    t = small_table()
    t["year"] = np.resize([1955, 1956, 1957, 1960], len(t))
    ev.temporal(t, [SPEC], 1)
    assert set(spy.trained[0]["year"]) == {1955, 1956}
    assert set(spy.trained[1]["year"]) == {1957, 1960}


def test_spatial_scores_use_every_shifted_grid(monkeypatch):
    seen = []

    def spy_blocks(lat, lon, km=BLOCK_KM, offset=0.0):
        seen.append(offset)
        return assign_blocks(lat, lon, km, offset)

    monkeypatch.setattr(ev, "fit_bagged", Spy())
    monkeypatch.setattr(ev, "assign_blocks", spy_blocks)
    ev.spatial_scores(small_table(), [SPEC], 1)
    assert seen == [0.0, 100.0, 200.0]


def test_leave_one_document_out_holds_out_a_whole_group(monkeypatch):
    """Two documents of one group (a wargame and its mirror) are never split across a fit and its
    scoring."""
    spy = Spy()
    monkeypatch.setattr(ev, "fit_bagged", spy)
    t = small_table()
    t["plan_id"] = np.resize(["a1", "a2", "b"], len(t))
    t["group"] = np.where(t["plan_id"] == "b", "gb", "ga")
    rows, kept = ev.leave_one_document_out(t, [SPEC], 1)
    assert len(spy.trained) == 2
    for train in spy.trained:
        assert set(train["group"]) in ({"ga"}, {"gb"})
    assert set(kept.groupby("plan_id").size().index) == {"a1", "a2", "b"}
    assert {r["holdout"] for r in rows} == {
        "leave-one-document-out (ga)",
        "leave-one-document-out (gb)",
    }


def test_a_plain_fit_on_complete_lists_learns_the_labels_it_is_given():
    """The path of the SAC headline: every list complete, so one fit and no bags."""
    t = small_table().assign(complete=True)
    spec = Spec("m", logistic_all, ["log_pop"])
    fitted = cfit.fit_bagged(spec, t, 5)
    assert len(fitted.models) == 1
    assert roc_auc_score(t["listed"], fitted.score(t)) > 0.95
    upended = t.assign(listed=1 - t["listed"])
    assert roc_auc_score(t["listed"], cfit.fit_bagged(spec, upended, 5).score(t)) < 0.05
