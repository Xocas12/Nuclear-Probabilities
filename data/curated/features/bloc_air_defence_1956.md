## Soviet-bloc air defences of June 1956 (`bloc_air_defence_1956.csv`)

- **What it is.** 313 rows: air defence headquarters, PVO fighter airfields, S-25 positions and
  radar units of the bloc around the study date. Each row is one unit at one place, so an airfield
  with three regiments has three rows.
  - Columns: `site`, `role`, `unit`, `country_1956`, `town`, `lat`/`lon`, `from_year`/`until_year`,
    `in_june_1956`, `decision`, `note`, `source`.
  - `from_year`/`until_year` are the years of the unit at the place. A blank means unknown, or that
    the role continued past 1991.
  - `note` quotes the dating evidence. `decision` explains every `uncertain` and `no` row. `source`
    gives the pages used, then the coordinate source after `coords:`.
- **Independence.** Nothing under `data/curated/sac1956`, `data/curated/labels` or `data/processed`
  was read. Rows were selected by rule from the unit pages (below), never by place. One provenance
  caveat applies to the S-25 points; see "Anachronism and provenance".

### Rows per role and `in_june_1956`

| role | yes | uncertain | no | rows |
|---|---|---|---|---|
| pvo_hq | 53 | 8 | 15 | 76 |
| pvo_fighter_base | 105 | 15 | 20 | 140 |
| sam_system | 23 | 34 | 0 | 57 |
| radar | 26 | 14 | 0 | 40 |
| **total** | 207 | 71 | 35 | 313 |

The 120 `yes` or `uncertain` fighter rows fall on 96 distinct points (86 for `yes` alone). 310 rows
are in the USSR, 2 in Bulgaria and 1 in Hungary. The `no` rows are not padding: they record near
misses that a later page could mistake for 1956 units. Exclude them from any feature, and exclude
the S-25 area row (`S-25 Berkut system, Moscow area`), whose point is central Moscow and not a site.

### How it was built

- **Pages.** Michael Holm's order of battle on ww2.dk: the PVO index (`pvo/pvo.htm`) and its
  district, army, corps, division, radar and SAM lists; `air force/division/iad/iad.htm`;
  `air force/regiment/iap/iap.htm`; the two fighter army pages; and the non-Soviet Warsaw Pact air
  force pages. Wikipedia: en *S-25 Berkut*; ru *1-я армия ПВО особого назначения*, *Московский округ
  ПВО*, *Бакинский округ ПВО* (wikitext read through `action=raw`). 726 pages were saved, with at
  least 1.2 s between requests on each stream. 17 pages came back empty while two streams ran and
  were fetched again singly. The 303 distinct URLs in `source` were all opened. `robots.txt` returned 404, so no
  rules were published. The section's index URL, `new/pvo/`, returned 403 (no directory listing), so
  the crawl started from `new/pvo/pvo.htm`.
- **Selection rule, fighter divisions and regiments.** Every page on the two lists was parsed for
  its dated `Bases` and `Subordination` lines.
  - A unit is in if a base line covers June 1956 and its parent at that date is labelled PVO or Air
    Defence, directly or through its division's page.
  - Where the parent is unlabelled, the last dated rename before June 1956 decides. A unit "renamed
    ... PVO" in 1942 and renamed out in 1951 is not PVO.
  - A PVO label in a page title is not evidence, since titles carry the unit's last name.
  - Left out: 115 pages with no PVO label at the date; 96 under the air force or naval aviation in
    June 1956 and not recorded as joining the PVO by 1957; 47 with no base line covering June 1956.
- **Selection rule, others.** HQ rows for armies, corps and districts were written by hand from the
  quoted lines. S-25 rows take every regiment with an S-25 line and a launch area, cross-checked
  against the four special corps' Organisation 1960 lists. Radar rows are every page on the
  radar lists whose base line covers June 1956.

### Decisions

- **`yes`:** a dated line covers June 1956 on both sides, or (HQ towns and page-less regiments) the
  same town appears in dated lists on both sides, 1952 or later and 1958 or earlier for regiments.
  HQs of the 56th, 78th and 88th corps rest on Organisation 1955 and the 1960 successor's activation.
