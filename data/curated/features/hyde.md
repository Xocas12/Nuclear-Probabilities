## HYDE gridded population (`nucprob/sources/hyde.py`)

- **What it is.** Gridded estimates of total, urban and rural inhabitants per 5 arc-minute cell
  (about 9 x 9 km at the equator; 2160 x 4320 cells covering the globe), from the History
  Database of the Global Environment, version **3.2.1**, baseline scenario (Klein Goldewijk,
  Beusen, Doelman and Stehfest 2017, "Anthropogenic land use estimates for the Holocene - HYDE
  3.2", *Earth System Science Data* 9, 927-953).
  - Variables: `popc` (all inhabitants), `urbc` (urban), `rurc` (rural); `urbc + rurc = popc`.
  - Years stored: 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010 and 2017.
  - World totals check out: 2.53 billion in 1950, 3.02 billion in 1960, 6.11 billion in 2000
    (logged per grid in `data/raw/population_grids/hyde/members.json`).
- **Source and licence.** DANS data station, doi:10.17026/DANS-25G-GEZ3, file
  `HYDE3_2_1-baseline.zip`. The station lists it as CC0 1.0, but the release readme says CC BY
  3.0, so cite the ESSD paper.
- **Why 3.2.1 and not 3.3.** HYDE 3.3 (doi:10.24416/UU01-AEZZIT, CC BY 4.0) has the same grid
  and goes on to 2023, so it would add 2020. Its landing page (public.yoda.uu.nl) opens from
  here, but the files are on geo.public.data.uu.nl, which answers every automated request with
  an "Anubis" proof-of-work bot check (a JavaScript challenge). It was not worked around.
  - To fetch 3.3 from a browser, download from
    `https://geo.public.data.uu.nl/vault-hyde/HYDE%203.3%5B1701183392%5D/original/hyde33_c7_base_mrt2023/zip/<year>AD_pop.zip`,
    with `<year>` = 1940, 1950, ..., 2020. Each zip holds `popc_`, `urbc_` and `rurc_<year>AD.asc`.
  - Then point `fetch()` at the local files; `parse_asc` reads the same format.
- **How it is stored.** The 5.3 GB zip is not downloaded. `fetch()` reads the central
  directory and the 30 needed members by HTTP range requests. The members are Deflate64, which
  Python's zipfile cannot read, so each one is rewrapped as a one-member zip and inflated with
  Info-ZIP `unzip`, which checks the CRC. The ASCII grid is then saved as a float32 `.npy`
  (`data/raw/population_grids/hyde/<var>_<year>.npy`, 37 MB each, 1.1 GB in all); no-data cells
  become 0.
- **Functions.**
  - `grid(year, var="popc")`: the array; row 0 is 90N, column 0 is 180W. Between stored years
    it is a linear interpolation.
  - `pop_within(lat, lon, year, km)`: the people within `km` (great-circle distance) of each
    point. The result is interpolated linearly between the two stored years around `year`;
    fractional years are allowed.
  - `urban_share_within(lat, lon, year, km)`: urban people divided by all people in the same
    disc (NaN where nobody lives).
  - Dates are clamped to 1930-2017: any year after 2017 uses the 2017 grid.
- **Method of the disc.**
  - The disc is an exact spherical cap. It is sampled in four latitude strips per cell row, and
    each strip's longitude half-width comes from the spherical law of cosines, so the
    cos(latitude) narrowing of cells is built in.
  - A strip's population is read off a running sum along its row, taking people as spread evenly
    over each cell. The grid wraps at the dateline.
  - Checked against brute-force sampling at 36 points per cell: within 1% at 25 km and 100 km,
    within about 1% at 10 km, and correct across the dateline and at 78N.
  - Speed: 50,000 points at 50 km take 0.3 s per grid once the running-sum table (75 MB,
    cached) is built.
- **How to join.** Join by any `lat`/`lon` and the plan date: `pop_within(places.lat,
  places.lon, plan_year, r)`. No names or countries are needed, so the same feature can be
  built for any country and year. It can stand in for, or check, the town-table features
  `log_pop_within_{25,50,100}km` in `nucprob/features/population.py`. Note that those features
  leave out the place itself, while the HYDE disc includes the cell of the place.

### Validation: people within 25 km and 50 km against census-based figures

`python -m nucprob.sources.hyde --check`. Every reference figure is read from a file, not typed
in:
- UN WUP 2018 file 12 gives urban agglomeration populations (census-based) and the
  coordinates of each disc's centre;
- pop-stat.mashke.org's Russia page gives the 1959 census populations of city proper.

| city | year | reference | HYDE 25 km | ratio | HYDE 50 km | ratio | urban share 25 km | reference figure |
|---|---|---:|---:|---:|---:|---:|---:|---|
| New York-Newark | 1950 | 12.34 M | 5.31 M | 0.43 | 8.45 M | 0.69 | 1.00 | WUP 2018 agglomeration |
| Chicago | 1960 | 6.18 M | 2.01 M | 0.32 | 4.42 M | 0.71 | 1.00 | WUP 2018 agglomeration |
| Los Angeles-Long Beach-Santa Ana | 1970 | 8.38 M | 2.93 M | 0.35 | 5.42 M | 0.65 | 1.00 | WUP 2018 agglomeration |
| London | 1950 | 8.36 M | 5.37 M | 0.64 | 8.95 M | 1.07 | 1.00 | WUP 2018 agglomeration (conurbation) |
| Paris | 1960 | 7.41 M | 7.05 M | 0.95 | 8.04 M | 1.09 | 0.66 | WUP 2018 agglomeration |
| Berlin | 1960 | 3.26 M | 3.76 M | 1.15 | 4.42 M | 1.36 | 0.75 | WUP 2018 agglomeration |
| Warszawa (Warsaw) | 1960 | 1.12 M | 1.45 M | 1.29 | 2.01 M | 1.80 | 0.91 | WUP 2018 agglomeration |
| Budapest | 1970 | 1.95 M | 2.44 M | 1.25 | 3.03 M | 1.56 | 0.65 | WUP 2018 agglomeration |
| Praha (Prague) | 1960 | 1.00 M | 1.34 M | 1.34 | 2.15 M | 2.15 | 0.72 | WUP 2018 agglomeration |
| Moskva (Moscow) | 1960 | 6.17 M | 6.39 M | 1.04 | 8.35 M | 1.35 | 0.89 | WUP 2018 agglomeration |
| Kyiv (Kiev) | 1960 | 1.16 M | 1.45 M | 1.25 | 1.89 M | 1.63 | 0.55 | WUP 2018 agglomeration |
| Tokyo | 1960 | 16.68 M | 9.67 M | 0.58 | 16.51 M | 0.99 | 0.60 | WUP 2018 (Keihin major metropolitan area) |
| Beijing | 1950 | 1.67 M | 1.34 M | 0.80 | 2.36 M | 1.41 | 0.23 | WUP 2018 (urban residents of the city) |
| Mumbai (Bombay) | 1970 | 6.41 M | 4.51 M | 0.70 | 7.04 M | 1.10 | 0.97 | WUP 2018 agglomeration |
| Al-Qahirah (Cairo) | 1960 | 3.68 M | 4.76 M | 1.29 | 6.84 M | 1.86 | 0.48 | WUP 2018 (Cairo governorate + Giza + Shubra) |
| São Paulo | 1980 | 12.09 M | 8.52 M | 0.70 | 11.47 M | 0.95 | 1.00 | WUP 2018 agglomeration |
| Moskva (city) | 1959 | 5.05 M | 6.24 M | 1.24 | 8.17 M | 1.62 | 0.89 | 1959 census, city proper (pop-stat) |
| Sankt Peterburg (city) | 1959 | 2.90 M | 2.95 M | 1.02 | 3.77 M | 1.30 | 0.68 | 1959 census, city proper (pop-stat) |
| Novosibirsk (city) | 1959 | 0.89 M | 1.02 M | 1.15 | 1.20 M | 1.36 | 0.97 | 1959 census, city proper (pop-stat) |
| Yekaterinburg (city) | 1959 | 0.78 M | 1.11 M | 1.42 | 1.50 M | 1.92 | 0.90 | 1959 census, city proper (pop-stat) |

How to read the table:
- **European and Soviet cities.** The 25 km disc lands within about 0.9-1.4 times the
  agglomeration or city figure. This is as expected, since the disc also takes in suburbs and
  villages.
- **Big sprawling metropolises.** In New York, Chicago, Los Angeles, Tokyo, London and São
  Paulo, 25 km catches only 30-65% of a metropolitan figure that reaches well past 25 km. At
  50 km the ratio is 0.65-1.1.
- **HYDE flattens city cores.** It spreads urban people over its built-up area proxy. New
  York's densest cell holds 0.74 M people in 1950, whereas Manhattan alone (about 3 cells) held
  far more. This understates dense cores and overstates their rings, which also pulls down the
  10 km figures.

### Caveats

- **Smooth by construction.** HYDE is a model. National and sub-national census totals
  (the HYDE country series) are downscaled with weights for urban and rural density and
  built-up area, so between two censuses a cell follows its country's trend, not the town's own
  history. Rank places by `pop_within` at 25 km or more; do not read a single cell's count
  literally.
- **Interpolation between decades.** Linear interpolation between decades misses wartime shocks:
  1940-1950 smooths over the losses of 1941-45 in the USSR, Poland and Germany. The grid has no
  1945 figure.
- **Today's borders and the urban definition.** HYDE country totals follow today's borders and
  its own urban definition, which is not each census's own, so the urban share is comparable
  across countries but not equal to official urban percentages.
- **End date.** There is no 2020 grid (3.3 is blocked, see above). Dates after 2017 return 2017
  values.
