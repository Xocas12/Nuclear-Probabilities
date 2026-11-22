## Wikidata facilities (`wikidata_facilities`)

- **What it is.** 158,648 rows on 154,266 Wikidata items with coordinates, in 31 classes:
  military bases and installations, economic plants and infrastructure, and political seats,
  worldwide, with opening and closing dates where Wikidata has them. Built by
  `nucprob/sources/wikidata_facilities.py` into `data/processed/wikidata_facilities.parquet`
  (git-ignored; `python -m nucprob.sources.wikidata_facilities all` rebuilds it).
- **Source and licence.** Wikidata via the Query Service, `https://query.wikidata.org/sparql`,
  retrieved 2026-11-22. CC0 1.0. Every raw response is kept, with its SPARQL text, under
  `data/raw/wikidata/` (gzipped JSON; 68 files, about 12 MB). They are listed in
  `data/sources.d/wikidata_facilities.yaml` with sha256 hashes.
- **Rows.** One row per item and class. For capitals, there is one row per city, polity and
  stint. The classes are mostly disjoint, but some items fall in two (a naval base can also be
  a port). Military bases leave out air bases, naval bases and radar stations, which have their
  own classes. Power stations leave out nuclear and hydroelectric plants, and factories leave
  out the plants that have their own classes.
- **Columns.**
  - `qid`, `class`, `family` (military, economic or political), and `subclass` /
    `subclass_qid` (the P31 types that put the item in the class).
  - `label_en`: the English label, or the `mul` label if there is no English one.
  - `label_orig` / `label_orig_lang`: P1705 (native label) or P1448 (official name) where
    present; otherwise the label in an official language of the item's present country.
    Filled for 35% of rows.
  - `country_qid` / `country`: the present P17 (the preferred statement, else one with no end
    date). `country_history` holds every P17 statement as JSON
    `[qid, label, start, end]`; only 5% of rows have dated statements.
  - `lat`, `lon` (P625).
  - `P571_year` (inception), `P729_year` (service entry), `P576_year` (dissolved),
    `P730_year` (service retirement) and `P3999_year` (official closure). Each is the earliest
    value; deprecated statements are skipped.
  - `start_year` is P729 if present, else P571, with `start_source` and `start_precision`
    (9 = year, 8 = decade, 7 = century, 10/11 = month or day). `end_year` is the earliest of
    P576, P730 and P3999, with `end_source`.
  - `undated` is true when there is no start year. These rows are kept.
  - `capacity_mw`: P2109, normalised to watts by Wikidata and divided by 10^6. If there are
    several values, the largest is kept.
  - `fuel`: power classes only. It is a keyword class (coal, gas, oil, nuclear, hydro, solar,
    wind, geothermal, biomass, storage) read from the subclass, P516 (powered by) and the P31
    labels.
  - `powered_by`, and `product` (P1056; for mines, the commodity).
  - `polity_qid`, `polity` and `capital_source` (P36 or P1376): capitals only.
  - `types` (all P31 labels) and `wikidata_url`.
- **How it is joined.** Use `lat`/`lon` and a date. `active(year, classes)` returns the rows
  with `start_year <= year` and either no end or `end_year > year`. Undated rows are
  included, flagged, unless you pass `include_undated=False`. It also adds `country_asof`
  (the dated P17 statement covering the year, else the present country). For countries, use
  `country_qid`, or the crosswalk once it exists.
- **How classes are defined.** Each class is a set of root classes. An item belongs to the
  class if its P31 is a root or (except for `government_seat`) any P279* subclass of one,
  minus the excluded subtrees. The roots and exclusions are in `CLASSES` in the module.
  - The exclusions are gendarmerie barracks; Second World War casemates, turrets and tobruks
    under bunker; quarries, gravel pits and show mines; marinas, fishing ports, landings and
    ferry stops; breweries and distilleries; and, under research institute, botanical gardens,
    academic departments, seminaries and think tanks.
  - Generic dams are left out (77k, mostly US irrigation dams). Only hydroelectric stations
    and hydroelectric dams are kept.
  - No Wikidata class exists for nuclear-weapons storage beyond "weapon storage area" (19
    items). No class exists for ICBM silo fields, so missile launch facilities and missile
    bases stand in for them.
- **Capitals.** The polities are instances of country, sovereign state, historical country
  or state (national), or of first-level administrative country subdivision (first level;
  this takes priority, so Scotland and the Soviet union republics count as first level).
  - Stints come from P36 on the polity and P1376 on the city, with their P580/P582
    qualifiers.
  - A statement with no qualifiers is dropped when the same city and polity have a qualified
    one.
  - A missing end falls back on the polity's dissolution (P576).
  - A missing start falls back on the polity's inception (or the city's, if later), but only
    when the polity has a single capital in Wikidata. Otherwise the stint stays undated. An
    unqualified statement is usually today's capital: without this rule, Islamabad would be
    Pakistan's capital in 1947.
  - Spot checks for 1956: Moscow (USSR), Bonn, East Berlin, Rio de Janeiro (until 1960),
    Canberra, New Delhi, Ankara and the Soviet republics' capitals are right. Pakistan has no
    dated capital, because Wikidata lacks a Karachi stint.

