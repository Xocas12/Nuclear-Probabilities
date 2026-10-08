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
| Category Code List (5 pp, complete) | 191 installation category codes (275 = "Population"). **Transcribed** | Label vocabulary |
| **Part I Urban-Industrial (complex) list, "Abdulino to Zychlin" (306 pp, complete)** | ~1,200 complexes, each a priority, reference coordinates, its DGZs and its BE-numbered installations; ~13,500 printed lines | T1–T3 |
| **Part II airfield list (42 pp, complete)** | ~1,110 airfields, each with a priority number (Bykhov 1, Orsha S.W. 2…) | T5 |
| Part I airfield list; Part II complex list; cross-reference list | Released only as excerpts | Cross-checks only |
| The Archive's spreadsheets for Moscow, Leningrad, Beijing and Warsaw | Per-city installation breakdowns | Validation |

**How a complex is printed** (checked on the scans):
- **Header:** priority, reference number, name with a country suffix, reference coordinates.
  For example `1 5150 MOSCOW 5545-03737`. Coordinates are degree-minute digits, so they are
  accurate to under 2 km.
- **Aim-point lines:** one per DGZ, with coordinates and a letter label. Moscow has 12 (A, AH,
  AM … K). Some complexes have none.
- **Installation lines:** a category code and a BE number, e.g. `227 0167-`. The first four
  digits of the BE number are the World Aeronautical Chart. The installation number is often
  blank.
- **Sub-complexes** are indented and carry their own coordinates.

**What is missing:**
- **Installation names.** The Bombing Encyclopedia itself is still classified, so
  installations have codes but no names.
- **Weapons.** Weapon numbers and types are blanked out of the released copy.

