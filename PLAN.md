# Nuclear-Probabilities — project plan

> What made a place a nuclear target? Describe every place in each targeted country as it
> stood when a plan was drawn up. Label it from declassified strike plans, starting with the
> US war plan of 1956. Fit one global model, one model per country and one per regime type.
> Map which characteristics drive targeting.

The repository is empty, so this plan starts from nothing.

- **Phase order.** The phases follow the order asked for: features, then strike plans, then
  models, then the map.
- **Phases 1 and 2 run side by side.** Both hang off one shared table of places.
- **Transcription starts on day one.** Transcribing the target list is the long pole (§9).

*Terms.* **DGZ**: designated ground zero, a single aim point. **BE number**: a
target's Bombing Encyclopedia identifier. **SAC**: Strategic Air Command.

---

## 1. Questions

1. **What predicted targeting in 1956?** Which observable traits of a place predicted
   whether SAC put it on its list, and how many DGZs it got? The candidate traits are
   population, administrative rank, industry, military presence, transport and geography.
2. **Countervalue or counterforce?** How much of the urban-industrial list does population
   alone explain? How much do industry and nearby military sites add?
3. **One logic or several?** Does the pattern differ by target country, and by the target
   state's regime type? This is answered with one global model, one model per country and one
   per regime type, plus a hierarchical model linking them (§5.3).
4. **Where does the model disagree with SAC?** The model can be wrong in two directions:
   - *Targeted places it calls unlikely.* These may be political or symbolic choices.
   - *Untargeted places it calls likely.* These may be intelligence blind spots, such as the
     closed nuclear cities, which may have been little known to US intelligence in 1956.
5. **Stretch: does it transfer?** To other plans and the other side; see §4.5.

**Prior work.** Searches found no statistical or ML study of what predicted inclusion in
these lists. The closest analogues are:
- Openshaw & Steadman's quantitative geography of hypothetical attacks on Britain
  (*Political Geography Quarterly* 1982; *Area* 1983).
- The WWII-bombing economics literature (Davis & Weinstein 2002).

---

## 2. Data spine

Everything joins on one table of places, built before either the features or the labels.

| Table | Grain | Contents |
|---|---|---|
| `places` | one settlement | id; the 1956 name, today's name and transliteration variants; 1956 country; lat/lon; administrative unit |
| `cells` | one H3 hexagon (resolution 5, ~250 km²) over each targeted country | for installations outside towns, and for the probability surface |
| `features` | place or cell, per as-of year | one column per feature; each tagged with its family, source, as-of year and an anachronism flag |
| `targets` | one DGZ or installation in one plan | plan, part, list, city, BE number, category code, country code, coordinates, priority, source page, transcription confidence |
| `labels` | place or cell, per plan | targeted or not, number of DGZs, best priority, whether it survives the restricted allocation |
| `countries` | country, per year | regime type under each coding (GWF, Kailitz, BMR, Polity5, V-Dem), alignment (NATO / Warsaw Pact / neutral / non-aligned), borders (CShapes) |
| `plans` | one target list | planner, year, label provenance (operational plan / study / exercise / defender's assumption / reconstruction), countries covered, source |

- **The candidate universe is fixed without looking at the labels.**
  - There is one universe per plan and target country. It holds every settlement in that
    country with at least 10k people at the plan's date (1959 census populations for the 1956
    list). Thresholds of 5k and 20k are run as sensitivity checks.
  - Targeted places below the threshold are **not** added to the place table. They are scored
    at cell level instead. Adding them would teach the model that small towns are always
    targets.
- **Features are functions of `(place, as_of_year)`.** The 1956 build is the main one. The
  same code can produce 1945 or 1964 builds, for transfer tests against other plans.
- **Storage.** Data is kept as GeoParquet. Every source has an entry in `data/sources.yaml`
  with its URL, licence, retrieval date and sha256.

---

## 3. Phase 1 — Features ("the world as of 1956")

### 3.1 The universe of places

| Region | Settlements and populations | Coordinates |
|---|---|---|
| USSR | **pop-stat.mashke.org** (T. Bespyatov): population series for cities, towns and urban-type settlements, with census columns including 1939 and 1959. Cross-checked against Demoscope's 1959 tables and Harris (1970), which covers 1,247 towns | `geonamescache` (PyPI) or Who's On First, plus a curated table of historical names: Stalino, Molotov, Stalinsk, Voroshilovgrad, Chkalov, Stalinogród, Karl-Marx-Stadt, Mukden… |
| Eastern Europe | pop-stat series for the satellite states; national historical lexicons (e.g. Czech 1950/1961) as checks | same |
| China | Ullman (1961), *Cities of Mainland China: 1953 and 1958* (US Census Bureau, public domain) | same |
| North Korea | effectively only UN World Urbanization Prospects and HYDE; left to a later phase | — |

- **Closed cities.** They are missing from the published 1959 tables.
  - They are added from the curated military table, with population imputed and flagged.
  - They are included because they existed, not because of how they were targeted.
- **The 1959 census is three years late.** US planners never had those figures. The 1939
  census and the 1939–59 growth rate serve as sensitivity checks.

### 3.2 Feature families

