# towns_ca_1956: Canada, census of 1 June 1956

**Source:** Dominion Bureau of Statistics, *The Canada Year Book 1957-58*, Chapter "Population", Section "Population of incorporated urban centres":
- Table 10, "Incorporated Cities, Towns and Villages having Populations of 1,000 or Over, by Province, Census Years 1951 and 1956", pp. 126-132 (all town rows).
- Table 9, size-group distribution, p. 126 (check totals).
- Table 8, census metropolitan areas 1956, p. 125 (CMA rows).
- Table 7, cities over 30,000, p. 125 (cross-check).

Scans (Internet Archive), saved under `data/raw/canada/cyb1957/`:
- https://archive.org/details/canada-statistics-canada-canada-year-book_1957-1958 : OCR text `..._djvu.txt` (https://archive.org/download/canada-statistics-canada-canada-year-book_1957-1958/canada-statistics-canada-canada-year-book_1957-1958_djvu.txt), page map `pn.json` (`..._page_numbers.json`), and page images `pages/leaf157.jpg`..`leaf164.jpg` (book pp. 125-132) from https://archive.org/download/canada-statistics-canada-canada-year-book_1957-1958/page/leafNNN_w2400.jpg
- https://archive.org/details/canadayearbook191957cana : second scan, OCR text `canadayearbook191957cana_djvu.txt` (https://archive.org/download/canadayearbook191957cana/canadayearbook191957cana_djvu.txt)

The figures were read from the page images, because the OCR scrambles the columns.

**Coverage:** every incorporated city, town and village with 10,000 or more people on 1 June 1956, using the municipal boundaries of that date. That gives **137 rows**. Rural municipalities, townships and district municipalities are not "incorporated urban centres" in the DBS sense and are not in the table. Large suburban units such as York, North York, Scarborough, Etobicoke and East York townships (Ont.), Burnaby and the District of North Vancouver (B.C.) are therefore missing. The 15 census metropolitan areas from Table 8 come after the towns as extra rows, named "X (CMA)" and flagged in `notes`. They overlap the city rows, so leave them out when you count towns. admin1 is the province. capital=1 only for Ottawa. admin1_seat=1 for the 10 provincial capitals, all of which are 10,000+. Whitehorse (Yukon, 2,570) is below the threshold.

**Checks:**
- The town rows match Table 9's 1956 size groups exactly, in count and in population for every band: 2/1/4/4/12/27/43/44 centres, 137 in all, totalling **6,742,084**.
- Ottawa (222,129) and the largest cities are present: Montreal 1,109,439, Toronto 667,706, Vancouver 365,844, Winnipeg, Hamilton, Edmonton, Calgary, Quebec.
- The rows hold 72.6% of the population of all 1,873 incorporated centres (9,286,126; Table 9) and about 42% of Canada's 1956 total population of 16,080,791.

**Doubts:**
- Vancouver is printed as 364,844 in Table 7 but 365,844 in Tables 9 and 10. 365,844 is used because it makes the Table 9 sum balance.
- Lancaster (N.B.) and St. James (Man.) were newly incorporated or reclassified since 1951 (table footnotes).
- `notes` lists the many later mergers (Montreal 2002, Quebec 2002, Saguenay, Thunder Bay, Cape Breton RM, Halifax RM, Toronto 1967/1998, Winnipeg 1972 and others).