**Anchors to validate against.** These correct the press coverage, which counted
installations as DGZs:
- **Moscow** is priority 1: 12 DGZs over 180 installations (13 and 190 with its three
  suburbs; the Archive's sheet counts 178 and 190).
- **Leningrad**: 7 DGZs over 139 installations (the Archive's sheet: 145; the pages are complete,
  so the difference is unexplained).
- **East Berlin**: 6 DGZs over 91 installations (68 in the city, 23 in six suburbs).
- **Countries on the list:** USSR, East Germany, Poland, Czechoslovakia, Hungary, Romania,
  Bulgaria, Albania, China (with Manchuria), North Korea and North Vietnam (8 complexes).
  Ulaanbaatar is printed with the suffix CHINA. Yugoslavia is absent, and Iran appears only in
  the category codes.
- **Part II totals:** the table of contents gives 1,209 DGZs; the Part II airfield list has
  1,128 rows. The Part II complex list survives only in excerpts, so the two cannot be reconciled.

**Transcribed in full (7 Oct 2026).** Both lists are in `data/curated/sac1956/` with a data card
(README.md) and a validation report (REPORT.md): 1,216 complexes, 873 sub-complexes, 1,405 DGZs,
10,220 installation lines, 34 Moscow-area "M-n" sites and 1,128 airfields, every value traced to a
printed line. Two findings change the label design below:
- **Half the complexes have no DGZ** (609 of 1,215 with a header), mostly low priorities: 98% of
  the top 100 have one, 5% of those ranked 901–1223.
- **Priorities come in tiers from about 321 down**, numbered alphabetically within each tier
  (`priority_tier` in the tables). Below the top 300 the rank inside a tier is noise.

### 4.2 The labels

| Task | Label | Unit |
|---|---|---|
| T1 Targeted? | The place is a Part I complex within r km. A variant requires at least one DGZ line; since half the complexes have none, the two variants are reported side by side | place (main), cell |
| T2 How hard? | Two counts: DGZs (aim points) and installations (target richness) | targeted places (hurdle model) |
| T3 Rank | Complex priority (every complex has one), modelled as an ordinal outcome over `priority_tier`: ranks 1–320 are individual, below that each alphabetical tier is one level | targeted places |
| T4 Kept under scarcity? | Survives into Part II. **Only feasible for airfields**: the Part II complex list was released only as excerpts | airfields |
| T5 Airfield priority | Priority number on the complete Part II airfield list | the ~1,110 airfields |

Population targeting is near-universal, so it is not a separate label: 2,081 of the 2,089
complex and sub-complex blocks have exactly one "Population" line (category 275). The few
exceptions are printed that way (SMOLENSK, priority 3, has none).

### 4.3 Getting a table out of the scans

The scans are image-only, 1-bit, with no usable text layer. A pilot on 4 pages (129 complex
lines and 27 airfield rows) found:
- only 0.1–0.3% of digits illegible;
- each page takes 1–3 minutes to read visually.

The full job is ~350 pages and ~14,600 lines. Two independent passes plus adjudication take
about 25–30 agent-hours, or ~3 hours with 10 parallel workers. So this step comes first.

0. **Fast path.**
   - In 2016 Alex Wellerstein and the Future of Life Institute mapped 1,154 targets from this
     list (blog.nuclearsecrecy.com/misc/targets1956/). That is probably one point per city.
   - **Not yet obtained.** The live blog sits behind a browser cookie check, and
     web.archive.org is not on this environment's allow-list.
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
   - minutes are under 60;
   - the BE chart prefix agrees across a complex and with its coordinates;
   - every block has one population line;
   - priorities are unique, with no gaps;
   - reference numbers run in alphabetical order;
   - airfield reference numbers match their parent complexes;
   - city totals match the Archive's spreadsheets and the anchors above;
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

| Source | Planner → target, year | Size and detail | Status after the first pass | Provenance |
|---|---|---|---|---|
| **SAC Atomic Weapons Requirements Study** | US → Soviet bloc, China, N. Korea, 1956 | ~1,200 complexes with priorities, DGZs and installations (~13,500 lines); ~1,110 airfields with priorities | **Transcribed in full** (Oct 2026): two independent passes, adjudication, cross-line checks; `data/curated/sac1956/` | Study |
| **Air Ministry city grading** | UK → USSR, 1957 | 131 cities over 100k, graded; 98 in range, 44 selected (counts unverified) | Not digitised. Open at Kew: AIR 2/13716, AIR 2/13717, DEFE 5/77/208, DEFE 5/78/224 | Study |
| Target Committee and orders | US → Japan, 1945 | 17 study areas → 5 reserved targets → 4 in the 25 July directive, with Kyoto and the Emperor's palace rejected | **Extracted: 42 rows**, one per city per decision stage | Plan |
| Chinese nuclear facilities | US → PRC, 1964 | Baotou plutonium reactor, Lanzhou gaseous diffusion plant | **Extracted: 2 rows** (EBB 488) | Study |
| SIOP-62 and the 1960 target list | US → bloc, 1961 | ~4,000 targets in the database; 1,043 DGZs, 706 of them in the USSR (China and satellite counts blacked out) | **Validation table: 8 rows** | Totals to check against |
| Norstad memo to Groves | US → USSR, Sep 1945 | Reportedly 66 cities, 21 Manchurian cities dropped | Not obtained: the blog has a cookie check and web.archive.org is not on the allow-list | Study |
| JIC 329/1 | US → USSR, Nov 1945 | 20 named cities | Not obtained: the CIA page renders by script; the old copy is on web.archive.org | Study |
| French Air Force staff study | France → USSR, 1959 | 20 named cities with air-defence grades | Not obtained: the open-access copies sit behind anti-bot challenges | Study |
| Broiler → Trojan → Offtackle → Dropshot | US → USSR, 1947–49 | 24 → 70 → 104 → ~100 cities | Print only (Ross & Rosenberg facsimiles) | Plan |
| OPS PLAN 25-58 | US → PRC, 1958 | ~10–30 airfields and bases | Halperin RM-4900 downloaded (237 scanned pages), not yet read | Plan |
| MacArthur's "retardation targets"; WINTEX-CIMEX 89; SAC–Bomber Command joint plans | US / NATO / US+UK | Small or counts only | Not yet attempted | Study / exercise / plan |

**Warsaw Pact planners → NATO and neutral states**

No Soviet *strategic* target list has ever been declassified. What exists are front-level
plans and exercises from the Czech, Polish, Hungarian and East German archives. The PHP
facsimiles turned out to be reachable through phpisn.ethz.ch, an archived copy of the old PHP
site.

| Source | Planner → target, year | What it gives | Status after the first pass | Provenance |
|---|---|---|---|---|
| **"Lato-67" directive** | Unified Command, for the Polish Coastal Front → FRG, NL, BE, DK, 1967 | 57 aim points at 49 places: transport hubs, ports, airfields | **Extracted: 57 rows**, from the Russian facsimile | Exercise |
| **1964 Czechoslovak war plan** | ČSLA → FRG (Bavaria), 1964 | Headquarters, missile units and regions. Nuremberg, Stuttgart and Munich are axes of advance, *not* targets | **Extracted: 21 rows** | Plan |
| **1965 Hungarian–Soviet war game** | → Austria, Italy, FRG, 1965 | 29 itemised strikes (the document says 30), including Vienna 2×500 kt, Verona, Vicenza, the nuclear-ammunition depot at Oberammergau | **Extracted: 23 rows**, from the Hungarian original plus the English translation | Exercise |
| "Burza" 1961 | Polish Maritime Front → DK, FRG, NL, 1961 | The directive gives only counts (93 missiles); two companion documents name targets | **Extracted: 23 rows** | Exercise |
| 1977 General Staff Academy front lesson | USSR → FRG, 1977 | Five FRG control-and-warning sites and real NATO units | **Extracted: 19 rows** (CIA translations, via archive.org) | Exercise (training) |
| Zealand landing plans | Poland → Denmark, 1965 / 1977 | 5 + 10 strikes near Roskilde, Slagelse, Næstved, Vordingborg | **Extracted: 15 rows**, secondary (Pałka 2022) | Plan |
| 1970 Coastal Front plan map | Poland → Denmark, 1970 | Only 5 of 17 strikes are named | Partial: 4 rows, secondary (Nielsen et al. 2016) | Plan |
| R-5M "Operation Atom" | USSR → UK and others, 1959 | — | 1 row (BBC 2012); Uhl's study is lending-only | Study |
| "Seven Days to the River Rhine" | Warsaw Pact, 1979 | Wikipedia's "known targets" all trace to *other* plans (the 1965 game, the 1964 plan, a 2003 Danish article) | 9 rows kept for audit; **not usable as 1979 labels** | — |
| Czechoslovak plans 1977 / 1989 | ČSLA → FRG | 258 / 546 warheads | Counts only (csla.cz); named targets need the Prague archive or Luňák 2007 | Plan |
| Polish plans against Denmark, 1961–89 | Poland → DK | 1989 plan: 131 first-phase strikes | Print only (Andersen 2026) | Plan |
| Lautsch 2021 (NVA 5th Army) | GDR → FRG | — | Contains no target list; his 2014 article may | Reconstruction |
| Bulgarian plans | → Greece, Turkey | 30 bombs set aside, no names | Archive only | Plan |
| Swedish inquiry SOU 2002:108 | — → Sweden | No developed attack plans found | Negative evidence, not used as labels | — |

**Warsaw Pact staffs' simulations of NATO strikes on the East (new find)**

These are the communist side's own expectations of where it would be hit. They mirror the
Western civil-defence lists below.

| Source | Simulated attacker → target, year | Status | Provenance |
|---|---|---|---|
| Polish command-staff map exercise | "Westerners" (NATO) → Poland, USSR, GDR, 1962 | **Extracted: 76 rows** (Poland 70) | Exercise (defender's expectation) |
| 1965 Hungarian war game, "Westerners'" plan | NATO → Hungary, Czechoslovakia, USSR, 1965 | **Extracted: 26 rows** | Exercise (defender's expectation) |

**Defenders' assumptions and analysts' reconstructions**

These lists add the US and the UK as target countries at scale. They are a different kind of
evidence: they record what a government expected its adversary to hit. **Lists generated by a
simple rule** (such as "every city over 50,000") **are excluded from training**, because a model
would only rediscover the rule.

| Source | Producer → target, year | Size and detail | Where | Effort | Provenance |
|---|---|---|---|---|---|
| **NAPB-90, *Nuclear Attack Planning Base 1990*** | FEMA, modelled on Soviet doctrine → US, 1987 | An *initial* set of 6,139 targets in 10 classes before editing; the final aim-point count is not printed. County tables of population and area by blast band (Annex A) and fallout (Annex B), ~3,100 counties each. State maps with blast rings | 510-page scan, obtained. The "National Aimpoint List" volume is not on archive.org or OSTI, so it would need FOIA | M: transcribe the county tables (~8–12 h by vision); georeference the rings (lower-bound counts) | Defender. No population class. Editing rules drop refineries under 75,000 bbl/day and hit power plants until 75% of capacity is gone |
| FEMA-196, *Risks and Hazards* | FEMA → US, 1990 | NAPB-90 blast rings, state by state; maps only | Same GitHub repo | M | Defender |
| Operation Alert attack patterns | FCDA → US, 1955–61 | 1955: 61 bombs on 60 cities; only 16 are named on the official map (extracted) | FCDA Annual Report 1955; 1956 hearings (full list probably in an appendix) | S–M | Defender (exercise) |
| TR-82 high-risk areas; CRP-2B | DCPA → US, 1975–79 | CRP-2B: 1,444 weapons, 6,559 Mt; TR-82 itself not obtained | OSTI (ORNL-5041); DTIC | M | Defender. Its "population over 50,000" class is a rule and is dropped |
| "Probable nuclear targets in the United Kingdom" | Home Office → UK, 1969–72 | Reported as 106 sites; **unverified** | File HO 322/785 is still retained by the department. DEFE 69/585 is open at Kew but not digitised | L | Defender |
| Square Leg / Hard Rock | Home Office → UK, 1980 / 1982 | Square Leg: 95 targets extracted from the *New Statesman*'s reproduction of the official bomb plot ("125 weapons … around 200 Megatons"). Hard Rock not obtained | *New Statesman* 1980/81 (secondary); Hard Rock files HO 322/985–1020 at Kew, not digitised | S (done) / L | Defender (exercise); politically edited |
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
  - possibly the UK, from Square Leg (95 targets);
  - Denmark and West Germany, if the print and archive sources are obtained.
- **Regime-type contrasts within one planner are scarce.**
  - Greece under the 1967–74 junta and Turkey would give a Warsaw Pact planner targets in
    NATO autocracies. They are reachable only through the Bulgarian archive.
  - Austria (neutral) differs from the other targets in alignment, not regime.
  - **The best route is to compare defenders' expectations across regimes.** On one side are
    Warsaw Pact staffs' simulations of NATO strikes on Poland, Hungary and the USSR (1962,
    1965). On the other are Western civil-defence lists for the US, UK and Canada (1955–87).
    Both are a defender's expectation, so provenance stays fixed while regime type changes.
    Era and country still differ.
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

**Progress (8 Oct 2026).** M2 is done: the full 1956 feature base for the whole bloc.
- **Universe.** 2,622 towns of 10,000+ near June 1956 with coordinates.
  - The USSR comes from the 1959 census, plus ten closed towns of the nuclear complex with
    imputed populations.
  - East Germany, Poland, Hungary, Czechoslovakia, Romania, Bulgaria and Albania come from
    their 1950s censuses and yearbooks, interpolated to the study date. Some had to be read from
    scans: the GDR's 1956 yearbook, Poland's 1957 yearbook and Votrubec (1959) for Slovakia.
  - China's universe is its 163 cities of the 1953 census. North Korea, North Vietnam and
    Mongolia have only the UN's estimates for their largest cities.
  - The SAC targets are linked per country, and the list's two scan gaps apply bloc-wide.
- **Features: 48 in six families.**
  - population;
  - administration: a cited table of the 1956 regional centres, with the oblasts of 1954–57;
  - geography and reach: terrain; the sea; the capitals; NATO territory, the bloc's frontier
    and SAC's overseas bases on the study date; the continental US;
  - industry: the Soviet defence industry active in 1956, from Dexter and Rodionov; WRI power
    plants;
  - military: a cited, dated table of 153 sites (district and fleet HQs, naval and Long-Range
    Aviation bases, the nuclear complex, test ranges) with a decision for June 1956; airfields;
  - transport.
- **Provenance.** Every feature names its sources and flags later knowledge
  (`data/FEATURES.md`). Every source in the manifest has a role. A guard test keeps the label
  sources out of the features.
- **Check run** (`runs/m2-check/`). This is a check, not a result. Under spatial CV, "on the
  list" scores a PR-AUC of 0.75 for the population rule and 0.84 for LightGBM or logistic
  regression on every feature. Transport and geography add the most over population. The
  military sites add little once the rest are in. Dropping the anachronistic features costs
  about 0.02. None of the ten closed towns is on the 1956 list. In several Eastern European
  countries the population rule alone does as well as the global model, so the per-country
  models (M7) will matter.
- **Gaps.**
  - Slovakia's towns that passed 10,000 after 1953 are missing.
  - China's towns below city rank are missing.
  - Ullman's 1958 figures for China need a manual download.
  - District HQs for Hungary, Albania, North Korea and North Vietnam are unverified.

**Progress (7 Oct 2026, later).** M0 and M1 are done. The scaffold (uv, Python 3.12, ruff,
pytest, Make, CI) and the provenance manifest are in place. The USSR slice runs end to end:
1,635 towns of 10,000+ in 1959 from pop-stat and Demoscope, 99% given coordinates by a
gazetteer over GeoNames; the SAC 1956 targets linked to them (coordinates first, names second);
population and administrative features; the population rule, logistic regression and LightGBM
under spatial-block CV, with the sealed test blocks set aside; and a map (`runs/m1-slice/`).
First read, not a result: population alone ranks the towns nearly as well as every slice model
(PR-AUC 0.79 vs 0.80 for "on the list"), so industry, military and transport must carry what is
left. Building the slice exposed a page missing from the SAC scan (Astrakhan, Ashgabat, Arzamas;
see the data card). Next: M2, the full 1956 feature base.

**Progress (7 Oct 2026).** M3 is done for the two complete lists: the Part I complex list and
the Part II airfield list are transcribed (two passes by different models, every disagreement
adjudicated on the scan, a second look at every line a consistency check flags), with an error
rate measured per pass and a data card. Outstanding for M3: the Part II complex excerpts.

**Progress (3 Oct 2026).** The first pass of M4 is done: 24 lists extracted, every row with a
page reference and a quote (see `data/INVENTORY.md`). For the 1956 list, everything is
downloaded and piloted, and the category codes are transcribed. Feature sources are confirmed
downloadable: pop-stat's 1939/1959 census series, the Dexter–Rodionov guide (v24, July
2026), GeoNames. The code scaffold (pyproject, tests, CI) is not started.

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

1. **Access that is still missing:**
   - **web.archive.org** is not on the allow-list. It holds the Wellerstein 1,154-target
     map data, the Norstad memo and the JIC 329 article.
   - **Some hosts block scripts with challenges, which are not bypassed:** HYDE's
     repositories (Yoda, DANS), hal.science, Sciences Po's repository, the FAS document
     pages and blog.nuclearsecrecy.com.
   - **Downloads needed by hand:** the HYDE 3.3 grids for 1950 and 1960, and Pelopidas &
     Philippe (2021) for the French 1959 list.
2. **Full transcription of the 1956 list.** About 350 pages and ~14,600 lines, in two
   independent passes. That is ~25–30 agent-hours, or ~3 hours wall-clock with 10 parallel
   workers. It needs your go-ahead to run as a multi-agent job.
3. **Regime coding.** Proposed: the 4-group scheme of §5.3 as primary, alignment as a second
   axis, and the other codings as robustness checks.
4. **Archive and print sources.** Can anyone fetch them? The items are:
   - Kew: AIR 2/13716–13717 and DEFE 5/77–78 (the 1957 UK grading); HO 322 (Hard Rock);
     DEFE 69/585;
   - the Ross & Rosenberg facsimiles;
   - Andersen (2026);
   - Luňák (2007) or the Prague military archive.
5. **Default branch.** The repo's only branch is the session branch, which GitHub made the
   default. Create `main` from it?
