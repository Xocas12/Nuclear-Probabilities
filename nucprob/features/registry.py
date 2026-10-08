"""Every feature with its family, sources and anachronism flag (PLAN section 3.2, rules for
features).

`sources` names where a feature comes from: ids of data/sources.yaml (a trailing * matches a
family of ids) or curated tables as "curated:<path under data/curated>". The leakage guard
(tests/test_leakage.py) checks that none of them is a label source. `anachronism` marks a
feature that uses knowledge from after 1956, a modern dataset standing in for the world of the
plan's date; phase 4 measures how much results depend on them.
"""

from dataclasses import dataclass

CENSUS = ("popstat_*", "demoscope_*", "geonames_*")
CAPITALS = ("curated:features/capitals_1956.csv",)
VPK = ("vpk_dexter_rodionov_v24",)
VPK_NOTE = "establishments of the guide's main series active in 1956, in the town; USSR only"


@dataclass(frozen=True)
class Feature:
    family: str
    source: str
    sources: tuple[str, ...]
    anachronism: bool = False
    note: str = ""


FEATURES = {
    # Population
    "log_pop": Feature(
        "population",
        "census nearest the study date",
        CENSUS,
        note="USSR 1959 census; elsewhere the census nearest June 1956",
    ),
    "log_pop_prewar": Feature(
        "population",
        "last pre-war census",
        CENSUS,
        note="USSR 1939; missing for areas annexed after January 1939 and for Uzbekistan",
    ),
    "pop_prewar_missing": Feature("population", "last pre-war census", CENSUS),
    "growth_prewar": Feature(
        "population",
        "the two censuses",
        CENSUS,
        note="annual log10 growth from the pre-war census; 0 where it is missing",
    ),
    "pop_rank_pct": Feature(
        "population", "census", CENSUS, note="percentile of population within its country"
    ),
    "log_pop_within_25km": Feature(
        "population", "census", CENSUS, note="other settlements of the table within 25 km"
    ),
    "log_pop_within_50km": Feature("population", "census", CENSUS),
    "log_pop_within_100km": Feature("population", "census", CENSUS),
    "log_km_to_100k": Feature(
        "population", "census", CENSUS, note="distance to the nearest other settlement of 100,000+"
    ),
    # Administrative
    "national_capital": Feature("administrative", "capitals as of June 1956", CAPITALS),
    "republic_capital": Feature(
        "administrative",
        "capitals as of June 1956",
        CAPITALS,
        note="union-republic capitals, Petrozavodsk (Karelo-Finnish SSR until July 1956) and Bratislava",
    ),
    "regional_centre": Feature(
        "administrative",
        "regional centres as of June 1956",
        ("curated:features/admin_centres_1956.csv",),
        note="oblast, krai, ASSR; voivodeship, Bezirk, kraj, county, region, okrug, province",
    ),
    "autonomy_centre": Feature(
        "administrative",
        "regional centres as of June 1956",
        ("curated:features/admin_centres_1956.csv",),
        note="autonomous oblasts and national okrugs of the USSR",
    ),
    "district_seat": Feature(
        "administrative", "GeoNames PPLA2 (today's districts)", ("geonames_*",), anachronism=True
    ),
    "city_status": Feature(
        "administrative",
        "pop-stat (bold) / Demoscope (г.)",
        ("popstat_*", "demoscope_*"),
        anachronism=True,
        note="pop-stat marks today's status",
    ),
    # Geography and reach
    "elevation_m": Feature(
        "geography", "terrain tiles (zoom 7)", ("aws_terrain_tiles",), note="the sea counts as 0 m"
    ),
    "log_relief_10km": Feature(
        "geography",
        "terrain tiles (zoom 7)",
        ("aws_terrain_tiles",),
        note="log10(1 + highest minus lowest metre within 10 km)",
    ),
    "log_km_to_coast": Feature(
        "geography",
        "Natural Earth coastline",
        ("naturalearth_10m_coastline",),
        note="the Caspian counts as sea; the Aral and other lakes do not",
    ),
    "log_km_to_moscow": Feature("geography", "capitals as of June 1956", CAPITALS),
    "log_km_to_capital": Feature(
        "geography",
        "capitals as of June 1956",
        CAPITALS,
        note="the union republic's capital in the USSR, the national capital elsewhere",
    ),
    "log_km_to_nato": Feature(
        "geography",
        "CShapes 2.0 borders on 15 June 1956",
        ("cshapes_2",),
        note="territory of the 15 members, Alaska and French Algeria",
    ),
    "log_km_to_frontier": Feature(
        "geography",
        "CShapes 2.0 borders on 15 June 1956",
        ("cshapes_2",),
        note="territory of any state or colony outside the bloc, across land or sea",
    ),
    "log_km_to_sac_base": Feature(
        "geography",
        "SAC's overseas bases in 1956",
        ("curated:features/sac_bases_1956.csv",),
        note="UK, Morocco, Greenland, Labrador, Newfoundland, Alaska, Guam, Puerto Rico",
    ),
    "log_km_to_conus": Feature(
        "geography",
        "CShapes 2.0 borders on 15 June 1956",
        ("cshapes_2",),
        note="the 48 states",
    ),
    # Industry
    "log_vpk_total": Feature("industry", "Dexter-Rodionov guide", VPK, True, VPK_NOTE),
    "log_vpk_factories": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "factories (type z); " + VPK_NOTE
    ),
    "log_vpk_design": Feature(
        "industry",
        "Dexter-Rodionov guide",
        VPK,
        True,
        "design bureaux and research institutes (kb, nii); " + VPK_NOTE,
    ),
    "log_vpk_large": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "size class 3 (large); " + VPK_NOTE
    ),
    "log_vpk_aero": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "aviation; " + VPK_NOTE
    ),
    "log_vpk_armour": Feature("industry", "Dexter-Rodionov guide", VPK, True, "tanks; " + VPK_NOTE),
    "log_vpk_arms": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "armament and munitions; " + VPK_NOTE
    ),
    "log_vpk_ship": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "shipbuilding; " + VPK_NOTE
    ),
    "log_vpk_elec": Feature(
        "industry", "Dexter-Rodionov guide", VPK, True, "radio and electronics; " + VPK_NOTE
    ),
    "log_vpk_atom": Feature("industry", "Dexter-Rodionov guide", VPK, True, "nuclear; " + VPK_NOTE),
    "log_vpk_within_25km": Feature(
        "industry",
        "Dexter-Rodionov guide",
        VPK,
        True,
        "all establishments in places within 25 km, the place's own included; USSR only",
    ),
    "log_power_mw_25km": Feature(
        "industry",
        "WRI Global Power Plant Database",
        ("wri_gppd",),
        True,
        "today's capacity of plants commissioned by 1956 within 25 km (survivors only; "
        "commissioning years unreliable for Soviet plants)",
    ),
    # Military
    "log_airfields_10km": Feature(
        "military",
        "OurAirports (today's airfields, open and closed)",
        ("ourairports", "cshapes_2"),
        True,
        "airfields within 10 km in the place's 1956 country",
    ),
    "log_airfields_25km": Feature(
        "military", "OurAirports", ("ourairports", "cshapes_2"), True, "within 25 km"
    ),
    "log_airfields_50km": Feature(
        "military", "OurAirports", ("ourairports", "cshapes_2"), True, "within 50 km"
    ),
    # Transport
    "log_km_to_rail": Feature(
        "transport", "Natural Earth railways (today's)", ("naturalearth_10m_railroads",), True
    ),
    "rail_lines_5km": Feature(
        "transport",
        "Natural Earth railways (today's)",
        ("naturalearth_10m_railroads",),
        True,
        "distinct line segments within 5 km: a junction proxy",
    ),
    "log_km_to_port": Feature(
        "transport", "Natural Earth ports (today's)", ("naturalearth_10m_ports",), True
    ),
    "log_km_to_major_river": Feature(
        "transport",
        "Natural Earth rivers",
        ("naturalearth_10m_rivers",),
        note="scalerank 6 or less (the Volga, Don, Oka, Dnieper...); reservoirs as centrelines",
    ),
}


def family(name: str) -> str:
    return FEATURES[name].family


def by_family(names: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for n in names:
        out.setdefault(FEATURES[n].family, []).append(n)
    return out
