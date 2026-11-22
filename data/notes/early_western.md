# Early Western plans against the USSR, 1945-1960: source notes

Topic: `early_western`. Session date 2026-11-22; all retrievals that day. Raw files are in
`data/raw/early_western/` (sha256 in `data/sources.d/early_western.yaml`). Every row has a page
reference and a verbatim quote from a document I opened. No list was filled from memory.
The CSVs were written by a one-off script (hand-typed name lists, no OCR on the map).

| file | rows | provenance | basis |
|---|---|---|---|
| `us_1945_jic329.csv` | 20 | study | secondary (Valero 2000) |
| `us_1945_aaf_15cities.csv` | 15 | study | primary (AAF map, 31 Aug 1945) |
| `us_1945_aaf_25cities.csv` | 25 | study | primary (same map) |
| `us_1949_trojan.csv` | 2 | plan | secondary (Condit 1996, official JCS history) |

## 1. JIC 329 (3 Nov 1945): Valero, Studies in Intelligence 44:3 (2000)

- URL: https://www.cia.gov/resources/csi/static/american-joint-intel-committee.pdf (32-page PDF
  with a text layer; pdfinfo misreports 8 pages).
- PDF p12: "JIC 329 identified 20 Soviet cities for atomic destruction"; the 20 are listed in one
  sentence. Footnotes 30-31 (PDF pp27-28) cite JIC 329, "Strategic Vulnerability of the U.S.S.R. to
  a Limited Air Attack", 3 November 1945, ABC Russia (22 August 1943) Sec. 1-A, RG 165, NACP.
- Valero says JIC 329, not 329/1. The brief's "JIC 329/1" may be the later version; I could not see
  either primary, so the plan_id is `us_1945_jic329`.
- Doubts: the order is Valero's (it matches neither population nor the AAF chart order, so it may
  follow the original). "Novosibrisk" and "Yarolavl" are Valero's typos, kept in `name_source`.
- Primary not online that I could find (CIA reading room search gives nothing parseable; the
  archive.org CIA mirror has no JIC 329).

## 2. AAF map "Russian & Manchurian Strategic Urban Areas" (31 Aug 1945)

