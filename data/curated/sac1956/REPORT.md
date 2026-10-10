# SAC 1956 list: assembly report

- Lines with a final reading: 16046 (15838 agreed by both passes, 208 adjudicated); lines with no reading yet: 0
- Complexes: 1217; sub-complexes: 873; DGZs: 1405; installation lines: 10220; M-n rows: 34; airfields: 1128
- Lines still carrying '?' or failing a rule: 5

## Transcription quality

- Data lines: 14904. Pass A differs from the final reading on 150 (1.01%), pass B on 63 (0.42%); both on 35. On 3 of these the two passes wrote the same legible text: errors the comparison cannot see, found by the consistency checks or by an adjudicator looking at the line for another reason (A004-L07, A004-L20, A006-L22).
- Adjudicated lines: 208; choice A 25, B 106, both 40, new 37; confidence high 115, low 11, medium 82

## Anchors

| Complex | Priority | DGZs | Installations (with sub-complexes) |
|---|---|---|---|
| MOSCOW | 1 | 13 | 190 |
| LENINGRAD | 2 | 9 | 152 |
| BERLIN GER SOVZONE | 61 | 6 | 91 |

## Priority numbers

- 1215 complexes carry a priority; highest 1223; duplicates: 0 []; numbers missing from 1..max: 8 [97, 303, 530, 603, 766, 872, 1054, 1220]
- Airfields: 1128 priorities, highest 1111, 18 with an A suffix (typed in later); duplicates: 1 ['10']; numbers missing from 1..max: 2 [18, 652]
- Reference numbers that drop below the previous complex (alphabetical order check): 1

## Complexes by country

| Country | Complexes | DGZs | Installations |
|---|---|---|---|
| USSR | 728 | 856 | 5064 |
| Poland | 101 | 123 | 982 |
| China | 81 | 66 | 595 |
| East Germany | 68 | 124 | 1159 |
| Czechoslovakia | 64 | 88 | 858 |
| Romania | 49 | 57 | 467 |
| China (Manchuria) | 38 | 50 | 319 |
| Hungary | 35 | 25 | 414 |
| Bulgaria | 24 | 16 | 222 |
| North Korea | 15 | 0 | 83 |
| North Vietnam | 8 | 0 | 34 |
| Albania | 6 | 0 | 23 |

## Most common installation categories

- 275 POPULATION: 2085
- 227 LIQUID FUELS, STORAGE NON-REFINERY: 660
- 248 MILITARY TROOP INSTALLATIONS: 556
- 246 MILITARY STORAGE AREAS, ARMY & NAVY: 459
- 290 RAILROAD BRIDGES: 229
- 208 GOVERNMENT CONTROL CENTERS: 213
- 281 PORTS, INLAND: 210
- 280 PORTS, MARITIME: 187
- 430 STEEL: 182
- 230 MACHINE TOOLS: 145
- 392 RAILROAD YARDS & SHOPS- SATELLITES / POLAND: 137
- 243 MILITARY SCHOOLS: 127
- 445 SULFURIC ACID: 122
- 245 MILITARY STORAGE AREAS, AIR FORCE: 121
- 226 LIQUID FUELS, STORAGE AT REFINERIES: 113

- Category codes not in the code list: []

- Airfields whose reference number is a Part I complex: 856 of 1128
- Duplicate scans left out of the tables: PDF page 46 (= page 45)
- Missing from the scan: C065-L04 opens without its header (header not in the scan: PDF page 64 is cut off at the foot); C010-L04 opens without its header (header not in the scan: the printed page after PDF page 9 is missing)

## External check: NSA city sheets

Installation lines by category against the National Security Archive's city sheets (validation_sac1956_nsa_city_sheets.csv).

| Sheet | Location | Block in the list | Lines here | Lines on the sheet | Categories that differ (here/sheet) |
|---|---|---|---|---|---|
| Moscow | Moscow/Suburbs | C166-L18 MOSCOW | 180 | 178 | 015: 6/5, 200: 2/1 |
| Moscow | Kuchino | C170-L07 KUCHINO | 2 | 2 | - |
| Moscow | Shchylkovo | C170-L10 SHCHELKOVO | 6 | 6 | - |
| Moscow | Tomilino | C170-L18 TOMILINO | 2 | 2 | - |
| Moscow | Mishutkino | not a block | 0 | 2 | 375: 0/1, 384: 0/1 |
| Leningrad | Leningrad/Suburbs | C143-L42 LENINGRAD | 139 | 145 | 010: 0/1, 055: 2/3, 082: 0/1, 230: 2/3, 430: 3/4, 485: 3/4 |
| Leningrad | Beloostrov | C146-L36 BELOOSTROV | 2 | 2 | - |
| Leningrad | Kolpino | C146-L39 KOLPINO | 7 | 7 | - |
| Leningrad | Sablino | C146-L48 SABLINO | 2 | 2 | 350: 0/1, 358: 1/0 |
| Leningrad | Sestroretsk | C146-L51 SESTRORETSK | 2 | 2 | - |
| Beijing | Beijing/Suburbs | C199-L38 PEI PING CHINA | 17 | 18 | 240: 1/2 |
| Beijing | Fengtai | C200-L17 FENG TAI CHINA | 5 | 5 | - |
| Warsaw | Warsaw | C292-L07 WARSAW POL | 39 | 39 | - |

## Consistency checks across lines

Lines that the checks still flag after the second look, with its outcome (checks.csv has the notes). Lines that the second look corrected no longer break a check and are not listed. In all, 37 lines ended with a reading that neither pass had (adjudication or second look, choice `new`).

| Check | Lines | Confirmed as printed | Not re-read |
|---|---|---|---|
| name a letter away from a nearby name | 10 | 10 | 0 |
| letter struck for a digit | 6 | 0 | 6 |
| WAC prefix differs from its block | 4 | 4 | 0 |
| DGZ far from its header | 3 | 3 | 0 |
| airfield row does not match the expected format | 3 | 3 | 0 |
| block with more than one population line | 2 | 2 | 0 |
| duplicate airfield priority | 2 | 2 | 0 |
| airfield BE number not 8xxx | 2 | 2 | 0 |
| header far from the other headers on its chart | 1 | 1 | 0 |
| reference number not above the previous complex | 1 | 1 | 0 |
| airfield out of alphabetical order | 1 | 1 | 0 |
| minutes>=60 | 1 | 1 | 0 |
| line does not match any expected format | 1 | 1 | 0 |
