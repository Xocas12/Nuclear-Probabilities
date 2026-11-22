"""The playground's algorithms and evaluation run on a small synthetic dataset."""

import numpy as np
import pandas as pd

from nucprob.playground import ALGORITHMS, Data, evaluate, transfer
from nucprob.playground.datasets import families
from nucprob.playground.evaluate import explain


def toy(n: int = 400, seed: int = 0) -> Data:
    rng = np.random.default_rng(seed)
    lat, lon = rng.uniform(40, 60, n), rng.uniform(20, 60, n)
    log_pop = rng.normal(4.5, 0.5, n)
    km = rng.uniform(0, 3, n)
    y = (log_pop + rng.normal(0, 0.4, n) - 0.3 * km > 4.6).astype(int)
    frame = pd.DataFrame(
        {
            "id": [f"p{i}" for i in range(n)],
            "name": "",
            "country": rng.choice(["A", "B", "C"], n),
            "lat": lat,
            "lon": lon,
            "year": 1956,
            "block": [f"{int(a // 3)}_{int(b // 3)}" for a, b in zip(lat, lon, strict=True)],
            "sealed": False,
            "y": y,
            "log_pop": log_pop,
            "log_km_to_naval_base": km,
        }
    )
    frame.loc[::17, "log_km_to_naval_base"] = np.nan  # missing values must be handled
    feats = ["log_pop", "log_km_to_naval_base"]
    return Data("toy", "synthetic", frame, feats, families(feats))


def test_every_algorithm_beats_chance_or_is_the_baseline():
    d = toy()
    board = evaluate(d, [n for n in ALGORITHMS if n != "svm"], k=3, verbose=False)
    got = board.set_index("algorithm")["roc_auc_mean"]
    for name, auc in got.items():
        if name != "dummy":
            assert auc > 0.6, (name, auc)


def test_select_and_transfer():
    d = toy()
    assert d.select("population").features == ["log_pop"]
    assert d.select(drop="population").features == ["log_km_to_naval_base"]
    board = transfer(d, toy(seed=1), ["logit"], verbose=False)
    assert board["roc_auc"].iloc[0] > 0.7


def test_explain_ranks_population_first():
    out = explain(toy(), "lgbm", n_repeats=2)
    assert out["feature"].iloc[0] == "log_pop"
