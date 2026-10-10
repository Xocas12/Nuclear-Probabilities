# Belgium, census of 31 December 1961: communes of 10,000+

**File:** `towns_be_1961.csv`. It has 172 rows, one per commune (*gemeente*) with 10,000 or more inhabitants. Communes are as they stood on 31 December 1961, before the 1964-1977 mergers and the 1983 Antwerp merger.

## Source

- Institut National de Statistique, *Recensement général de la population au 31 décembre 1961*, **Tome I: Chiffres de la population** (Brussels, 1963).
  - Table used: Deuxième partie, **Tableau I**, "Population, étendue territoriale, nombre de propriétaires, densité de la population, revenu imposable et nombre de parcelles cadastrales. Chiffres par commune au 31 décembre 1961". It runs over printed pp. 83-205 (PDF pp. 90-212).
  - `pop` is column 4, "Total" (de jure population).
  - URL: https://doc.statbel.fgov.be/publications/S210.A7/S210.A7F_Recensement_1961_Tome_01.pdf
  - The link was found through the Statbel archive wiki (Wikibase item Q11897, distribution Q17312): https://wiki.statbel.fgov.be/wiki/S210.A7_fr
  - Saved as `data/raw/belgium/S210.A7F_Recensement_1961_Tome_01.pdf`.
- The PDF is an image-only scan. Its pages were OCR'd with Tesseract 5 (fra), using only the left half of the even pages (commune name, men, women, total).
  - The OCR text is in `data/raw/belgium/ocr_tome1_tableau1/`, with `parse.py` and `build.py`.

## Coverage and choices

- **Threshold:** 10,000 inhabitants.
- **Brussels:** the 19 communes of the Brussels agglomeration (today's Brussels-Capital Region) are **separate rows**, as the census counts them. `Bruxelles (Brussel)` is the City of Brussels commune only, 170,489. The 19 together come to 1,022,795. All 19 are above 10,000.
  - Antwerp is likewise only the pre-1983 commune (253,295). Its 7 suburban communes are separate rows (Deurne, Borgerhout, Berchem, Merksem, Wilrijk, Hoboken, Ekeren).
- **admin1:** the province at the census date. Brabant was still undivided.
  - Mouscron was in West Flanders on 31 December 1961. It moved to Hainaut on 1 September 1963 (noted on its row).
- **Seats:**
  - `capital` = Bruxelles (Brussel).
  - `admin1_seat` marks Antwerpen, Bruxelles, Brugge, Gent, Mons, Liège, Hasselt, Arlon and Namur.
- **Names:** `name` is the printed name, with the alternative-language name in parentheses where the volume gives one. In the scanned copy someone has crossed out many of these by hand; the crossings are ignored.
  - The names were typed from the OCR, so their spelling is normalised: OCR garbled several, and those were read off the page images.
- **name_today:** the present municipality the commune now belongs to, when it differs (for example Jumet → Charleroi, Wilrijk → Antwerpen). For the Brussels communes it gives the official bilingual form.

## Checks

- **Kingdom total:** 9,189,741. It is printed in the table and matches the official census result. The 9 province totals were also read.
- **Totals from the sexes:** every row's total equals men + women as read by OCR. For 6 rows the OCR garbled the total or one sex: Niel, Balen, Forest, Ixelles, Saint-Gilles and Heusden. Anderlues, Ans and Saint-Gilles were also parsed by hand. Each figure was checked against the arrondissement totals, and the notes say so.
- **Missing communes:**
  - For each arrondissement and province, the sum of the parsed commune totals was set against the printed arrondissement and province totals. The gaps match the OCR-damaged rows: exactly for Antwerp, West Flanders and Limburg, and within a few hundred elsewhere. East Flanders is off by about 1,500, too little to hide a commune of 10,000.
  - The largest communes just under the threshold are Essen 9,850, Bornem 9,834, Diest 9,816, Dendermonde 9,815, Lede 9,795, Ingelmunster 9,785, Wavre 9,706, Tessenderlo 9,643, Liedekerke 9,602, Geraardsbergen 9,582 and Tubize 9,483.
- **Count and share:**
  - 172 communes out of about 2,670 in 1961. By province: Brabant 35, Hainaut 35, Antwerp 29, East Flanders 23, West Flanders 23, Liège 15, Limburg 9, Namur 2, Luxembourg 1.
  - Together they hold 4,519,326 people, 49.2% of the kingdom. That is plausible for Belgium: urban sprawl was spread over many small communes, and only about half the population lived in communes of 10,000+.

## Doubts

- OCR digit errors that keep men + women = total consistent are possible but unlikely. Figures near the threshold (Wemmel 10,040, Buggenhout 10,019, Pâturages 10,011) were sum-checked.
- The arrondissement given in `notes` comes from the nearest heading read by OCR. It was not checked row by row.
- There is a handwritten erratum on the scan's flyleaf (for p. 140, "Montignies-sur-Sambre"). It is unclear which column it corrects (it reads "12564"). The population of 24,143 = 11,711 + 12,432 is consistent, so it was kept.
