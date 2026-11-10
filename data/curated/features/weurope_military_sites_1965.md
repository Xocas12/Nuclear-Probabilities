## Western European military sites of 1965 (`weurope_military_sites_1965.csv`)

- **What it is.** 323 rows: military installations in the FRG, the Netherlands, Belgium, Denmark,
  Austria and northern Italy as they stood in mid-1965 (30 June 1965), plus AFCENT's HQ at
  Fontainebleau (France), kept because it commanded the Central Region. Each row is one role at
  one site. A base with two roles has two rows. Ramstein, for example, has a 4 ATAF/17th AF HQ row
  and an air-base row.
  - Columns: `site`, `role`, `unit`, `country`, `town`, `lat`/`lon`, `from_year`/`until_year`,
    `in_role_1965`, `decision`, `note`, `coord_source` and `source`.
  - `country` is where the site lies, not whose forces used it. The Dutch, Belgian, French and US
    Nike and HAWK units in the FRG are `DE` rows.
  - `from_year`/`until_year` are the years of the role at the site. A blank means the year is
    unknown, or the role continued past 1991.
  - The scope is Italy north of the Po and the Venetian plain: Lombardy, Veneto,
    Friuli–Venezia Giulia, Trentino–Alto Adige and Novara. Turin-based units are left out.
- **Coordinates.** Every row is held at the centre of its 0.5-degree cell, up to about 39 km from the site, and
  its coordinate text is removed: an end year dates the role, not the facility, which may be in use today
  (`configs/protocol_amendment_19.yaml` for rows with no end year, `configs/protocol_amendment_20.yaml` for the
  rest; `scripts/coarsen_site_coordinates.py`). Earlier commits of this table in git history still hold exact
  points; see the features README, "Site coordinates".
- **How it was built.** Every row cites Wikipedia articles, and their URLs are in `source`:
  - de, en, nl, da and it articles on bases, units, towns and lists;
  - mainly *Kernwaffen in Deutschland* (its table of FRG nuclear sites), *Nike (Rakete)* (the
    tables and location maps of the Nike belt) and *MIM-23 HAWK* (the HAWK belt);
  - en *List of Nike missile sites* (grid references in Belgium, Denmark and Italy), *38th
    Tactical Missile Wing* (Mace launch sites) and *59th Ordnance Brigade*;
  - the Sondermunitionslager articles, and the base, wing and division articles.

  The wikitext was saved under `data/raw/weurope_military/wikipedia/<lang>/`, one JSON file per
  page, with the URL it was fetched from. The action API answered HTTP 429, so the pages came
  through `index.php?action=raw`, and redirects were followed by hand. `/w/index.php` is a path en.wikipedia.org's robots.txt disallows, so these copies were fetched against it; they are not held. The pages are registered through allowed paths in `cited_pages.csv` (README, "Robots").
  `scripts/weurope_military_1965_fetch.py` now fetches through `/wiki/<title>?action=raw`, which
  robots.txt allows.

  The scripts:
  - `scripts/weurope_military_1965_fetch.py` downloads the pages.
  - `scripts/weurope_military_1965_spec.py` holds the rows, years and decisions. Each row also
    has a regex that has to match its cited text: wikitext, or the same text with links and
    refs stripped.
  - `scripts/weurope_military_1965_build.py` rebuilds the CSV. It stops if a regex, a quoted map
    entry or a country bounding box fails.
  - `scripts/weurope_military_1965_coords.py` reads the coordinate templates.

  No Warsaw Pact target list, war plan or strike analysis was used. This excludes the PHP
  dossiers, "Lato-67", "Burza", the 1964 Czechoslovak plan, the 1965 Hungarian war game and
  "Seven Days to the River Rhine".
- **Where the points came from.** The build reads each point from its source, then holds it at its cell centre
  (above); `coord_source` says where it came from:
  - 239 rows use the article's title or infobox coordinate: `{{coord}}`, `{{Coordinate}}`, or
    the de/nl infobox degrees.
  - 20 rows use a named coordinate in a list. These are the Mace sites, the Danish Nike sites and
    the HAWK positions of FlaRakBtl 31/32.
  - 72 rows take a point written in an article. The de Nike location map (`Positionskarte~`)
    gives 51 of them, and the en Nike list's grid references give the rest. The specification keeps
    only each point's cell centre, and the build checks that the saved page gives a point in that cell.
  - The de Nike map points are approximate. Where a site article or en grid exists, they differ
    by 2–5 km, 12 km for Düren and 34 km for Albach. Albach, Oedingen, Kleingartach and
    Mainbullau therefore use their own articles.
  - About 64 rows, most of them HQs, garrisons and Honest John groups, are placed at the
    HQ/garrison town (the note says "Point is the town"). Some of these HQs are a barracks a few
    km from the town centre.
  - The it and nl town articles take their coordinates from Wikidata, so en or de town articles
    were used. Treviso's point is the Treviso label of the de Nike map.