### Counts by class and start decade

"open YYYY" counts dated rows active in that year. Undated rows are not counted there.

| class | <1800 | 1800s | 1900-19 | 1920-39 | 1940s | 1950s | 1960s | 1970s | 1980s | 1990s | 2000s | 2010+ | undated | rows | % undated | with end | open 1945 | open 1956 | open 1962 | open 1985 | open 2000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| airport | 0 | 0 | 56 | 208 | 158 | 86 | 88 | 117 | 60 | 98 | 71 | 95 | 23921 | 24958 | 96 | 337 | 369 | 434 | 502 | 681 | 769 |
| aluminium_smelter | 0 | 3 | 2 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 29 | 38 | 76 | 7 | 4 | 5 | 8 | 8 | 7 |
| chemical_plant | 0 | 12 | 7 | 9 | 1 | 3 | 5 | 4 | 1 | 3 | 2 | 3 | 90 | 140 | 64 | 19 | 25 | 26 | 27 | 33 | 33 |
| factory | 342 | 1895 | 626 | 475 | 145 | 199 | 167 | 97 | 67 | 53 | 58 | 63 | 7650 | 11837 | 65 | 1735 | 2590 | 2714 | 2792 | 2800 | 2676 |
| hydroelectric | 8 | 78 | 352 | 462 | 226 | 530 | 445 | 358 | 337 | 341 | 865 | 985 | 4760 | 9747 | 49 | 189 | 1001 | 1475 | 1762 | 2628 | 3108 |
| mine | 100 | 267 | 101 | 51 | 15 | 69 | 101 | 82 | 50 | 47 | 73 | 83 | 49866 | 50905 | 98 | 467 | 415 | 451 | 496 | 590 | 588 |
| nuclear_facility | 0 | 0 | 0 | 0 | 11 | 22 | 27 | 21 | 22 | 8 | 9 | 9 | 175 | 304 | 58 | 68 | 4 | 14 | 35 | 69 | 67 |
| nuclear_power_plant | 0 | 0 | 1 | 0 | 0 | 5 | 56 | 94 | 82 | 17 | 7 | 26 | 95 | 383 | 25 | 104 | 1 | 4 | 15 | 193 | 207 |
| oil_refinery | 0 | 2 | 5 | 16 | 6 | 16 | 33 | 13 | 3 | 1 | 3 | 5 | 168 | 271 | 62 | 13 | 24 | 38 | 54 | 87 | 90 |
| port | 30 | 50 | 25 | 20 | 6 | 10 | 17 | 28 | 24 | 29 | 43 | 42 | 5011 | 5335 | 94 | 29 | 127 | 132 | 142 | 191 | 231 |
| power_station | 1 | 52 | 114 | 108 | 36 | 109 | 150 | 131 | 86 | 156 | 333 | 1260 | 16187 | 18723 | 86 | 548 | 286 | 372 | 442 | 705 | 880 |
| rail_junction | 0 | 16 | 16 | 10 | 1 | 5 | 7 | 3 | 2 | 6 | 5 | 7 | 3162 | 3240 | 98 | 28 | 42 | 46 | 47 | 52 | 55 |
| research_institute | 40 | 183 | 230 | 365 | 326 | 508 | 457 | 397 | 506 | 823 | 914 | 660 | 3177 | 8586 | 37 | 199 | 942 | 1462 | 1781 | 2755 | 3849 |
| steelworks | 55 | 87 | 14 | 5 | 4 | 4 | 5 | 3 | 2 | 3 | 3 | 0 | 512 | 697 | 73 | 70 | 133 | 134 | 137 | 135 | 132 |
| air_base | 1 | 4 | 166 | 241 | 645 | 95 | 48 | 17 | 8 | 15 | 8 | 8 | 1886 | 3142 | 60 | 853 | 841 | 751 | 721 | 670 | 598 |
| arsenal | 39 | 39 | 14 | 14 | 12 | 3 | 10 | 0 | 0 | 2 | 0 | 1 | 303 | 437 | 69 | 26 | 107 | 110 | 114 | 118 | 117 |
| bunker | 1 | 6 | 24 | 252 | 134 | 17 | 19 | 8 | 7 | 3 | 16 | 4 | 1754 | 2245 | 78 | 36 | 414 | 425 | 439 | 461 | 473 |
| launch_site | 0 | 0 | 0 | 2 | 7 | 14 | 16 | 3 | 1 | 5 | 1 | 9 | 84 | 142 | 59 | 8 | 4 | 13 | 28 | 36 | 40 |
| military_academy | 30 | 109 | 51 | 66 | 61 | 78 | 48 | 30 | 24 | 44 | 37 | 21 | 173 | 772 | 22 | 116 | 240 | 321 | 354 | 431 | 458 |
| military_base | 194 | 383 | 188 | 181 | 128 | 150 | 107 | 34 | 30 | 14 | 25 | 34 | 4343 | 5811 | 75 | 201 | 1004 | 1111 | 1186 | 1294 | 1290 |
| military_hq | 4 | 8 | 5 | 6 | 17 | 14 | 8 | 2 | 5 | 12 | 20 | 23 | 78 | 202 | 39 | 42 | 30 | 45 | 52 | 57 | 66 |
| missile_site | 0 | 0 | 0 | 0 | 1 | 0 | 32 | 0 | 1 | 1 | 1 | 0 | 22 | 58 | 38 | 19 | 0 | 1 | 18 | 22 | 20 |
| naval_base | 13 | 16 | 6 | 9 | 27 | 9 | 10 | 4 | 4 | 1 | 5 | 8 | 240 | 352 | 68 | 17 | 61 | 71 | 75 | 87 | 84 |
| nuclear_test_site | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 12 | 15 | 80 | 1 | 0 | 1 | 2 | 2 | 2 |
| radar_station | 0 | 0 | 0 | 5 | 12 | 50 | 4 | 0 | 0 | 4 | 3 | 3 | 151 | 232 | 65 | 21 | 15 | 49 | 59 | 57 | 58 |
| shipyard | 47 | 116 | 84 | 46 | 45 | 23 | 22 | 24 | 15 | 19 | 18 | 9 | 380 | 848 | 45 | 163 | 290 | 317 | 331 | 338 | 326 |
| weapons_storage | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 16 | 19 | 84 | 4 | 0 | 0 | 0 | 3 | 3 |
| capital_first_level | 471 | 540 | 140 | 238 | 181 | 191 | 123 | 142 | 90 | 294 | 220 | 236 | 2194 | 5060 | 43 | 1359 | 811 | 997 | 1054 | 1263 | 1506 |
| capital_national | 1690 | 400 | 213 | 142 | 125 | 40 | 89 | 66 | 25 | 64 | 21 | 28 | 875 | 3778 | 23 | 3267 | 372 | 271 | 289 | 293 | 280 |
| government_seat | 13 | 25 | 5 | 3 | 1 | 2 | 1 | 1 | 3 | 4 | 2 | 6 | 36 | 102 | 35 | 2 | 46 | 48 | 49 | 53 | 57 |
| parliament | 25 | 33 | 9 | 21 | 1 | 4 | 11 | 3 | 5 | 3 | 7 | 6 | 141 | 269 | 52 | 5 | 87 | 91 | 98 | 109 | 115 |
| **all** | 3104 | 4324 | 2454 | 2955 | 2333 | 2259 | 2111 | 1682 | 1460 | 2070 | 2770 | 3635 | 127491 | 158648 | 80 | 9953 | 10285 | 11929 | 13109 | 16221 | 18185 |


