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


REGIONS = {
    "wp_west_1965": Region(
        "Warsaw Pact targets in NATO Europe and Austria, 1961-1977",
        1965,
        (
            ("FRG", "DE", "towns_frg_1961"),
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
        ),
        military="weurope_military_sites_1965.csv",
        note="one universe for the 1960s plans; the 1970s lists use it too",
    ),
    "uk_1980": Region(
        "The United Kingdom, 1980",
        1980,
        (("UK", "GB", "towns_uk_1981"),),
        ("cd_1980_square_leg",),
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
        ("cd_1956_canada_target_areas",),
    ),
}
