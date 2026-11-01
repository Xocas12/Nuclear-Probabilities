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
| | | Austria: census 1961 (pop-stat; the 1961 Land seats from `POPSTAT_SEATS` in `places.py`) | 50 | 50 |
| | | Italy: census 1961 (ISTAT, comuni) | 814 | 814 |
| | | FRG, 1961 census (`towns_frg_1961.md`) | 583 | 582 |
| `uk_1980` (1980) | Square Leg 1980 | UK: census 1981 (GB districts from Nomis; NI towns from NISRA) | 476 | 476 |
| `japan_1945` (1945) | Target Committee 1945 | Japan: census 1940 (cities and towns) | 579 | 560 |
| `usa_1955` (1955) | Operation Alert 1955 | USA: census 1950 (urban places, 48 states and DC) | 1,262 | 1,262 |
| `canada_1956` (1956) | Canadian target areas 1956 | Canada: census 1956 (Canada Year Book) | 137 | 137 |

The other side's lists of targets **in the bloc** are scored on the bloc's own 1956 universe
(`data/processed/dataset_sac1956.parquet`), leaving out the sealed test:
- NATO's mirror lists from Polish (1962) and Hungarian (1965) exercises;
- the US lists for China (1958, 1963, 1964).

## How places get coordinates

`nucprob/transfer/places.py` looks each town up by name in its country's GeoNames dump: the
printed name, today's name, and the name without qualifiers, and only inside the town's own
first-order unit: `admin1_crosswalk.csv` lists the GeoNames units each table unit may lie in today
(Italian provinces also their province codes), and an unlisted unit stops the build. Among several
hits it prefers the town's province where known, then a place with at least a fifth of the town's
census people (main name before alternate name), then a seat, then the most people today. A town
with no hit in its unit stays unplaced, never on a same-named place elsewhere; the build prints
them. A fuzzy match (ratio 90+) must lie in the town's own unit. Hand-checked points take
precedence; a row with blank `lat` records why a town could not be placed:
- `transfer_links.csv` covers towns GeoNames does not know by their old name or places wrongly:
  Dutch rural municipalities placed at their seat, Canadian towns later merged, US unincorporated
  places, Japanese towns later merged (approximate centres) and one Italian comune; the
  `admin1` column tells apart towns of one name.
- `uk_districts_1981_seats.csv` gives each of Great Britain's 456 districts of 1981 the
  town where its council had its headquarters, checked against Wikipedia (card:
  `uk_districts_1981_seats.md`).

The pop-stat page for Austria has no seat column, and it underlines today's Land capitals
(St. Pölten, capital of Lower Austria only since 1986, and Dornbirn instead of Bregenz).
`POPSTAT_SEATS` in `places.py` lists the seats of 1961 instead: Wien (also the seat of Lower
Austria), Eisenstadt (under 10,000, so outside the universe), Klagenfurt, Linz, Salzburg,
Graz, Innsbruck and Bregenz. A seat name the page does not print exactly once stops the build.

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
`../features/uk_military_sites_1980.csv`. They are blank wherever no table covers a town:
- the US 1955, Canada 1956 and Japan 1945, which have no military table;
- Italy outside the 1965 table's scope. The table covers Italy north of the Po and the
  Venetian plain only: Lombardy, Veneto, Friuli-Venezia Giulia, Trentino-Alto Adige and the
  province of Novara (`Region.military_scope`, by 1961 province). The rest of Italy,
  including Turin, Genoa, La Spezia, Rome, Naples and Taranto, is blank, so 630 of the 814
  Italian comuni have no military distances.

Denmark, the Netherlands, Belgium, Austria and the UK are covered whole. A covered town near
the edge of the Italian scope is still measured only to the sites in the table, although an
uncovered site (La Spezia, say) may be closer. The leakage guard (`tests/test_leakage.py`)
covers this code.

The check scores "LightGBM, common + military" only on towns with all three distances. The
bloc never lacks one, so LightGBM learns no direction for a missing value and would score a
blank town as if it sat 0 km from all three kinds of site. A list with any blank town (the
US, Canada and Japan lists, and the Hungarian war game of 1965 through its Italian towns)
gets no metrics for that model.

Differences from the bloc:
- the tables stop at 10,000, so neighbour sums run a little lower than the bloc's (which
  count down to 5,000 in most countries). `pop_rank_pct` is not affected: it is ranked among
  towns of 10,000 or more in the bloc and here alike;
- the UK rows are districts, not towns;
- airfields, rail, ports and rivers are today's data, as for the bloc.

## Linking targets

`nucprob/transfer/labels.py` places each target in its own country:
- by a hand-checked point (`transfer_target_links.csv`, e.g. "8 km N of Køge" as printed);
- else by a town of the table with the same name;
- else by GeoNames.

It then links the target to the nearest town within 15 km; on a point shared by several towns,
to the town the target names, else the town rather than its rural municipality. Targets with no point, or no town
within 15 km (an air base or Nike site in open country), stay unlinked. The link report is
`data/processed/transfer_links.csv`.