| Family | Example features | Sources | Caveat |
|---|---|---|---|
| **Population** | log population 1959 and 1939; growth 1939–59; rank in country; population within 25/50/100 km; urban share; distance to the nearest city over 100k | pop-stat census series; HYDE 3.3 grids for 1950 and 1960 (5′ ≈ 9 km, CC BY 4.0) | HYDE spreads regional totals onto a grid with a model, so it is a smooth background, not an observation |
| **Administrative** | capital of a nation, union republic, ASSR, oblast or krai; Eastern European regional capitals | CShapes 2.0 capitals; a hand-built 1956 table of administrative centres | Oblasts were reshuffled in 1954–57; the Karelo-Finnish SSR ended in July 1956 |
| **Industry** | defence establishments founded by 1956, counted by branch (aero, armour, shipbuilding, nuclear, radio…); power plants commissioned by 1956; steel, refining and chemicals flags; coal or ore basin | Dexter & Rodionov, *Soviet defence industry guide* (~33,600 entries in the 2024 version, Excel, no coordinates, so geocoded by town); WRI Global Power Plant Database; Global Energy Monitor trackers; RiStat (RSFSR oblasts, 1959) | Dexter–Rodionov is post-Soviet knowledge: it records what existed, not what SAC knew. Only ~200 bloc plants in the power-plant database predate 1957 (survivorship bias), so it is a weak flag |
| **Military** | airfields within 10/25/50 km; long-range aviation base; fleet base; military district HQ; closed city; nuclear-complex or test site; Moscow S-25 air-defence ring; Soviet garrisons in Eastern Europe | OurAirports (7,021 bloc rows with coordinates but no dates); a hand-curated table of ~50–100 dated sites built from Holm's order-of-battle pages, Podvig and Wikipedia | No dataset dates airfields to 1956, so status has to be curated. **The plan's own airfield list is a label, never a feature** |
| **Transport** | degree of the nearest rail junction; trunk-line flag; seaport or river port; major river crossing | Natural Earth railroads and ports; a partial copy of the World Port Index; Ma & Tang's China railways (with construction years); OpenHistoricalMap | Natural Earth railways are the modern network, so they are flagged |
| **Geography and reach** | elevation and ruggedness; distance to the coast, to Moscow or the national capital, and to the NATO border; great-circle distance to the nearest 1956 SAC base and to the continental US | Copernicus GLO-90 (on AWS); Natural Earth; CShapes 2.0; a hand-coded list of 1956 SAC bases (excluding the Spanish bases, which opened 1957–59) | Reservoirs filled after 1956 (Bratsk, Krasnoyarsk, Volgograd) are flagged |

### 3.3 Beyond the Soviet bloc

Per-country and per-regime models need a universe and features for every *targeted* country at
its plan's date. For Warsaw Pact plans and civil-defence lists, that means NATO and neutral
countries between the 1960s and 1990. The feature code is the same; only the as-of year and
the sources change.

| Need | Global sources (as-of years) | Country sources |
|---|---|---|
| Settlements and population | GHSL population and built-up grids (1975–1990, global, 250 m–1 km); HYDE 3.3 (decadal, 1950–1990); UN World Urbanization Prospects city series (1950 onwards, survivorship-biased) | US Census places and counties, 1950–1990 (NHGIS); UK censuses (Vision of Britain); West German municipal directories (1970/1987); national statistics offices |
| Administrative rank | CShapes 2.0 capitals; first-level administrative units (modern, flagged) | Curated state, Land and county capitals |
| Industry | WRI power plants (commissioning years); Global Energy Monitor trackers | Curated defence industry where it exists |
| Military | OurAirports; Arkin & Fieldhouse, *Nuclear Battlefields* (1985), whose appendix lists nuclear-related facilities worldwide (print, so it needs digitising); "Where They Were" (Norris, Arkin & Burr 1999), US nuclear deployments abroad by country and year | Curated NATO airbases, naval bases, nuclear storage sites and HQs, with dates |
| Transport, geography | Natural Earth, Copernicus DEM, World Port Index, CShapes | — |

Nuclear-infrastructure lists are features, not labels: they record where weapons were, not
where an adversary aimed. The guard test treats them as feature sources.

**Rules for features**

- **Nothing derived from a target list.**
  - The plan's own installation categories are labels, not features.
  - A guard test checks every feature source against the label sources.
- **Flag anachronisms.** These are modern datasets standing in for 1956:
  - OSM railways;
  - power plants that survived long enough to be catalogued;
  - post-Soviet archive knowledge of secret plants.

  Phase 4 measures how much the results depend on them. That is a finding, not just a
  caveat: a secret plant that predicts nothing tells us SAC did not know about it.
- **Coordinates are not driver features.**
  - Lat/lon and spatial lags go only into the spatial models.
  - Otherwise "where" crowds out "what".

---

## 4. Phase 2 — Labels (declassified strike plans)

### 4.1 The source

The primary source is SAC's **Atomic Weapons Requirements Study for 1959**, dated June 1956.

- **Where.** It is published by the National Security Archive as Electronic Briefing Book
  538. The archive posted it in December 2015 and added the full city list in April 2016.
- **Size.** Over 800 pages.
- **Status.** A US government document, so public domain.