- **`uncertain` (71):**
  - 33 outer-ring S-25 rows, one of which (the 636th) also lacks an activation date, and one with
    no site code (below).
  - 11 radar units activated "1956", month not given, and 3 whose base line begins before June 1956
    while the activation line is later (9th Brigade 1.8.58, 164th Brigade 13.8.57, 172nd Regiment
    1.11.67).
  - 8 HQs: 37th, 49th and 72nd Guards corps; Leningrad Special Army; Minsk, Lvov and Primorskiy
    corps; the 26th division. Most have a town known only from a name or a 1960 successor.
  - 15 fighter rows: 10 page-less regiments known from division lists far from 1956; the 64th
    Regiment's undated 1956 move (Omsk-Severnyy, Tunoshna); the 849th, renamed PVO on 23.6.56 while
    still under an assault division until 8.56; and the two Bulgarian regiments, listed under "Air
    Defence" on Holm's index but dated to it only from 1968 or not at all.
- **`no` (35):** 20 fighter rows and 7 division HQs under air force or naval aviation in June 1956,
  several of which joined the PVO in January-March 1957 (the 146th, 165th, 181st, 254th and 60th
  divisions), and 8 air defence bodies activated in 1957.

### S-25

- 56 regiment positions, matching the 14 regiments of each of the four corps. Holm gives a launch
  area for each, and that point is used. The instructions allowed site rows only if a citable source gave
  them; these pages do.
- **The site codes do not match Wikipedia's split.** Holm's codes give 22 C sites and 33 E sites,
  with the 756th uncoded; en-Wikipedia gives 24 inner and 32 outer. Holm calls E-coded sites the
  outer ring (`sam/1284zrp.htm`). Reading C as inner is an inference of this card, not the source's statement.
- **June 1956 is contested for the outer ring.**
  - en-Wikipedia says combat ready in June 1956, with site construction through 1958.
  - ru-Wikipedia says second-echelon regiments began combat duty in July 1956.
  - Holm's "1953 to 19xx equipped with S-25" is loose: ru-Wikipedia has equipment arriving from
    March 1954 and acceptance on 7 May 1955.

  So C rows are `yes` (regiment at the site) and E rows are `uncertain`. Treating the second echelon
  as the outer ring is also an inference. A `yes` does not assert combat readiness.

### Coordinates

| role | OurAirports, checked within 5 km of Holm's point | OurAirports, by name | GeoNames town | Holm's point |
|---|---|---|---|---|
| pvo_fighter_base | 121 | 5 | 12 | 2 |
| pvo_hq | | | 76 | |
| sam_system | | | 1 | 56 |
| radar | | | 15 | 25 |

- **Deviation from the instructions.** S-25 and radar points use Holm's coordinate where it has one (81
  rows), because the row is a site and not a town or airfield. To follow them strictly, replace
  them with the town's GeoNames point.
- HQ rows are the town, not the HQ building or the division's airfield; the gap to Holm's point is
  in `source` where he gives one (up to 16.7 km, Komsomolsk-na-Amure).
- The two fighter rows on Holm's point are Savasleyka and Severno-Vostochniy Bank, which had no
  OurAirports or GeoNames match.
- Holm's point for the 38th Guards Regiment reads `39 88 19E`, an impossible value; it was rejected
  and Rostov-na-Don's OurAirports point used.
- Holm's radar points can be a unit's later position, since many base lines run to "today".
- Isakogorka and Tukums use GeoNames because Holm marks their radar points "possibly".
- Tukums' GeoNames choice is flagged in `source`: its region could not be confirmed by name.

### Coverage by air defence body (`yes` and `uncertain` rows)

There is no June 1956 order of battle on Holm's site. The bodies below are those named by dated
subordination lines, so this is a reconstruction and no denominator exists. Radar rows are not
attributed (39 USSR, 1 Hungary).

| body | HQ rows | fighter rows | HQ of the body itself |
|---|---|---|---|
| Moscow Air Defence District | 24 | 30 | Located, with 57 S-25 rows. Best covered. 37th Corps `uncertain` |
| Leningrad Special Air Defence Army | 5 | 11 | `uncertain` |
| Baku Air Defence District | 5 | 10 | Located. 62nd Corps not located |
| North Caucasus Air Defence Army | 3 | 9 | Not located |
| 72nd Guards Corps / Turkmenistan Corps | 4 | 9 | 72nd `uncertain`, Turkmenistan not located |
| 49th Fighter Aviation Corps | 4 | 8 | `uncertain` |
| 32nd Fighter Air Defence Army | 3 | 8 | Not located, no page |
| 42nd Fighter Air Defence Army | 0 | 6 | Not located, no page |
| Minsk Air Defence Corps | 2 | 3 | `uncertain` |
| Turkestan Air Defence Region | 1 | 3 | Not located |
| Amurskaya Air Defence Army | 1 | 2 | Not located |
| Sakhalinskaya Air Defence Division | 1 | 2 | Not located |
| Belomorskiy Air Defence Corps | 1 | 2 | Not located |
| 36th Fighter Aviation Corps | 1 | 1 | Not located |
| GK PVO direct (GK PVO itself, Odessa Corps) | 2 | 0 | Located |
| Carpathian Air Defence Zone | 1 | 0 | Zone not located. Lvov Corps `uncertain` |
| Parent unnamed or unmapped | 3 | 14 | Includes the Transbaikal 246th division, and the Far East and Siberian regiments under an unnumbered "000" division, the 222nd, 93rd and 32nd |
| Bulgaria | 0 | 2 | |

