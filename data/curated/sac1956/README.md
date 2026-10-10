# SAC 1956 target list: data card

A complete, line-by-line transcription of the target lists in the US Strategic Air Command's
**Atomic Weapons Requirements Study for 1959** (SM 129-56, 15 June 1956), declassified and
published by the National Security Archive (Electronic Briefing Book 538, William Burr ed.,
December 2015, full city list added April 2016). The scans have no usable text layer; every
line was read twice, independently, and every disagreement was settled on an enlarged image
of the scan.

Counts, checks and the comparison with the Archive's own spreadsheets are in
[REPORT.md](REPORT.md), which `scripts/sac1956_assemble.py` regenerates with the tables.

## What is covered

| Part of the study | Source file (EBB 538) | Pages | Here |
|---|---|---|---|
| Part I complex list, "Abdulino to Zychlin" (urban-industrial targets) | `1st city list complete.pdf` | 306 (study pp. 200–504) | complete |
| Part II airfield list | `section6.pdf` | 43 (42 list pages, study pp. 505–546) | complete |
| Category code list | `section3.pdf` | 5 | `../labels/sac1956_category_codes.csv` |
| Part I airfield list (excerpt) | `section4.pdf` | 11 (270 rows, AFRIKANDA to PALANGA in stretches) | `excerpts/` |
| Part II complex list, with weapons (excerpt) | `section7.pdf` | 25 (43 complexes in stretches: BERDICHEV–BUKACHACHA, LEISNIG–LENINOGORSK, MOROZOVSK–MOSCOW, PEI LI–PEN CHI, POZNAN–PRAGUE, WAN HSIEN–WARSAW, SERPUKHOV–SHAKHUNYA, UKH?A (Ukhta)–ULYANOVSK, WISMAR) | `excerpts/` |
| Cross-reference list (excerpt) | `section2.pdf` | 14 (237 entries in stretches) | `excerpts/` |
| Atomic weapon requirements and summary | `section8.pdf` | 15 | read, not transcribed: every figure is redacted (b)(3), 42 USC 2168; only weapon types (Mk 6, 15, 27, 28, 36, 39, W-35, W-37) and delivery vehicles (B-47, B-52, RB-47, F-101, TM-61, Crossbow) remain |

The weapons columns (numbers and types of weapons, and which command delivers them) are
redacted in the released copy: the right half of every page is a blank box. Installation names
are not in the document; the Bombing Encyclopedia that the BE numbers point to is still
classified.

## Files

| File | One row per | Main columns |
|---|---|---|
| `complexes.csv` | complex or sub-complex header | `id` (line id of the header, e.g. `C166-L18`), `level` (complex / subcomplex), `priority`, `ref`, `name`, `name_printed`, `country`, `lat`, `lon`, `parent_id` (sub-complexes), `n_dgz`, `n_installations`, `n_population`, `n_msites`, `priority_tier`, `tier_size` |
| `dgz.csv` | designated ground zero (aim point) | `complex_id`, `label` (A, AH, BM ...), `ba` (the "BA" column: empty in Part I; Part II marks two aim points `X`), `lat`, `lon` |
| `installations.csv` | installation line | `complex_id`, `category`, `category_name`, `category_group`, `be_wac` (chart), `be_number` (blank where the print has none) |
| `msites.csv` | "M-n" site (Moscow region) | `complex_id` (blank for stand-alone rows), `top_complex_id`, `ref`, `name`, `m_number`, `lat`, `lon`, `label` |
| `airfields.csv` | Part II airfield | `priority`, `ref` (mostly the reference number of the complex the airfield serves), `name`, `country`, `be`, `lat`, `lon`, `code` (trailing letter, meaning unknown) |
| `lines.csv` | printed line, in page order | `id`, `page`, `kind` (data / header / footer / blank), `text` as printed (spacing normalised: single spaces, none around hyphens), `source` (agreed / adjudicated), `type` |
| `anomalies.csv` | line that keeps a `?` or breaks a format rule | `problem` |
| `checks.csv` | line flagged by a consistency check | `check`, `detail`, `second_look` (confirmed as printed / corrected), `second_look_note` |
| `../labels/us_1956_sac_complexes.csv` | top-level complex, in the shared label schema | see `../labels/SCHEMA.md`; DGZ and installation totals and the priority tier are in `notes` |
| `../labels/us_1956_sac_airfields.csv` | airfield, in the shared label schema | see `../labels/SCHEMA.md` |
| `audit.csv` | line of the audit sample | `curated`, `audit` (the independent re-reading), `judged` (blind judgement where they differ), `outcome` |
| `excerpts/` | the three excerpted lists and their comparison with the full lists | see "The excerpts" below and `excerpts/REPORT.md` |
| `../validation_sac1956_nsa_city_sheets.csv` | category count on the Archive's city sheets | Moscow, Leningrad, Beijing, Warsaw |

