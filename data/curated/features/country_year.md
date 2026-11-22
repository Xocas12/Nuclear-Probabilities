## Country-year political, economic and military data, 1940-2025 (`country_year`)

- **What it is.** A tidy panel, one row per state and year, of political, economic and military
  data on the targeted (and planning) states, for the "context" features of PLAN section 5.3
  (regime type, alignment, capability). It is built by `nucprob/sources/country_year.py` into
  `data/processed/country_year.parquet` (git-ignored): 12,682 rows, 202 states, 1940-2025.
  - **Key:** `cow_code` (Correlates of War state code) and `year`. `iso3` is also given, valid
    for that year (SUN for the USSR to 1991, CSK, YUG/SCG, DDR, VDR for North Vietnam, YMD).
  - **Universe:** a row exists when the state existed. That means COW state-system membership
    (states2024, carried from 2024 to 2025), with three changes. Second World War occupation
    gaps that start in 1939 or later and end by 1955 are filled (Netherlands, Belgium, Norway,
    Denmark, France, Poland, Czechoslovakia, Albania, Yugoslavia, Greece, Luxembourg, Japan
    1945-52). The FRG and GDR are given 1949 onwards, and Austria 1945-54, before COW admits
    them. `cow_member` = 0 marks these 65 added years.
- **Curated tables built with it** (committed, in this folder):
  - `country_codes.csv`, the crosswalk: 1,021 rows. Each row maps a `name` to `cow_code`,
    `cow_abb` and `iso3`, valid from `start_year` to `end_year`. `kind` says where the name
    comes from:
    - `project` (66 rows): the names this project's tables use, from the `target_country`,
      `country_1956` and `country` columns and `nucprob/bloc.py`. These include USSR, East
      Germany/GDR, FRG, Czechoslovakia, Yugoslavia, China/PRC/China (Manchuria), North Korea,
      North Vietnam, Mongolia, the satellites, UK/England/Scotland/Wales/Northern Ireland, USA
      and its territories, Canada (Labrador/Newfoundland), Japan, Denmark/Greenland and the ISO2
      codes AT, BE, DE, DK, FR, IT, NL;
    - `cow_state` (221 rows): every COW state from 1940;
    - `alias` (734 rows): spellings used by V-Dem, Polity5, BMR and troopdata (each mapped by
      that source's own code), plus hand aliases for SIPRI's names.
    - "Germany" in a Cold War table means the FRG (260) for 1949-90, and unified Germany (255)
      otherwise. "Sino-Soviet Bloc" has no code.
  - `alliance_membership.csv`, 178 rows of membership with `start_date` and `end_date`:
    - `nato` and `warsaw_pact`;
    - `us_defense` and `ussr_defense`: every COW defence pact with the USA or the USSR/Russia
      in force after 1940, with `bilateral` = 1 for two-member pacts (Japan, South Korea,
      Taiwan, the Philippines, Pakistan, Turkey, Canada...).
    - Asymmetric pacts count when any member's obligation is a defence one.
  - `nuclear_status.csv`, 52 rows. Each has a country, a role and its dates (`start_date`,
    `end_date`, `start_year`, `end_year`, `precision`), with a source key and a short verbatim
    `quote`. The roles are:
    - `first_test`;
    - `arsenal`;
    - `inherited` (Soviet weapons left in Ukraine, Kazakhstan and Belarus);
    - `host_us`, from Norris, Arkin and Burr 1999 (NAB1999), with end dates from Wikipedia;
    - `host_us_territory` (Okinawa);
    - `host_ussr`.

    The source keys are NAB1999 (*Where They Were*, BAS Nov/Dec 1999, read in full), WP-LIST
    (Wikipedia, *List of states with nuclear weapons*, rev. 1386301986) and WP-SHARING
    (*Nuclear sharing*, rev. 1385978401).
- **How to join.** By country: `nucprob.sources.country_year.lookup(name, year)` resolves a name
  through the crosswalk (project names first, then COW names, then aliases) and returns the row.
  For the plan's date, use the year of the plan; the panel is annual.
- **"As of" dates.** The flags are "at any time during the year". For exact dating, the
  alliance and nuclear tables keep day or month dates where the source has them.

### Sources and licences

| Columns | Source | Coverage used | Licence |
|---|---|---|---|
| `vdem_polyarchy`, `vdem_libdem`, `vdem_regime` | V-Dem v16 core CSV (2026) | 1940-2025 | CC BY-SA 4.0 |
| `polity2` | Polity5 p5v2018 | to 2018 | CSP, free for research use |
| `bmr_democracy` | Boix-Miller-Rosato v4 (Dataverse FENWWR) | to 2020 | CC0 |
| `lied_lexical` | Lexical Index of Electoral Democracy v5.2 (Dataverse 29106) | to 2019 | CC0 |
| `mad_gdppc`, `mad_pop` | Maddison Project Database 2023 | to 2022 | CC BY 4.0 |
| `nmc_*` | COW National Material Capabilities **v7** (2026; v6 also downloaded) | to 2022 | COW, cite |
| `sipri_*` | SIPRI Military Expenditure Database, 1949-2025 xlsx | 1949-2025 | SIPRI, non-commercial with attribution |
| `us_troops` | troopdata (Allen, Flynn and Machain), rebuilt Kane/DMDC series | 1950-2024 | GPL-3 package |
| `nato` … `ussr_defense_pact` | COW formal alliances v4.1 (member level), plus nato.int | to 2012 (NATO to 2025) | COW, cite |
| `nuc_*`, `host_*` | `nuclear_status.csv` (hand-curated, cited) | 1945-2025 | n/a |

URLs, paths and hashes are in `data/sources.d/country_year.yaml`.

### Columns

| Column | Meaning and units |
|---|---|
| `cow_code`, `year` | key |
| `iso3` | ISO 3166 alpha-3 valid that year (former-state codes as above; Kosovo XKX) |
| `country` | COW state name (COW calls 365 "Russia" throughout, so the USSR is 365) |
| `cow_member` | 1 if a COW system member during the year, 0 for an added year (see Universe) |
| `vdem_polyarchy`, `vdem_libdem` | V-Dem electoral and liberal democracy indices, 0-1 |
| `vdem_regime` | Regimes of the World: 0 closed autocracy, 1 electoral autocracy, 2 electoral democracy, 3 liberal democracy |
| `polity2` | -10 to +10 |
| `bmr_democracy` | 0/1 |
| `lied_lexical` | 0-6 |
| `mad_gdppc` | GDP per capita, 2011 international dollars |
| `mad_pop` | population, thousands |
| `nmc_milex` | military expenditure, thousands of current US$ |
| `nmc_milper` | military personnel, thousands |
| `nmc_irst` | iron and steel production, thousands of tons |
| `nmc_pec` | primary energy consumption, thousands of coal-ton equivalents |
| `nmc_tpop`, `nmc_upop` | total and urban population, thousands |
| `nmc_cinc` | share of world capabilities, 0-1 |
| `sipri_milex_usd2024` | US$ m at constant 2024 prices |
| `sipri_milex_usd` | US$ m, current |
| `sipri_milex_gdp` | share of GDP, as a fraction |
| `us_troops` | US active-duty personnel in the country, highest value reported in the year (for the USA itself: at home) |
| `nato`, `warsaw_pact` | member during the year (0/1) |
| `us_defense_pact`, `us_bilateral_pact`, `ussr_defense_pact` | in a COW defence pact with the USA (any, or bilateral) or the USSR/Russia; NA after 2012 |
| `nuc_first_test_year` | year of first nuclear test (NA if none) |
| `nuc_tested` | 1 from the first test year |
| `nuc_arsenal` | own weapons that year |
| `nuc_inherited` | Soviet weapons on its territory after 1991 (NA for Belarus after 1991; end not sourced) |
| `host_us_nukes` | US weapons or non-nuclear components stored there; NA after the start year when the end is unknown (France from 1959, Morocco from 1966) |
| `host_ussr_nukes` | Soviet/Russian weapons stationed there; NA in 1955-91 for the GDR, Czechoslovakia, Hungary, Poland and Mongolia (dates not sourced); Cuba 1962; Belarus from 2023 (claimed) |

### Coverage: non-missing values by decade

| decade | 1940 | 1950 | 1960 | 1970 | 1980 | 1990 | 2000 | 2010 | 2020 |
|---|---|---|---|---|---|---|---|---|---|
| rows | 674 | 844 | 1226 | 1461 | 1600 | 1834 | 1924 | 1949 | 1170 |
| states | 83 | 90 | 134 | 157 | 161 | 195 | 194 | 195 | 195 |
| vdem_regime | 661 | 844 | 1225 | 1440 | 1509 | 1673 | 1714 | 1739 | 1044 |
| polity2 | 613 | 823 | 1186 | 1374 | 1421 | 1588 | 1612 | 1489 | 1 |
| bmr_democracy | 671 | 840 | 1223 | 1460 | 1597 | 1826 | 1922 | 1938 | 194 |
| lied_lexical | 656 | 840 | 1223 | 1460 | 1600 | 1830 | 1924 | 1948 | 0 |
| mad_gdppc | 470 | 802 | 1152 | 1330 | 1400 | 1591 | 1624 | 1630 | 489 |
| nmc_milex | 470 | 734 | 1220 | 1408 | 1484 | 1709 | 1807 | 1665 | 519 |
| nmc_cinc | 625 | 828 | 1226 | 1461 | 1600 | 1834 | 1924 | 1949 | 585 |
| sipri_milex_usd2024 | 16 | 342 | 686 | 960 | 1134 | 1359 | 1483 | 1523 | 922 |
| us_troops | 0 | 836 | 1216 | 1455 | 1600 | 1833 | 1924 | 1949 | 975 |
| us_defense_pact | 674 | 844 | 1226 | 1461 | 1600 | 1834 | 1924 | 584 | 0 |

`python -m nucprob.sources.country_year` prints the full table.

### Caveats

- **Maddison is territorial.** Its Germany is all of Germany, so there is no Maddison series
  for the FRG or the GDR in 1949-90, and those values are left missing. Its Vietnam is all of
  Vietnam, so it is used only from 1976. The USSR, Czechoslovakia and Yugoslavia series are
  used while those states existed, and Serbia's series stands for COW 345 from 1992.
- **SIPRI has no Soviet figures** for most of the Cold War ("..."), and its Chinese and other
  communist figures are sparse or estimates. Use NMC `milex` there, keeping in mind that NMC's
  own Soviet and Chinese figures are reconstructions.
- **Some source codes differ from COW's.**
  - Polity and BMR use their own codes for the USSR (364), unified Vietnam (818), Ethiopia
    (529), FRY and Serbia, Sudan and South Sudan. These are mapped to COW. In a transition year
    the successor's value is kept.
  - troopdata codes West Germany as 255 and South Vietnam as 816. These are moved to 260
    (1949-90) and 817 (to 1975).
- **Alliance coding.**
  - COW ends most Warsaw Pact memberships in late 1989 and Albania's in 1968. It ends
    Hungary's in November 1956 and never restores it, which the table corrects by hand
    (Hungary 1956-89).
  - COW v4.1 lacks NATO's 2004 and 2009 enlargements and ends in 2012. The NATO accessions
    missing from it come from nato.int, and the 2025 membership (32) matches nato.int.
  - Other pacts open in 2012 are NA afterwards, not assumed to continue.
- **Nuclear hosting is incomplete.**
  - Spain is named in NAB1999 without dates. France's US weapons have a start (August 1958) but
    no sourced end. The years of Soviet stationing in Eastern Europe and Mongolia are not
    sourced. These are NA, not 0.
  - The OSD custody history's Appendix B (the primary source, `nsa_19991020_appendix-B.pdf`,
    a scan) was downloaded but not transcribed.
  - Arsenal starts for China (1966), India (1988), Pakistan (mid-1980s), Israel (1966) and
    South Africa (1982-c.1991) are approximate (`precision` = approx).
- **No regime-group variable yet.** PLAN 5.3's primary grouping (communist party-based or
  personalist, non-communist autocracy, liberal democracy) needs Geddes-Wright-Frantz or
  Kailitz from the `democracyData` bundle, whose R data files were not read here. The present
  columns give the democracy dimension and the alignment axis (NATO, Warsaw Pact, US and Soviet
  pacts).
- **Penn World Table** was not added, because Maddison covers GDP per capita for 1940-2022.
