"""Give census settlements coordinates by matching them to GeoNames populated places.

Names are matched in Cyrillic (GeoNames carries the Russian name of nearly every place in its
alternate names), within the settlement's country. When several places share the name:
1. the region decides: each census region is mapped to the GeoNames first-level region that
   most of its unambiguous settlements fall in;
2. then the place whose modern GeoNames population is closest to the census series' latest
   figure, and the higher administrative rank.
Names that match nothing exactly get a fuzzy match (rapidfuzz) within the mapped region.
Every match records how it was made, so weak ones can be reviewed.
"""

from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from nucprob.gazetteer.names import key, latin_key, variants

RANK = {"PPLC": 5, "PPLA": 4, "PPLA2": 3, "PPLA3": 2, "PPLA4": 2}
FUZZY_CUTOFF = 90


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


def choose(cands: list[int], gn: pd.DataFrame, admin1: str | None, modern_pop: float) -> int:
    def score(pos: int) -> float:
        row = gn.iloc[pos]
        s = 10.0 if admin1 and row["admin1"] == admin1 else 0.0
        s += RANK.get(row["feature_code"], 1 if row["feature_code"].startswith("PPL") else 0)
        if row["population"] > 0 and modern_pop and modern_pop > 0:
            s -= 2 * abs(np.log10(row["population"] + 1) - np.log10(modern_pop + 1))
        elif modern_pop and modern_pop > 0:
            s -= 3  # GeoNames gives no population: weaker evidence
        return s

    return max(cands, key=score)


def match(settlements: pd.DataFrame, gn: pd.DataFrame) -> pd.DataFrame:
    """Add geonameid, lat, lon, admin1, feature_code, gn_name, gn_population, match_method and
    n_candidates to `settlements` (columns name_ru, notes, region, modern_pop)."""
    gn = gn.reset_index(drop=True)
    index = name_index(gn)
    tries = [
        variants(n, notes)
        for n, notes in zip(settlements["name_ru"], settlements["notes"], strict=True)
    ]
    candidates, used = [], []
    for names in tries:
        hit = next(
            ((n, index[key(n)]) for n in names if key(n) in index), (names[0] if names else "", [])
        )
        used.append(hit[0])
        candidates.append(hit[1])
    regions = region_map(candidates, settlements["region"], gn)
    towns = [pos for pos, code in enumerate(gn["feature_code"]) if code.startswith("PPL")]
    fuzzy_pool = cyrillic_names(gn, towns)
    rows = []
    for (_, s), names, name_used, cands in zip(
        settlements.iterrows(), tries, used, candidates, strict=True
    ):
        admin1 = regions.get(s["region"])
        pick, method = None, ""
        if len(cands) == 1:
            pick, method = cands[0], "exact, unique"
        elif cands:
            pick = choose(cands, gn, admin1, s.get("modern_pop", np.nan))
            method = (
                "exact, region" if admin1 and gn["admin1"].iat[pick] == admin1 else "exact, ranked"
            )
        else:
            # Fuzzy: within the mapped region if there is one, else the whole country (stricter).
            pool = {
                p: v for p, v in fuzzy_pool.items() if not admin1 or gn["admin1"].iat[p] == admin1
            }
            cutoff = FUZZY_CUTOFF if admin1 else FUZZY_CUTOFF + 3
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
                }
            )
        rows.append(row)
    return pd.concat([settlements.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
