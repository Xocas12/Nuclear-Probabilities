"""pop_rank_pct is ranked over the same population floor in every bloc country and every
transfer table (issue #7): a source that goes down to 5,000 must not shift its towns' ranks
against a source that stops at 10,000."""

import numpy as np
import pandas as pd
import pytest

from nucprob import places
from nucprob.features.population import RANK_FLOOR
from nucprob.features.population import population as bloc_population
from nucprob.paths import CURATED
from nucprob.transfer import features as transfer

# The same four towns of 10,000+ in both countries; "Deep" also lists four of 5,000-9,999, as
# the USSR's pop-stat tables do and East Germany's yearbook does not.
TOP = [12_000, 30_000, 80_000, 250_000]
SMALL = [5_200, 6_500, 8_000, 9_999]


def table(country_col: str) -> pd.DataFrame:
    pops = TOP + TOP + SMALL
    n = len(pops)
    return pd.DataFrame(
        {
            "lat": 50 + np.arange(n) * 0.5,
            "lon": np.full(n, 20.0),
            "pop": pops,
            country_col: ["Shallow"] * 4 + ["Deep"] * 8,
            "region": "r",
        }
    )


def check_floor(rank: pd.Series, t: pd.DataFrame, country_col: str) -> None:
    deep = t[country_col] == "Deep"
    above = t["pop"] >= RANK_FLOOR
    # a town of 10,000+ ranks the same whether or not its country's table goes below 10,000
    assert rank[deep & above].tolist() == pytest.approx(rank[~deep].tolist())
    assert rank[~deep].tolist() == pytest.approx([0.25, 0.5, 0.75, 1.0])
    assert (rank[~above] == 0).all()


def test_rank_floor_is_the_universe_threshold():
    assert RANK_FLOOR == places.UNIVERSE == 10_000


def test_bloc_pop_rank_pct_uses_the_common_floor():
    t = table("country_1956").assign(pop_year=1956, pop_prewar=np.nan, pop_prewar_year=1939)
    check_floor(bloc_population(t)["pop_rank_pct"], t, "country_1956")


def test_transfer_pop_rank_pct_uses_the_common_floor():
    t = table("country")
    check_floor(transfer.population(t)["pop_rank_pct"], t, "country")


def test_every_transfer_town_table_reaches_the_floor():
    """Every town table of the transfer regions holds only towns at or above the floor, so the
    floor, not the table, decides what a transfer town is ranked against."""
    csvs = sorted(CURATED.glob("gazetteer/towns_*.csv"))
    assert len(csvs) >= 9
    for path in csvs:
        pop = pd.to_numeric(pd.read_csv(path)["pop"], errors="coerce").dropna()
        assert pop.min() >= RANK_FLOOR, path.name