| Part | Contents | Use |
|---|---|---|
| Category Code List (5 pp) | Key to the installation category codes (275 = "Population") | Label vocabulary |
| **Urban-Industrial Target List, Part I, "Abdulino to Zychlin" (306 pp, complete)** | 1,200+ cities ("complexes"), each a group of DGZs over BE-numbered installations | T1–T3 |
| Part I complex list; cross-reference list (excerpts) | City-level summaries | Fast path and cross-checks |
| Part II "restricted allocation" (1,209 DGZs) and the airfield list | What survives a cap on fissile material; 1,100+ airfields with priority numbers (Bykhov 1, Orsha 2…) | T4, T5 |
| The Archive's spreadsheets for Moscow and Beijing | Per-city breakdowns | Validation |

**Each row records:**
- a BE number, whose first four digits identify a World Aeronautical Chart, i.e. a
  location zone;
- a category code and a country code;
- coordinates as degree-minute digits (central Moscow is 55°45′N 37°37′E), so they are
  accurate to under 2 km;
- a priority.

**What is missing:**
- **Installation names.** The Bombing Encyclopedia itself is still classified, so
  installations have codes but no names.
- **Weapons.** Weapon numbers and types are blanked out of the released copy.

**Anchors to validate against:**
- Moscow is priority 1 with 179 DGZs; Leningrad is priority 2 with 145.
- East Berlin has 91 DGZs.
- China and North Korea together have about 146 targets.
- Reported DGZ totals vary by source (about 3,400 for Part I, 1,209 for Part II), so they
  are reconciled from the transcription itself.

### 4.2 The labels

| Task | Label | Unit |
|---|---|---|
| T1 Targeted? | The place has at least one Part I urban-industrial DGZ within r km | place (main), cell |
| T2 How hard? | Number of DGZs | targeted places (hurdle model) |
| T3 Rank | City priority order | targeted places |
| T4 Kept under scarcity? | The place keeps DGZs under the Part II restricted allocation | targeted places |
| T5 Airfield priority | Priority number on the Air Power list | the ~1,100 airfields |

According to the Archive, every city on the list includes a "Population" DGZ (category
275). Population targeting was therefore universal, so it is not a separate label.

### 4.3 Getting a table out of the scans

The Archive's OCR is garbled, and Wellerstein described the pages as impossible to OCR.
So this step comes first.

0. **Fast path.**
   - In 2016 Alex Wellerstein and the Future of Life Institute mapped 1,154 targets from this
     list (blog.nuclearsecrecy.com/misc/targets1956/). That is probably one point per city.
   - Ask them for the CSV, with credit. It gives T1 labels for the first slice at once.
1. **Get the PDFs.** This needs network access, or an upload; see §11.
2. **Prepare page images** at 300–400 dpi, deskewed and binarised.
3. **Read every page twice, independently.**
   - First, a vision-language model transcribes each page into a fixed schema.
   - Second, Tesseract reads it, splitting columns by position. Typed tables of the period
     are usually fixed-width.
4. **Run automatic checks:**
   - fields match their formats;
   - coordinates fall inside the 1956 border of the stated country (CShapes);
   - the BE chart prefix agrees with other rows from the same chart;
   - category codes exist in the code list;
   - city totals match the published anchors;
   - the two reads agree.
5. **Review and measure.**
   - Flagged rows go to a review queue.
   - A random 5% sample is keyed in twice by hand to measure the remaining error rate.
   - That rate goes into the data card.
6. **Link targets to places.**
   - Each DGZ goes to the nearest place within r km, confirmed by name where possible, and to
     its H3 cell.
   - Targets that match no place stay at cell level.

### 4.4 Data card

The data card for the labels records:
- provenance, with page numbers;
- known redactions;
- the measured transcription error rate;
- how DGZs were linked to places;
- what remains uncertain, such as the exact meaning of category codes.

### 4.5 More targeting data: a catalogue

A deeper search turned up no second list on the scale of the 1956 study. It did find enough
smaller lists to add new planners, new target countries and a range of years. Every list is
tagged with its **provenance**, because a war plan, an exercise and a civil-defence guess are
different kinds of evidence:
- **Plan**: an approved war plan or weapons allocation.
- **Study**: a staff study or requirements study. The 1956 list itself is formally a
  requirements study.
- **Exercise**: a war game or exercise that mirrors standing plans.
- **Defender**: a government's own list of where it expected to be hit.
- **Reconstruction**: an analyst's or a former planner's reconstruction.

Effort: **S** is hours to a day; **M** is a few days; **L** needs an archive visit or a print
book.

**Western planners → the Soviet bloc, China, North Korea, Japan**

