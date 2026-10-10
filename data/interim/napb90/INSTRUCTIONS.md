# Transcribing the NAPB-90 county tables (Annex A, direct effects risk)

You are transcribing tables from FEMA's *Nuclear Attack Planning Base - 1990* (1987; released
under FOIA, public domain) for a historical research dataset. Every digit matters.

Your prompt gives you a **chunk file** (a JSON list of page names) and an **output directory**.

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push. Create the
  output directory if needed.
- Each page is `data/interim/napb90/pages/<name>.png` (upright, 2200×1700). Read it with the
  Read tool. To check a figure, enlarge part of it, e.g.
  `convert data/interim/napb90/pages/A139.png -crop 900x500+1100+400 -resize 160% <your scratch dir>/z.png`
  (make your own scratch dir under
  `/tmp/claude-0/-home-user/5dc41ab3-0c21-52fc-847b-369ea7502809/scratchpad/napb_<chunk>/`;
  other workers use the scratchpad too).
- Open only this file, your chunk file, the page images, and your own output files.

## What the pages look like

Each table has a name column and four risk bands, each with POPULATION and AREA (square miles):
VERY HIGH (GT 10 PSI), HIGH (5-10 PSI), MEDIUM (2-5 PSI), LOW/NO* (0.5-2 PSI). On county pages
a county's figures appear in **one** band only; the other bands are a row of dots. Numbers are
printed with a space as thousands separator (`1 337 360`). An `*` after an area in the LOW/NO
column means "less than .5 psi" (no risk). `---` means none.

Page types: `national` (NATIONAL ... SUMMARY, rows are FEMA regions), `region` (FEMA REGION ...
SUMMARY, rows are states), `state` (STATE OF ..., rows are counties, independent cities,
parishes, boroughs), `other` (anything else, e.g. "DATA WILL BE FURNISHED SEPARATELY").

Under a total row, the LOW/NO column often has two parenthesised lines: `( 230 026  7 074)` is
the low-risk part, `( 175 491  7 166)*` the no-risk part.

## Output: one file per page, `<output dir>/<page>.tsv`, tab-separated, no header

First line: `#page	<type>	<title exactly as printed>	<printed page number, e.g. A-91>`
Then, if printed: `#header	<estimated 1985 population, digits only>	<land area, digits only>`
Then one line per printed row, top to bottom, 11 tab-separated fields:

`kind	name	vh_pop	vh_area	h_pop	h_area	m_pop	m_area	l_pop	l_area	star`

- `kind`: `county` (a row of a state table), `row` (a region or state row of a summary
  table), `total` (STATE TOTAL, TOTAL STATE, TOTAL REGION ..., NATIONAL), `split` (a
  parenthesised line under a row).
- `name`: exactly as printed, typos included (`Knos`, `Osford`). Empty for `split`.
- Numbers: digits only, spaces removed (`1 337 360` → `1337360`). Leave a field empty where
  the band is dots or blank; write `---` where `---` is printed. `?` for each digit you cannot
  read with confidence. Never guess a digit from what a total "should" be.
- Put each figure in the band whose column it is printed under. Check against the column
  headings, not the order of numbers: a county whose figures sit under MEDIUM RISK has only
  `m_pop` and `m_area`.
- `split` lines: only `l_pop`, `l_area`, and `star` = 1 if the line ends with `)*`, else 0.
- `star`: 1 if the LOW/NO area of the row has a `*`, else 0 (for all kinds).

**Column placement is the commonest error.** A county's figures sit at the right end of its
row of dots: the band is the column whose heading is directly above the figures (compare their
x position with the POPULATION/AREA headings, and with the total row at the foot of the page),
not the first band after the name. A county with figures far to the right is LOW/NO; one with
figures just right of the names is VERY HIGH. When unsure, enlarge the row together with the
column headings.

## Check every page before moving on

On a state page with a total row, add up each column of the county rows (all pages of the state
in your chunk; a state that began in an earlier chunk cannot be checked by you) and compare
with the total row; also check that the two `split` lines add up to the LOW/NO total. Where
a sum is off, look again at the figures of that column on the image (enlarge) and correct
misreads. If the sum is still off and the image is clear, keep what is printed: printed
tables can carry slips.

## Final message (under 150 words)

Pages written, their types and states, the checks that pass and fail (with the column and the
difference), and the time taken.