Line ids are `<page>-L<nn>`: `C` pages are the complex list (PDF page number), `A` pages the
airfield list. Every value traces back to a line id, and `lines.csv` has the printed text.
Coordinates are converted from the printed degrees and minutes (`5545-03737` is 55°45′N,
37°37′E; a `W` marks western longitudes in Chukotka). A coordinate with minutes of 60 or more
is left blank.

## How to read a complex

```
1 5150 MOSCOW 5545-03737          header: priority, reference number, name, coordinates
5545- 3737E A                     aim point (DGZ) with its letter label
208 0167-0001                     installation: category code (208 = government control
...                                centres) and BE number (chart 0167, installation 0001)
275 0167-9999                     category 275 = population; BE numbers 9xxx
KUCHINO 5545-03759                sub-complex: name and coordinates, then its own lines
```

- No country suffix means the USSR. The suffixes are `POL`, `E GER`, `GER SOVZONE` (Berlin),
  `CZECH`, `HUNG`, `RUM`, `BULG`, `ALB`, `CHINA`, `MANCH`, `N KOREA` and `N VIETNAM`. The name
  column holds 25 characters, which cuts some suffixes (`CZEC`, `CHIN`, `E GE`); `country`
  resolves them. `country` follows the printed suffix, the planners' attribution: ULAAN BAATAR
  is printed with CHINA (the label file gives Mongolia, the state that contained it).
- Reference numbers follow the alphabet. A fifth digit inserts a complex between two
  numbers: `00255` lies between `0025` and `0030`.
