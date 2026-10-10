# United States, census of 1 April 1950: urban places of 10,000+

**File:** `towns_us_1950.csv`. There are 1,279 rows:
- 1,262 in the 48 states and DC;
- 17 in the territories: Alaska 1, Hawaii 2, Puerto Rico 14. Their `notes` say "Territory".

## Source
- U.S. Bureau of the Census, *Census of Population: 1950*, Vol. I, *Number of Inhabitants*, U.S. Summary chapter.
  - **Table 24**, "Population of urban places in continental United States, Alaska, Hawaii, and Puerto Rico: 1950 and 1940". It runs over printed pp. 1-48 to 1-65. `source_page` gives the printed page.
  - Downloaded from https://www2.census.gov/library/publications/decennial/1950/population-volume-1/vol-01-04.pdf and saved in `data/raw/united_states/`.
- The state chapters `vol-01-05.pdf` to `vol-01-56.pdf`, from the same directory, are also saved there. They were used to cross-check figures, and so was Table 16 of the U.S. Summary (places by size class and state, p. 1-24).
- A secondary tabulation was used only to vote between OCR readings, never as the source of a figure: Stanford CESTA, *Historical U.S. City Populations*, https://raw.githubusercontent.com/cestastanford/historical-us-city-populations/master/data/1790-2010_MASTER.csv, saved as `data/raw/united_states/stanford/master.csv`.

## Method
- The scans are bilevel images at 300 dpi, and their digits 3/8, 5/6 and 0/9 are often confused. Every 1950 figure therefore needed at least two independent readings that agreed. The readings came from:
  - Tesseract OCR of the Table 24 page panels (saved in `ocr_table24_tesseract/`, with the scripts);
  - the PDF's own OCR layer;
  - the OCR of the state chapter;
  - the Stanford tabulation.
- The percent-change column was used as an extra check.
- About 90 rows were settled by reading the page image directly.

## Coverage
- The universe is the census's "urban places" of 10,000 or more: incorporated places plus about 30 unincorporated places delineated by the Census Bureau. `notes` marks each unincorporated place.
  - Boundaries are those of 1 April 1950.
  - New England towns, and townships in NJ, PA and other states, were not urban places in 1950. Examples are Brookline MA, Greenwich CT, Upper Darby PA and Arlington VA. These units were "other urban territory", so they are absent, as in the census's own count.
- New York City is a single row. Its five boroughs are given in `notes`.
- `admin1` is the state.
- `capital` is 1 for Washington DC.
- `admin1_seat` is 1 for state capitals of 10,000+. Five capitals fall below the threshold: Dover, Carson City, Pierre, Montpelier and Juneau.
- The smallest row has 10,001.

## Checks
- **Size-class totals.** The rows were checked against Table 16 (number and population of places of 100,000+, 50-100k, 25-50k and 10-25k, by state).
  - The 48 states and DC have **1,262 places**, exactly the census count (106 + 126 + 252 + 778).
  - Their population is **73,916,666**, exactly the printed national total of those classes.
  - Every state's count matches.
- **Urban share.** The rows hold 76.6% of the urban population (96,467,686, new definition) and 49.0% of the total population (150,697,361).
- **Largest cities.** New York 7,891,957, Chicago 3,620,962, Philadelphia 2,071,605, Los Angeles 1,970,358, Detroit 1,849,568 and Washington 802,178 are all present.

## Doubts
- In a few state cells, the Table 16 figures read from the image differ from the row sums by 9 to 90. Ambiguous digits in that table are the likely cause, since the national total matches exactly.
- The Stanford tabulation has some wrong values, such as Whittier 23,433, where the page image gives 23,820. It also rounds some New England figures. It was never used alone.
- The territories (Alaska, Hawaii, Puerto Rico) were checked less thoroughly, against the image and the percent-change column only.
- Names follow the 1950 print, for example Boise City, San Buenaventura, Middlesborough and De Kalb. `name_today` is filled only for notable changes.