### Rows per role and country (in role at mid-1965 / all)

| role | DE | NL | BE | DK | AT | IT | FR | in 1965 | rows |
|---|---|---|---|---|---|---|---|---|---|
| nato_hq | 4 |  |  | 1 |  | 2 | 1 | 8 | 8 |
| national_hq | 6 | 1 |  | 3 | 1 | 1 |  | 12 | 12 |
| corps_hq | 7 |  |  |  |  | 3 |  | 10 | 10 |
| division_hq | 22 |  |  | 1 |  | 5 |  | 28 | 28 |
| air_base_strike | 14 | 1 | 1 |  |  | 1 |  | 17 | 17 |
| air_base | 15 | 4 | 3 | 3 | 2 | 5 |  | 31 | 32 |
| air_base_support | 7 | 6 | 3 | 3 | 3 | 1 |  | 23 | 23 |
| nike_site | 59 |  |  | 5 |  | 13 |  | 77 | 77 |
| hawk_site | 21 |  |  |  |  |  |  | 20 | 21 |
| ssm_site | 17 |  |  |  |  | 5 |  | 20 | 22 |
| nuclear_storage | 26 |  |  |  |  | 1 |  | 23 | 27 |
| naval_base | 8 | 1 |  | 3 |  | 1 |  | 13 | 13 |
| army_garrison | 13 |  |  |  | 1 | 4 |  | 18 | 18 |
| radar_station | 8 | 1 | 1 | 2 | 1 |  |  | 12 | 13 |
| military_port | 2 |  |  |  |  |  |  | 2 | 2 |
| **total** | 229 | 14 | 8 | 21 | 8 | 42 | 1 | 314 | 323 |

What each role covers:
- **air_base_strike:** bases whose aircraft had a nuclear strike role. These are the F-104G
  wings of the Luftwaffe, Netherlands, Belgium and Italy; the RCAF CF-104s; the USAF
  F-100/F-105s; the RAF Canberras; and the French F-100Ds at Lahr and Bremgarten. Aviano is an `air_base`: no allowed page found dates a
  strike role there in 1965 (below).
- **air_base** and **air_base_support:** other combat flying units, and
  transport/training/naval/army aviation respectively.
- **nike_site:** one row per battery position, or per group HQ where no battery is located. The
  Danish sites had conventional warheads only.
- **hawk_site:** battery positions for the two Luftwaffe battalions with coordinates, and
  battalion garrisons otherwise.
- **ssm_site:** Pershing, Mace, Sergeant, Corporal and Honest John units, grouped by base.
- **nuclear_storage:** special ammunition sites that a source locates. Nike sites and strike
  air bases carry their own stores and are not repeated.

### Decisions (`in_role_1965`)

- **Out (8 rows):**
  - Mace Site V, abandoned 1961, and Site VII, closed 1960.
  - SAS Wahner Heide (1960–62) and SAS Stilleking (1960–63).
  - SAS Hemau, from April 1966.
  - SAS Dülmen-Visbeck, completed on 22 Sept 1965.
  - The French HAWK of the 402e RA at Dachau (1965–66, month unknown).
  - Chièvres, which had no Belgian wing after 1963.
- **In, although the role began close to 1965:**
  - Batteries and bases that began in 1964: the Albach and Kemel Nike batteries, HAWK FlaRakBtl
    32, the Dutch HAWK groups, Olpenitz and the 1. Luftlandedivision in Bruchsal.
  - Hopsten, whose first F-104G arrived in Feb 1965.
  - SAS Golf and RakArtBtl 250: Sergeant warheads "from 1965".
  - SAS Bellersdorf, built "about 1965".
  - The US HAWK battalion at Freising, handed over during 1965.
  - Memmingerberg: JaboG 34 flew F-104G from 1964, but its USAF custodial squadron is dated
    1966–96.
- **SAS without an opening date** (Riedheim, Kriegsfeld, Fischbach, Siegelsbach,
  Hanau-Erlensee, Münster-Dieburg, Diensthop, Dortmund and Arnsberg-Holzen) are counted as in role
  and flagged `UNCERTAIN`. The de Sondermunitionslager article says every corps and division had
  such a store from the early 1960s. Later sites are omitted: Fort Black Jack, Lehmgrube,
  Waldheide, Mutlangen, Görisried, Horressen, Eschborn, Landsberg-Leeder, Gießen and Meyn
  (all 1969 or later).

### Rows that rested on general knowledge (resolved 2026-11-03)