Read this as thin outside Moscow, Leningrad and the Caucasus, especially east of the Urals. Rows
per body reflect what Holm documents as well as what was there, so a feature built on this table
may measure Holm's coverage in part.

### What could not be obtained, or was not covered

- **HQ towns.** The bodies marked "not located" above are named with dates but no town, so they have
  no row rather than a guessed one.
- **Regiments.** 8 regiments in division lists have no page and no list near 1956, and were left
  out: 735th, 266th, 423rd, 940th, 976th, 722nd, 772nd, 304th. Some have conflicting towns.
- **Anti-aircraft artillery.** The AAA divisions and regiments that were much of 1956 air defence
  are not a role here. Holm names a few only in passing (the 78th, 95th and 100th).
- **SAM pages.** The crawl was stopped once S-25 and radar were complete, leaving 184 of the 259
  pages on the SAM lists unopened. They are not named in the S-25 corps lists, so they are probably
  later S-75 and S-125 units, but that was not checked page by page.
- **Radar.** Companies and radar models are not given. Holm's list is regiments and brigades only.
- **Satellites.** Polish, Czechoslovak, East German and Romanian air defence pages begin in 1959 or
  later; their predecessors are named without 1956 dates. Only Budaörs (Hungary) and the two
  Bulgarian regiments have rows. Soviet units in those countries appear under the air force and are
  excluded unless PVO. The 787th at Neuruppin, for example, left the PVO in 1951.
- **China, North Korea, Albania, Mongolia, North Vietnam.** No cited page documents a unit in June
  1956, so there are no rows. No PVO base line covering June 1956 lies in China.
- **Wikipedia.** ru has no article at the S-25 title tried (404), so it is not cited. Wikipedia was
  not searched for HQ towns beyond the S-25 and district articles.

### Anachronism and provenance

- **S-25 points.** Holm labels his launch areas "US designation: Moscow SAM site ...", which suggests
  the positions descend from US intelligence. When the codes were assigned, and from what, was not
  checked. The rows were not chosen as targets, but this is the one place the independence depends
  on Holm's unstated sources, so a check of any result without the S-25 rows is advisable.
- **Unit names.** `unit` is the page's name, often later than 1956. The 52nd Brigade was the 6th
  Radio-Technical Regiment then; see `note`.
- **Town names.** `town` is Holm's spelling, not normalised to June 1956 as elsewhere in this
  directory. Perm was Molotov, Volgograd was Stalingrad, and Holm's oblasts mix eras (Tver for
  Kalinin).
- **Single source.** Most rows rest on Holm alone, whose pages cite no sources per unit. Conflicts
  with ru-Wikipedia are in `note`: the district name dates, the 1st Army's start, the 6th, 10th and
  17th corps towns.
- **Reproducibility.** The saved pages and build scripts were working files outside the repository
  and are not preserved by this table.
- **Overlap.** `military_sites_1956.csv` already has three `air_defence` rows (S-25 at Balashikha,
  Moscow and Baku districts); they agree on place. Combining the tables would double count them.

**Provenance.** The pages this table cites are in `cited_pages.csv` in this folder: for each, the licence, retrieval date, status and sha256, with `python -m nucprob.sources.cited_pages` to fill in what is missing. Each is the page as fetched on that date, not as first read: the table was made from earlier copies, and nothing shows the two agree. Licences: Wikipedia CC BY-SA 4.0; ww2.dk states no open licence, so its pages are cited and not kept; the few others were not assessed. sha256 of this table: `f49e4e30cccc5a49394bdb13841f59f4e7672aedd5974c16d6ecda97dd2caa3f`.
