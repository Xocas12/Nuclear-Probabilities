# Second read of candidate rows, November 2026

Independent check of the `wp_1977_gsa_lessons` and `wp_1975_soyuz75` rows in `data/notes/soviet_search_2026-11.md`. Output: `data/curated/labels/wp_1977_gsa_lessons.csv` and `data/curated/labels/wp_1975_soyuz75.csv`.

Result: lessons 44 confirmed, 4 rejected; Soyuz-75 2 confirmed, 5 rejected.

## What was read

- 19 full pages read as images, 14 cited and 5 for context. The downloaded PDFs have no text layer, so no quote here comes from OCR.
- Cited: 0001197557 pp.13, 14, 15, 17, 19, 20, 21, 24; 0001197532 p.21; 0001197561 pp.26, 27; 0001197563 p.15; 0001197576 pp.15, 17.
- Context: 0001197563 pp.14, 16; 0001197561 p.25; 0001197532 pp.15, 18.
- Names that could be misread were also checked on crops at 260 to 420 dpi. Printed page numbers equal PDF page numbers on all 19 pages.
- Soyuz-75 was read as HTML from the Wayback capture. This is an English translation and no scan was read, so no image check was possible. The quote was matched to the downloaded text by script.

## Rule applied to rejections

A row was dropped if the document does not state a country and the place cannot be identified from the name as printed, including names that only the translator's query or bracket makes readable. A row was also dropped if the strike is not stated to be nuclear.

## Rows the first reader's table had wrong

- Row 10: DEIMOLD is an OCR misreading. The scan prints DETMOLD (0001197557 p.15).
- Row 12: DEIMENHORST is an OCR misreading. The scan prints DELMENHORST (0001197557 p.17).
- Row 15: BUCKERURG is an OCR misreading. The scan prints BUCKEBURG (0001197557 p.20).
- Rows 22 to 25: the quote's "conmand" is an OCR error. The scan prints "command".
- Row 23: the note calls ECHERNFORDE probably OCR. The scan does print ECHERNFORDE on 0001197557 p.24; ECKERNFORDE is on 0001197532 p.21. The source spelling is kept.
- Row 45: weapons 17 removed and "shared across its list" is wrong. OLDENBURG is the only target named in that sentence (0001197576 p.17), but 17 is the brigade's allotment, not a per-target count.
- Row 44: the quote was cut short, and now reads "the control and warning post at SPRINGE".
- Rows 28 to 37 (0001197563 p.15): the cited sentences do not say the strike is nuclear, and the table's notes did not address this. Support is the section heading on p.14, "Organizing nuclear destruction of the enemy by rocket troops". Rows 36 and 37 also have explicit nuclear wording on 0001197561 p.26. These are the least explicit confirmed rows.
- Search-note caveat on Lesson 2 p.15: it reports an OCR variant 35 for Kloppenburg. The scan reads 33 at the resolution used.
- The first reader's pointer to 0001197562 p.49 was not opened and is not cited. The first reader's claim that the held lesson lists No. 24 where Lesson 2 lists No. 29 was not checked either.

The LATEN reading on p.27 is correct as the first reader gave it from the scan; the row fails on identification, not spelling.

## Row by row

Numbers are the first reader's seq.