| Source | Planner → target, year | Size and detail | Where | Effort | Provenance |
|---|---|---|---|---|---|
| **SAC Atomic Weapons Requirements Study** | US → Soviet bloc, China, N. Korea, 1956 | 1,200+ cities and 1,100+ airfields; installations with coordinates | Electronic Briefing Book 538 | L (transcription) | Study |
| **Air Ministry city grading** | UK → USSR, 1957 | 131 cities over 100k, graded on population and administrative, economic and transport importance; 98 in range, 44 selected. **Selected and rejected cities in one list** | UK National Archives, Air Ministry/Bomber Command files (not online; cited by Wynn 1994, Jones 2017) | L | Study |
| Norstad memo to Groves | US → USSR, Sep 1945 | 66 cities (15 first-priority named), plus 21 Manchurian cities studied and dropped | Scanned memo and map (nuclearsecrecy.com, 2012) | S | Study |
| JIC 329/1 | US → USSR, Nov 1945 | 20 named cities | *Studies in Intelligence* 44:3 | S | Study |
| Broiler → Trojan → Offtackle → Dropshot | US → USSR, 1947–49 | 24 → 70 → 104 → ~100 cities; counts online, named annexes possibly in the Ross & Rosenberg facsimiles | Print, 15 volumes | L | Plan |
| French Air Force staff study | France → USSR, 1959 | 20 named cities, each with air-defence grade and bombers needed | Pelopidas & Philippe, *Cold War History* 2021 (open access) | S | Study |
| SAC–Bomber Command joint plans | US + UK → USSR, 1958–63 | Counts: e.g. 106 targets (69 cities, 17 bomber bases, 20 air-defence sites) | Jones 2019; UK National Archives AIR/DEFE files for names | L | Plan |
| Target Committee | US → Japan, 1945 | 4–17 cities, **including rejected ones** (Kyoto) | Briefing book "Atomic Bomb and the End of WWII" | S | Plan |
| MacArthur's "retardation targets" | US → Korea, Manchuria, China, Soviet Far East, 1950 | ~9 named cities, 26–34 bombs | Dingman, *International Security* 1988 | S | Study |
| OPS PLAN 25-58 | US → PRC, 1958 | ~10–30 airfields and bases, Amoy to Shanghai | Halperin RM-4900 (released by Ellsberg); Van Staaveren 1962 | M | Plan |
| Chinese nuclear sites | US → PRC, 1963–64 | 4–6 named facilities | Burr & Richelson, *International Security* 2000 | S | Study |
| WINTEX-CIMEX 89 | NATO → USSR, GDR, Poland, ČSSR, Hungary, 1989 | 17 scripted weapons | *Der Spiegel*; Bundestag records | S | Exercise |
| SIOP-62 and the 1960 target list | US → bloc, 1961 | Counts only (3,729 installations, ~1,060 targets, 199/295 cities) | Briefing books 130, 236 | — | Totals to check against |

**Warsaw Pact planners → NATO and neutral states**

No Soviet *strategic* target list has ever been declassified. What exists are front-level
plans and exercises from the Czech, Polish, Hungarian and East German archives, mostly at city
or installation-name level, without coordinates.