- URL used: the Commons 1920 px thumbnail
  https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/1945_Russian_and_Manchurian_Strategic_Urban_Areas.jpg/1920px-1945_Russian_and_Manchurian_Strategic_Urban_Areas.jpg
  The 3972 x 2941 original (https://upload.wikimedia.org/wikipedia/commons/9/95/1945_Russian_and_Manchurian_Strategic_Urban_Areas.jpg)
  returned HTTP 429 every time.
- Commons cites the map to Norstad to Groves, "Atomic Bomb Production", 15 Sep 1945, MED Top
  Secret correspondence, NARA M1109, roll 1, target 4, folder 3, by way of Wellerstein's blog post
  of 9 May 2012. The draftsman's signature reads "J R Hagan 31 Aug 1945"; "TOP SECRET" at the foot.
- The sheet has four bar charts. Two name cities:
  - "15 SELECTED SOVIET CITIES (PRODUCTION PERCENTAGE)", with "TOTAL POP. 10,151,000" and
    "TRANSPORT IMPORTANCE - 1ST PRIORITY 5 CITIES, 2ND PRIORITY 3 CITIES, 3RD PRIORITY 4 CITIES".
  - "25 SELECTED SOVIET CITIES (PRODUCTION PERCENTAGE)", with "TOTAL POP 14,103,000" and
    "1ST PRIORITY 6 CITIES, 2ND PRIORITY 6 CITIES, 3RD PRIORITY 9 CITIES".
  - The other two ("RUSSIAN CITIES (INDICATED ON MAP)", "MANCHURIAN CITIES (INDICATED ON MAP)") give
    only industry shares, no names.
  The bars are shares of Soviet output by industry (planes 83%, tanks 86% ...), not per city, so no
  per-city priority or bomb count is in the CSV. The transport-priority counts are not tied to names.
- Norstad's memo (page images embedded in a Substack article, see 4) gives "incapacitation of 15
  first priority targets - 39" bombs and "destruction of 66 cities of strategic importance - 204".
  That the 15-city chart is Norstad's 15 first-priority targets is my inference. What the 25-city
  set was for is not stated.
- Not done: the map itself marks about 60-70 "selected centers" (factory, oil and communications
  symbols, a priority digit and an area in square miles on leader lines), Russian and Manchurian.
  This is probably the 66-city set. At 1920 px the names are legible but several leader lines are
  ambiguous, so I did not transcribe it. It should be done from the full-resolution original.

## 3. TROJAN (JCS, approved 28 Jan 1949): Condit, JCS and National Policy vol. II (1996)

- URL: https://archive.org/download/DTIC_ADA323796/DTIC_ADA323796.pdf (DTIC ADA323796 mirrored on
  archive.org; jcs.mil's Policy_V002.pdf gave 403). Book p158 = PDF p165, footnote 16 cites JCS 1974,
  13 Dec 48 (the atomic annex), CCS 373.11 (12-14-48) sec 1.
- Text: 70 cities; "Twenty of these cities, including Moscow and Leningrad, were considered first
  priority targets"; 133 bombs, "eight would be dropped on Moscow and seven on Leningrad".
- Only 2 rows; `use: audit`. Condit pp161-162 on OFFTACKLE (292 bombs) and the HALFMOON/BROILER
  sections name no cities.
- Harmon report (JCS 1953/1, 12 May 1949; NSA 2022 casualty-estimates posting, Doc 1,
  https://nsarchive.gwu.edu/sites/default/files/documents/reuyy0-k92to/01.pdf, 110 pp.): App. A
  para 7 (report p37, PDF p37) says "Annex 'A' to this Appendix sets forth the cities ... together
  with the number of atomic bombs tentatively allocated to each urban area" (30 first-stage, 40
  second-stage cities). The copy jumps from p37 to p41: the annex is missing. No rows.

## 4. Norstad to Groves, "Atomic Bomb Production", 15 Sep 1945

- Wellerstein's PDF (http://blog.nuclearsecrecy.com/wp-content/uploads/2012/05/1945-Atomic-Bomb-Production.pdf)
  and the blog (blog.nuclearsecrecy.com) reset the connection.
- Page images of the cover memo, the study's p1, the summary para 18 and Groves's reply of 26 Sep 1945
  are embedded in https://michelchossudovsky.substack.com/p/us-war-department-september-1945-plan-nuclear-war-ussr
  (advocacy site; images only used). They confirm the totals (15 first-priority targets / 39 bombs;
  66 cities / 204 bombs; 123 minimum and 466 optimum stock), but the pages with city names (Tabs A-C)
  are not among them. No CSV beyond the map lists in 2.

## 5. Not obtained

- French Air Force staff study, 1959 (Pelopidas & Philippe, Cold War History 21:3, 2021,
  doi 10.1080/14682745.2020.1832472): tandfonline 403 (Cloudflare); hal.science/hal-03384910/document
  and sciencespo.hal.science behind Anubis (WebFetch also refused); H-Diplo review 403.
- UK 1957 city grading and SAC-Bomber Command coordination (1958): a summary is in Air Power Review
  vol. 7 no. 1 (https://www.raf.mod.uk/what-we-do/centre-for-air-and-space-power-studies/aspr/apr-vol7-iss1-7-pdf/),
  403 from here. Search snippets give 131 cities over 100,000, 98 within about 3,000 km, and Bomber
  Command's 106 targets (69 cities, 17 airfields, 20 air-defence sites), citing AIR 8/2201 (SAC/BC
  co-ordination, 11 Jul 1958). No city names appear in the snippets. Files at Kew are not digitised (see
  `western.md` 9).
- PINCHER, BROILER, HALFMOON/FLEETWOOD, OFFTACKLE, DROPSHOT, HARROW: no public document or open
  scholarly text that names their cities was found. Ross (1988), Ross & Rosenberg (facsimiles),
  Brown's *Dropshot* (1978) and Kaku & Axelrod (1987) are print only, or lending-only on archive.org.
  Wikipedia ("United States war plans (1945-1950)") gives the JWPC July 1947 study as Moscow 7,
  Leningrad 3, Kharkov 2, Stalingrad 2, citing Ross 1988 pp54-57. That is tertiary, so I did not
  extract it.
- Rate limits: the Wikimedia API and originals gave 429; the Google Books API quota was exhausted.
