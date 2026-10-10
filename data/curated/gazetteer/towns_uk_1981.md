# towns_uk_1981: United Kingdom, census of 5 April 1981

**File:** `towns_uk_1981.csv` (476 rows). It was built by `data/raw/uk/build_towns_uk_1981.py`. The raw files are in `data/raw/uk/`.

## The unit is mixed. Read this first.

- **Great Britain (454 rows): 1981 local government districts, not urban areas.** These are the 1974/75 districts: London boroughs, metropolitan and non-metropolitan districts, and Scottish districts and islands areas. A district such as "Kirklees" or "Wychavon" is a local authority area. It is not a town. Large cities line up well with their districts. Rural districts contain several small towns.
- **Northern Ireland (22 rows): towns.** Each town is the built-up rectangle drawn by the NI Census Office.

The preferred source, OPCS *Census 1981: Key Statistics for Urban Areas* (HMSO 1984), is only in print. I could not reach any machine-readable copy or faithful tabulation of it:
- web.archive.org, archive.today, Vision of Britain and HathiTrust were all blocked or down.
- The old citypopulation.de UK pages were checked through Common Crawl captures from 2009/10, 2013 and 2014 (raw files in `commoncrawl_*`). They only ever carried 1991 and 2001 figures for Great Britain.
- de.wikipedia's UK list does have 1981 figures for built-up areas. It only covers places of 50k+ in 2021, has gaps, and its source is unclear: for example, Mansfield is 71,325 there against 72,108 in the KS Urban Areas table cited on en.wiki. I did not use it.

## Sources
1. **Great Britain:** OPCS/GRO(S) 1981 Census Small Area Statistics, Nomis dataset NM_66_1. Geography type 496 is "pre-1996 local authority districts" and type 498 is counties/regions.
   - https://www.nomisweb.co.uk/api/v01/dataset/NM_66_1.data.csv?geography=2092957698TYPE496&cell=1,8,36&measures=20100&select=geography_name,geography_code,geography_type,cell,cell_name,obs_value
   - The county totals and the district-to-county lookup come from the same API (`.../geography/{county}TYPE496.def.sdmx.json`).
   - `pop` is the usually resident population: cell 1 (present residents) plus cell 8 (absent residents). The persons present on census night (cell 36) are given in `notes`.
2. **Northern Ireland:** Census Office NI, *The Northern Ireland Census 1981: Towns and Villages Booklet*.
   - https://www.nisra.gov.uk/files/nisra/publications/1981-Census-towns-villages-booklet.pdf (OCR text is in `nisra_1981_towns_villages.txt`)
   - Figures are usually resident persons as enumerated, **not adjusted for the 1981 non-enumeration** (the census boycott during the hunger strikes). Belfast is printed "as per DC", meaning the whole Belfast district.
   - Also downloaded: the NISRA 1981 report index, the preliminary report and the summary report (https://www.nisra.gov.uk/publications/1981-census-reports).

## Columns
- `admin1` is the county for England and Wales (1974–96 counties, with the metropolitan counties still existing in 1981), the region or islands area for Scotland, and the district council area for NI.
- `name` is the Nomis label. Nomis uses the later pre-1996 names. Where I know the 1981 name differed, `notes` gives it (for example North Bedfordshire for Bedford, Bracknell, West Derbyshire, Wimborne, Yeovil, Langbaurgh, Beverley, Anglesey, Preseli, Tiverton, Montgomery, Radnor, North Wolds, Eastwood, Tweeddale). These rename dates come from my memory and are unverified.
- `capital` is 1 only on the City of Westminster. London appears as its 32 boroughs.
- `admin1_seat` is 1 for the district that contained the county or regional council headquarters, so it is 1 for Blaby (Glenfield, Leicestershire) and Rushcliffe (West Bridgford, Nottinghamshire). Surrey (County Hall at Kingston, inside Greater London) and Mid Glamorgan (sat in Cardiff) have no seat row. Castlereagh DC has no town of 10k+ that was its seat.

## Threshold and counts
- The threshold is 10,000 usual residents.
- **GB:** 454 of 459 districts qualify. Excluded: City of London (4,701), Isles of Scilly (1,853), Badenoch and Strathspey (9,363), Nairn (9,640), Skye and Lochalsh (9,945). Because districts tile the whole country, the GB rows sum to 53,521,409, which is 99.9% of GB usual residents (53,556,911). This is total population, not urban population.
- **NI:** 22 towns of 10k+, summing to 794,045. That is 54% of the 1,481,959 enumerated (about 1.53m estimated including non-enumerated). Holywood (9,209), Downpatrick (9,924), Dungannon (9,201) and Limavady (8,924) fall just below the threshold. Craigavon is split as printed into Lurgan, Portadown and Craigavon central.

## Checks
- The GB, England, Wales and Scotland totals of cell 1 match the published present-resident figures (for example England 45,214,323, the same as en.wiki "List of counties of England by population in 1981"). Cells 1+8 give England and Wales 48,521,596, the usual published usually-resident total.
- The largest units are Birmingham (996,369), Glasgow City (755,429), Leeds (696,714), Sheffield, Liverpool, Bradford, Manchester and Edinburgh. Belfast is 295,223.
- NI town rows were checked so that males + females = persons. Armagh (13,863) and Newtownards (21,289) were read from the page image because the OCR text was off.

## Doubts
- The district unit is unlike the town units used for the other countries. A GB urban-area table for 1981 still needs the HMSO KS Urban Areas volumes.
- The NI figures are undercounts because of non-enumeration (Belfast has about 7,900 non-enumerated per the preliminary report). The NI town rectangles are 1981 Census Office definitions, not today's settlement boundaries.
- The Borders regional seat flag (Ettrick and Lauderdale, for Newtown St Boswells) and the Northumberland flag (Castle Morpeth, where County Hall moved c.1981) are uncertain.

No nuclear target lists or civil-defence material were used.