- wp_1977_gsa_lessons 1: confirmed as HUSUM, FRG, 0001197557 p.13, new seq 1.
- wp_1977_gsa_lessons 2: confirmed as MARNE, FRG, 0001197557 p.13, new seq 2.
- wp_1977_gsa_lessons 3: confirmed as ITZEHOE, FRG, 0001197557 p.13, new seq 3.
- wp_1977_gsa_lessons 4: confirmed as KLOPPENBURG, FRG, 0001197557 p.14, new seq 4.
- wp_1977_gsa_lessons 5: confirmed as QUAKENBRUCK, FRG, 0001197557 p.14, new seq 5.
- wp_1977_gsa_lessons 6: confirmed as OLDENBURG, FRG, 0001197557 p.14, new seq 6.
- wp_1977_gsa_lessons 7: confirmed as VEGESACK, FRG, 0001197557 p.14, new seq 7.
- wp_1977_gsa_lessons 8: confirmed as KLOPPENBURG, FRG, 0001197557 p.14, new seq 8.
- wp_1977_gsa_lessons 9: confirmed as BREMEN, FRG, 0001197557 p.14, new seq 9.
- wp_1977_gsa_lessons 10: confirmed as DETMOLD, FRG, 0001197557 p.15, new seq 10. Spelling corrected from the first reader's OCR form.
- wp_1977_gsa_lessons 11: confirmed as GUTERSLOH, FRG, 0001197557 p.15, new seq 11.
- wp_1977_gsa_lessons 12: confirmed as DELMENHORST, FRG, 0001197557 p.17, new seq 12. Spelling corrected from the first reader's OCR form.
- wp_1977_gsa_lessons 13: confirmed as WURSTERHEIDE, FRG, 0001197557 p.19, new seq 13.
- wp_1977_gsa_lessons 14: confirmed as OSNABRUCK, FRG, 0001197557 p.20, new seq 14.
- wp_1977_gsa_lessons 15: confirmed as BUCKEBURG, FRG, 0001197557 p.20, new seq 15. Spelling corrected from the first reader's OCR form.
- wp_1977_gsa_lessons 16: confirmed as DIEPHOLZ, FRG, 0001197557 p.20, new seq 16.
- wp_1977_gsa_lessons 17: rejected. BERGER: the strike is nuclear and the spelling is right (0001197557 p.21, also 0001197532 p.15: one bomb on airfield No. 31), but the place is not identified and the document gives no country.
- wp_1977_gsa_lessons 18: confirmed as EGGEBEK, FRG, 0001197557 p.24, new seq 17.
- wp_1977_gsa_lessons 19: confirmed as JAGEL, FRG, 0001197557 p.24, new seq 18.
- wp_1977_gsa_lessons 20: confirmed as RENDSBURG, FRG, 0001197557 p.24, new seq 19.
- wp_1977_gsa_lessons 21: confirmed as FRIEDRICHSORT, FRG, 0001197557 p.24, new seq 20.
- wp_1977_gsa_lessons 22: confirmed as FLENSBURG, FRG, 0001197557 p.24, new seq 21.
- wp_1977_gsa_lessons 23: confirmed as ECHERNFORDE, FRG, 0001197557 p.24, new seq 22. Quote or note adjusted.
- wp_1977_gsa_lessons 24: confirmed as KIEL, FRG, 0001197557 p.24, new seq 23.
- wp_1977_gsa_lessons 25: confirmed as HOLTENAU, FRG, 0001197557 p.24, new seq 24.
- wp_1977_gsa_lessons 26: confirmed as BRAMSCHE, FRG, 0001197532 p.21, new seq 25.
- wp_1977_gsa_lessons 27: confirmed as IBBENBUREN, FRG, 0001197532 p.21, new seq 26.
- wp_1977_gsa_lessons 28: confirmed as RIJSSEN, Netherlands, 0001197563 p.15, new seq 27.
- wp_1977_gsa_lessons 29: confirmed as LOCHEM, Netherlands, 0001197563 p.15, new seq 28.
- wp_1977_gsa_lessons 30: rejected. VEGDAM: printed, but marked /sic -- probably in The Netherlands/. Place not identified and the country is only 'probably'.
- wp_1977_gsa_lessons 31: rejected. AL'FRED: printed, with translator's /probably ALFERDE/. The document does not establish the place; the country would rest on a queried reading.
- wp_1977_gsa_lessons 32: confirmed as ESCHERSHAUSEN, FRG, 0001197563 p.15, new seq 29.
- wp_1977_gsa_lessons 33: confirmed as EINBECK, FRG, 0001197563 p.15, new seq 30.
- wp_1977_gsa_lessons 34: confirmed as APELDOORN, Netherlands, 0001197563 p.15, new seq 31.
- wp_1977_gsa_lessons 35: confirmed as RHEINE, FRG, 0001197563 p.15, new seq 32.
- wp_1977_gsa_lessons 36: confirmed as LINGEN, FRG, 0001197563 p.15, new seq 33.
- wp_1977_gsa_lessons 37: confirmed as ENSCHEDE, Netherlands, 0001197563 p.15, new seq 34.
- wp_1977_gsa_lessons 38: confirmed as ENSCHEDE, Netherlands, 0001197561 p.26, new seq 35.
- wp_1977_gsa_lessons 39: confirmed as ROTENBURG, FRG, 0001197561 p.27, new seq 36.
- wp_1977_gsa_lessons 40: rejected. LATEN: the scan does print LATEN /?LATHEN/ in a nuclear strike on airfields (0001197561 p.27), but the translator queries the place and the document gives no country.
- wp_1977_gsa_lessons 41: confirmed as LINGEN, FRG, 0001197561 p.27, new seq 37.
- wp_1977_gsa_lessons 42: confirmed as MUNSTER, FRG, 0001197561 p.27, new seq 38.
- wp_1977_gsa_lessons 43: confirmed as OCHTRUP, FRG, 0001197576 p.15, new seq 39.
- wp_1977_gsa_lessons 44: confirmed as SPRINGE, FRG, 0001197576 p.15, new seq 40. Quote or note adjusted.
- wp_1977_gsa_lessons 45: confirmed as OLDENBURG, FRG, 0001197576 p.17, new seq 41. Weapons count removed: brigade allotment.
- wp_1977_gsa_lessons 46: confirmed as EMSDETTEN, FRG, 0001197576 p.17, new seq 42.
- wp_1977_gsa_lessons 47: confirmed as BILLERBECK, FRG, 0001197576 p.17, new seq 43.
- wp_1977_gsa_lessons 48: confirmed as VECHTA, FRG, 0001197576 p.17, new seq 44.
- wp_1975_soyuz75 1: confirmed as GRONINGEN, Netherlands, para. 2, new seq 1.
- wp_1975_soyuz75 2: confirmed as LEEUWARDEN, Netherlands, para. 2, new seq 2.
- wp_1975_soyuz75 3: rejected. [KAROLINENSIN]: named under nuclear strikes, but the bracketed reading is not identified and the document gives no country.
- wp_1975_soyuz75 4: rejected. DORNU: named under nuclear strikes, but the translator only offers 'possibly DORNUM' and the document gives no country.
- wp_1975_soyuz75 5: rejected. [DURICH]: named under nuclear strikes, but the bracketed reading is not identified and the document gives no country.
- wp_1975_soyuz75 6: rejected. EDE: para. 4 says the 31st rbr 'will launch strikes on nuclear-capable aircraft'; the targets are nuclear-capable, but the strike is not stated to be nuclear.
- wp_1975_soyuz75 7: rejected. ZEIST: same sentence as EDE, strike not stated to be nuclear.
