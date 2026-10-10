# towns_jp_1940 — Japan (home islands), census of 1 October 1940

**File:** `towns_jp_1940.csv` (579 rows: 168 cities (shi) + 411 towns (machi) of 10,000+)

## Source
Statistics Bureau of Japan, *Showa 15-nen kokusei chosa* (1940 Population Census), Table 1
"Number of households, household members and total population by sex, for All Japan, Do, Fu, Ken,
Shi, Ku, Machi and Mura (all persons including military personnel)". Scanned volume on e-Stat
(survey 00200521, tstat 000001036871). Raw PDFs in `data/raw/japan/`:

| file | e-Stat download URL | content |
|---|---|---|
| s15_7914029.pdf | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000007914029&fileKind=2 | Table 1, All Japan to 11 Saitama |
| s15_7914030.pdf | ...statInfId=000007914030&fileKind=2 | 12 Chiba to 23 Aichi |
| s15_7914031.pdf | ...statInfId=000007914031&fileKind=2 | 24 Mie to 35 Yamaguchi |
| s15_7914032.pdf | ...statInfId=000007914032&fileKind=2 | 36 Tokushima to 47 Okinawa |
| s15_7914024/025/026/028.pdf | statInfId 000007914024, -025, -026, -028 | survey outline, notes, prefecture totals, area list |

The listing pages are saved too (`estat_*.html`). `source_page` gives the statInfId and the PDF page,
which is a two-page scan spread.

## What the table covers
- All 47 prefectures of 1940, including Okinawa and Hokkaido. Korea, Taiwan and Karafuto are excluded
  (they are not in this table).
- **Cities:** every shi on 1 Oct 1940 (168), at its boundaries on that date. Fujisawa got city status
  on census day and the census lists it as a shi. For the six cities with wards (Tokyo, Osaka,
  Kyoto, Nagoya, Yokohama, Kobe), the row is the city total. The wards are not listed separately.
- **Towns:** machi with a total population of 10,000 or more. Villages (mura) are excluded, even ones
  with 10,000+ people (there are many, e.g. Kotoni, Mikasayama, Hiro, Etajima).
- `pop` is the census "total population (all persons including military personnel)".
- `name` is the romanization printed in the source (Hepburn-like, e.g. Gumma, Matsuzaka, Kawauchi).
  City notes give the kanji. `name_today` is filled for cities whose current name differs
  (e.g. Urawa→Saitama, Fuse→Higashiosaka, Kawauchi→Satsumasendai). It is not researched for towns,
  many of which have since merged into larger cities.
- `admin1` is the prefecture. `admin1_seat` = 1 for the 47 prefectural capitals. `capital` = 1 for Tokyo-shi.

## Method and checks
The scans have no text layer, so I OCRed them with tesseract. A figure was accepted only when at
least two independent readings agreed: total = male + female, total = ordinary-household members +
quasi-household members, or two OCR passes giving the same number. I read the remaining ~30 rows by
eye from the scan (they are noted in `notes`). Three duplicate scan pages were dropped.
- **Cities:** for every prefecture, the city rows add up exactly to the printed "All shi" (市部)
  row. All 168 cities together = 27,577,539. The census's All-Japan "All shi" row is 27,494,237,
  and the gap is exactly Okinawa's two cities (83,302), because the census's All-Japan row
  (72,539,729) leaves Okinawa out. The 47 prefecture rows sum to 73,114,308, the known 1940 total.
  Tokyo (6,778,804) and the largest cities are present.
- **Towns:** I classified town vs village by reading every candidate row's 町/村 character on the
  scan, 717 rows in all. 411 towns, totalling 6.88 M. Cities plus towns = 34.46 M, or 47% of the population.
- 168 cities is the expected number for late 1940.

## Doubts
- Some town rows may be missing. If OCR failed so badly on a row that no reading reached 9,000, the
  row was never flagged for review. I scanned the six worst pages by eye; other pages could still
  hide a few towns just over 10,000.
- Town names are as printed, read by eye. A few printed romanizations are odd (e.g. "Kutchan" for 倶知安,
  "Hayame" for 駛馬, "Horigawa"). Two different Aichi towns are both called Shinkawa.
- Town figures that passed the agreement checks were not compared with any other publication.
