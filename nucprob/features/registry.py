"""Every feature with its family, source and anachronism flag (PLAN section 3.2, rules for
features). `anachronism` marks a feature that uses knowledge from after 1956: a modern
dataset standing in for the world of the plan's date. Phase 4 measures how much results
depend on them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    family: str
    source: str
    anachronism: bool = False
    note: str = ""


FEATURES = {
    # Population (pop-stat census series; Demoscope 1959 for Uzbekistan)
    "log_pop_1959": Feature("population", "1959 census"),
    "log_pop_1939": Feature(
        "population",
        "1939 census",
        note="missing for areas annexed after Jan 1939 and for Uzbekistan",
    ),
    "pop_1939_missing": Feature("population", "1939 census"),
    "growth_1939_59": Feature(
        "population", "1939 and 1959 censuses", note="log ratio; 0 where 1939 is missing"
    ),
    "pop_rank_pct": Feature(
        "population", "1959 census", note="percentile of 1959 population within the USSR"
    ),
    "log_pop_within_25km": Feature(
        "population", "1959 census", note="other settlements of the table within 25 km"
    ),
    "log_pop_within_50km": Feature("population", "1959 census"),
    "log_pop_within_100km": Feature("population", "1959 census"),
    "log_km_to_100k": Feature(
        "population", "1959 census", note="distance to the nearest other settlement of 100,000+"
    ),
    # Administrative
    "national_capital": Feature("administrative", "hand list (1956)"),
    "republic_capital": Feature(
        "administrative",
        "hand list (1956)",
        note="union-republic capitals as of June 1956, incl. Petrozavodsk (Karelo-Finnish SSR until July 1956)",
    ),
    "regional_seat": Feature(
        "administrative", "GeoNames PPLA (today's first-level regions)", anachronism=True
    ),
    "district_seat": Feature(
        "administrative", "GeoNames PPLA2 (today's districts)", anachronism=True
    ),
    "city_status": Feature(
        "administrative",
        "pop-stat (bold) / Demoscope (г.)",
        anachronism=True,
        note="pop-stat marks today's status",
    ),
}


def family(name: str) -> str:
    return FEATURES[name].family


def by_family(names: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for n in names:
        out.setdefault(FEATURES[n].family, []).append(n)
    return out
