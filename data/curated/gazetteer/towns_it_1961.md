# Italy, census of 15 October 1961: comuni of 10,000+

File: `towns_it_1961.csv`, 814 rows. Each row is a comune (municipality) with a resident population (*popolazione residente*, the legal population) above 10,000 at the 10° Censimento generale della popolazione, 15 October 1961.

## Source

- **ISTAT, *10° Censimento generale della popolazione, 15 ottobre 1961*, Vol. I *Dati riassuntivi comunali e provinciali sulla popolazione e sulle abitazioni* (Roma, 1963)**
  - Tav. 7, "Popolazione residente, popolazione presente, abitazioni, per comune", PDF pp. 40-158. It gives M, F and MF for every comune, at the boundaries of the census date.
  - Download: https://ebiblio.istat.it/digibib/Censimenti%20popolazione/censpop1961/IST0005323Vol1_Dati_Riassuntivi_Comunali_e_Provinciali_Popolazione_e_Abitazioni+OCRottimizz.pdf
  - Saved as `data/raw/italy/IST0005323Vol1_Dati_Riassuntivi_Comunali_e_Provinciali.pdf`.
- **Cross-check only:** ISTAT (1994), *Popolazione residente dei comuni, censimenti dal 1861 al 1991*. Its figures are recomputed to 1991 boundaries, so no value in the table comes from it.
  - https://ebiblio.istat.it/digibib/Censimenti%20popolazione/Censimentipopolazioneresidentedal1861/RML0050288Pop_res_cens_1861_1991.pdf
- **Names today:** the ISTAT list of comuni, https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv
- `data/raw/italy/SOURCES.tsv` lists every file and URL.

## Columns

- `pop` is MF *residente*, as printed in Tav. 7.
- `name` is the 1961 name in today's standard spelling. The table prints stress marks that are not part of the name (e.g. "Cùneo", "Pàdova"); these are dropped.
  - Where the name has changed since 1961, `name` keeps the 1961 form and `name_today` gives the current one (23 rows). Examples: Resina → Ercolano, Nicastro and Sambiase → Lamezia Terme, Darfo → Darfo Boario Terme, Riva → Riva del Garda, Iesolo → Jesolo, San Remo → Sanremo, Piedimonte d'Alife → Piedimonte Matese, Rossano and Corigliano Calabro → Corigliano-Rossano.
- `admin1` is the 1961 province. There were 92, in ISTAT order: Pordenone, Isernia, Oristano and the later provinces did not yet exist.
  - The Valle d'Aosta had no province and is entered as `Valle d'Aosta`.
  - The region is in `notes`, under its 1961 name. Abruzzi and Molise were still one region ("Abruzzi e Molise").
- `admin1_seat` is set for all 92 province capitals. Massa is the seat of Massa-Carrara and Pesaro the seat of Pesaro e Urbino.
- `capital` is 1 for Roma only.
- `source_page` is the PDF page number, not the printed page.

## How it was read

The PDF is a scan with a poor embedded OCR layer. I read Tav. 7 twice: once from the embedded layer (`pdftotext -layout`) and once by re-running tesseract on the page images. Both readings are in `data/raw/italy/`. The `notes` column says how each row was confirmed:

| Confirmation | Rows |
|---|---|
| Both readings agree, and M+F=MF | 477 |
| One reading, with M+F=MF checked | 278 |
| Row number illegible but M+F=MF holds | 18 |
| Read from the page image, or rebuilt from M+F=MF after the image was checked | 41 |

The build scripts are in `data/raw/italy/build_scripts_1961/`.

## Checks

- **Against the census's own size-class table (Vol. I, Tav. 4, PDF pp. 28-31).**
  - Italy had 8,035 comuni, of which 814 had more than 10,000 people. The table has 814 rows.
  - The count and population match ISTAT's figures exactly in every class above 10,000: 10,001-15,000 (353 comuni, 4,259,679 people), 20,001-30,000, and so on up to "oltre 500.000" (6 comuni, 7,351,510).
  - In the 15,001-20,000 class the count matches (135). The printed population is cut off in the scan after "2.313.2", which agrees with 2,313,290.
  - No comune had exactly 10,000 people, so the 10,001 lower bound of the classes does not change anything.
- **Totals.** The rows sum to 30,352,248, which is 60.0% of the 1961 resident population of 50,623,569.
- **Largest cities and capitals.** The national capital is present: Roma, 2,188,160. Milano, Napoli, Torino, Genova and Palermo are present, and so are all 92 province seats.
- **Completeness.** Every comune listed above 10,000 in 1961 in the 1991-boundary series is either in the table or is explained in the doubts below.
- **Single-reading rows.** I checked a sample of rows that only one reading confirmed against the page image (Fivizzano, Maddaloni, Castellana Grotte, Paceco, among others). All were correct.

## Doubts and notes

- **Boundaries.** All figures are for the comune as it stood on 15 October 1961.
  - Several comuni later lost territory. Examples: Marino (Ciampino split off in 1974), Gragnano, Boscotrecase, Sessa Aurunca, Carinola, Mesola, Carmignano, Siracusa, Cagliari, Nardò, Pachino, Bronte and Caltagirone. Their 1961 figures are therefore larger than the 1991-boundary series, and `notes` says so for these rows.
  - Busto Garolfo is printed as 12,099, but the 1991-boundary series has 8,720. Both readings agree on 12,099, so it is kept.
- **Comuni missing because they did not yet exist.**
  - Ciampino was part of Marino.
  - Lamezia Terme did not exist; Nicastro and Sambiase appear separately.
- **Misprints in the source**, where the printed MF is kept:
  - Taggia: M+F = 10,891, but MF is printed as 10,896.
  - Terranuova Bracciolini: the name is misprinted "Terrnauova", and M+F = 10,021, but MF is printed as 10,076.
- **One page has its numbers shifted by a row** (PDF p. 80, Pavia). Vigevano (57,069) and Voghera (35,747) were assigned from the page image.
- **Two comuni with the same figure.** Spinea and Santo Stino di Livenza (both Venezia province) are both 10,565. This is correct: I checked it on the page image and against Tav. 4.