- **Half of the complexes have no aim point.** 608 of the 1,215 complexes have no DGZ line,
  neither their own nor in a sub-complex. They are mostly low priorities: 98% of complexes
  ranked 1–100 have a DGZ, 5% of those ranked 901–1223. North Korean, North Vietnamese and
  Albanian complexes have none. Being on the list and being given an aim point are different
  labels; `n_dgz` (with the sub-complexes' DGZs) separates them.
- **Population lines are near-universal.** 2,081 of the 2,089 complex and sub-complex blocks
  have exactly one line of category 275. SMOLENSK (priority 3), NIEDER ULLERSDORF POL, VAYENGA
  and DIOSGYOR HUNG have none; TULOMA and KAZINCBARCIKA HUNG have two (DIOSGYOR's is printed
  under its neighbour KAZINCBARCIKA); GLIWICE-SOSNOWIEC POL and HALLE-MERSEBURG E GER are
  umbrella headers whose lines are all in sub-complexes. SMOLENSK, TULOMA and KAZINCBARCIKA were
  checked on the scan and are printed that way.
- **Priorities come in tiers below the top 300.** From priority 321 down, the numbers run
  through the alphabet in long stretches (701 ABDULINO … 732 YERSHOVO, then 739 APOSTOLOVO …):
  the study ranked complexes in tiers and numbered each tier alphabetically. `priority_tier`
  groups six or more consecutive priorities in alphabetical order into one tier (by chance six
  names fall in order once in 720 tries); other complexes are tiers of their own. This finds 38
  tiers holding 692 complexes, the first starting at 321. Within a tier, the number carries no
  ranking information.
- **M-n rows** (`DEDENEVO M-29 5615-03732 QB`) are 34 sites, all 44–96 km from Moscow's
  reference point, in two bands: 17 at 44–64 km and 17 at 72–96 km. That is the pattern of
  the two rings of the Moscow surface-to-air missile system, which is probably what they are
  (an interpretation; the document does not say). A row with a reference number stands alone in
  the alphabetical order; one without belongs to the complex above it. A 35th row (KOSTINO
  M-70) has a six-digit longitude and is in `anomalies.csv`.
- **Airfield reference numbers** name the complex an airfield belongs to (all Moscow airfields
  carry 5150, MOSCOW's number); 856 of the 1,128 name a complex in Part I.

## How it was made

1. **Line images** (`scripts/sac1956_strips.py`): each page rendered at 300 dpi, character-sized
   ink components located, one band per printed line, numbered `L01`, `L02`... in a red margin.
   The bands were checked against the passes' readings: a pass added a `+` row for any printed
   line without a label.
2. **Two independent transcriptions** (`data/interim/sac1956/INSTRUCTIONS.md`), by two
   different vision-language models (Claude agents), page by page. Each pass wrote every
   character as printed, `?` for anything not legible, and was told not to correct anything or
   use knowledge of real places. Neither pass saw the other's work.
3. **Comparison** (`scripts/sac1956_compare.py`): readings normalised for spacing and hyphen
   characters; lines that differ, carry a `?`, or break a format rule (coordinates with minutes
   of 60 or more, unknown category codes, population lines without a 9xxx number) are
   disputes.
4. **Adjudication** (`data/interim/sac1956/ADJUDICATE.md`): every dispute re-read by a third
   agent on a 2.5× crop of the scan, deciding from the glyphs, with consistency inside the
   document allowed only as a tiebreaker and noted.
5. **Consistency checks** (`scripts/sac1956_assemble.py`): errors that both passes share agree
   and parse, so the assembled tables are checked across lines: aim points and sub-complexes
   far from their header, headers far from the others on their chart, chart prefixes that
   differ inside a block, duplicate or missing priorities, alphabetical and reference order,
   airfields far from the complex they reference, and names one letter away from the same
   place's name elsewhere. Every flagged line got a second look on the scan (`checkNN` batches).
6. **External check** against the Archive's city spreadsheets, an independent count of the
   same lines (REPORT.md).

The decisions, with each adjudicator's note and confidence, are in
`data/interim/sac1956/adjudicate/decisions/`; both passes are in `data/interim/sac1956/pass*/`.

## Quality

See REPORT.md for the current numbers. In brief:

- 16,046 printed lines, of which 14,904 are table rows. The two passes agreed on all but 179
  lines (1.1%). Measured against the final reading, one pass erred on 1.0% of table rows and
  the other on 0.4%, mostly B read as 8 in aim-point labels, scanner specks read as
  punctuation, and 3/5/6/8/9 or a 2 without its base bar in worn digits.
- 208 lines were decided on the scan: every dispute and the 49 lines the consistency checks
  flagged (21 lines were both). 34 ended with a reading neither pass had. The checks found 2
  errors that both passes made identically, an airfield priority and an airfield latitude, both
  on 200 dpi pages. Errors the two passes share and that break no check cannot be counted; they
  are the main residual risk, most of all for installation numbers, which nothing cross-checks.
  Three lines keep an illegible digit, and 2 coordinates are printed with impossible minutes
  (left blank in the tables).
- **Audit of the final reading.** A random 5% of the table rows (743 lines, seed 1956) was
  read again by four readers who saw neither the passes nor the final text
  (`scripts/sac1956_audit.py`, `data/interim/sac1956_excerpts/AUDIT.md`). They differed from
  the final reading on 10 lines; judged blind on the scan (the two readings shown in random
  order), the final reading was right on all 10. Residual error rate: 0 of 743, 95% interval
  0 to 0.51% (Wilson). The auditors' own error rate was 1.3%. `audit.csv` has every line.
- **Cross-document check of the airfields.** 270 airfield rows are printed twice: in the
  Part II airfield list (transcribed here in full) and in the excerpt of the Part I airfield
  list, typed separately. The two transcriptions differ on 19 rows; each pair was judged on
  both scans. 3 were misreads in the Part II transcription, all on 200-dpi pages, all now
  corrected (`check04`): BERAT/KUCOVE's longitude (01954, which also removes one of the two
  "impossible minutes"), CHANG CHIAO's letter (R) and MOZYR's latitude (5159). 12 are real
  differences between the printings, mostly an 8 in Part I where Part II has a 0 or a 9
  (AMDERMA 6945 against 5945, BIROBIDZHAN 4845 against 4945): the Part II list carries typing
  slips of its own, and the tables keep each list as printed. 4 stay unresolved (a blotted
  digit). So the residual misread rate is higher on the 200-dpi airfield pages, about 1 in 90
  rows there, than the audit's overall bound suggests.
- A pilot reading of four pages made before this pipeline (152 lines, a third independent
  read) agrees with the final reading on every character it could read.
- Anchors reproduce (the study's own totals cannot be checked: its summary pages, section 8,
  are redacted figure by figure): Moscow (priority 1) has 12 aim points and 180 installation lines, 13 and
  190 with its three suburbs; East Berlin (`BERLIN GER SOVZONE`, priority 61) has 6 aim points
  and 91 installation lines with its suburbs, the Archive's figure.
- The Archive's sheets match category by category for Warsaw, Fengtai and every Moscow and
  Leningrad suburb that is a block in the list, except Sablino, whose railroad yard the sheet
  codes 350 (Caucasus region) and the list prints as 358 (Northern region). Moscow's own block
  has 2 lines more than its sheet, Peiping 1 fewer, and Leningrad 6 fewer (one each of six
  categories). Leningrad's pages are complete and their BE numbers run on without a break, so
  the difference is not a lost page. The sheets have slips of their own (they give Mishutkino,
  an M-site row without installation lines, a railroad yard and a population line).

## Known gaps and quirks

- **A printed page is missing between PDF pages 9 and 10**, and PDF page 46 is a second scan
  of page 45 in its place (the duplicate's lines are in `lines.csv`, type `duplicate of page
  C045`, but not in the tables). The missing page held the rest of ARTSIZ's block and the
  complexes from ARTSIZ to ATBASAR. The airfield list names three of them by reference number:
  ARZAMAS (0310), ASHKHABAD (0330) and ASTRAKHAN (0340). Page 10 opens inside a complex on
  chart 0248 with the sub-complex ILINKA beside Astrakhan; its lines sit under a placeholder
  (`C010-L04-lost`). ASTRAKHAN, ASHKHABAD and ARZAMAS were therefore almost certainly on the
  list, but their entries are lost. Places whose name falls in this stretch of the alphabet get
  no label in the models (see the label code in `nucprob/labels/sac1956.py`).
- **The scan of PDF page 64 is cut off at the foot.** Page 65 opens inside a complex whose
  header was on the lost strip: a Bulgarian complex (chart 0322, sub-complex GORNA
  ORYAKHOVITSA BULG) that sorts between DROGOBYCH and DUBNICE NAD VAHOM. Its lines sit under
  a placeholder complex without name or coordinates (`C065-L04-lost`), which is left out of the
  label file. It is probably priority 1054, the only number missing from its alphabetical tier
  (between DORONINSKOYE 1053 and DUBOSSARY 1055).
- **Priority numbers not found** in the complex list: see REPORT.md (after the checks: 97, 303,
  530, 603, 766, 872, 1220, and 1054 above). Most are likely on the missing page (ASTRAKHAN,
  ASHKHABAD, ARZAMAS and possibly others in that stretch). A check of every page break (the chart
  number of the lines that continue a block against the location of its header, and reference
  numbers that run on) finds no other gap.
- **Lower-resolution scans.** Nine pages of the complex list (PDF pages 1, 2, 8, 9, 32–34, 112
  and 113) and 11 of the 43 airfield pages (1, 2, 4–6, 20, 23, 24, 27, 29, 30) were scanned at
  about 200 dpi, against 300 dpi or more for the rest. 22 of the 24 airfield lines that ended
  with a reading neither pass had, and all three illegible digits, are on those pages.
- **Strips start 250 px from the left edge of a page.** On pages shifted left this cut the
  first digits of two priorities (VLADIVOSTOK 19, VLADIMIR VOLYNSKIY 1094); both were read in
  full on the source PDF. In the complex list, unique priorities rule out the same problem
  elsewhere: every small number is taken, so a cut number would duplicate another.
- **The cross-reference excerpt does not reach the lost page**: it covers ABAKAN to ALTENHAIN
  and then jumps to LEBA, so it cannot restore the complexes from ARTSIZ to ATBASAR.
- Lines whose print is unclear keep a `?` and are listed in `anomalies.csv`.
- What the DGZ letter labels mean (A, AH, BM ...; Q-labels for M-sites), what the airfield
  trailing letters mean (R, S, T ...), and why some airfield priorities carry an `A` (typed in
  later, in a different typeface) is not explained in the released pages.

## The excerpts (`excerpts/`)

The Archive published the Part I airfield list, the Part II complex list and the
cross-reference list only in excerpt. They went through the same pipeline
(`data/interim/sac1956_excerpts/`: two passes by different models, 92 disputes adjudicated on
the scan, a second look at the lines that break a rule) and are parsed by the same code
(`scripts/sac1956_excerpts.py`, which also writes `excerpts/REPORT.md`). Of 1,899 table rows,
pass A erred on 3.0% and pass B on 2.2%, against 1.0% and 0.4% on the full lists: these scans
are poorer. 12 lines keep a `?` (`excerpts/anomalies.csv`).

| File | One row per |
|---|---|
| `part2_complexes.csv`, `part2_dgz.csv`, `part2_installations.csv` | Part II complex or sub-complex, aim point, installation line (same columns as the Part I tables; `part1_id`: the Part I row it repeats; `part1_owner`: the Part I complex of lines at the top of a page that continue a complex begun on an unpublished page) |
| `part2_vs_part1.csv` | Part II complex beside the Part I complex of the same reference: `seen_whole`, aim points and installation lines kept, dropped and added |
| `part1_airfields.csv`, `part1_vs_part2_airfields.csv` | Part I airfield row; beside its Part II row, with the cross-document verdict |
| `crossref.csv` | cross-reference row: `level` (entry, with a reference number, or listed under one), `airfield` (AF), `see_ref`/`see_name` (SEE: the place is targeted under another complex) |
| `lines.csv`, `anomalies.csv` | as for the full lists |

What they show:

- **Part II is Part I with fewer aim points.** Every Part II complex in the excerpt is a Part I
  complex with the same reference number and the same priority, in the same order, and its
  installation lines are nearly the same: 554 of 569 recur in the 33 complexes seen whole
  (the others are one-character differences in Part II's blurred print, and 7 lines added to
  Leningrad). The aim points are not: those 33 complexes have 65 in Part I and 24 in Part II;
  19 are kept, 46 dropped and 5 are new points (Leningrad M and AM, Ulan Ude D, and new
  coordinates for Shakhty B and Leninakan R). Aim points, Part II against Part I: Leningrad 5
  and 9, Budapest 4 and 11, Berlin 5 and 6, Ulan Ude 1 and 4; among complexes cut by a skipped
  page (so the Part II count is a floor), Moscow 6 and 13, Prague 6 and 15, Warsaw 1 and 8.
  Of the 11 whole complexes with a single aim point in Part I, 9 have none in Part II.
- **Who keeps an aim point follows the Part I priority.** All 16 excerpted complexes ranked
  1 to 236 keep at least one; of the 13 ranked 295 to 834, only Ukhta (592) and Leninakan
  (738, at a new point) do (`excerpts/REPORT.md` has the table). Part II was the study's
  "desired stockpile" allocation, Part I's the unconstrained one: with fewer weapons, the
  plan concentrated them on the top of the priority list and thinned the aim points inside the
  biggest cities.
- **The Part II label.** `../labels/us_1956_sac_part2_complexes.csv` has the excerpted
  complexes in the shared schema (`selected` = 1 if the complex keeps an aim point). In the
  modelling table (`nucprob.labels.sac1956.part2_labels`), `part2_has_dgz` is 1 for a
  settlement that keeps an aim point in Part II, 0 for one known to have none (every
  settlement with no Part I entry, since Part II lists only Part I complexes, and the entries
  of complexes seen whole), and blank where the excerpt does not show it. In the universe it
  is known for about 1,400 settlements, 28 of them positive: enough to describe, not to model.
- **Two Part II aim points carry an X** in the "BA" column (LENINAKAN R, WARSAW T). What it
  marks is not explained in the released pages.
- **The Part I airfield list** prints the same airfields, with the same priorities and BE
  numbers, as the Part II list for all 270 rows in the excerpt (see the cross-document check
  under Quality).
- **The cross-reference list** maps every reference number to a name and lists the places and
  airfields under it. 99 of its 237 entries are `SEE` rows: a place targeted as part of another
  complex (MONINO AF SEE 5570 NOGINSK); 95 of those point to a Part I complex. Six entries
  carry a reference number that is no Part I complex (AFRIKANDA, SHABSKIY, SHCHUCHIN, SHANG
  JAO, WEI HAI WEI and one with an illegible name); the airfield list uses the first three
  for its airfields, so these are references that exist for airfields alone.

## Licence and citation

The study is a US government record and in the public domain. Cite it as: Strategic Air
Command, *SM-129-56, Atomic Weapons Requirements Study for 1959*, 15 June 1956, National
Archives, Record Group 342; published in William Burr (ed.), "U.S. Cold War Nuclear Target
Lists Declassified for First Time", National Security Archive Electronic Briefing Book No. 538
(2015). The transcription, scripts and checks are part of this repository.