29 rows gave "UNCERTAIN: ... from general knowledge": the fact had no cited text, only the town's page for the
point. Each had to be cited or dropped (`configs/protocol_amendment_16.yaml`), and each was looked for in Wikipedia pages fetched
through `/wiki/<title>?action=raw`, which robots.txt allows (`CITED` and `DROPPED` at the end of
`scripts/weurope_military_1965_spec.py`; the build checks each row's quoted pattern against its cited page):
- **Cited as they stood (15):** the HQs of the 14th ACR at Fulda (Downs Barracks, 1951-1972), the British 1st,
  2nd and 4th Divisions (Verden, Lübbecke, Herford), the Belgian I Corps (Köln-Weiden, in the 1952 order of
  battle), the FFA (Baden-Baden), the Danish Western Command (Viborg) and the Italian III, IV and V Corps
  (Milano, Bolzano, Vittorio Veneto); RAF Wildenrath's Canberra strike role to 1970; Rivolto (Frecce Tricolori
  from 1961); Cameri (21º Gruppo from April 1964); the US Army port of embarkation at Bremerhaven; and CRC
  Nieuw-Milligen (a Command & Reporting Centre from 1960).
- **Corrected to what the source states (6):** Luftwaffengruppe Nord and Süd become the 6. and 2.
  Luftwaffendivision HQs at Münster and Karlsruhe (1963-1970; the 3. Luftwaffendivision was at Kalkar);
  Skrydstrup's and Baumholder's uncited units become "Royal Danish Air Force station" (opened 1953) and "US
  Army garrison" (from the 1950s); Aviano becomes an air base of rotating USAF fighter squadrons, not a strike
  base; CRC Glons is dated 1972 by its source, so it is not in role in 1965.
- **Dropped (8):** the Dutch I Corps HQ at Apeldoorn, the Belgian defence ministry at Evere (the cited quarter
  was built 1971-1976), Bierset's 1965 wing, the British Corporal regiments at Dortmund (type and years
  uncited), the Belgian naval base at Ostend, CRC Semmerzake, and the ports of Rotterdam and Antwerp.

Six of these rows feed features (`air_base_strike`, `naval_base`, `radar_station`). The changes move
`log_km_to_naval_base`, `log_km_to_air_defence` and `log_air_defence_sites_50km` on rows of LATO-67 and the 1977
staff-academy lessons, and `log_km_to_lra_base` on rows of the 1965 Hungarian war game. No other column or
document changes. `configs/protocol_amendment_16.yaml` refits the classifier on the corrected table; the
`table_sha256` of `runs/classifier/manifest.json` names the table the committed fit used.

### Uncertainties and gaps

- **45 rows have a `decision` starting with `UNCERTAIN`:**
  - The US HAWK battalions of the second HAWK line. The source gives 1970s–80s designations and
    no dates.
  - The dates of SOC 2 and SOC 3.
  - The SAS listed above.
  - Mace Site VIII. Its closure is undated, and a separate source says the Bitburg Mace B became
    operational in June 1964.
  - Source conflicts:
    - Schöneck and Obersayn Nike: 1966 in the Nike table, 1964 in the nuclear-weapons table.
    - Belgian 9th Missile Wing: 1959–62 in the en list, 1970 in de.
    - 2. and 7. Panzergrenadierdivision: the HQ moves are undated.
    - 3-84 Artillery: Heilbronn in en, Neckarsulm in de.
- **Unit designations.** US Nike/HAWK battalions are named as in the de article. Some names
  date from after 1965; for example, 2-1 ADA was 5-1 until 1972.
- **Not covered, or only partly:**
  - Honest John battalions as separate rows; they appear through their SAS rows.
  - US Sergeant and 8-inch artillery units.
  - Most brigade garrisons and barracks, and Bundeswehr depots.
  - Dutch and Belgian division HQs in their home countries.
  - Austrian brigades.
  - Dutch Nike 222 Sqn, which was at Twenthe in 1964–70 and is not located.
  - US communications sites and NADGE/ACE High stations.
  - Berlin, deliberately left out.
- **Anachronism.** Sites are curated from present-day articles and dated to 1965. Article
  titles are today's: the 50th TFW's article is *50th Space Wing*, Bitburg's is *Bitburg Airport*,
  and AFCENT's is *Allied Joint Force Command Brunssum*. Where an article's coordinate is a unit's later HQ, the 1965 HQ town
  was used instead. This applies, for example, to 1. Panzerdivision (Oldenburg today, Hannover
  in 1965) and 10. Panzerdivision.

**Provenance.** The pages this table cites are in `cited_pages.csv` in this folder: for each, the licence, retrieval date, status and sha256, with `python -m nucprob.sources.cited_pages` to fill in what is missing. Each is the page as fetched on that date, not as first read: the table was made from earlier copies, and nothing shows the two agree. Licences: Wikipedia CC BY-SA 4.0; ww2.dk states no open licence, so its pages are cited and not kept; the few others were not assessed. sha256 of this table: `43776a707ccb5cc97ff59276a5254b282968f4a9ba34d9102d2400fcaa491d34`.
