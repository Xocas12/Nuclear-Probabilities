# uk_districts_1981_seats: council headquarters of the 1981 districts

**File:** `uk_districts_1981_seats.csv` (456 rows, UTF-8). It gives one point per district: the town where the district council had its headquarters (administrative centre) in about 1981.

**Rows:** the input list. It has 454 Great Britain districts and 2 Northern Ireland districts (Belfast and Londonderry). It has the same names as `towns_uk_1981.csv`, and Nomis labels such as "East Wood", "Tweedale", "Taff - Ely" and "Westminster, City of" are kept as they are.

**Columns:** `name`, `admin1`, `seat`, `lat`, `lon` (WGS84, 3 decimals), `source` (the Wikipedia page used), and `notes`.

## Method
1. **Finding the district article.** For each district I built a list of possible English Wikipedia titles and fetched them in bulk with `Special:Export`. Examples: "X District", "X (district)", "Borough of X", "London Borough of X", "X District Council", "X Borough Council" and "City of X". The API itself returned HTTP 429 for most calls, so I used bulk export instead. Redirects were followed. A page was kept only if it is a district or council article and not a town article (`Infobox UK place`). The raw XML is in `data/raw/uk/district_seats/xml/`, and the merged page store is `export_pages.json`.
2. **Reading the HQ.** For every row I read the infobox fields (`HQ`, `seat`, `admin_hq`, `meeting_place`) and the sentences about premises (for example "based at", "headquarters", "offices" and "moved to"). I compared them with a first list I drafted from my own knowledge (`scripts/guess.py`). Every disagreement, and every article that dates a move, was resolved by reading the article text. The decisions and their reasons are in `scripts/decisions.py` and in `notes`. Where an article dates a move, the 1981 location is given, not today's. Examples:
   - Sandwell → West Bromwich (moved to Oldbury in 1989)
   - Merton → Wimbledon (moved to Morden in 1985)
   - Wyre Forest → Stourport-on-Severn
   - Langbaurgh → Eston
   - Newark and Sherwood → Kelham Hall
   - Rossendale → Rawtenstall
   - East Devon → Sidmouth
3. **Coordinates.** I took the seat town's own Wikipedia article. For towns whose infobox gives the point, it was parsed from the exported wikitext. For towns that use Wikidata-backed coordinates, I used one `prop=coordinates` API call (`seat_coordinates_api_extra.json`). Bury, Chesterfield, Epping, Grays and Redditch had no coordinates through either route, so I took their points from GeoNames (`geonames/GB.zip`, populated place with the largest population). The `notes` column says this on those 6 rows. The district article's own point was never used. The town-level results are in `seat_coordinates.json`.

## Checks
- **Bounding box.** All GB points are within lat 49.8–61 and lon −8.7–2. Belfast and Derry are in Northern Ireland, which is west of −5.4.
- **GeoNames comparison.** Every seat point was compared with the nearest GeoNames populated place of the same name. All are within 5 km. St Pancras has no GeoNames name match. Belfast first failed this check because the parser had taken a map-centre coordinate, so it now uses the article's own coordinates (54°35′49″N 5°55′45″W).
- **Distance within the county.** Each point is within 60 km of another seat in the same county, with three exceptions: Wigtown/Stranraer (63 km), Caithness/Wick (75 km) and Lochaber/Fort William (90 km). These are explained by how large and empty Highland and Dumfries and Galloway are.
- **Source pages.** Every `source` page was fetched and names the seat, except Bath, where only a photo caption does. I removed pages about the wrong place that came up during matching (Birmingham District, Alabama; City of Ipswich, Queensland; Sandwell District, a record label) and replaced them.

**Coverage:** all 456 rows were checked against English Wikipedia. Of these, 452 have the HQ town in the district or council article. The other four (The Wrekin, Sedgemoor, Richmondshire and Roxburgh) have no premises text, so the seat there is my own knowledge.

## Seats outside their own district (correct for 1981)
- North East Derbyshire → Chesterfield
- South Bucks → Slough
- South Cambridgeshire → Cambridge
- South Herefordshire → Hereford
- Monmouth → Pontypool (Mamhilad, in Torfaen)
- South Wight → Newport (Isle of Wight)
- Bolsover → Mansfield

## Rows I am unsure of
- **East Yorkshire (North Wolds until February 1981):** the infobox says Pocklington, but the East Riding council article names Bridlington Town Hall as this council's office. I chose Bridlington.
- **Rochester upon Medway:** the infobox says "Rochester". I gave the Civic Centre at Strood, from memory, about 1.5 km away.
- **Offices split across several towns before a later merger,** so the 1981 "HQ" is a judgement:
  - Vale Royal (Northwich chosen)
  - Elmbridge (Walton-on-Thames chosen)
  - Alyn and Deeside (Hawarden, from the infobox)
  - Delyn (Flint; Delyn House was built "in the early 1980s")
  - Rhymney Valley (Ystrad Mynach; HQ merged there in 1983)
  - Strathkelvin (Kirkintilloch)
  - Rhuddlan (Rhyl)
  - Lewes (Lewes and Newhaven)
  - Mid Suffolk (Needham Market or Eye)
  - Vale of White Horse (Abingdon)
  - North Tyneside (Wallsend)
- **Barking and Dagenham:** Barking Town Hall or Dagenham Civic Centre.
- **East Lindsey:** the Manby date is not given.
- **Bolsover:** the Mansfield offices are given, but the dates are thin.
- **Sites known only for after 1981, so the 1981 town is assumed the same:** Northavon (Thornbury), Wychavon (Pershore), Dover, and Cherwell (Banbury; Bodicote House is 2 km south).
- **Dual seats noted:** Sefton (Bootle and Southport), Halton (Widnes and Runcorn), Lancaster (Lancaster and Morecambe), High Peak (Buxton and Glossop), Erewash (Ilkeston and Long Eaton), Caithness (Wick and Thurso), East Northamptonshire (Thrapston and Rushden).

## Sources
- English Wikipedia, read in October 2026 through `Special:Export` and the MediaWiki API.
- GeoNames GB dump (download.geonames.org/export/dump/GB.zip).

No nuclear target lists or civil defence documents were used.
