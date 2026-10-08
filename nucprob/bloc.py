"""The countries of the Soviet bloc on the study date, named as the SAC 1956 list names them.

Each country has its name in CShapes 2.0 (borders and capital on the study date) and the
GeoNames country files that cover its 1956 territory today. NATO_1956 lists the CShapes units
that were NATO territory on the study date.
"""

from dataclasses import dataclass

STUDY_DATE = (1956, 6, 15)  # SAC's study is dated June 1956 (PLAN section 4.1)


@dataclass(frozen=True)
class Country:
    cshapes: str
    geonames: tuple[str, ...]


COUNTRIES = {
    "USSR": Country(
        "Russia (Soviet Union)",
        ("RU", "UA", "BY", "MD", "LT", "LV", "EE", "GE", "AM", "AZ", "KZ", "KG", "TJ", "TM", "UZ"),
    ),
    "Poland": Country("Poland", ("PL",)),
    "East Germany": Country("German Democratic Republic", ("DE",)),
    "Czechoslovakia": Country("Czechoslovakia", ("CZ", "SK")),
    "Hungary": Country("Hungary", ("HU",)),
    "Romania": Country("Rumania", ("RO",)),
    "Bulgaria": Country("Bulgaria", ("BG",)),
    "Albania": Country("Albania", ("AL",)),
    "China": Country("China", ("CN",)),
    "North Korea": Country("Korea, People's Republic of", ("KP",)),
    "North Vietnam": Country("Vietnam, Democratic Republic of", ("VN",)),
    "Mongolia": Country("Mongolia", ("MN",)),
}

# SAC's own country names that fold into one of COUNTRIES.
SAC_COUNTRY = {"China (Manchuria)": "China"}

# Members' territory in June 1956 (West Germany joined in May 1955). Alaska was US territory in
# the North Atlantic Treaty's area (Article 6); so were the Algerian departments of France
# until 1962. Other colonies and overseas territories are not counted.
NATO_1956 = (
    "United States of America",
    "Alaska",
    "Canada",
    "United Kingdom",
    "France",
    "Algeria",
    "Italy/Sardinia",
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "Norway",
    "Denmark",
    "Iceland",
    "Portugal",
    "Greece",
    "Turkey (Ottoman Empire)",
    "German Federal Republic",
)

CONUS = "United States of America"  # in CShapes, the 48 states (Alaska and Hawaii are apart)


def sac_country(name: str) -> str:
    return SAC_COUNTRY.get(name, name)