| Source | Planner → target, year | Size and detail | Where | Effort | Provenance |
|---|---|---|---|---|---|
| **Polish plans against Denmark, 1961–89** | Poland → Denmark, Schleswig-Holstein | 1989 plan: 131 first-phase strikes on HQs, airfields and bunkers; full series ~150+ installations | Andersen, *Planerne om at eliminere Danmark* (2026, 702 pp., print) | L | Plan |
| **ČSLA war plans** | Czechoslovakia → FRG (Bavaria, Baden-Württemberg), 1964 / 1977 / 1989 | 131 / 258 / 546 strikes; 1964 gives target classes only; 1980s name target areas (Grafenwöhr, Regensburg, Erlangen…) | Prague military archive (VÚA); Luňák 2007 (print); dossier at the Parallel History Project (PHP) | L | Plan |
| "Lato-67" Coastal Front directive | Poland/USSR → FRG, NL, BE, DK, 1967 | 57 strategic strikes on ~45 named junctions, ports, airfields, air-defence sites, a reactor; 46 more army-level strikes | PHP facsimile (Russian) | S–M | Exercise |
| Coastal Front plan map | Poland → DK, FRG, NL, BE, 1970 | ~170–190 weapons; named cities plus strike symbols | Nielsen et al., *Geoforum Perspektiv* 2016 (open access) | M (georeference) | Plan |
| Hungarian–Soviet war game | Hungary/USSR → Austria, Italy, FRG, 1965 | 30 weapons with yields: Vienna, Munich, Verona, Vicenza, airfields, depots (plus the mirror: 30 NATO strikes on Hungary) | PHP, "European Cities Targeted for Nuclear Destruction" | S | Exercise |
| Zealand landing plan | Poland → Denmark, 1977 | 15 weapons near Roskilde, Slagelse, Næstved, Vordingborg | Pałka, *Kwartalnik Historyczny* 2022 (open access) | S | Plan |
| "Seven Days to the River Rhine" | Warsaw Pact → FRG, Benelux, DK, 1979 | ~12 cities | Map released by Poland, 2005 | S | Exercise |
| NVA 5th Army plans | GDR → FRG (Schleswig-Holstein, Hamburg), 1983–88 | Up to 32 first-salvo strikes on Lance units, airfields, command posts | Lautsch, BMVg report 2021 | M | Reconstruction |
| R-5M "Operation Atom" | USSR → UK, France, Benelux, FRG, 1959 | ~10 places: Thor bases, London, Paris, Brussels, Ruhr, Bonn | Uhl & Ivkin | S | Study (scholar's summary) |
| Burza 1961; Soyuz-75/83, VAL-77, Shchit-88; General Staff Academy 1977 | Warsaw Pact → FRG, Benelux, DK | Mostly counts or target classes (e.g. 680 warheads, northern FRG) | PHP; Wilson Center; CIA reading room | M | Exercise |
| Swedish government inquiry SOU 2002:108 | — → Sweden | No developed attack plans found | Government report | — | Negative evidence (not used as labels) |
| Bulgarian plans | Bulgaria/USSR → Greece, Turkey, 1978 | 30 bombs set aside; no names published | Bulgarian military archive | L | Plan |

**Defenders' assumptions and analysts' reconstructions**

These lists add the US and the UK as target countries at scale. They are a different kind of
evidence: they record what a government expected its adversary to hit. **Lists generated by a
simple rule** (such as "every city over 50,000") **are excluded from training**, because a model
would only rediscover the rule.

| Source | Producer → target, year | Size and detail | Where | Effort | Provenance |
|---|---|---|---|---|---|
| **NAPB-90, *Nuclear Attack Planning Base 1990*** | FEMA, modelled on Soviet doctrine → US, 1987 | ~6,100 aim points in 8 classes (ICBM silos and control centres, other military, military-support industry, ports, refineries, political, power plants, chemical plants). County tables of population and area by blast band (972 counties at 2 psi or more). State maps with blast rings | 510-page scan, **reachable now** through a public GitHub repo (`5usc2302/risk`). The separate "National Aimpoint List" volume would need a FOIA request | M: OCR the county tables, georeference the rings | Defender. No population class, but industrial classes were trimmed by capacity rules |
| FEMA-196, *Risks and Hazards* | FEMA → US, 1990 | NAPB-90 blast rings, state by state; maps only | Same GitHub repo | M | Defender |
| Operation Alert attack patterns | FCDA → US, 1955–61 | 1955: 61 cities with yields, chosen by judgment | FCDA records (1955 widely reported) | S–M | Defender (exercise) |
| TR-82 high-risk areas; CRP-2B | DCPA → US, 1975–79 | 829 counties; 1,444 weapons | OSTI reports | M | Defender. Its "population over 50,000" class is a rule and is dropped |
| **"Probable nuclear targets in the United Kingdom"** | Cabinet Office → UK, 1972 (released 2014) | 106 named sites: 38 towns and government centres, 37 UK/US air bases, 25 command, communications and radar sites, 6 naval sites | UK National Archives (file reference to confirm) | S once located | Defender, chosen by judgment |
| Square Leg / Hard Rock | Home Office → UK, 1980 / 1982 | ~131 weapons, bomb plots published / under 50 Mt | Campbell, *War Plan UK*; Openshaw et al., *Doomsday* (print) | M | Defender (exercise); politically edited |
| Canadian target areas | Canada → Canada, 1956–62 | 13 named areas (1956 Hansard); Exercise Tocsin B (1961) | Hansard | S | Defender |
| China's key civil-air-defence cities | China → China, present | City classes 1–3, compiled from municipal plans | Municipal documents | M | Defender (modern era) |
| Helfand et al. 2002 | PSR/NRDC → US | 1,249 targets of a 2,000-warhead Russian attack | *Medicine & Global Survival* 7(2); coordinates unpublished | M | Reconstruction |
| NRDC 2001 | NRDC → Russia | Russian target database of ~7,000 sites (not public); counterforce attack of 1,289 warheads | Report on the same GitHub repo; data on request from NRDC | L | Reconstruction |

**Excluded as rule-generated:**
- FCDA's 1953 "critical target areas" (40,000+ manufacturing employees);
- the Toon/Robock target sets (cities by population density);
- NRDC's city-attack sets;
- OTA's case of the 77 largest refineries;
- Helfand's 500-target scenario, which maximises population;
- hobbyist lists with no documented method, such as nuclearwarmap.com.

**What this means for the models**

- **Countries with enough labels for their own model** (§5.3):
  - the USSR, China and most satellite states, from the 1956 list (to be confirmed after
    transcription);
  - the US, from NAPB-90 at county level;
  - probably the UK, from the 1972 list plus Square Leg;
  - Denmark and West Germany, if the print and archive sources are obtained.
- **Regime-type contrasts within one planner are scarce.**
  - Greece under the 1967–74 junta and Turkey would give a Warsaw Pact planner targets in
    NATO autocracies. They are reachable only through the Bulgarian archive.
  - Austria (neutral) differs from the other targets in alignment, not regime.
  - A second, partial route is to compare defenders' lists across regimes. Democracies (US,
    UK, Canada) can be set against China's and Russia's civil-defence city classes, but era
    is then confounded.
- **Across the whole catalogue, regime type mostly tracks provenance.**
  - Communist-state targets come from attacker plans.
  - Democratic-state targets come mostly from defenders' assumptions.

  Provenance is therefore always a control, and results are reported for each provenance
  separately.
- **Small lists are test sets, not training sets.** The 4–30-target lists are used to check
  whether a model transfers (§5.2), not to fit one.

---

## 5. Phase 3 — Models

### 5.1 Freeze the protocol first

Before any model is fit, `configs/protocol.yaml` is committed and its hash recorded. It
fixes:
- the universe rule;
- the feature list;
- the label definitions;
- the split seeds and blocks;
- the metrics and the primary comparison.

How it is enforced:
- Every run in `runs/` carries the protocol hash and the data hashes.
- The sealed test set is scored once, at the end.

Without this, the answer to "what drives targeting" could be steered by whichever runs got
looked at.

### 5.2 Splits

