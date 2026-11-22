## Historical city populations (`nucprob/sources/historical_cities.py`)

- **What it is.** One tidy table of city populations with coordinates, one row per city and
  year, built by `python -m nucprob.sources.historical_cities` into
  `data/processed/historical_cities.parquet` (43,832 rows).
  - Columns: `source`, `name`, `other_name`, `country` (today's), `lat`, `lon`, `year`
    (negative = BC), `pop` (persons), `certainty` (Reba only: 1 = location sure .. 3 =
    doubtful), `city_code` and `note` (WUP only), `projected` (WUP years after 2018).
- **Sources.**
  - **Reba, Reitsma and Seto 2016**, "Spatializing 6,000 years of global urbanization from
    3700 BC to AD 2000", *Scientific Data* 3:160034. Figshare, CC BY 4.0; version 2 of each
    file.

    | `source` | file | rows | cities | years |
    |---|---|---:|---:|---|
    | `reba_chandler` | `chandlerV2.csv` (doi:10.6084/m9.figshare.2059494) | 9,438 | 1,573 | 2250 BC-AD 1975 |
    | `reba_modelski_ancient` | `modelskiAncientV2.csv` (2059497) | 621 | 153 | 3700 BC-AD 1000 |
    | `reba_modelski_modern` | `modelskiModernV2.csv` (2059500) | 293 | 292 | AD 2000 only |

    In the Cold War years Chandler has 430 cities in 1950 (80,000 to 12.5 million people;
    61 in the US, 37 in Russia, 34 in China, 27 in Germany, 23 in the UK), 73 in 1970 and 393
    in 1975. The years 1936-1953 other than 1950 hold only a couple of dozen scattered values.
  - **UN World Urbanization Prospects 2018, file 12** (`WUP2018-F12-Cities_Over_300K.xls`,
    from `WUP2018-Excel-files.zip` on the WUP site's archive page; CC BY 3.0 IGO):
    - 1,860 urban agglomerations of 300,000 or more in 2018, in 154 countries, every five
      years 1950-2035, with coordinates (`wup2018`: 33,480 rows; 2020-2035 are projections);
    - `note` refers to the NOTES sheet (`wup_notes()`), which says whether a figure is city
      proper, urban agglomeration or metropolitan area. 63% of rows have no note, meaning the
      standard urban agglomeration definition.
- **Functions.**
  - `load()`: the whole table.
  - `as_of(table, year, source)`: one row per city whose observations bracket `year`, with the
    population interpolated linearly between the two nearest observations and never
    extrapolated.
- **How to join.** Join by `lat`/`lon` (for example the nearest city within a few km, or
  sums within r km with `nucprob.geo.Points`) and the plan date via `as_of`. Names are in
  English (WUP adds the local form, "Moskva (Moscow)"). Chandler uses today's names (Saint
  Petersburg, not Leningrad), and `country` is today's state for all sources. It does not map
  onto the plan-date country without the `country_codes.csv` crosswalk (once that exists) or
  CShapes.
- **Caveats.**
  - **Chandler's figures are his own estimates for the metropolitan area.** They are rounded
    (Moscow 1950: 5.1 M; Berlin 1950: 3.707 M) and are not census counts. Use Chandler to cover
    the early and pre-census years, not as a precise figure.
  - **WUP is a list of survivors.** It only holds places of 300,000 or more in **2018**, so a
    1950 city that later stagnated below 300,000 is missing, and many 1950 values are tiny (the
    smallest is 5 people). Do not use WUP as a complete city list for 1950-1970. It is best for
    the largest cities, at five-year steps.
  - **Definitions differ between sources and over time.** Notes 70 (Tokyo: Keihin/Keihinyo/Kanto
    M.M.A.), 125 (London: conurbation, then urban area) and 39/40 (Chinese cities: city
    districts) mark breaks in the series.
  - **No end dates.** Cities do not end; a missing year means the source has no figure, not
    that the city did not exist.
  - **Validation.** WUP agglomerations and 1959 census figures are compared with HYDE's disc
    sums in `hyde.md`.
