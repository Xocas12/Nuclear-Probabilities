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
| Part I airfield list, Part II complex list, cross-reference list | sections 4, 7, 2 | excerpts only | not transcribed |

The weapons columns (numbers and types of weapons, and which command delivers them) are
redacted in the released copy: the right half of every page is a blank box. Installation names
are not in the document; the Bombing Encyclopedia that the BE numbers point to is still
classified.

## Files

| File | One row per | Main columns |
|---|---|---|
| `complexes.csv` | complex or sub-complex header | `id` (line id of the header, e.g. `C166-L18`), `level` (complex / subcomplex), `priority`, `ref`, `name`, `name_printed`, `country`, `lat`, `lon`, `parent_id` (sub-complexes), `n_dgz`, `n_installations`, `n_population`, `n_msites`, `priority_tier`, `tier_size` |
| `dgz.csv` | designated ground zero (aim point) | `complex_id`, `label` (A, AH, BM ...), `lat`, `lon` |
| `installations.csv` | installation line | `complex_id`, `category`, `category_name`, `category_group`, `be_wac` (chart), `be_number` (blank where the print has none) |
| `msites.csv` | "M-n" site (Moscow region) | `complex_id` (blank for stand-alone rows), `top_complex_id`, `ref`, `name`, `m_number`, `lat`, `lon`, `label` |
| `airfields.csv` | Part II airfield | `priority`, `ref` (mostly the reference number of the complex the airfield serves), `name`, `country`, `be`, `lat`, `lon`, `code` (trailing letter, meaning unknown) |
| `lines.csv` | printed line, in page order | `id`, `page`, `kind` (data / header / footer / blank), `text` exactly as printed, `source` (agreed / adjudicated), `type` |
| `anomalies.csv` | line that keeps a `?` or breaks a format rule | `problem` |
| `checks.csv` | line flagged by a consistency check | `check`, `detail` |
| `../labels/us_1956_sac_complexes.csv` | top-level complex, in the shared label schema | see `../labels/SCHEMA.md` |
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

- No country suffix means the USSR. Suffixes are as printed (`POL`, `E GER`, `GER SOVZONE`
  for Berlin, `CZECH`, `HUNG`, `RUM`, `BULG`, `ALB`, `CHINA`, `MANCH`, `N KOREA`, `VIETNAM`).
  The name column holds 25 characters, which cuts some suffixes (`CZEC`, `CHIN`, `E GE`);
  `country` resolves them.
- Reference numbers follow the alphabet. A fifth digit inserts a complex between two
  numbers: `00255` lies between `0025` and `0030`.
- **Half of the complexes have no aim point.** 609 of the 1,216 complexes have no DGZ line,
  neither their own nor in a sub-complex. They are mostly low priorities: 98% of complexes
  ranked 1–100 have a DGZ, 5% of those ranked 901–1223. North Korean, North Vietnamese and
  Albanian complexes have none. Being on the list and being given an aim point are different
  labels; `n_dgz` (with the sub-complexes' DGZs) separates them.
- **Priorities come in tiers below the top 300.** From priority 321 down, the numbers run
  through the alphabet in long stretches (701 ABDULINO … 732 YERSHOVO, then 739 APOSTOLOVO …):
  the study ranked complexes in tiers and numbered each tier alphabetically. `priority_tier`
  groups six or more consecutive priorities in alphabetical order into one tier (by chance six
  names fall in order once in 720 tries); other complexes are tiers of their own. Within a tier,
  the number carries no ranking information.
- **M-n rows** (`DEDENEVO M-29 5615-03732 QB`) are 34 sites, all 44–96 km from Moscow's
  reference point, in two bands: 16 at 44–64 km and 18 at 72–96 km. That is the pattern of
  the two rings of the Moscow surface-to-air missile system, which is probably what they are
  (an interpretation; the document does not say). A row with a reference number stands alone in
  the alphabetical order; one without belongs to the complex above it.

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
  lines (1.1%). Measured against the final reading, one pass erred on about 1 line in 100 and
  the other on 1 in 260, mostly B read as 8 in aim-point labels, scanner specks read as
  punctuation, and 3/5/6/8/9 in worn digits.
- Anchors reproduce: Moscow (priority 1) has 12 aim points and 180 installation lines, 13 and
  190 with its three suburbs; East Berlin (`BERLIN GER SOVZONE`, priority 61) has 6 aim points
  and 91 installation lines with its suburbs, the Archive's figure.
- The Archive's sheets match exactly for Warsaw, Fengtai and every Moscow and Leningrad suburb
  that is a block in the list. Moscow's own block has 2 lines more than its sheet, Peiping 1
  fewer, and Leningrad 6 fewer (one each of six categories). Leningrad's pages are complete and
  their BE numbers run on without a break, so the difference is not a lost page. The sheets have
  slips of their own (they give Mishutkino, an M-site row without installation lines, a
  railroad yard and a population line).

## Known gaps and quirks

- **PDF page 46 is a second scan of page 45.** Its lines are in `lines.csv` (type
  `duplicate of page C045`) but not in the tables.
- **The scan of PDF page 64 is cut off at the foot.** Page 65 opens inside a complex whose
  header was on the lost strip: a Bulgarian complex (chart 0322, sub-complex GORNA
  ORYAKHOVITSA BULG) that sorts between DROGOBYCH and DUBNICE NAD VAHOM. Its lines sit under
  a placeholder complex without name or coordinates (`C065-L04-lost`), which is left out of the
  label file. It is probably priority 1054, the only number missing from its alphabetical tier
  (between DORONINSKOYE 1053 and DUBOSSARY 1055).
- **Priority numbers not found** in the complex list: see REPORT.md (after the checks: 97, 303,
  530, 603, 766, 872, 1220, and 1054 above). Either the complexes are not in Part I or their
  headers are lost; no page break shows a gap.
- **Lower-resolution scans.** Nine pages of the complex list (PDF pages 1, 2, 8, 9, 32–34, 112
  and 113) and 11 of the 43 airfield pages were scanned at about 200 dpi, against 300 dpi or
  more for the rest; readings there are less certain.
- **Strips start 250 px from the left edge of a page.** On pages shifted left this cut the
  first digits of two priorities (VLADIVOSTOK 19, VLADIMIR VOLYNSKIY 1094); both were read in
  full on the source PDF. In the complex list, unique priorities rule out the same problem
  elsewhere: every small number is taken, so a cut number would duplicate another.
- Lines whose print is unclear keep a `?` and are listed in `anomalies.csv`.
- What the DGZ letter labels mean (A, AH, BM ...; Q-labels for M-sites), what the airfield
  trailing letters mean (R, S, T ...), and why some airfield priorities carry an `A` (typed in
  later, in a different typeface) is not explained in the released pages.

## Licence and citation

The study is a US government record and in the public domain. Cite it as: Strategic Air
Command, *SM-129-56, Atomic Weapons Requirements Study for 1959*, 15 June 1956, National
Archives, Record Group 342; published in William Burr (ed.), "U.S. Cold War Nuclear Target
Lists Declassified for First Time", National Security Archive Electronic Briefing Book No. 538
(2015). The transcription, scripts and checks are part of this repository.
