"""Give census settlements coordinates by matching them to GeoNames populated places.

Names are matched in Cyrillic (GeoNames carries the Russian name of nearly every place in its
alternate names), within the settlement's country. When several places share the name:
1. the region decides: each census region is mapped to the GeoNames first-level region that
   most of its unambiguous settlements fall in, unless the caller gives the mapping
   (`admin1_of`), in which case places outside the region are not candidates at all;
2. then the place whose GeoNames population is closest to the settlement's own figure: the
   census series' latest figure (`modern_pop`) where the source has one, else the figure on
   or near the study date (`pop`, or `pop_1959`), which counts mostly as a floor (towns
   grew). A place GeoNames gives no population is marked down, so a town is not put on a
   same-named hamlet of population 0;
3. then the higher administrative rank.
Names that match nothing exactly get a fuzzy match (rapidfuzz) within the mapped region.
Every match records how it was made, so weak ones can be reviewed.
"""

from collections import Counter, defaultdict
from collections.abc import Collection, Mapping

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from nucprob.gazetteer.names import key, latin_key, variants

RANK = {"PPLC": 5, "PPLA": 4, "PPLA2": 3, "PPLA3": 2, "PPLA4": 2}
FUZZY_CUTOFF = 90


def positive(value) -> float | None:
    """`value` as a float if it is a positive number; None for NaN, None, 0 or text."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None  # NaN > 0 is False


def census_figure(settlement: Mapping) -> float | None:
    """The settlement's figure on or near the study date: `pop` (the bloc's sources) or
    `pop_1959` (the USSR's, which get `pop` only after matching)."""
    return positive(settlement.get("pop")) or positive(settlement.get("pop_1959"))


def name_index(gn: pd.DataFrame) -> dict[str, list[int]]:
    """Matching key -> positions in `gn` of the places that carry the name."""
    index: dict[str, set[int]] = defaultdict(set)
    for pos, (name, ascii_name, alt) in enumerate(
        zip(gn["name"], gn["asciiname"], gn["alternatenames"], strict=True)
    ):
        for n in {name, ascii_name, *alt.split(",")}:
            if n:
                index[key(n)].add(pos)
    return {k: sorted(v) for k, v in index.items()}


def cyrillic_names(gn: pd.DataFrame, positions: list[int]) -> dict[int, list[str]]:
    """Every Cyrillic name of each place, as matching keys (for fuzzy matching)."""
    out = {}
    for pos in positions:
        names = [gn["name"].iat[pos], *gn["alternatenames"].iat[pos].split(",")]
        out[pos] = [
            key(n) for n in names if n and any("а" <= ch <= "я" or ch in "іїєґ" for ch in n.lower())
        ]
    return out


def region_map(candidates: list[list[int]], regions: pd.Series, gn: pd.DataFrame) -> dict[str, str]:
    """Census region -> GeoNames admin1 code, from settlements with exactly one candidate."""
    votes: dict[str, Counter] = defaultdict(Counter)
    for cands, region in zip(candidates, regions, strict=True):
        if len(cands) == 1:
            votes[region][gn["admin1"].iat[cands[0]]] += 1
    out = {}
    for region, counter in votes.items():
        code, n = counter.most_common(1)[0]
        if n >= 2 and n / sum(counter.values()) >= 0.6:
            out[region] = code
    return out


def choose(
    cands: list[int],
    gn: pd.DataFrame,
    admin1: str | Collection[str] | None,
    modern_pop: float | None,
    census_pop: float | None = None,
) -> int:
    """The most likely of several places that share the settlement's name: one in the
    settlement's region (`admin1`, a code or a set of codes), of a population close to the
    settlement's, of high administrative rank. The population is `modern_pop`, or `census_pop`
    (the figure near the study date) when there is no modern one: without either, a hamlet of
    the same name could win on rank or file order alone.

    A modern figure should be close to GeoNames' either way. A figure from the 1950s is closer
    to a floor: towns have grown since, and GeoNames gives many Chinese cities the population
    of their whole urban district, so a place much larger than the figure is marked down only
    a quarter as much as one equally smaller. Otherwise a county seat or suburb of about the
    1953 size beats the city itself (Nantong, Baoji and Weifang did)."""
    region = {admin1} if isinstance(admin1, str) else set(admin1 or ())
    region.discard("")
    target, above = positive(modern_pop), 2.0
    if target is None:
        target, above = positive(census_pop), 0.5

    def score(pos: int) -> float:
        row = gn.iloc[pos]
        s = 10.0 if row["admin1"] in region else 0.0
        s += RANK.get(row["feature_code"], 1 if row["feature_code"].startswith("PPL") else 0)
        if target is not None and row["population"] > 0:
            gap = np.log10(row["population"] + 1) - np.log10(target + 1)
            s -= above * gap if gap > 0 else 2 * -gap
        elif target is not None:
            s -= 3  # GeoNames gives no population: weaker evidence
        return s

    return max(cands, key=score)


def match(
    settlements: pd.DataFrame,
    gn: pd.DataFrame,
    admin1_of: Mapping[str, Collection[str]] | None = None,
) -> pd.DataFrame:
    """Add geonameid, lat, lon, admin1, feature_code, gn_name, gn_population, match_method and
    n_candidates to `settlements` (columns name_ru, notes, region, and the population columns
    of `choose`: modern_pop, else pop or pop_1959).

    `admin1_of` maps a census region to the GeoNames admin1 codes its territory lies in today,
    where that is known by hand: a settlement of such a region is matched only to places in
    those codes, and is left unmatched rather than put on a namesake elsewhere (or fuzzily on
    another name in the region). Regions it does not cover are mapped from the data
    (`region_map`)."""
    gn = gn.reset_index(drop=True)
    gn_admin1 = gn["admin1"].to_numpy()
    index = name_index(gn)
    known = {region: frozenset(codes) for region, codes in (admin1_of or {}).items()}
    tries = [
        variants(n, notes)
        for n, notes in zip(settlements["name_ru"], settlements["notes"], strict=True)
    ]
    candidates, used, dropped = [], [], []
    for names, region in zip(tries, settlements["region"], strict=True):
        allowed = known.get(region)
        hit, outside = (names[0] if names else "", []), 0
        for n in names:
            found = index.get(key(n), [])
            inside = found if allowed is None else [p for p in found if gn_admin1[p] in allowed]
            outside = outside or len(found) - len(inside)
            if inside:
                hit = (n, inside)
                break
        used.append(hit[0])
        candidates.append(hit[1])
        dropped.append(outside)
    regions = region_map(candidates, settlements["region"], gn)
    towns = [pos for pos, code in enumerate(gn["feature_code"]) if code.startswith("PPL")]
    fuzzy_pool = cyrillic_names(gn, towns)
    rows = []
    for (_, s), names, name_used, cands, outside in zip(
        settlements.iterrows(), tries, used, candidates, dropped, strict=True
    ):
        allowed = known.get(s["region"])
        admin1 = regions.get(s["region"]) if allowed is None else None
        area = allowed if allowed is not None else frozenset({admin1} if admin1 else ())
        pick, method = None, ""
        if len(cands) == 1 and admin1 and gn_admin1[cands[0]] != admin1:
            # The only place of that name lies outside the settlement's region: a namesake.
            # Keep it only if no place in the region comes close by name.
            pool = {p: v for p, v in fuzzy_pool.items() if gn_admin1[p] == admin1}
            choices = {(p, i): k for p, ks in pool.items() for i, k in enumerate(ks)}
            hit = process.extractOne(
                key(names[0]), choices, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF - 5
            )
            if hit:
                pick, method = hit[2][0], f"fuzzy {hit[1]:.0f}, in region"
            else:
                pick, method = cands[0], "exact, unique, other region"
        elif len(cands) == 1:
            pick, method = cands[0], "exact, unique"
        elif cands:
            pick = choose(cands, gn, area, s.get("modern_pop"), census_figure(s))
            method = "exact, region" if gn_admin1[pick] in area else "exact, ranked"
        elif outside:
            # The name is GeoNames' own spelling, only not in this region: a fuzzy match here
            # would find another name, and an exact one elsewhere a namesake.
            method = f"unmatched, no place of that name in the region ({outside} elsewhere)"
        else:
            # Fuzzy: within the region if it is known, else the whole country (stricter).
            scoped = allowed is not None or bool(admin1)
            pool = {p: v for p, v in fuzzy_pool.items() if not scoped or gn_admin1[p] in area}
            cutoff = FUZZY_CUTOFF if scoped else FUZZY_CUTOFF + 3
            choices = {(p, i): k for p, ks in pool.items() for i, k in enumerate(ks)}
            best = None
            for n in names:
                hit = process.extractOne(key(n), choices, scorer=fuzz.ratio, score_cutoff=cutoff)
                if hit and (best is None or hit[1] > best[1]):
                    best, name_used = hit, n
            if best:
                pick, method = best[2][0], f"fuzzy {best[1]:.0f}"
            elif s.get("name_lat"):
                # Last resort: the transliterated name against GeoNames' ASCII names.
                ascii_pool = {p: latin_key(gn["asciiname"].iat[p]) for p in pool}
                hit = process.extractOne(
                    latin_key(s["name_lat"]), ascii_pool, scorer=fuzz.ratio, score_cutoff=cutoff
                )
                if hit:
                    pick, method = hit[2], f"fuzzy latin {hit[1]:.0f}"
        if pick is not None and name_used != names[0]:
            method += f" (as {name_used})"
        row = {"n_candidates": len(cands), "match_method": method or "unmatched"}
        if pick is not None:
            g = gn.iloc[pick]
            row.update(
                {
                    "geonameid": int(g["geonameid"]),
                    "lat": float(g["lat"]),
                    "lon": float(g["lon"]),
                    "admin1": g["admin1"],
                    "feature_code": g["feature_code"],
                    "gn_name": g["name"],
                    "gn_population": int(g["population"]),
                    "gn_alternatenames": g["alternatenames"],
                    "gn_dem": g.get("dem"),
                }
            )
        rows.append(row)
    return pd.concat([settlements.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
