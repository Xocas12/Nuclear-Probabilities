# NAPB-90 county table: data card

FEMA's *Nuclear Attack Planning Base - 1990* (NAPB-90, Final Project Report, April 1987;
released under FOIA in 2005) modelled a Soviet attack on the United States "based on Soviet
doctrine" for civil-defence planning. Annex A, Part 2, "Highest Direct Effects Risk by County",
gives for every county the highest blast overpressure it would see anywhere within it, with the
county's whole estimated 1985 population and land area printed in that band's column. This
folder is a complete transcription of those tables: every county of the 50 states and DC.

Provenance: **defender**. This is the US government's own expectation of where a Soviet attack
would fall, not a Soviet plan. The attack behind it is NAPB-90's set of aim points (an initial
6,139 in ten classes, edited; see `data/notes/civil_defence.md` section 1a), which was not
released. The county band is therefore a derived label: it says that some aim point's blast
reaches the county, not that the county was itself a target.

## Files

| File | One row per | Columns |
|---|---|---|
| `counties.csv` | county, parish, borough, census area or independent city (3,142 rows) | `state`, `county_printed` (as printed, typos kept), `fips` (1990 FIPS code, matched by name), `census_name`, `band` (highest risk: very high >=10 psi, high 5-10, medium 2-5, low 0.5-2, no <0.5), `band_rank` (4 to 0), `pop_1985_napb` and `area_sqmi` (as printed), `census_pop_1985` (Census Bureau intercensal estimate, July 1985), `pop_ratio`, `page` (PDF page), `printed_page` |
| `state_totals.csv` | state | the printed TOTAL STATE row and the page header (estimated 1985 population, land area) |
| `checks.csv` | failed check | column sums that differ from the printed total, split lines, counties far from the census estimate, rows without a census match |
| `REPORT.md` | | counts by band |
| `../labels/cd_1987_napb90_counties.csv` | county | the same table for the label inventory (`provenance` defender) |

The earlier 33-row pilot (`../labels/cd_1987_napb90_county_pilot.csv`) is superseded.

## How it was made

1. **Pages.** PDF pages 135-292 of the compilation in `data/raw/civil_defence/` (1-bit, 200 ppi,
   scanned on their side) rendered upright (`scripts/napb90_pages.py`).
2. **Two independent transcriptions** (`data/interim/napb90/INSTRUCTIONS.md`), one by each of two
   models, eight pages per worker, each worker checking its column sums against the printed
   totals and re-reading failures on enlarged images.
3. **Comparison** (`scripts/napb90_compare.py`). The passes agree on **every figure** of all 158
   pages (3,519 rows). They differ on 20 cells: two county names (pass 1 keeps the printed
   misspellings "Schuykill" and "East Carrol", checked on the scan) and the star on summary and
   total rows, which is not used. The final reading is pass 1.
4. **Checks** (`checks.csv`):
   - 81 column sums and 9 split lines differ from the printed totals. Both passes read the same
     figures, and the workers re-read every failing column enlarged: these are slips in FEMA's
     tables. Many are equal and opposite between two bands of the same state (Indiana's very
     high and low/no population both off by 699,400; South Carolina by 117,319, Berkeley
     County's population), which suggests that totals were computed before some counties were
     moved between bands.
   - Each county's printed population was compared with the Census Bureau's estimate for 1985
     (`nucprob/sources/census_us.py`, `data/raw/census/e8089co.txt`). The median ratio is close
     to 1 (1.013; 90% of counties within 0.96-1.07; NAPB's figures are an earlier projection); five counties are off by a third or more,
     all printed as transcribed: Kent DE 15,037 (census 102,818; the state total and header
     include the slip), Alachua FL 789,260 (169,515), Martin KY 1,063 (13,869), Columbiana OH
     11,603 (109,127), and Valencia NM, split in 1981 (NAPB used the earlier county).
   - Unmatched: Alaska's Aleutian Islands census area (split in 1987) and the territories.

## Contents

| Highest risk band | Counties | 1985 population (NAPB) | Share |
|---|---|---|---|
| very high (>=10 psi) | 730 | 160.3 m | 67.0% |
| high (5-10 psi) | 88 | 7.2 m | 3.0% |
| medium (2-5 psi) | 245 | 15.0 m | 6.3% |
| low (0.5-2 psi) | 666 | 24.4 m | 10.2% |
| no (<0.5 psi) | 1,411 | 32.2 m | 13.5% |

## Caveats

- **Not a target list.** A county is in a band because some aim point's blast reaches part of
  it. Large western counties reach "very high" from a single missile field or base; a county
  with one city may be "very high" over a few square miles only. The band says nothing about
  how much of the county is affected.
- **Rule-based classes.** NAPB-90's refinery, power and chemical classes were selected by rule
  (capacity, industry code; `data/notes/civil_defence.md` 1a), so part of the pattern is a rule
  applied to the industrial map, not judgment. There is no population class.
- **Puerto Rico and the Virgin Islands** print "DATA WILL BE FURNISHED SEPARATELY"; the Pacific
  territories have one row each with 1980 populations.
- **Interim data.** The table of contents marks Arkansas, Louisiana, Oklahoma, Texas,
  Mississippi and Kansas as "Interim data; to be corrected" (in Annex B; the same caution may
  apply here).
- Annex B (fallout risk by county, PDF pp. 293-508) is not transcribed.

## Citation

Federal Emergency Management Agency, *Nuclear Attack Planning Base - 1990, Final Project
Report*, April 1987, Annex A; FOIA release, 27 April 2005. Census Bureau, *Intercensal Estimates
of the Resident Population of States and Counties 1980-1989* (1992); cartographic boundary file
co99_d90 (1990).
