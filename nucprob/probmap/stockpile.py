"""From cited inventories to warheads delivered, for one attacker of a scenario.

    delivered, for each delivery = available x its share x theatre share x its reliability, less defences

`available` is a triangular draw from a low inventory (forces deployed or loaded) to a high one (the
military stockpile), with its mode midway, because how much of a reserve could be used is not known.
Each figure comes from data/curated/stockpiles/stockpiles.csv by year, state, count basis and source.
Reliability, theatre share and the losses to defences are given in configs/scenarios.yaml, each with a
source or expressly as a stated assumption. Interceptors take off a uniform draw from none to one warhead
each, an upper bound that assumes every interceptor stops one warhead; one force shared by several attackers
is drawn once and divided among them (`share_interceptors`). Totals by attacker and delivery are inputs to
the map; nothing here divides them among places.
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


def mix_of(attacker: Mapping, mix: pd.DataFrame) -> pd.Series:
    """Shares by delivery for this attacker in its stock year, summing to 1; empty if none is known."""
    rows = mix[(mix["state"] == attacker["state"]) & (mix["year"] == attacker["stock_year"])]
    shares = rows.set_index("delivery")["share"].astype(float)
    return shares / shares.sum() if len(shares) else shares


def draw_by_delivery(
    attacker: Mapping,
    n: int,
    rng,
    table: pd.DataFrame,
    mix: pd.DataFrame,
    share: np.ndarray | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """For each delivery, the draws of warheads available and delivered. Without a known mix there is
    one entry, `unspecified`. Interceptors come off each delivery in proportion: no source says how
    they would divide, and the map uses only the total. `share`, if given, replaces the theatre-share
    draw (nucprob.probmap.run.theatre_share_variance)."""
    high = inventory(table, attacker["stock_year"], attacker["state"], *attacker["inventory_high"])
    low = inventory(table, attacker["stock_year"], attacker["state"], *attacker["inventory_low"])
    scale = float(attacker.get("stock_multiplier", 1.0))
    low, high = low * scale, high * scale
    available = triangle((low, (low + high) / 2, high), n, rng)
    share = triangle(attacker["theatre_share"], n, rng) if share is None else share
    shares = mix_of(attacker, mix)
    named = attacker["reliability"]
    if len(shares) and "by_delivery" in named:
        reliability = {d: triangle(named["by_delivery"][d], n, rng) for d in shares.index}
    else:
        common = triangle(named["all"], n, rng)
        reliability = {d: common for d in shares.index} or {"unspecified": common}
    if not len(shares):
        shares = pd.Series({"unspecified": 1.0})
    lost = triangle(attacker["fraction_lost_to_defences"], n, rng)
    interceptors = rng.uniform(0, attacker.get("interceptors", 0), n)
    before = {d: available * shares[d] * share * reliability[d] * (1 - lost) for d in shares.index}
    total = sum(before.values())
    kept = np.divide(
        np.clip(total - interceptors, 0, None), total, out=np.zeros(n), where=total > 0
    )
    return {
        d: {"available": available * shares[d], "delivered": before[d] * kept} for d in shares.index
    }


def share_interceptors(
    parts: Mapping[str, dict[str, dict[str, np.ndarray]]], groups: list[Mapping], n: int, rng
) -> None:
    """One interceptor force against several attackers: a single uniform draw from none to `count`,
    taken from those attackers' delivered warheads in proportion to each one's. Changes `parts`, a
    {attacker: draw_by_delivery result}, in place."""
    for group in groups:
        hit = [parts[a] for a in group["attackers"]]
        total = sum(p["delivered"] for attacker in hit for p in attacker.values())
        stopped = rng.uniform(0, group["count"], n)
        kept = np.divide(np.clip(total - stopped, 0, None), total, out=np.zeros(n), where=total > 0)
        for attacker in hit:
            for p in attacker.values():
                p["delivered"] = p["delivered"] * kept


def draw_delivered(
    attacker: Mapping, n: int, rng, table: pd.DataFrame, mix: pd.DataFrame
) -> np.ndarray:
    parts = draw_by_delivery(attacker, n, rng, table, mix)
    return sum(p["delivered"] for p in parts.values())


def by_delivery_draws(
    attacker: Mapping, n: int, rng, share: np.ndarray | None = None
) -> dict[str, dict[str, np.ndarray]]:
    return draw_by_delivery(attacker, n, rng, pd.read_csv(TABLE), pd.read_csv(MIX), share)
