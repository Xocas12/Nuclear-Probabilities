"""The algorithm zoo: every classifier as a factory returning an unfitted scikit-learn estimator
with `predict_proba`.

Linear, kernel, neighbour and neural models get median imputation and scaling. Tree ensembles
that handle missing values natively (HistGradientBoosting, LightGBM, XGBoost, CatBoost) get the
raw features; the others get median imputation. Optional libraries (xgboost, catboost,
interpret) are used only if installed (`uv sync --extra playground`).
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib.util import find_spec

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

SEED = 0


@dataclass(frozen=True)
class Algorithm:
    factory: Callable
    family: str
    note: str


def _scaled(model):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), model)


def _imputed(model):
    return make_pipeline(SimpleImputer(strategy="median"), model)


def _lightgbm():
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=20,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=SEED,
        n_jobs=1,
        verbose=-1,
    )


def _xgboost():
    from xgboost import XGBClassifier

    return XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=SEED,
        n_jobs=1,
        eval_metric="logloss",
    )


def _catboost():
    from catboost import CatBoostClassifier

    return CatBoostClassifier(
        iterations=400,
        depth=5,
        learning_rate=0.05,
        random_seed=SEED,
        verbose=False,
        thread_count=1,
        allow_writing_files=False,
    )


def _ebm():
    from interpret.glassbox import ExplainableBoostingClassifier

    return ExplainableBoostingClassifier(random_state=SEED, n_jobs=1)


ALGORITHMS: dict[str, Algorithm] = {
    "dummy": Algorithm(
        lambda: DummyClassifier(strategy="prior"), "baseline", "predicts the base rate"
    ),
    "logit": Algorithm(
        lambda: _scaled(LogisticRegression(max_iter=5000)), "linear", "L2 logistic regression"
    ),
    "logit_l1": Algorithm(
        lambda: _scaled(LogisticRegression(penalty="l1", solver="liblinear", C=0.5, max_iter=5000)),
        "linear",
        "L1 (lasso) logistic regression: sparse",
    ),
    "spline_logit": Algorithm(
        lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            SplineTransformer(n_knots=5, degree=3),
            StandardScaler(),
            LogisticRegression(C=0.3, max_iter=5000),
        ),
        "additive",
        "logistic regression on cubic splines of each feature (a GAM-like additive model)",
    ),
    "nb": Algorithm(lambda: _scaled(GaussianNB()), "probabilistic", "Gaussian naive Bayes"),
    "knn": Algorithm(
        lambda: _scaled(KNeighborsClassifier(n_neighbors=25, weights="distance")),
        "neighbours",
        "k nearest neighbours (k=25, distance-weighted)",
    ),
    "svm": Algorithm(
        lambda: _scaled(SVC(C=1.0, kernel="rbf", probability=True, random_state=SEED)),
        "kernel",
        "RBF support vector machine with Platt probabilities",
    ),
    "mlp": Algorithm(
        lambda: _scaled(
            MLPClassifier(
                hidden_layer_sizes=(64, 32),
                alpha=1e-3,
                max_iter=2000,
                early_stopping=True,
                random_state=SEED,
            )
        ),
        "neural",
        "two-layer perceptron with early stopping",
    ),
    "tree": Algorithm(
        lambda: _imputed(DecisionTreeClassifier(max_depth=5, min_samples_leaf=20)),
        "tree",
        "a single decision tree (depth 5)",
    ),
    "rf": Algorithm(
        lambda: _imputed(
            RandomForestClassifier(
                n_estimators=500, min_samples_leaf=3, n_jobs=1, random_state=SEED
            )
        ),
        "ensemble",
        "random forest",
    ),
    "extratrees": Algorithm(
        lambda: _imputed(
            ExtraTreesClassifier(n_estimators=500, min_samples_leaf=3, n_jobs=1, random_state=SEED)
        ),
        "ensemble",
        "extremely randomised trees",
    ),
    "hgb": Algorithm(
        lambda: HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, random_state=SEED),
        "boosting",
        "scikit-learn histogram gradient boosting",
    ),
    "lgbm": Algorithm(_lightgbm, "boosting", "LightGBM, the project's default"),
}
if find_spec("xgboost"):
    ALGORITHMS["xgb"] = Algorithm(_xgboost, "boosting", "XGBoost")
if find_spec("catboost"):
    ALGORITHMS["catboost"] = Algorithm(_catboost, "boosting", "CatBoost")
if find_spec("interpret"):
    ALGORITHMS["ebm"] = Algorithm(
        _ebm, "additive", "Explainable Boosting Machine: a GA2M, interpretable"
    )

# Slow on large tables; left out of "all" (ask for them by name).
SLOW = {"svm", "ebm"}


def algorithms(names: str | list[str]) -> dict[str, Algorithm]:
    """Resolve "all", "fast" or a comma-separated list of names."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    if names in (["all"], ["fast"]):
        return {k: v for k, v in ALGORITHMS.items() if k not in SLOW}
    unknown = [n for n in names if n not in ALGORITHMS]
    if unknown:
        raise KeyError(f"unknown algorithms {unknown}; known: {sorted(ALGORITHMS)}")
    return {n: ALGORITHMS[n] for n in names}
