## The US military sites of 1985 (`us_military_sites_1985.csv`)

- **What it is.** 196 rows: US military installations, command centres and nuclear-weapons
  plants in the 50 states as they stood in mid-1985. Each row is one role at one site. A base
  with two roles has two rows: Ellsworth, for example, has a bomber row and an ICBM-wing row.
  - Columns: `site`, `role`, `unit`, `state`, `town`, `lat`/`lon`, `county_fips`/`county`,
    `from_year`/`until_year`, `in_role_1985`, `decision`, `note` and `source`.
  - `county_fips` and `county` come from the 1990 county boundaries (`co99_d90`). Shemya's
    point lies off the polygons, so it was given the nearest county (Aleutians West), and its
    note says so.
- **How it was built.** Every row cites Wikipedia articles, and their URLs are in `source`:
  - each base's article and *List of Strategic Air Command bases* (which gives each SAC unit's
    years at each base);
  - the ICBM wing and squadron articles;
  - the five "*n*th Missile Wing LGM-30 Minuteman Missile Launch Sites" lists;
  - the DOE site articles.

  The wikitext was saved under `data/raw/us_military/wikipedia/`, one JSON file per page, with
  the URL it was fetched from. The API was rate-limited, so most pages came through
  `index.php?action=raw`.

  `scripts/us_military_1985_spec.py` holds the rows, years and decisions. Each row also has a
  regex that has to match its article; every match was read by hand. The CSV is rebuilt with
  `scripts/us_military_1985_build.py`. No nuclear target list or strike analysis was used,
  including NAPB-90, FEMA-196 and TR-82, Helfand and the NRDC studies, and nuclearwarmap.
- **Coordinates.** Each point is the article's `{{coord}}`, taken from the title or infobox and
  rounded to 3 decimals. There are four exceptions:
  - Savannah River's coordinates come from the rendered page (its template takes them from
    Wikidata), saved in `data/raw/us_military/html/`.
  - The Puget Sound Naval Shipyard article has none, so the row uses Bremerton's, about 2 km
    away.
  - The Atlantic and Pacific Fleet HQs use NS Norfolk's and Pearl Harbor's points.
- **Missile fields.** There is one `missile_field` row per wing:
  - The centre is the mean of the facilities Wikipedia lists with coordinates. For each
    Minuteman wing, that is every launch facility and missile alert facility, flights A–T
    (165 or 220 per wing). For each Titan II wing, it is the 18 launch complexes in its two
    squadron articles.
  - The note gives the radius that contains all the sites (95–164 km for Minuteman) and every
    county the sites fall in, with its FIPS code and site count.
  - The 90th SMW field covers Wyoming, Nebraska and Colorado. Its flights P–T are the 400th
    SMS, which took Peacekeeper from 1986, so Peacekeeper has no separate field row.

### Rows per role (in role at mid-1985 / all)

| role | in 1985 | rows | role | in 1985 | rows |
|---|---|---|---|---|---|
| sac_bomber (B-52, FB-111) | 16 | 19 | naval_base | 22 | 23 |
| sac_bomber_b1b | 0 | 4 | naval_shipyard | 7 | 7 |
| sac_tanker | 6 | 6 | fleet_hq | 3 | 3 |
| sac_reconnaissance | 4 | 4 | command_centre | 8 | 9 |
| icbm_wing (Minuteman) | 6 | 6 | nuclear_weapons_complex | 18 | 18 |
| icbm_wing_titan | 2 | 3 | army_corps_division_hq | 11 | 11 |
| icbm_wing_peacekeeper | 0 | 1 | army_major_post | 17 | 17 |
| missile_field | 8 | 9 | usaf_tac | 20 | 20 |
| icbm_test_base (Vandenberg) | 1 | 1 | usaf_mac | 12 | 12 |
| ssbn_base | 5 | 5 | usaf_other | 5 | 5 |
| | | | marine_corps_base | 13 | 13 |

The table has 184 rows in role and 12 out.

### Decisions (`in_role_1985`)

- **Out:**
  - Bombers had left Robins (1983), March (1982) and Seymour Johnson (1982). Their rows are
    kept as out, and the same bases have tanker rows that are in.
  - All four B-1B rows are out. Dyess received its first B-1B in June 1985, but the aircraft
    were on nuclear alert only from October 1986. Ellsworth, Grand Forks and McConnell got
    theirs in 1987.
  - Peacekeeper is out: first alert came in October 1986 and full operation on 30 December
    1986.
  - The 390th SMW and its Titan field are out: the last Titan was off alert in May 1984, and
    the wing was inactivated in July 1984.
  - Naval Station Everett is out: it was built from 1987 and opened in 1994.
  - Falcon AFS is out: the 2nd Space Wing moved in only in September 1985.
- **In, with a note:**
  - The two Titan II wings that were being drawn down are in. By the dates in the squadron
    articles, 15 of the 308th's 18 complexes were still in service on 30 June 1985, and 9 of
    the 381st's.
  - K-25 is in: gaseous diffusion ended on 27 August 1985.
  - Fort Drum is in: the 10th Mountain Division was activated there on 13 February 1985.

### Uncertainties and gaps

- **Wording of the Titan II dates.** The squadron articles' dates may be off-alert dates or
  deactivation dates. One case shows the problem: the 373rd SMS article dates complex 373-8
  to October 1986, but the Titan II article says it was the last missile, deactivated on 5 May
  1987.
- **Facts from general knowledge rather than the cited text:**
  - Seymour Johnson's intermediate KC-10 unit (the 68th Air Refueling Group, 1982–86);
  - the Grand Forks B-1B years;
  - the Kaneohe Bay brigade.

  Altus's SAC tanker wing starts in 1977 in the base article and in 1984 in the List of SAC
  bases.
- **Hand-written years and units.** Many `from_year`/`until_year` values are the role's years
  as written by hand: the base's founding or command change, and its closure. They were
  checked against the article where it states them. Units are the main ones in 1985, not a
  full order of battle.
- **Not covered:**
  - Air National Guard tanker units gained by SAC;
  - Guam (Andersen) and the overseas bases;
  - NORAD radars and air defence sites;
  - VLF and TACAMO communication stations, apart from Patuxent River's note;
  - Army depots and arsenals other than Redstone;
  - Air Training Command bases.

  The civilian continuity sites (Mount Weather, the Greenbrier) are included as command
  centres.
- **Anachronism.** Sites are curated from present-day articles and dated to 1985. The
  articles' titles are today's (Fort Cavazos/Hood, Space Force bases). The `site` column uses
  the 1985 names.
