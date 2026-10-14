# Transfer regions: data card

The smaller target lists (PLAN sections 4.5 and 5.2) are too small to train on. They test
whether a model fitted on the Soviet bloc in 1956 ranks another plan's targets above the other
places of that plan's country and date. Each list needs a **place universe**: every town of its
countries near its date, with the same features as the bloc's towns. This folder holds those
universes. The code is in `nucprob/transfer/`.

```
python -m nucprob.transfer.places     # town tables -> data/processed/transfer_places.parquet
python -m nucprob.transfer.features   # common features -> features_transfer.parquet
python -m nucprob.transfer.labels     # list targets -> transfer_links.csv, labels_transfer.parquet
python -m nucprob.transfer.check      # runs/m4-transfer-check/
```

## Regions and their town tables

Each table is a census table for one country at one date, with towns of 10,000 or more.
Every table has its own card (`towns_<country>_<year>.md`) giving the source, checks and
doubts, and the specification is in `TOWNS_INSTRUCTIONS.md`. No table uses a target list or
war plan.

| Region (`nucprob/transfer/regions.py`) | Lists | Country: table | Places | Located |
|---|---|---|---|---|
| `wp_west_1965` (feature year 1965) | Warsaw Pact exercises and plans 1961-1977 | Denmark: census 1960 (Statistisk Årbog 1961) | 55 | 55 |
| | | Netherlands: census 1960 (CBS, municipalities) | 220 | 220 |
| | | Belgium: census 1961 (INS, communes) | 172 | 172 |
| | | Austria: census 1961 (pop-stat) | 50 | 50 |
| | | Italy: census 1961 (ISTAT, comuni) | 814 | 814 |
| | | FRG: **withheld** (see below) | (356) | |
| `uk_1980` (1980) | Square Leg 1980 | UK: census 1981 (GB districts from Nomis; NI towns from NISRA) | 476 | 476 |
| `japan_1945` (1945) | Target Committee 1945 | Japan: census 1940 (cities and towns) | 579 | 579 |
| `usa_1955` (1955) | Operation Alert 1955 | USA: census 1950 (urban places, 48 states and DC) | 1,262 | 1,262 |
| `canada_1956` (1956) | Canadian target areas 1956 | Canada: census 1956 (Canada Year Book) | 137 | 137 |

The other side's lists of targets **in the bloc** are scored on the bloc's own 1956 universe
(`data/processed/dataset_sac1956.parquet`), leaving out the sealed test:
- NATO's mirror lists from Polish (1962) and Hungarian (1965) exercises;
- the US lists for China (1958, 1963, 1964).

## How places get coordinates

`nucprob/transfer/places.py` looks each town up by name in its country's GeoNames dump: the
printed name, today's name, and the name without qualifiers. Among several hits it prefers the
town's own first-order unit, then a seat, then the most people today. A fuzzy match (ratio
90+) must lie in the town's own unit. Hand-checked points take precedence:
- `transfer_links.csv` covers towns GeoNames does not know by their old name: 16 Dutch
  rural municipalities placed at their seat, 6 Canadian towns later merged, 4 US
  unincorporated places, 14 Japanese towns later merged (approximate centres), and one
  Italian comune.
- `uk_districts_1981_seats.csv` gives each of Great Britain's 456 districts of 1981 the
  town where its council had its headquarters, checked against Wikipedia (card:
  `uk_districts_1981_seats.md`).

## Features

`nucprob/transfer/features.py` builds the bloc's features wherever the same source covers every
region in the same way (`COMMON`, 20 features):
- population, its rank in the country, and the people of the other towns within 25, 50 and
  100 km;
- the distance to a town of 100,000+;
- capital and regional seat, and the distance to the capital;
- elevation, relief and the distance to the coast;
- WRI power capacity within 25 km, counting only plants commissioned by the region's year;
- OurAirports airfields within 10, 25 and 50 km;
- Natural Earth rail, ports and major rivers.

Three military distances (naval base, strike or bomber base, nuclear site) come from the
curated tables `../features/weurope_military_sites_1965.csv` and
`../features/uk_military_sites_1980.csv`. They are blank for the US 1955, Canada and
Japan. The leakage guard (`tests/test_leakage.py`) covers this code.

Differences from the bloc:
- the tables stop at 10,000, so neighbour sums run a little lower than the bloc's (which
  count down to 5,000);
- the UK rows are districts, not towns;
- airfields, rail, ports and rivers are today's data, as for the bloc.

## Linking targets

`nucprob/transfer/labels.py` places each target in its own country:
- by a hand-checked point (`transfer_target_links.csv`, e.g. "8 km N of Køge" as printed);
- else by a town of the table with the same name;
- else by GeoNames.

It then links the target to the nearest town within 15 km. Targets with no point, or no town
within 15 km (an air base or Nike site in open country), stay unlinked. The link report is
`data/processed/transfer_links.csv`.

| List | Targets in scored countries | Located | Linked | Towns listed / universe |
|---|---|---|---|---|
| Canada target areas 1956 | 13 | 13 | 13 | 13 / 137 |
| Operation Alert 1955 (full) | 53 | 53 | 52 | 51 / 1,262 |
| Square Leg 1980 | 95 | 87 | 78 | 75 / 476 |
| Target Committee 1945 | 42 | 40 | 40 | 17 / 579 |
| Lato-67 (DK, NL, BE) | 29 | 29 | 26 | 23 / 447 |
| Hungarian war game 1965 (AT, IT) | 15 | 9 | 9 | 9 / 864 |
| NATO mirror, Poland 1962 | 70 | 69 | 54 | 28 / 126 |
| NATO mirror, Hungary 1965 | 23 | 13 | 13 | 13 / 120 |

## Check run (`runs/m4-transfer-check/`)

