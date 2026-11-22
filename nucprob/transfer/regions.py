"""The transfer regions: which town tables make each universe, which lists label it, and the
date its features describe.

Each country entry: (country name used in the label files, GeoNames code, town table stem in
data/curated/gazetteer/ or "popstat:<page>:<column>" for a pop-stat page).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Region:
    name: str
    year: int
    countries: tuple[tuple[str, str, str], ...]
    lists: tuple[str, ...]
    military: str = ""  # curated military table in data/curated/features/, if any
    note: str = ""
    extra: dict = field(default_factory=dict)
    withheld: tuple[tuple[str, str, str], ...] = ()  # countries with a table not yet complete


REGIONS = {
    "wp_west_1965": Region(
        "Warsaw Pact targets in NATO Europe and Austria, 1961-1977",
        1965,
        (
            # The FRG table is partial (about 356 of 583 towns; no official 1961 table could
            # be fetched, see towns_frg_1961.md), so the FRG is withheld from the universe.
            ("Denmark", "DK", "towns_dk_1960"),
            ("Netherlands", "NL", "towns_nl_1960"),
            ("Belgium", "BE", "towns_be_1961"),
            ("Austria", "AT", "popstat:austria:pop_1961-03-21"),
            ("Italy", "IT", "towns_it_1961"),
        ),
        (
            "wp_1961_burza",
            "wp_1964_csla_plan",
            "wp_1965_hu_wargame",
            "wp_1965_coastal_front_zealand",
            "wp_1967_lato67",
            "wp_1970_coastal_front_map",
            "wp_1977_gsa_front_lesson",
            "wp_1977_zealand",
            "wp_1961_duszynski_report",
            "wp_1977_gsa_initial_strike_table",
            "wp_1977_gsa_lesson_variants",
        ),
        military="weurope_military_sites_1965.csv",
        note="one universe for the 1960s plans; the 1970s lists use it too",
        withheld=(("FRG", "DE", "towns_frg_1961"),),
    ),
    "uk_1980": Region(
        "The United Kingdom, 1980",
        1980,
        (("UK", "GB", "towns_uk_1981"),),
        ("cd_1980_square_leg", "cd_1982_hard_rock_partial"),
        military="uk_military_sites_1980.csv",
    ),
    "japan_1945": Region(
        "Japan, 1945",
        1945,
        (("Japan", "JP", "towns_jp_1940"),),
        ("us_1945_target_committee",),
    ),
    "usa_1955": Region(
        "The United States, 1955",
        1955,
        (("USA", "US", "towns_us_1950"),),
        ("cd_1955_operation_alert", "cd_1955_operation_alert_full"),
    ),
    "canada_1956": Region(
        "Canada, 1956",
        1956,
        (("Canada", "CA", "towns_ca_1956"),),
        ("cd_1956_canada_target_areas", "cd_1962_canada_target_areas"),
    ),
    # Post-1990 regions: no census town tables, so today's GeoNames towns of 10,000+
    # ("geonames:<code>"), with GeoNames' recent populations.
    "russia_2001": Region(
        "Russia, 2001 (NRDC's reconstruction of a US counterforce attack)",
        2001,
        (("Russia", "RU", "geonames:RU"),),
        ("rec_2001_nrdc_maonf_targets",),
        note="GeoNames towns of 10,000+ with recent populations",
    ),
    "modern_2020": Region(
        "Targets of Russian and North Korean lists and statements, 2013-2025",
        2020,
        (
            ("USA", "US", "geonames:US"),
            ("Japan", "JP", "geonames:JP"),
            ("South Korea", "KR", "geonames:KR"),
            ("UK", "GB", "geonames:GB"),
            ("France", "FR", "geonames:FR"),
            ("Norway", "NO", "geonames:NO"),
            ("Estonia", "EE", "geonames:EE"),
            ("Romania", "RO", "geonames:RO"),
            ("Turkey", "TR", "geonames:TR"),
            ("Israel", "IL", "geonames:IL"),
        ),
        (
            "ru_2024_ft_japan_korea",
            "ru_2024_ft_europe",
            "ru_2019_kiselyov",
            "kp_2013_threats",
            "kp_2023_published_maps",
            "ir_2025_dimona_threats",
        ),
        note="GeoNames towns of 10,000+ with recent populations; the lists are tiny",
    ),
}
