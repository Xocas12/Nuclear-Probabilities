# Netherlands, census of 31 May 1960: municipalities of 10,000+

**File:** `towns_nl_1960.csv`. There are 220 rows: 219 municipalities (gemeenten) and the Noordoostelijke Polder.

## Source
- CBS, *13e Algemene Volkstelling, 31 mei 1960*, Deel 2, *Bevolking van gemeenten en plaatsen*, **Tabel 1** ("bevolking, oppervlakte en bevolkingsdichtheid van de gemeenten ..., per provincie in alfabetische volgorde"), column 2 (*Inwonertal*). The table runs over printed pp. 22-66. `source_page` gives the printed page.
- Scan source: DANS dataset "13th General population census May 31, 1960", doi:10.17026/DANS-XSC-VKWS (CC-BY-4.0).
  - Volume PDF: https://ssh.datastations.nl/api/access/datafile/290666, saved as `data/raw/netherlands/VT_1960_02.pdf`. Its OCR text is in `vt02.txt`; the OCR is noisy.
  - Dataset metadata: https://ssh.datastations.nl/api/datasets/:persistentId/?persistentId=doi:10.17026/DANS-XSC-VKWS, saved as `dans_xsc_vkws.json`.
  - Volume overview: https://ssh.datastations.nl/api/access/datafile/291075, saved as `vt1960_overzicht.pdf`.
- The figures were transcribed by eye from 220-dpi renders of column 2, not taken from the OCR.

## Coverage
- Units are gemeenten as they stood on 31 May 1960, with the boundaries of that date.
- The threshold is 10,000 or more inhabitants; the smallest row is Wildervank, with 10,001.
- `admin1` is the provincie. The Noordoostelijke Polder was then a Rijk-administered public body outside any province, so its `admin1` is empty. It joined Overijssel in 1962.
- `capital`: Amsterdam. 's-Gravenhage is coded as the provincial seat of Zuid-Holland and as the seat of government, but not as the capital.
- `notes` record later mergers and renames.

## Checks
- **Size-class totals.** The rows were checked against Staat 1 of the same volume (p. 12, gemeenten by size class per province).
  - Every province's count and population sum match exactly.
  - Groningen 10, Friesland 15, Drenthe 7, Overijssel 23, Gelderland 34, Utrecht 10, Noord-Holland 29, Zuid-Holland 35, Zeeland 4, Noord-Brabant 31, Limburg 21: 219 in all.
  - Their total is 8,564,560. Adding the NOP (28,545) gives the row total of 8,593,105.
- **National share.** The national total is 11,461,964 in 992 municipalities, so the rows hold 75.0% of the population.
- **Largest cities.** Amsterdam 864,747, Rotterdam 729,030, 's-Gravenhage 605,136, Utrecht 255,021, Haarlem 169,220 and Eindhoven 167,577 are all present.

## Doubts
- Many units are rural municipalities with dispersed villages, such as Friesland's -deel municipalities, Emmen, Hardenberg and Haarlemmermeer. They are not towns in the urban sense.
- The Zuidelijke IJsselmeerpolders (863 inhabitants) are excluded because they fall below the threshold.
