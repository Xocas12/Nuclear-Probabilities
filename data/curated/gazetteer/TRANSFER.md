# Transfer regions: data card

> **Rerun 2 November 2026** on the labels of the eighth amendment (`configs/protocol_amendment_8.yaml`). The classifier's reading is `REPORT.md`. Lists here cover whole countries, not the sectors of `SECTORS.yaml`.

The smaller target lists (PLAN sections 4.5 and 5.2) were first too small to train on, and tested
whether a model fitted on the Soviet bloc in 1956 ranks another plan's targets above the other
places of that plan's country and date. The classifier (`configs/protocol.yaml`) now also trains on them. Each list needs a **place universe**: every town of its
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
| | | Belgium: census 1961 (INS, communes) | 172 | 172 |
| | | Austria: census 1961 (pop-stat; the 1961 Land seats from `POPSTAT_SEATS` in `places.py`) | 50 | 50 |
| | | Italy: census 1961 (ISTAT, comuni) | 814 | 814 |
| | | FRG, 1961 census (`towns_frg_1961.md`) | 583 | 582 |
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
  Dutch rural municipalities placed at their seat (18 rows, unused since the nineteenth amendment withdrew
  the Dutch towns), Canadian towns later merged, US unincorporated
  places, Japanese towns later merged (approximate centres) and one Italian comune; the
  `admin1` column tells apart towns of one name.
- `uk_districts_1981_seats.csv`, the council seats of the 1981 districts, was removed from the tree:
  its district names came from Nomis output that robots.txt disallows, and nothing has read it since the
  tenth amendment withdrew Great Britain's table.

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
curated table `../features/weurope_military_sites_1965.csv`. A UK table of 1980 was built for Square Leg 1980 and
removed after the tenth amendment withdrew that list (git history holds it). They are blank wherever no table covers a town:
- the US 1955, Canada 1956 and Japan 1945, which have no military table;
- Italy outside the 1965 table's scope. The table covers Italy north of the Po and the
  Venetian plain only: Lombardy, Veneto, Friuli-Venezia Giulia, Trentino-Alto Adige and the
  province of Novara (`Region.military_scope`, by 1961 province). The rest of Italy,
  including Turin, Genoa, La Spezia, Rome, Naples and Taranto, is blank, so 630 of the 814
  Italian comuni have no military distances.

Denmark, Belgium and Austria are covered whole. A covered town near
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
- airfields, rail, ports and rivers are today's data, as for the bloc.

## Linking targets

`nucprob/transfer/labels.py` places each target in its own country:
- by a hand-checked point (`transfer_target_links.csv`, e.g. "8 km N of Køge" as printed);
- else by a town of the table with the same name;
- else by GeoNames.

It then links the target to the nearest town within 15 km; on a point shared by several towns,
to the town the target names, else the town rather than its rural municipality. Targets with no point, or no town
within 15 km (an air base or Nike site in open country), stay unlinked. The link report is
`data/processed/transfer_links.csv`. "Linked" counts rows of the list with a town; "towns listed" counts
towns linked to a row the document designates (`selected = 1`), so the Czechoslovak plan's 7 linked rows, none of
which states a nuclear weapon, list no town. Counts are of the tables rebuilt at 31d0ab3 (the links corrected by `configs/protocol_amendment_17.yaml`) and of
`runs/m4-transfer-check/metrics.csv`; `tests/test_transfer_paired.py` checks the last column against that file.

| List | Targets in scored countries | Located | Linked | Towns listed / universe |
|---|---|---|---|---|
| Canada target areas 1956 | 13 | 13 | 13 | 13 / 137 |
| Operation Alert 1955 (full) | 53 | 53 | 52 | 51 / 1,262 |
| Target Committee 1945 | 42 | 40 | 40 | 6 / 549 |
| Lato-67 (FRG, DK, BE) | 48 | 45 | 42 | 37 / 809 |
| Hungarian war game 1965 (AT, IT, FRG) | 19 | 12 | 12 | 12 / 1,446 |
| Burza 1961 (FRG, DK) | 14 | 8 | 7 | 6 / 637 |
| Czechoslovak plan 1964 (FRG) | 21 | 14 | 7 | 0 / 576 |
| General Staff Academy lesson 1977 (FRG) | 5 | 4 | 3 | 3 / 582 |
| NATO mirror, Poland 1962 | 70 | 69 | 54 | 27 / 126 |
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
| Canada target areas 1956 | 13 / 137 | 0.85 / 0.81 | -0.04 [-0.12, +0.04] | 0.77 / 0.77 | 0.00 [-0.15, 0.00] | 0.96 / 0.97 | +0.01 [-0.03, +0.06] |
| Operation Alert 1955 (full) | 51 / 1,262 | 0.70 / 0.32 | -0.37 [-0.45, -0.26] | 0.59 / 0.31 | -0.27 [-0.39, -0.12] | 0.98 / 0.95 | -0.03 [-0.04, -0.02] |
| Target Committee 1945 | 6 / 549 | 0.55 / 0.14 | -0.42 [-0.82, -0.11] | 0.67 / 0.00 | -0.67 [-1.00, -0.17] | 0.99 / 0.95 | -0.04 [-0.08, -0.01] |
| Lato-67 | 37 / 809 | 0.10 / 0.12 | +0.02 [-0.02, +0.08] | 0.11 / 0.16 | +0.05 [-0.05, +0.22] | 0.70 / 0.68 | -0.01 [-0.07, +0.04] |
| NATO mirror, Poland 1962 | 27 / 126 | 0.44 / 0.59 | +0.14 [+0.07, +0.21] | 0.44 / 0.52 | +0.07 [0.00, +0.22] | 0.68 / 0.74 | +0.06 [-0.01, +0.13] |
| NATO mirror, Hungary 1965 | 13 / 120 | 0.41 / 0.28 | -0.13 [-0.24, +0.04] | 0.38 / 0.38 | 0.00 [-0.08, +0.15] | 0.69 / 0.68 | -0.02 [-0.09, +0.05] |
| Hungarian war game 1965 (AT, IT, FRG) | 12 / 1,446 | 0.09 / 0.21 | +0.12 [-0.03, +0.35] | 0.17 / 0.25 | +0.08 [-0.17, +0.33] | 0.79 / 0.83 | +0.04 [-0.01, +0.11] |

