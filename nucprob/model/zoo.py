"""Models of the slice (PLAN section 5.4, milestone M1).

- population rule: "hit the N biggest", as a logistic regression on log population alone, so
  it also gives probabilities; its ranking is the population ranking.
- logistic regression (L2) on the population family, then on every feature;
- LightGBM.
"""

from collections.abc import Callable

from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from nucprob.features.registry import FEATURES, by_family


def logistic(c: float = 1.0) -> Pipeline:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=c, max_iter=5000),
    )


def lightgbm(seed: int = 0) -> LGBMClassifier:
    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=20,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=seed,
        verbose=-1,
    )


ALL = list(FEATURES)
POPULATION = by_family(ALL)["population"]

# name -> (factory, feature columns)
MODELS: dict[str, tuple[Callable, list[str]]] = {
    "population rule": (logistic, ["log_pop"]),
    "logistic, population family": (logistic, POPULATION),
    "logistic, all features": (logistic, ALL),
    "LightGBM, all features": (lightgbm, ALL),
}