| Split | Purpose |
|---|---|
| **Sealed test**: 20% of places, held out by spatial block (~300 km), stratified on the label | Final numbers, scored once |
| **Model selection**: 5-fold spatial-block cross-validation on the other 80%, repeated with shifted block grids | Tuning and comparing models |
| **Random-split cross-validation**, reported alongside | Shows how much nearby places leaking across the split inflates scores |
| **Within-country CV**: the same spatial blocks, restricted to one country | Scores the per-country models and the specialisation gain (§5.3) |
| **Leave-one-country-out** and **leave-one-regime-out** | Does a model built elsewhere predict this country or regime type? These fill the transfer matrix |
| **Plan transfer**: other plans (§4.5) scored with the 1956 model, using as-of builds | Did the logic change over time, or between sides? |

### 5.3 Three levels: one global model, one per country, one per regime type

| Level | Trained on | Question it answers | Notes |
|---|---|---|---|
| **G — Global** | every labelled place, across all plans and countries | What is common to all targeting? | Adds context features: planner, plan year, label provenance, the target state's regime type and alignment |
| **C — Country** | one target country at a time | Does the logic differ by country? | A country gets its own model only if it has at least 30 targeted and 30 untargeted places. Smaller countries are scored, not fitted |
| **R — Regime type** | all target states that share a regime type at the plan's date | Does it differ by regime type? | The primary coding is fixed in the protocol; the other codings are robustness checks |
| **H — Hierarchical** (the bridge) | everything, partially pooled: place → country → regime type | Are the country and regime differences real, or noise? | A Bayesian multilevel logistic regression (PyMC/bambi) with varying intercepts and slopes, plus GPBoost with grouped random effects. Small countries borrow strength from their regime group |

**Same algorithms at every level.** The top two algorithms from the global zoo, plus regularised
logistic regression as the low-variance option for small groups, are refitted at levels C and R.
Differences between levels then reflect the data, not the algorithm.

**How the levels are compared**

- **Specialisation gain.** For each country, levels G, R, C and H are scored on the same held-out
  folds of that country. If C or R barely beats G, the logic is shared.
- **Transfer matrix.** Train on country *i*, score on country *j*. Countries whose targeting
  predicts one another's share a logic. The matrix is shown as a clustered heatmap.
- **Driver profiles.** Family ablation and SHAP are run for each country and each regime type
  and compared side by side. Two tests check whether the differences are real:
  - feature × regime interactions, tested with likelihood-ratio tests in the GLM;
  - pairwise terms in the EBM.

**Regime type**

- **Whose regime.** It is coded for the *targeted* state at the plan's date. The source is the
  `democracyData` bundle, which is already reachable from here through raw GitHub. It includes:
  - Geddes–Wright–Frantz autocratic regime types (1946–2010);
  - Kailitz (1945–2010), which has a "communist ideocracy" type;
  - Boix–Miller–Rosato democracy (0/1);
  - Polity5;
  - the V-Dem polyarchy index.
- **Proposed primary grouping:**
  1. communist party-based (USSR, most satellite states, China, North Vietnam, Yugoslavia);
  2. communist personalist (Romania, North Korea, later Cuba);
  3. non-communist autocracy (Franco's Spain, Salazar's Portugal, Greece 1967–74, Iran,
     South Korea);
  4. liberal democracy (most of NATO, and the neutral states).
- **Alignment is a second grouping axis**, not part of regime type. Its values are NATO /
  Warsaw Pact / neutral / non-aligned. It is reported separately because the two differ:
  Austria is a neutral democracy, Portugal a NATO autocracy, Yugoslavia a non-aligned communist
  state.

**Caveats that shape the design**

- **The 1956 list alone has almost no regime variation.** Every country on it is coded as a
  communist one-party state, except Hungary (coded "in transition" during the revolution) and
  Iran (a monarchy). Regime-type models only become meaningful with the additional plans of
  §4.5.
