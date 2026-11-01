"""From cited inventories to warheads delivered, for one attacker of a scenario.

    delivered = available x theatre share x mean reliability over the delivery mix, less defences

`available` is a triangular draw from a low inventory (forces deployed or loaded) to a high one (the
military stockpile), with its mode midway, because how much of a reserve could be used is not known.
Each figure comes from data/curated/stockpiles/stockpiles.csv by year, state, count basis and source.
Reliability, theatre share and the losses to defences are given in configs/scenarios.yaml, each with a
source or expressly as a stated assumption. Interceptors take off a uniform draw from none to one warhead
each, an upper bound that assumes every interceptor stops one warhead. Totals by attacker are inputs to the
map; nothing here divides them among places.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from nucprob.paths import CURATED

TABLE = CURATED / "stockpiles" / "stockpiles.csv"
MIX = CURATED / "stockpiles" / "delivery_mix.csv"


def inventory(table: pd.DataFrame, year: int, state: str, basis: str, source: str) -> float:
    r = table[
        (table["scenario_year"] == year)
        & (table["state"] == state)
        & (table["count_basis"] == basis)
        & (table["source_id"] == source)
    ]
    # A total where the source gives one, else its delivery rows add up to it.
    total = r[r["delivery"] == "unspecified"]
    r = total if len(total) else r[r["delivery"] != "nonstrategic"]
    if r.empty or len(total) > 1:
        raise ValueError(f"expected rows for {year} {state} {basis} {source}, found {len(r)}")
    return float(r["central"].sum())


def triangle(spec, n: int, rng) -> np.ndarray:
    low, mode, high = spec
    if low == high:
        return np.full(n, float(low))
    return rng.triangular(low, mode, high, n)


def draw_delivered(
    attacker: Mapping, n: int, rng, table: pd.DataFrame, mix: pd.DataFrame
) -> np.ndarray:
    high = inventory(table, attacker["stock_year"], attacker["state"], *attacker["inventory_high"])
    spec = attacker["inventory_low"]
    if isinstance(spec, list):
        low = inventory(table, attacker["stock_year"], attacker["state"], *spec)
    else:
        low = high * float(spec["fraction_of_high"])
    scale = float(attacker.get("stock_multiplier", 1.0))
    low, high = low * scale, high * scale
    available = triangle((low, (low + high) / 2, high), n, rng)
    share = triangle(attacker["theatre_share"], n, rng)
    shares = mix[mix["state"] == attacker["state"]].set_index("delivery")["share"]
    table_rel = attacker["reliability"]
    if len(shares) and "by_delivery" in table_rel:
        total = shares.sum()
        reliability = sum(
            shares[d] / total * triangle(table_rel["by_delivery"][d], n, rng) for d in shares.index
        )
    else:
        reliability = triangle(table_rel["all"], n, rng)
    lost = triangle(attacker["fraction_lost_to_defences"], n, rng)
    interceptors = rng.uniform(0, attacker.get("interceptors", 0), n)
    return np.clip(available * share * reliability * (1 - lost) - interceptors, 0, None)


def delivered_draws(attacker: Mapping, n: int, rng) -> np.ndarray:
    return draw_delivered(attacker, n, rng, pd.read_csv(TABLE), pd.read_csv(MIX))
