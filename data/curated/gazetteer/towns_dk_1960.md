# towns_dk_1960 — Denmark, census 26 September 1960

**Source.** Danmarks Statistik, *Statistisk Årbog 1961* (vol. 66, publ. 1962), chapter "Areal og befolkning":
- Tabel 8 "Befolkningen i Hovedstaden, provinsbyerne og forstæderne den 26. september 1960" (pp. 12-15): main source for every row.
- Tabel 9 "Bymæssige bebyggelser med 500 indbyggere og derover" (pp. 15-19): checked for urban areas in rural parish municipalities. Only Birkerød and Hørsholm (whole kommuner, already in Tabel 8) reach 10,000. The largest others are Ikast (5,797), Odder (5,562) and Grindsted (5,289).
- Tabel 7 (administrative units, pp. 9-11): used to assign each town to its amt.
- PDF: https://www.dst.dk/pubfile/13352/areal (landing page https://www.dst.dk/pubomtale/13352). Raw files and URLs are in `data/raw/denmark/` (`README_sources.txt`).
- Amt seats come from da.wikipedia amt articles (Maribo amt seat Nykøbing F.; Præstø amt seat Præstø; Skanderborg amt seat Skanderborg; Sorø amt seat Sorø).

**Unit (as the source counts towns).**
- Capital area (Hovedstadsområdet, 1,348,454): one row per municipality as listed in Tabel 8. København, Frederiksberg and Gentofte are separate rows. The source sums these three as "Hovedstaden" (923,974). The other rows are forstadskommuner and omegnskommuner with 10,000 or more inhabitants. Ballerup-Måløv and Høje Tåstrup are whole municipalities whose largest urban parts (Tabel 9) were under 10,000. This is noted on their rows.
- Provincial towns: the figure for the "købstad med forstæder" (the town municipality plus contiguous suburbs in neighbouring parish municipalities). The købstad-only figure is in `notes`. As a result, Middelfart, Kalundborg, Thisted and Ringsted qualify only with their suburbs. Nørresundby is a separate row from Ålborg, as in the source.
- admin1 = amt at 1960. Københavns kommune belonged to no amt. Roskilde and Køge lay in Roskilde amtsrådskreds of Københavns amt.

**Threshold.** 10,000 or more inhabitants. **Rows: 55** (16 capital-area municipalities and 39 provincial towns).

**Checks.**
- The capital and all large cities are present: Århus 177,234; Odense 129,833; Ålborg 96,438.
- The source has 35 købstæder with 10,000 or more inhabitants by the municipal figure (its size-class summary: 2+2+14+17). All 35 are here; the class sums match exactly, e.g. 10-20k: 17 towns, 248,357. The four suburb-only additions make 39 provincial rows.
- The rows sum to 2,542,771. That is 91.6 % of the source's urban total (Hovedstadsområdet plus provincial towns with suburbs, 2,775,654) and 55.5 % of the national total of 4,585,256.

**Doubts.**
- The OCR of the size-class summary reads "3" towns of 50-100k and "13" of 20-50k. The sums show 2 and 14.
- The seat of the joint Åbenrå-Sønderborg amt is taken as Åbenrå (not verified).
- København has admin1_seat=0. The administration of Københavns amt sat in the city, but the city was outside the amt.
- Municipal boundaries are those of 1960, before the 1970 reform. Many rows (Søllerød, Birkerød, Brøndbyvester-Brøndbyøster, Nørresundby, Hasseris and others) are now merged into larger kommuner.