- **Across plans, regime type is confounded.** US plans target communist states and Warsaw Pact
  plans target democracies. So regime type moves together with:
  - the planner;
  - the kind of label (actual plan vs. defender's assumption);
  - the era.

  Regime comparisons are therefore made *within one planner* wherever possible:
  - within Warsaw Pact plans: NATO democracies vs. NATO autocracies vs. neutral states;
  - within the US 1956 list: party-based vs. personalist communist states.

  Planner, label provenance and year also enter as controls.
- **The codings disagree on borderline cases.** For example, Turkey and Greece in 1956 are
  democracies according to Boix–Miller–Rosato, but Kailitz codes Turkey an electoral autocracy.
  Every regime result is therefore re-run under each coding.

### 5.4 The model zoo

Every model gets the same splits, features and tuning budget: Optuna, inner spatial
cross-validation, a fixed number of trials.

| Model | Why it is in the zoo | What it tells us |
|---|---|---|
| Population-rank rule ("hit the N biggest") | Naive baseline | If ML barely beats it, targeting was about population |
| Logistic regression, L2 and L1 | Interpretable baseline; L1 also selects features | Odds ratios with confidence intervals |
| Poisson / negative-binomial GLM, hurdle model | DGZ counts (T2) | How DGZs scale with population and industry |
| EBM (InterpretML) / GAM | Non-linear but fully inspectable | Shape functions, thresholds, pairwise interactions |
| Random forest, ExtraTrees | Robust non-linear baseline | Interactions and importance |
| Gradient boosting: LightGBM, XGBoost, CatBoost | Usually the strongest on tabular data | SHAP explanations |
| SVM (RBF), k-NN, small MLP | A range of inductive biases | Performance comparison; k-NN shows "places like this" |
| GPBoost (boosting with a Gaussian-process random effect) | Handles spatial autocorrelation | Separates "where" from "what" |
| MaxEnt (`elapid`) / inhomogeneous Poisson point process on cells | The list is presence-only data, like species sightings | The continuous probability surface |
| LambdaMART (LightGBM ranker) | Priority order (T3, T5) | What moves a target up the list |

### 5.5 Metrics

- **T1 and T4:**
  - PR-AUC as the primary metric, because the classes are imbalanced;
  - ROC-AUC, log-loss and Brier score;
  - a calibration curve;
  - precision@k, where k is the true number of targets in the fold.
- **T2:** Poisson deviance and Spearman correlation.
- **T3 and T5:** NDCG@k and Kendall's τ.
- **Uncertainty:** every metric is reported with its fold-to-fold spread, and with a
  bootstrap confidence interval on the sealed test.
- **Calibration:** probabilities are calibrated (isotonic, inside cross-validation), because
  the map displays them.

---

## 6. Phase 4 — What drives targeting

Population, industry and administrative rank move together, so no single attribution
method can be trusted alone. Several are run:

1. **Family ablation** (the headline answer). Retrain without each feature family and
   measure the drop in PR-AUC, with confidence intervals across folds.
2. **Grouped permutation importance** on the held-out folds.
3. **SHAP** (TreeSHAP):
   - a global beeswarm;
   - interaction values (e.g. population × defence industry);
   - a waterfall for each place, which feeds the map.
4. **ALE curves**, which cope with correlated features, and **EBM shape functions**. For
   example: where does the population effect level off?
5. **Separate fits** by region, and by list (urban-industrial vs. Air Power).
6. **Residuals.**
   - Moran's I on the residuals, and a map of where they cluster.
   - Case studies of the largest false negatives and false positives: blind spots versus
     political choices.
7. **Robustness.** Rerun after each of these changes:
   - drop the anachronistic features;
   - vary the universe threshold;
   - vary the radius r that links targets to places.

A conclusion is reported as a finding only if the methods agree on it. Where they disagree,
that is reported too.

---

## 7. Phase 5 — Interactive map

- **Stack.**
  - Python exports (GeoParquet → GeoJSON/FlatGeobuf) feed a static page.
  - The page uses MapLibre GL JS + deck.gl (ScatterplotLayer, H3HexagonLayer).
  - There is no server; it deploys to GitHub Pages.
  - Prototyping in notebooks uses `lonboard`/`pydeck`.
- **Base map.** Borders as they stood at the selected plan's date (CShapes 2.0), not today's.
  This also removes any need for a tile server.
- **Model level selector**: global / country / regime type / hierarchical. Switching level
  recolours the map, so the places where country-specific logic matters stand out.
- **Views:**
  - **Actual**: the DGZs of the selected plan by list and category, sized by priority.
  - **Predicted**: places coloured by calibrated P(target), with a model selector.
  - **Errors**: false positives and false negatives highlighted.
  - **Drivers**: pick a feature, and every place is coloured by that feature's SHAP
    contribution. This shows where population, defence industry or airfields push
    targeting up or down.
  - **Surface**: the H3 probability surface from the cell model.
  - **Compare**: Part I vs. the Part II restricted allocation, and other plans where data
    exist.
- **Place card** (click a place):
  - its names, in 1956 and today;
  - population;
  - actual DGZs and their categories;
  - P(target) from each model;
  - a SHAP waterfall.
- **Side panel.**
  - Family-ablation bars per level, so drivers can be compared across a country and its
    regime group; clicking a bar switches the map to that family's contribution.
  - The transfer matrix (train on country *i*, score on country *j*) as a clustered heatmap.
  - Countries shaded by regime type or alignment at the plan's date.
  - Filters by country, list and probability.
  - Name search.
- **Context layers.** 1956 SAC bases with notional reach rings, airfields, defence plants,
  railways.

---

## 8. Repository layout and tooling

This matches gosplan-env: uv, Python 3.12, ruff (line length 100), pytest, pre-commit, Make,
GitHub Actions, and a flat package layout.

```
nuclear-probabilities/
  PLAN.md  README.md  pyproject.toml  Makefile
  data/
    sources.yaml         provenance manifest (URL, licence, retrieved, sha256)
    curated/             small hand-built CSVs, committed with citations
                         (historical names, 1956 SAC bases, naval bases, closed cities,
                         1956 admin centres)
    raw/ interim/        git-ignored, rebuilt by `make data`
    processed/           places / cells / features / targets / labels (GeoParquet)
  nucprob/
    sources/             one module per source: fetch + parse
    gazetteer/           transliteration, historical names, fuzzy matching (rapidfuzz)
    labels/              one module per plan; SAC 1956: page images → two reads → checks →
                         review → link
    features/            population, admin, industry, military, transport, geography
    model/               splits, model registry, train, calibrate, evaluate
    explain/             ablation, permutation, SHAP, ALE
    viz/                 exports for the web map
  configs/protocol.yaml  frozen before any training
  web/                   static MapLibre + deck.gl app
  runs/                  outputs, each with a manifest (protocol hash, data hashes, git SHA)
  tests/                 parsers, coordinate and BE checks, gazetteer matching,
                         leakage guard, split integrity
```

- **Make targets:** `setup data labels features dataset protocol train explain map test lint`.
- **Dependencies** (all on PyPI): geopandas, shapely, pyproj, h3, rasterio, rapidfuzz,
  scikit-learn, lightgbm, xgboost, catboost, interpret, shap, gpboost, elapid, PyALE, optuna.
- **OCR:** ocrmypdf and pytesseract, plus the Tesseract binary (e.g. from conda-forge).

---

## 9. Order of work

Phases 1 and 2 run side by side. Transcribing the labels is the long pole, so it starts first.

| # | Milestone | Size | Done when |
|---|---|---|---|
| M0 | Scaffold; network access working; ask for the 1,154-target CSV | S | `make setup test lint` green in CI; every source is listed in `data/sources.yaml` |
| M1 | **Vertical slice**: USSR only; 1959 universe; population and administrative features only; city-level labels from the fastest source; population rule vs. logistic regression vs. LightGBM; a quick lonboard map | M | Every join works end to end on real data. The slice's numbers are not results |
| M2 | Full 1956 feature base: all families, whole bloc, curated military and administrative tables, leakage guard | L | Feature table with provenance and anachronism flags; tests green |
| M3 | Full 1956 labels: the Part I table of DGZs, the Part II subset, the airfield list | L | Error rate measured; published anchors reproduced; data card written |
| M4 | **More labels, cheapest first.** The S-effort lists of §4.5, then the M lists, plus as-of feature builds for each new country and year. L items (archives, print books) only if someone can fetch them | M → L | Each list has a data card and provenance tag |
| M5 | Freeze the protocol (including the regime coding); seal the test blocks | S | `configs/protocol.yaml` committed with its hash |
| M6 | **Level G**: the global model zoo across T1–T5 | M | Leaderboard with cross-validation spreads |
| M7 | **Levels C, R, H**: per-country, per-regime-type and hierarchical models; transfer matrix | M | Specialisation gains with CIs, for every country and regime group that has enough data |
| M8 | Explanations and findings memo, including driver profiles by country and regime type | M | Ablation, SHAP and ALE agree, or the disagreement is reported; sealed test scored once |
| M9 | Interactive map on GitHub Pages, with the level selector and transfer-matrix panel | M | All views and place cards work, including at phone width |
| M10 | Stretch: L-effort archive lists; optional present-day counterfactual | L | — |

The slice (M1) comes early on purpose. It tests the risky joins (transliteration, historical
renames, linking DGZs to places) on real data before anything is scaled up. It also gives an
early read on how much population alone explains.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Transcription** of ~350 pages that cannot be OCR'd | Fast-path CSV; two independent reads; automatic checks; review queue; measured error rate |
| **Choosing the universe** biases the result | A fixed rule chosen before seeing labels; sensitivity runs; small targets kept at cell level |
| **Leakage** from target lists into features | Guard tests; the airfield list is never a feature; airfields get their own task (T5) |
| **Anachronism**: modern data, or post-Soviet knowledge, standing in for 1956 | Flags and an ablation; reported as "what SAC knew" vs. "what existed" |
| **Spatial autocorrelation** inflating scores | Spatial-block cross-validation; random splits reported only for contrast; GPBoost |
| **Correlated features** muddying attribution | Family-level ablation; ALE; only methods that agree count as findings |
| **Historical names and transliteration** | Curated rename table; match on coordinates first, names second |
| **Redactions**: weapons blanked; some lists only excerpts | Weapons are not needed for labels; check whether the Part II airfield list is complete |
| **Licences** | CShapes is CC BY-NC-SA. Dexter–Rodionov and Holm state no open licence, so commit derived counts, not raw copies. US documents are public domain. Ask before republishing the FLI/Wellerstein CSV |
| **Regime type is confounded** with planner, label provenance and era (§5.3) | Compare regimes within one planner where possible; planner, provenance and year as controls; call regime-level results descriptive, not causal |
| **Small per-country samples** | Minimum-size rule for level C; partial pooling at level H; low-variance models for small groups |
| **Key lists exist only in archives or print** (UK 1957 grading, Trojan/Dropshot annexes, Danish and Czechoslovak plans) | Work through the online lists first; the archive items are a separate decision (§11) |
| **Framing** | This is history: a declassified plan from 70 years ago. Any present-day extrapolation is labelled a counterfactual of 1956 logic, not a forecast |

---

## 11. Decisions needed

1. **Network access.** It is still blocked in this session. The project touches dozens of
   hosts: archives, census sites, Wikidata, HYDE and GHSL, PHP, the Wilson Center, CIA, DTIC,
   FAS. A broader access level is simpler than an allow-list. If you prefer an allow-list, see
   the domain list in the session notes.
2. **Regime coding.** Proposed: the 4-group scheme of §5.3 as primary, with alignment as a
   second axis, and the other codings as robustness checks.
3. **Archive and print sources.** Can anyone fetch them? The items are:
   - the UK National Archives files (the 1957 grading of 131 cities);
   - the Ross & Rosenberg facsimiles (the Trojan and Dropshot annexes);
   - Andersen (2026) on Denmark;
   - Luňák (2007), or the Prague military archive, for the Czechoslovak plans.

   Without them, levels C and R rest on the 1956 list plus the online lists.
4. **Fast path.** Will you email Wellerstein or FLI for the 1,154-target CSV?
5. **Repo initialisation.** Should this plan, plus the M0 scaffold, become the first commit on
   `main`?
