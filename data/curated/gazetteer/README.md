# The place universe: sources and caveats

`python -m nucprob.places` builds `data/processed/places_1956.parquet`. It holds the settlements
of the countries of the SAC 1956 list near the study date (June 1956), down to 5,000 people
where the source goes that low and to the source's own floor where it does not (the "Table
floor" column below). The universe proper is 10,000 or more. Every row has its 1956 country and first-order
unit, a population on or near the study date (`pop`, `pop_year`), a pre-war population where
a source has one, and coordinates from GeoNames. The rule is fixed before looking at the labels
(PLAN section 2).

| Country | Source | Figures | `pop` | Table floor | Universe (10,000+) |
|---|---|---|---|---|---|
| USSR | pop-stat (14 republics), Demoscope (Uzbekistan) | censuses of 1939 and 1959 | 1959 census | 5,000 | 1,620 located of 1,635 |
| East Germany | *Statistisches Jahrbuch der DDR 1956*, table I.10 | 1939, 1946, 1950, end-1955, end-1956 | interpolated to 15 June 1956 | 10,000 (end of 1956) | 214 |
| Poland | *Rocznik Statystyczny 1957*, table 7 | 1950 census, end-1956 estimate | interpolated | 10,000 (end of 1956) | 207 |
| Czechoslovakia: Czech lands | pop-stat | censuses of 1930, 1950, 1961 | interpolated | 5,000 | 90 |
| Czechoslovakia: Slovakia | Votrubec (1959), `slovakia_towns_1954_1958.csv` | 1 January 1954 and 1958 | interpolated | 10,000 (1953) | 25 |
| Hungary | KSH, 2011 census historical series | censuses of 1941, 1949, 1960 | interpolated | 5,000 | 120 |
| Romania | pop-stat | censuses of 1930, 1948, 1956 | 1956 census | 5,000 | 101 |
| Bulgaria | pop-stat | censuses of 1934, 1946, 1956 | 1956 census | 5,000 | 56 |
| Albania | pop-stat | census of 1955 | 1955 census | 5,000 | 9 |
| China | 1953 census, via Wikipedia (from Shabad 1959) | 1953 census | 1953 census | cities (*shi*) only | 162 located of 163 |
| North Korea, North Vietnam, Mongolia | UN World Urbanization Prospects 2018 | annual model estimates | 1956 estimate | cities of 300,000+ today | 5, 2, 1 |

The floor matters in two places.

- **`pop_rank_pct`** is ranked within each country among its settlements of 10,000 or more
  only (`RANK_FLOOR` in `nucprob/features/population.py`), a floor that every country's table
  and every transfer town table reaches. Ranked over the whole table, a town of 10,000 sat near
  the middle in the USSR and at the bottom in East Germany. Coverage above the floor still
  differs: China's towns (*zhen*) and Poland's *osiedla* are missing, so their cities rank
  against fewer places.
- **Linking SAC targets** (`nucprob/labels/sac1956.py`). A target nearest to a settlement below
  10,000 stays with it, so it does not make a larger neighbour look targeted. Where the table
  stops at 10,000 (East Germany, Poland, Slovakia) or at cities (China, North Korea, North
  Vietnam, Mongolia) there are no such settlements, and a target at a town of 5,000-10,000
  goes to a larger town within 10 km. No absorbers below 10,000 are added for these countries,
  and the 5,000 sensitivity threshold cannot be run there.

## Caveats

- **Boundaries.**
  - pop-stat's Czech figures and KSH's Hungarian series are for today's municipal territory.
    This inflates towns that later absorbed villages. Budapest's 1949 figure is Greater
    Budapest, which existed from 1950.
  - The GDR yearbook gives each date's own boundaries.
- **Coverage.**
  - Poland's table lists towns (*miasta*) only. Urban-type settlements (*osiedla*, 389,000
    people in 1956) are not in it.
  - Slovakia's list is the 25 towns that had 10,000 or more early in 1953. Towns that passed
    10,000 later are missing, perhaps three to five of them.
  - China's universe is its 163 cities (*shi*) of 1953. The roughly 1,450 towns (*zhen*) have no
    accessible figures. Six of the cities are given only as "over 50,000"
    (`notes` says so). Ullman (1961), *Cities of Mainland China: 1953 and 1958*, would add
    1958 figures. It is in the public domain but its scans block scripts.
  - North Korea, North Vietnam and Mongolia have only the UN's model estimates, for cities of
    300,000+ today. Their universes are those cities.
- **Closed towns** of the Soviet nuclear complex and test ranges are missing from the
  published 1959 tables. They come from `closed_cities_1956.csv`: towns founded by June 1956
  with 5,000 or more people. Their populations are imputed and flagged `pop_imputed`. The towns
  are Sarov, Ozersk, Seversk, Zheleznogorsk, Novouralsk, Lesnoy, Snezhinsk, Trekhgorny,
  Znamensk, Kurchatov and Leninsk (Baikonur).
  - **Figures.** Most are read off Reissig (2024, *Izvestiya RAN, Ser. Geogr.* 88(5), Fig. 2),
    to about ±1,000. Kurchatov has only a 1990 figure; Leninsk's is for the end of 1959.
  - **Membership.** It was checked against the published 1959 urban tables:
    - Zarechny (Penza-19), Sillamäe, Severomorsk, Chkalovsk, Zhovti Vody and Mailuu-Suu are in
      those tables, so they are not added twice.
    - Zelenogorsk, Priozersk, Mirny, Stepnogorsk and Krasnokamensk were founded after June 1956.
  - **Why they are in.** They are in the universe because they existed, not because of how they
    were targeted (PLAN section 3.1).
- **Names.** `name_1956` is the name on the study date, where the sources record renamings
  (Molotov, Stalino, Stalinogród, Karl-Marx-Stadt, Stalinstadt, Orașul Stalin, Kolarovgrad).

## Reading the scanned tables

- **The GDR yearbook** is read from its PDFs' text layer by word position (`nucprob/sources/ddr.py`).
  Seven names missing from the text layer were read off the page images: Anklam, Halberstadt,
  Haldensleben, Heidenau, Rodewisch, Roßlau and Saßnitz. So was one figure, Stralsund 1956.
  Towns merged after 1946 (Annaberg-Buchholz, Limbach-Oberfrohna, Ribnitz-Damgarten) print
  their parts' 1939 and 1946 figures stacked; the parser sums them.
- **The Polish yearbook** is read from Polona's ALTO OCR (`nucprob/sources/gus.py`). Fifteen
  names the OCR missed were read off the page images, the Kieleckie voivodeship heading among
  them.
- **Votrubec's Slovak rows** were transcribed and checked against the scan. The text layer
  misreads Nitra's change (2 030 for 2 630) and Trnava's (1 706 for 1 796).

## `geonames_links.csv`

Hand-checked GeoNames links for names the matcher cannot resolve. They cover towns renamed
since the census whose old name GeoNames lacks, and East German names with a suffix that
GeoNames drops ("Neuenhagen bei Berlin"). The two Oelsnitz are told apart by hand.

## Transfer regions

The place universes of the smaller target lists (census town tables of Japan 1940, the US 1950,
Canada 1956, Denmark, the Netherlands, Belgium, Austria and Italy around 1961, and the UK 1981)
are described in [TRANSFER.md](TRANSFER.md).
