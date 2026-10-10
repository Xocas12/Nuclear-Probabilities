## Western European military sites of 1965 (`weurope_military_sites_1965.csv`)

- **What it is.** 331 rows: military installations in the FRG, the Netherlands, Belgium, Denmark,
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
- **How it was built.** Every row cites Wikipedia articles, and their URLs are in `source`:
  - de, en, nl, da and it articles on bases, units, towns and lists;
  - mainly *Kernwaffen in Deutschland* (its table of FRG nuclear sites), *Nike (Rakete)* (the
    tables and location maps of the Nike belt) and *MIM-23 HAWK* (the HAWK belt);
  - en *List of Nike missile sites* (grid references in Belgium, Denmark and Italy), *38th
    Tactical Missile Wing* (Mace launch sites) and *59th Ordnance Brigade*;
  - the Sondermunitionslager articles, and the base, wing and division articles.

  The wikitext was saved under `data/raw/weurope_military/wikipedia/<lang>/`, one JSON file per
  page, with the URL it was fetched from. The action API answered HTTP 429, so the pages came
  through `index.php?action=raw`, and redirects were followed by hand.

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
- **Coordinates.** Each point is rounded to 3 decimals, and `coord_source` says where it came
  from:
  - 239 rows use the article's title or infobox coordinate: `{{coord}}`, `{{Coordinate}}`, or
    the de/nl infobox degrees.
  - 20 rows use a named coordinate in a list. These are the Mace sites, the Danish Nike sites and
    the HAWK positions of FlaRakBtl 31/32.
  - 72 rows take a point written in an article. The de Nike location map (`Positionskarte~`)
    gives 51 of them, and the en Nike list's grid references give the rest. For these the build
    checks that the quoted string is in the saved page.
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
| national_hq | 8 | 1 | 1 | 3 | 1 | 1 |  | 15 | 15 |
| corps_hq | 7 | 1 |  |  |  | 3 |  | 11 | 11 |
| division_hq | 20 |  |  | 1 |  | 5 |  | 26 | 26 |
| air_base_strike | 14 | 1 | 1 |  |  | 2 |  | 18 | 18 |
| air_base | 15 | 4 | 4 | 3 | 2 | 4 |  | 31 | 32 |
| air_base_support | 7 | 6 | 3 | 3 | 3 | 1 |  | 23 | 23 |
| nike_site | 59 |  |  | 5 |  | 13 |  | 77 | 77 |
| hawk_site | 21 |  |  |  |  |  |  | 20 | 21 |
| ssm_site | 18 |  |  |  |  | 5 |  | 21 | 23 |
| nuclear_storage | 26 |  |  |  |  | 1 |  | 23 | 27 |
| naval_base | 8 | 1 | 1 | 3 |  | 1 |  | 14 | 14 |
| army_garrison | 13 |  |  |  | 1 | 4 |  | 18 | 18 |
| radar_station | 8 | 1 | 2 | 2 | 1 |  |  | 14 | 14 |
| military_port | 2 | 1 | 1 |  |  |  |  | 4 | 4 |
| **total** | 230 | 16 | 13 | 21 | 8 | 42 | 1 | 323 | 331 |

What each role covers:
- **air_base_strike:** bases whose aircraft had a nuclear strike role. These are the F-104G
  wings of the Luftwaffe, Netherlands, Belgium and Italy; the RCAF CF-104s; the USAF
  F-100/F-105s; the RAF Canberras; the French F-100Ds at Lahr and Bremgarten; and Aviano.
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

### Uncertainties and gaps

- **74 rows have a `decision` starting with `UNCERTAIN`:**
  - HQ towns, units or years taken from general knowledge: several BAOR, Dutch, Belgian, Italian
    and Danish HQs; Luftwaffengruppe Nord/Süd; the 14th ACR at Fulda.
  - The US HAWK battalions of the second HAWK line. The source gives 1970s–80s designations and
    no dates.
  - The radar/CRC sites in BE and NL, and the dates of SOC 2 and SOC 3.
  - The military ports.
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
