"""Fitting: the protocol's baselines and candidates, with bagged positive-unlabeled learning.

A list marked `complete: false` in the registry names only some targets, so a town off it is
unlabeled, not negative (Mordelet and Vert 2014). `fit_bagged` fits 50 models. Each keeps every
positive and every labelled negative of the complete lists, and from each incomplete list draws
as many of its unlabeled towns as it has positives. A town that any document in the training data
lists is never drawn as a negative from an incomplete list. Scores are the mean over the bags;
they rank towns and are not probabilities until calibrated (nucprob.classifier.evaluate).
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from nucprob.classifier.features import DEFENCE, MILITARY, NMC_FEATURES
from nucprob.model.zoo import lightgbm, logistic
from nucprob.transfer.features import COMMON

N_BAGS = 50
N_THREADS = 3  # the machine rule: at most 3 cores
FAMILIES = {
    "population": [
        "log_pop",
        "pop_rank_pct",
        "log_pop_within_25km",
        "log_pop_within_50km",
        "log_pop_within_100km",
        "log_km_to_100k",
    ],
    "administration": ["national_capital", "regional_centre", "log_km_to_capital"],
    "geography": ["elevation_m", "log_relief_10km", "log_km_to_coast"],
    "industry": ["log_power_mw_25km"],
    "transport": [
        "log_airfields_10km",
        "log_airfields_25km",
        "log_airfields_50km",
        "log_km_to_rail",
        "rail_lines_5km",
        "log_km_to_port",
        "log_km_to_major_river",
    ],
    "military": MILITARY,
    "defence": DEFENCE,
    "national_power": NMC_FEATURES,
}
ALL_FEATURES = [*COMMON, *MILITARY, *DEFENCE, *NMC_FEATURES]


def logistic_country(seed: int = 0) -> object:
    """Log population plus one intercept per country; a country unseen in training gets the
    reference level, so on a left-out country this is the population rule."""
    return make_pipeline(
        ColumnTransformer(
            [
                ("pop", StandardScaler(), ["log_pop"]),
                ("country", OneHotEncoder(handle_unknown="ignore"), ["country"]),
            ]
        ),
        LogisticRegression(max_iter=5000),
    )


def population_rule(seed: int = 0):
    return logistic()


def lightgbm_quiet(seed: int = 0):
    m = lightgbm(seed)
    m.set_params(n_jobs=1)
    return m


def logistic_all(seed: int = 0):
    # Median imputation inside the fold; a NaN family says "no table covers this town".
    return make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(max_iter=5000),
    )


@dataclass(frozen=True)
class Spec:
    name: str
    factory: Callable
    columns: list[str]
    baseline: bool = False


def specs() -> list[Spec]:
    return [
        Spec("population rule", population_rule, ["log_pop"], True),
        Spec("population + country", logistic_country, ["log_pop", "country"], True),
        Spec("logistic, all permitted", logistic_all, ALL_FEATURES),
        Spec("LightGBM, all permitted", lightgbm_quiet, ALL_FEATURES),
    ]


def bag_rows(
    y: np.ndarray, doc: np.ndarray, complete: np.ndarray, place: np.ndarray, rng
) -> np.ndarray:
    """Row positions of one bag; see the module docstring."""
    y = np.asarray(y).astype(int)
    keep = (y == 1) | complete
    listed = set(place[y == 1])
    pool = (y == 0) & ~complete & ~np.isin(place, list(listed))
    picks = [np.flatnonzero(keep)]
    for d in np.unique(doc[~complete]):
        here = np.flatnonzero(pool & (doc == d))
        n = int(((doc == d) & (y == 1)).sum())
        if len(here) and n:
            picks.append(rng.choice(here, size=min(n, len(here)), replace=False))
    return np.concatenate(picks)


class Fitted:
    def __init__(self, models: list, columns: list[str]):
        self.models, self.columns = models, columns

    def score(self, x: pd.DataFrame) -> np.ndarray:
        return np.mean([m.predict_proba(x[self.columns])[:, 1] for m in self.models], axis=0)


def fit_bagged(spec: Spec, train: pd.DataFrame, n_bags: int = N_BAGS, seed: int = 1956) -> Fitted:
    """One plain fit if every list is complete, else `n_bags` bags."""
    y = train["listed"].to_numpy(int)
    complete = train["complete"].to_numpy(bool)
    if complete.all():
        return Fitted([spec.factory().fit(train[spec.columns], y)], spec.columns)
    rng = np.random.default_rng(seed)
    doc, place = train["plan_id"].to_numpy(), train["place_id"].to_numpy()
    draws = [bag_rows(y, doc, complete, place, rng) for _ in range(n_bags)]

    def one(b: int, rows: np.ndarray):
        return spec.factory(seed=b).fit(train.iloc[rows][spec.columns], y[rows])

    models = Parallel(n_jobs=N_THREADS, prefer="threads")(
        delayed(one)(b, rows) for b, rows in enumerate(draws)
    )
    return Fitted(models, spec.columns)