### Caveats

- **80% of rows are undated.** Airports, mines, ports, rail junctions and power stations are
  mostly bulk imports with no dates (96–98% undated for airports, mines and junctions).
  Military academies, research institutes, capitals and nuclear power plants are mostly dated
  (22–43% undated). Use the undated rows as a present-day presence flag with an anachronism
  marker, not as an as-of feature.
- **Coverage is skewed.** 42% of items are in the United States (GNIS and FAA imports), and
  the UK, Germany, France and Australia are dense. The Soviet bloc and China are sparse,
  except for their capitals. The modern catalogue under-represents sites that closed before
  the Internet era (survivorship bias), so a missing site is not evidence that none existed.
- **Dates mean different things.** P571 can be the start of construction rather than of
  operation: nuclear plants, for example, use P729 when it is present. 4% of dated rows are
  only precise to the decade or century. Air bases cluster in the 1940s (wartime fields), and
  many have end dates.
- **The classes are noisy.** `military_hq` comes from the "headquarters (military unit type)"
  tree and mixes units with sites. `military_base` includes barracks and historical garrisons
  (Roman castra are not in it: they sit under "military installation", which was not used). `research_institute` includes many civil and humanities institutes. `factory`
  includes mints and brickworks.
- **Historical states inflate the national capitals.** `capital_national` includes many
  pre-modern states (1,690 stints start before 1800). Some historical countries have no
  dissolution date, so they stay "open" in later years. Filter on `polity` or join to
  CShapes for the modern state system.
- **`country` is today's country.** Use `country_asof` or the plan's own country crosswalk
  for historical borders.
- **This file is features only.** No label source or target list was used.
