"""A playground for trying machine-learning algorithms on every dataset of the project.

    python -m nucprob.playground list                      # datasets and algorithms
    python -m nucprob.playground run -d sac1956 -a logit,rf,lgbm,xgb
    python -m nucprob.playground run -d napb90:very_high -a all -f population,military
    python -m nucprob.playground transfer --train sac1956 --test transfer:cd_1980_square_leg
    python -m nucprob.playground explain -d sac1956 -a lgbm

Or from Python or a notebook:

    from nucprob.playground import load, algorithms, evaluate
    ds = load("sac1956")
    board = evaluate(ds, ["logit", "rf", "lgbm"])

Every dataset comes as a `Data` with one row per place and:
- the features, by family;
- the target `y`;
- the place's id, name, country, coordinates, spatial block and the plan's year.

The sealed test blocks of a dataset (PLAN section 5.1) are left out unless asked for. They are
kept for the single final scoring of milestone M8.
"""

from nucprob.playground.algos import ALGORITHMS, algorithms
from nucprob.playground.datasets import DATASETS, Data, load
from nucprob.playground.evaluate import evaluate, transfer

__all__ = ["ALGORITHMS", "DATASETS", "Data", "algorithms", "evaluate", "load", "transfer"]
