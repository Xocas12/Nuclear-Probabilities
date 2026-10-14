# The place universe: sources and caveats

`python -m nucprob.places` builds `data/processed/places_1956.parquet`. It holds every settlement
of 5,000 or more people near the study date (June 1956) in the countries of the SAC 1956
list. The universe proper is 10,000 or more. Every row has its 1956 country and first-order
unit, a population on or near the study date (`pop`, `pop_year`), a pre-war population where
a source has one, and coordinates from GeoNames. The rule is fixed before looking at the labels
(PLAN section 2).

| Country | Source | Figures | `pop` | Universe (10,000+) |
|---|---|---|---|---|
| USSR | pop-stat (14 republics), Demoscope (Uzbekistan) | censuses of 1939 and 1959 | 1959 census | 1,620 located of 1,635 |
| East Germany | *Statistisches Jahrbuch der DDR 1956*, table I.10 | 1939, 1946, 1950, end-1955, end-1956 | interpolated to 15 June 1956 | 214 |
| Poland | *Rocznik Statystyczny 1957*, table 7 | 1950 census, end-1956 estimate | interpolated | 207 |
| Czechoslovakia: Czech lands | pop-stat | censuses of 1930, 1950, 1961 | interpolated | 90 |
| Czechoslovakia: Slovakia | Votrubec (1959), `slovakia_towns_1954_1958.csv` | 1 January 1954 and 1958 | interpolated | 25 |
| Hungary | KSH, 2011 census historical series | censuses of 1941, 1949, 1960 | interpolated | 120 |
| Romania | pop-stat | censuses of 1930, 1948, 1956 | 1956 census | 101 |
| Bulgaria | pop-stat | censuses of 1934, 1946, 1956 | 1956 census | 56 |
| Albania | pop-stat | census of 1955 | 1955 census | 9 |
| China | 1953 census, via Wikipedia (from Shabad 1959) | 1953 census | 1953 census | 162 located of 163 |
| North Korea, North Vietnam, Mongolia | UN World Urbanization Prospects 2018 | annual model estimates | 1956 estimate | 5, 2, 1 |

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

## Matching to GeoNames

`nucprob/gazetteer/match.py` gives each settlement the GeoNames populated place of its name.
When several places share the name, it prefers the one in the settlement's region, then the
one whose GeoNames population is closest to the settlement's own figure, then the higher
administrative rank.
- **The figure** is the latest census where pop-stat gives a series (`modern_pop`). The East
  German, Polish, Hungarian, Slovak and Chinese sources and Demoscope's Uzbek table have no
  modern figure, so their figure near the study date (`pop`, or `pop_1959`) is used instead,
  mostly as a floor: towns grew, and GeoNames gives many Chinese cities their whole urban
  district's population, so a place larger than the figure is marked down a quarter as much
  as one equally smaller. A GeoNames place with population 0 is marked down, so a town does
  not land on a same-named hamlet.
- **The region** is inferred: each census region is mapped to the GeoNames region that most
  of its unambiguous settlements fall in. Two maps are made by hand instead
  (`nucprob/places_bloc.py`). With them a settlement is matched only within its own region,
  or not at all:
  - `CHINA_ADMIN1`: China's 1953 provinces to the provinces their territory lies in today. A
    province later split (Liaodong, Liaoxi, Rehe) or trimmed (Sichuan, Guangdong, Hebei,
    Jiangsu) maps to every province that took part of it. Chinese city names recur across
    provinces, and few provinces have enough unambiguous cities to be inferred. Population
    alone would put Suzhou on Jiuquan, in Gansu, which GeoNames also calls Suzhou.
  - `EAST_GERMANY_ADMIN1`: the GDR's Bezirke to today's Länder. Five Bezirke were divided in
    1990, and the inferred map sends each to a single Land: it sent Bezirk Leipzig to Saxony,
    which put Meuselwitz and Schmölln, Thuringian since 1990, on Saxon hamlets.
- **Before these rules** the bloc sources were matched without any population, and China
  without its provinces. Rematched on the GeoNames dumps of October 2026, 43 towns of East
  Germany, Poland and China moved 17 to 2,480 km: Dessau, Sosnowiec and Anshan among them,
  and Baotou, which had been on Hainan. Shandong's "Zhangzhou" (over 50,000 in 1953) has no
  place of that name in Shandong and is left unmatched. Hungary's and Slovakia's matches did
  not change. Uzbekistan's have not been rematched yet.
- **The population check.** `python -m nucprob.places` writes
  `data/processed/places_1956_population_check.csv`: every match whose GeoNames place has
  population 0, or under a tenth of `pop`. A town put on a hamlet shows up there. So do real
  towns that GeoNames records without a population, and towns since merged into a neighbour.
  A namesake of about the town's size does not: that is what the region maps are for.
  `population_check_reviewed.csv` explains the rows already checked, each for the GeoNames
  place it names; the build prints how many are left. East Germany, Poland, Hungary,
  Slovakia and China have been checked (12 rows, all real places without a GeoNames
  population); the other countries have not.

## `geonames_links.csv`

Hand-checked GeoNames links for names the matcher cannot resolve. They cover towns renamed
since the census whose old name GeoNames lacks, and East German names with a suffix that
GeoNames drops ("Neuenhagen bei Berlin"). Some towns are told apart from namesakes by hand:
the two Oelsnitz; Ebersbach; Grodziec and Cieplice, now parts of Będzin and Jelenia Góra;
Jinzhou, which shares Liaoning with a Jinzhou district of Dalian; Tianshui, Qulja and
Chaozhou, where a namesake or a county seat is nearer the 1953 size or carries the name.

## Transfer regions

The place universes of the smaller target lists (census town tables of Japan 1940, the US 1950,
Canada 1956, Denmark, the Netherlands, Belgium, Austria and Italy around 1961, and the UK 1981)
are described in [TRANSFER.md](TRANSFER.md).
