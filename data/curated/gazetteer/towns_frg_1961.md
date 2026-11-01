# towns_frg_1961: West Germany (FRG including West Berlin), census of 6 June 1961

**File:** `towns_frg_1961.csv`, 583 rows, one per Gemeinde of 10,000 or more on the boundaries of
6 June 1961. That is the whole table the volume prints.

**Source:** Statistisches Bundesamt, *Fachserie A, Bevölkerung und Kultur. Volkszählung vom 6. Juni
1961, Vorbericht 3: Wohnbevölkerung der Gemeinden mit 10 000 und mehr Einwohnern* (June 1962).
Table 2, pp. 8-20. Retrieved 2026-11-01 from statistischebibliothek.de; manifest entry
`census_frg_1961`. The site states "Alle Rechte vorbehalten", so the PDF is not committed: the table
holds the published population figures and the page they are on.

**Figures are preliminary.** The Vorbemerkung calls the 1961 figures "vorläufige Ergebnisse". They
differ slightly from the final census (West Berlin 2,197,607 here, 2,197,408 final; München
1,084,474 here, 1,085,014 final). Features use the log of population, so this does not matter to
them. The table is used because it is the published list of all towns at that threshold.

## How it was read

The PDF is a scan with an OCR text layer. `scripts/frg_1961_read.py` reads table 2 by word position
and `scripts/frg_1961_build.py` applies `frg_1961_corrections.csv`: 54 entries, of them one row
the OCR lost (no. 488, Bad Segeberg), 5 figures and 48 names. Figures and the lost row were read on
the page image. Most name corrections were read from the OCR spelling and not each looked up on the
scan; every name that then reached a place in GeoNames is in the next section.

## Checks

- **Printed total.** Table 1 (p. 6) gives 29,720.5 thousand people in the 582 towns outside Berlin.
  This table sums to 29,720,480.
- **Order.** Table 2 prints towns in descending order of population. One row breaks it, as printed:
  Saarbrücken, 130,705, after Recklinghausen, 130,581 (read on the scan). The check also caught a
  misread of Espelkamp, now 10,454 from the scan.
- **Land by Land.** Table 1 prints the number of towns and thousands of people per Land. Every Land
  matches on towns; on people all are within 0.15 thousand except Schleswig-Holstein, 1,176.9
  against 1,176.5, not explained. `scripts/frg_1961_build.py` prints the comparison.
- **Land column.** Printed Land brackets span rows and the OCR keeps one token for a bracket. A row
  with no token takes its Land from GeoNames, and five were set by location and Table 1's totals
  (`LAND_READ` in the script). `admin1` uses GeoNames' spelling of the Land, because the town match
  prefers a hit in its own unit.
- **Not checked figure by figure.** 34 rows have no support from the printed percentages, because
  column runs in the OCR break those figures. The order check and the totals bound them.

## Conventions

- `name` is as printed without the suffix ("Stadt"), and with "X, Bad" written "Bad X".
- `name_today` carries a today's name where the printed form does not reach GeoNames, mostly towns
  merged after 1961, taken from the earlier Wikipedia-based table or the script's `TODAY` list.
- `capital` = 1 for Bonn. `admin1_seat` = 1 for the 11 Land capitals.
- **Coordinates are today's GeoNames points** (`nucprob/transfer/places.py`). West Berlin takes
  Berlin's point, which lies in the former East: it is the only place where that matters by more
  than a few km, and its distances are good to about 15 km. Schloß Neuhaus, which GeoNames does not
  hold, has a hand point in `transfer_links.csv`.
- Towns merged after 1961 often have no population in GeoNames today, so their match rests on the
  name and Land alone.

## What it replaced

`frg_1961_wikipedia.csv` is the earlier fallback: 356 of the 583 towns (about 60%) from
de.wikipedia's tables, withheld from the universe for that reason. It now serves only as a source
of `name_today`.