- **City lists.** On Operation Alert the bloc model ranks the top of the list clearly worse than population alone,
  on every metric. The 14 Operation Alert towns on the map, a subset of the full list, show it most: PR-AUC 0.74 for the
  rule and 0.09 for LightGBM, -0.65 [-0.81, -0.44]. On the Target Committee's 6 designated towns, PR-AUC -0.42 [-0.82, -0.11] is also worse, with a wide interval. On Canada's target areas the
  two cannot be told apart, -0.04 [-0.12, +0.04]. That row rests on a text extract of unrecorded origin (`data/sources.yaml`) and is not scored in the classifier.
- **Mixed lists** (Lato-67, the two mirror lists, the Hungarian war game). No
  gain is detectable, with one exception: PR-AUC on the Polish mirror list, +0.14 [+0.07, +0.21]. The Polish list records what Polish staff expected
  NATO to strike, not an attacker's plan.
- These margins are fragile. Before Square Leg was withdrawn, leaving one small Uzbek town unlocated, which changes no label in
  these lists, moved the Square Leg ROC-AUC interval's lower end across zero. An interval that barely excludes zero is not a finding.
- ROC-AUC differences are small on every list, which is why the ROC table alone read the city
  lists as "adds nothing".

Burza shows no gain: 6 linked towns of 637 (this card reads whole countries; the classifier reads its sector), PR-AUC 0.04 for the rule and 0.04 for LightGBM
on the common features, a difference of 0.00 [-0.06, +0.03], which includes zero. 0 of
Burza's intervals exclude zero. `paired.csv` holds 111 intervals (the military model has no row on a
list with any town outside its table's scope), so at 95% a few will exclude zero by chance.

This is a check that the pipeline joins end to end, not a result: it was read before the protocol (`configs/protocol.yaml`) was frozen. The classifier run is in `REPORT.md`.

## Caveats

- **FRG added 1 November 2026.** The official table of all 583 towns of 10,000+ could be fetched
  (`towns_frg_1961.md`), so the FRG is in the Western European universe and the plans and exercises
  that aim there are scored. The earlier Wikipedia table is kept as `frg_1961_wikipedia.csv`.
- **No Netherlands universe.** The Dutch census volume of 1960 came through a path of `ssh.datastations.nl`
  that robots.txt disallows and no allowed copy was found, so the Dutch towns were withdrawn
  (`configs/protocol_amendment_19.yaml`). Lato-67 and Burza are scored on their other countries.
- **No UK universe.** Square Leg 1980 (95 targets) is no longer scored (tenth amendment). Its universe was Great
  Britain's 1981 districts, whose totals came through a Nomis path that robots.txt disallows; no allowed copy was
  found (`towns_uk_1981.md`). Until 46021d7 it scored 73 linked districts of 476, PR-AUC 0.38 for the rule and 0.41
  for LightGBM; those rows are in that commit's `runs/m4-transfer-check/`.
- **Japan's towns.** Town (machi) figures were read once by OCR with internal checks; the city
  figures are checked against the census's own totals. Villages of 10,000+ are left out.
- **Small lists.** Most lists have fewer than 30 linked towns, and several have under five, so
  their metrics have wide uncertainty.

## Places that share a point

Some census units are a rural municipality around a town, or a district absorbed into it, and have no point of their
own in GeoNames. They are placed at the point of the town whose name they carry or that absorbed them, so the two get
identical distance and density features. No point is invented for them. The pairs in the classifier table:

| Town | Unit at the same point | Country |
|---|---|---|
| Varel | Varel - Land * (rural municipality; the asterisk is the census table's) | FRG |
| Ibbenbüren | Ibbenbüren, Land (rural municipality) | FRG |
| Bielefeld | Senne II (now part of Bielefeld) | FRG |
| Newport News | Newsome Park-Hilton Park (now part of Newport News) | USA |

Before the nineteenth amendment withdrew the Dutch towns, Zwolle and Zwollerkerspel were a fifth pair.
`tests/test_shared_points.py` fails if any other pair of places shares a point.