The check fits on the bloc's SAC 1956 labels and scores each list:
- with the common features only;
- for the bloc lists, without the list's country;
- against the population rule as baseline.

PR-AUC is the primary metric (PLAN section 5.5): the lists' base rates run from 1% to 22%,
and ROC-AUC barely moves when the top of a ranking goes wrong. Each difference below is
LightGBM (common) minus the population rule, with a 95% interval from a paired bootstrap:
2,000 resamples, positives and negatives resampled separately, the same towns scoring both
models. `runs/m4-transfer-check/paired.csv` has every model and list
(`python -m nucprob.transfer.paired` rebuilds it from `scores.csv`). Precision@k takes k as
the number of towns listed.

| List | Listed / towns | PR-AUC, rule / LightGBM | PR-AUC difference [95% CI] | Precision@k, rule / LightGBM | Precision@k difference [95% CI] | ROC-AUC, rule / LightGBM | ROC-AUC difference [95% CI] |
|---|---|---|---|---|---|---|---|
| Canada target areas 1956 | 13 / 137 | 0.85 / 0.84 | -0.01 [-0.11, +0.12] | 0.77 / 0.69 | -0.08 [-0.15, +0.15] | 0.96 / 0.98 | +0.02 [-0.02, +0.08] |
| Operation Alert 1955 (full) | 51 / 1,262 | 0.70 / 0.33 | -0.36 [-0.44, -0.25] | 0.59 / 0.41 | -0.18 [-0.27, -0.04] | 0.98 / 0.92 | -0.06 [-0.10, -0.03] |
| Target Committee 1945 | 17 / 579 | 0.88 / 0.34 | -0.54 [-0.67, -0.30] | 0.76 / 0.41 | -0.35 [-0.65, -0.18] | 0.98 / 0.95 | -0.03 [-0.05, -0.01] |
| Square Leg 1980 | 75 / 476 | 0.39 / 0.42 | +0.04 [-0.04, +0.13] | 0.39 / 0.40 | +0.01 [-0.07, +0.11] | 0.66 / 0.70 | +0.04 [-0.02, +0.11] |
| Lato-67 | 23 / 447 | 0.32 / 0.24 | -0.08 [-0.20, +0.08] | 0.30 / 0.43 | +0.13 [-0.13, +0.22] | 0.74 / 0.76 | +0.02 [-0.10, +0.13] |
| NATO mirror, Poland 1962 | 28 / 126 | 0.47 / 0.54 | +0.07 [-0.01, +0.15] | 0.46 / 0.50 | +0.04 [-0.11, +0.18] | 0.69 / 0.71 | +0.02 [-0.06, +0.09] |
| NATO mirror, Hungary 1965 | 13 / 120 | 0.41 / 0.31 | -0.11 [-0.20, +0.04] | 0.38 / 0.38 | 0.00 [0.00, +0.15] | 0.69 / 0.68 | -0.02 [-0.10, +0.06] |
| Hungarian war game 1965 (AT, IT) | 9 / 864 | 0.16 / 0.26 | +0.09 [-0.05, +0.30] | 0.11 / 0.44 | +0.33 [0.00, +0.56] | 0.86 / 0.85 | -0.01 [-0.04, +0.01] |

- **City lists.** On Operation Alert and the 1945 Target Committee list, the bloc model ranks
  the top of the list clearly worse than population alone, on every metric. The 14 Operation
  Alert towns on the map, a subset of the full list, show it most: PR-AUC 0.74 for the rule
  and 0.12 for LightGBM, -0.62 [-0.78, -0.39]; 9 of the 14 largest US places are listed,
  against 1 of LightGBM's top 14. Only on Canada's target areas do the two match.
- **Mixed lists** (Square Leg, Lato-67, the two mirror lists, the Hungarian war game). No
  gain is detectable: every interval includes zero, on all three metrics. Lato-67 even
  points different ways on PR-AUC and precision@k.
- ROC-AUC differences are small on every list, which is why the ROC table alone read the city
  lists as "adds nothing".

Two other lists have a model interval in `paired.csv` that excludes zero in the model's
favour, and neither is much to lean on. Burza has 3 linked towns of 275, and both scores sit
near its 1% base rate (PR-AUC 0.013 for the rule, 0.027 for LightGBM). On the Polish mirror
list, the model with the military distances added gains in PR-AUC, +0.12 [+0.02, +0.20], but
its ROC-AUC and precision@k intervals include zero. `paired.csv` holds 144 intervals (16
lists, three models, three metrics), so at 95% a few will exclude zero by chance.

This is a check that the pipeline joins end to end, not a result: the protocol is frozen at M5.

## Caveats

- **FRG withheld.** No official 1961 table could be fetched. The Statistische Bibliothek and
  Mannheim's yearbook scans were unreachable, GDZ has not digitised the yearbooks, and the
  archive.org copies are lending-only. `towns_frg_1961.csv`, built from de.wikipedia's
  municipality articles, covers about 356 of some 583 towns and misses some large ones.
  Until an official table is in, the FRG is out of the universe
  (`Region.withheld`), and its targets (all of the ČSLA plan, the 1977 GSA lesson, most of
  Burza and the FRG part of Lato-67) are not scored.
- **The UK universe is districts.** Official 1981 urban-area tables exist only in print, so a
  "place" is a 1981 district, located at its council's town. Square Leg's targets are linked
  to the district seat within 15 km, not to the district that contains them. Military
  targets in large rural districts can stay unlinked.
- **Japan's towns.** Town (machi) figures were read once by OCR with internal checks; the city
  figures are checked against the census's own totals. Villages of 10,000+ are left out.
- **Small lists.** Most lists have fewer than 30 linked towns, and several have under five, so
  their metrics have wide uncertainty.