| List | Targets in scored countries | Located | Linked | Towns listed / universe |
|---|---|---|---|---|
| Canada target areas 1956 | 13 | 13 | 13 | 13 / 137 |
| Operation Alert 1955 (full) | 53 | 53 | 52 | 51 / 1,262 |
| Square Leg 1980 | 95 | 87 | 78 | 75 / 476 |
| Target Committee 1945 | 42 | 40 | 40 | 17 / 579 |
| Lato-67 (FRG, DK, NL, BE) | 57 | 49 | 46 | 42 / 1,030 |
| Hungarian war game 1965 (AT, IT, FRG) | 19 | 12 | 12 | 12 / 1,447 |
| Burza 1961 (FRG, DK, NL) | 15 | 11 | 10 | 9 / 858 |
| Czechoslovak plan 1964 (FRG) | 21 | 14 | 7 | 6 / 583 |
| General Staff Academy lesson 1977 (FRG) | 5 | 4 | 3 | 3 / 583 |
| NATO mirror, Poland 1962 | 70 | 69 | 53 | 27 / 126 |
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
| Canada target areas 1956 | 13 / 137 | 0.85 / 0.82 | -0.03 [-0.13, +0.06] | 0.77 / 0.77 | 0.00 [-0.23, 0.00] | 0.96 / 0.97 | +0.01 [-0.02, +0.07] |
| Operation Alert 1955 (full) | 51 / 1,262 | 0.70 / 0.33 | -0.37 [-0.45, -0.26] | 0.59 / 0.37 | -0.22 [-0.33, -0.08] | 0.98 / 0.95 | -0.03 [-0.04, -0.02] |
| Target Committee 1945 | 17 / 579 | 0.88 / 0.26 | -0.62 [-0.75, -0.40] | 0.76 / 0.24 | -0.53 [-0.82, -0.29] | 0.98 / 0.94 | -0.04 [-0.07, -0.02] |
| Square Leg 1980 | 75 / 476 | 0.39 / 0.41 | +0.02 [-0.04, +0.11] | 0.39 / 0.39 | 0.00 [-0.07, +0.09] | 0.66 / 0.71 | +0.05 [+0.01, +0.10] |
| Lato-67 | 42 / 1,030 | 0.13 / 0.12 | -0.01 [-0.08, +0.06] | 0.14 / 0.19 | +0.05 [-0.07, +0.19] | 0.74 / 0.71 | -0.03 [-0.08, +0.02] |
| NATO mirror, Poland 1962 | 27 / 126 | 0.44 / 0.59 | +0.14 [+0.07, +0.21] | 0.44 / 0.52 | +0.07 [0.00, +0.22] | 0.68 / 0.73 | +0.06 [-0.01, +0.12] |
| NATO mirror, Hungary 1965 | 13 / 120 | 0.41 / 0.27 | -0.14 [-0.24, +0.02] | 0.38 / 0.38 | 0.00 [-0.08, +0.15] | 0.69 / 0.67 | -0.02 [-0.09, +0.04] |
| Hungarian war game 1965 (AT, IT, FRG) | 12 / 1,447 | 0.09 / 0.19 | +0.09 [-0.04, +0.32] | 0.17 / 0.33 | +0.17 [0.00, +0.50] | 0.79 / 0.83 | +0.04 [-0.01, +0.10] |

- **City lists.** On Operation Alert and the 1945 Target Committee list, the bloc model ranks
  the top of the list clearly worse than population alone, on every metric. The 14 Operation
  Alert towns on the map, a subset of the full list, show it most: PR-AUC 0.74 for the rule
  and 0.10 for LightGBM, -0.64 [-0.80, -0.43]; 9 of the 14 largest US places are listed,
  against 1 of LightGBM's top 14. Only on Canada's target areas do the two match.
- **Mixed lists** (Square Leg, Lato-67, the two mirror lists, the Hungarian war game). No
  gain is detectable, with two exceptions: PR-AUC on the Polish mirror list, +0.14 [+0.07, +0.21],
  and ROC-AUC on Square Leg, +0.05 [+0.01, +0.10]. The Polish list records what Polish staff expected
  NATO to strike, not an attacker's plan. Square Leg's PR-AUC and precision@k intervals include zero.
- These margins are fragile. Leaving one small Uzbek town unlocated, which changes no label in
  these lists, moved the Square Leg ROC-AUC interval's lower end from 0.00 to +0.01 and so
  across zero. An interval that barely excludes zero is not a finding.
- ROC-AUC differences are small on every list, which is why the ROC table alone read the city
  lists as "adds nothing".

Burza shows no gain: 9 linked towns of 858, PR-AUC 0.0965 for the rule and 0.0557 for LightGBM
on the common features, a difference of -0.0408 [-0.1930, +0.0103], which includes zero. None of
Burza's intervals excludes zero. `paired.csv` holds 129 intervals (the military model has no row on a
list with any town outside its table's scope), so at 95% a few will exclude zero by chance.

This is a check that the pipeline joins end to end, not a result: the protocol is frozen at M5.

## Caveats

- **FRG added 1 November 2026.** The official table of all 583 towns of 10,000+ could be fetched
  (`towns_frg_1961.md`), so the FRG is in the Western European universe and the plans and exercises
  that aim there are scored. The earlier Wikipedia table is kept as `frg_1961_wikipedia.csv`.
- **The UK universe is districts.** Official 1981 urban-area tables exist only in print, so a
  "place" is a 1981 district, located at its council's town. Square Leg's targets are linked
  to the district seat within 15 km, not to the district that contains them. Military
  targets in large rural districts can stay unlinked.
- **Japan's towns.** Town (machi) figures were read once by OCR with internal checks; the city
  figures are checked against the census's own totals. Villages of 10,000+ are left out.
- **Small lists.** Most lists have fewer than 30 linked towns, and several have under five, so
  their metrics have wide uncertainty.
