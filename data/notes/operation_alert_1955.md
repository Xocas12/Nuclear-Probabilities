# Operation Alert 1955: target list reconstruction

Goal: the full list of the ~60 cities "struck" in FCDA's Operation Alert 1955 exercise (15 June 1955).
FCDA says: "60 cities in the United States, Hawaii, Puerto Rico, the Canal Zone, and Alaska were struck by
61 bombs ranging in size from 20 kilotons to 5 megatons". Ideally with yield and burst type per city.
This follows on from `civil_defence.md` section 4 and `cd_1955_operation_alert.csv` (16 rows). That file is unchanged.

**Output:** `data/curated/labels/cd_1955_operation_alert_full.csv`, **60 rows**:

- Rows 1-16 are the 16 map-labelled cities, copied from the existing file. Only `plan_id` and `notes` were changed:
  - Newspaper yields were added for Chicago and St. Louis.
  - Kansas City evidence was added.
  - The notes point to the hearing's Appendix 1 map.
- Rows 17-60 come from newspapers only. Each one's `notes` starts with "SECONDARY:".

All fetched files are listed with URL and sha256 in
`data/raw/civil_defence/operation_alert_1955_fetch_manifest.tsv` (160 entries).

## Sources tried

| Source | Route | Outcome |
|---|---|---|
| Hearings *Civil Defense for National Survival*, pt. 4 (Apr-May 1956), Exhibit 5, Appendix 1 | archive.org item `sim_united-states-congress-hearings-prints-and-reports_april-10-12-17-19-may-15-17-18-1956`. Used `_page_numbers.json` to map p.1495 to leaf 464, then fetched the BookReader image `.../page/n464.jpg` (the page-level route works; no 142 MB PDF needed). | Appendix 1 (p.1495) is **the same "OPERATION ALERT 1955 ATTACK PATTERN" map**, not a list. Its labels are the same as the FCDA annual-report map. It adds insets for Alaska (3 symbols), Hawaii (1), Puerto Rico (1) and the Canal Zone, but the inset labels cannot be read on the microfilm, even at full 2504x3740 resolution. Appendix 2 (p.1496) is a casualty chart and Appendix 3 (p.1497) covers medical supplies. Saved as `US_Congress_Hearings_1956_p1495_Appendix1_Operation_Alert_1955_attack_pattern_n464.jpg` (`30ce8eeb…a8fd`). |
| Same OCR, p.1493 | text | Names Kansas City as an attacked city (evacuation casualty table). |
| FCDA Annual Report 1955, PDF p.39 | `pdfimages` extract (1650x2550, 1-bit) | Re-checked. It has no insets and no names beyond the 16 labels. The unlabelled "other target" symbols are discussed below. |
| Chronicling America | old `chroniclingamerica.loc.gov/search/pages/results` returns a 308 redirect, then 404. The new API `https://www.loc.gov/collections/chronicling-america/?q=…&dates=…&fo=json` works. Page OCR comes from `tile.loc.gov/text-services/word-coordinates-service?…&full_text=1`. | **Main find.** I searched 1955 issues of the *Evening Star* (Washington), *Key West Citizen*, *Nome Nugget*, *Arizona Sun* and *Atlanta Daily World* (about 45 pages). The AP pre-attack list is in *Key West Citizen* 15 Jun 1955 p.2. Washington's yield and burst type, and Portland (Maine), are in the *Evening Star* 15 Jun p.1 and 16 Jun p.4. New Orleans and Flint are in *Nome Nugget* 17 Jun p.3. |
| archive.org newspapers | `advancedsearch` (metadata only) to list issues dated 13-20 Jun 1955. Full-text search via `services/search/beta/page_production/?service_backend=fts&page_target=newspapers`. Then I downloaded the `_djvu.txt` of 103 US issues dated 14-18 Jun (plus a few others). Papers included the Atlanta Constitution, St. Louis Post-Dispatch, Lincoln Star/Journal, Gettysburg Times, Kingston Daily Freeman, Dixon Evening Telegraph, Cumberland News and about 20 small dailies. | Small dailies did not print the list. The *Dixon Evening Telegraph* 16 Jun gives **Chicago 5 Mt** and **St. Louis 1/5 of that (1 Mt)**. The *Atlanta Constitution* OCR is badly garbled multi-column text, and its 14 and 16 Jun `_djvu.txt` downloads returned HTTP 500. |
| Other Congress hearings | archive.org full-text search over `pub_united-states-congress-hearings-prints-and-reports` | No hit for any list-style query (e.g. "Operation Alert" with Schenectady, Fort Wayne or Balboa). Part 7 (June 1956) has only Op Alert **1956** totals: 128 bombs, 39 in the megaton range of which 5 are 5 Mt, on 82 cities plus 2 in Alaska. That is not used here. One candidate item returned HTTP 500. |
| nuke.fas.org, DTIC | — | Blocked, not tried. |

## What was found

1. **The AP pre-attack list** (*Key West Citizen* 15 Jun 1955 p.2; the same story without the list is in *Nome Nugget* 15 Jun p.1).
   - The lead names "Washington and 48 other major cities" and "New York, Chicago, Los Angeles, St. Louis, Cleveland, Pittsburgh".
   - It then gives "Other known target cities": 38 names. Of these, 32 are continental (Gary is also on the map) and 6 are territorial: Anchorage, Fairbanks, Juneau, Balboa (C.Z.), Honolulu and San Juan.
   - It also says "Forty-two of the cities know in advance … The other seven cities haven't known until today."
   - So the AP list covers cities that **knew in advance**. It is not exhaustive. It omits several map-labelled megaton cities: Philadelphia, Detroit, Buffalo, Houston, Atlanta, Kansas City, Minneapolis-St Paul and San Francisco. Detroit and Buffalo were among the cities not notified (hearing p.1491).
2. **Yields and burst types stated** (all from newspapers except Los Angeles):
   - **Washington:** 200 kt, air burst ("burst high in the air"), over 11th and F Sts NW, at 3:25 p.m. Fallout fan drawn 240 miles to Durham, N.C. (*Evening Star*).
   - **Chicago:** 5 Mt at 2:20 p.m. CDT (*Dixon Evening Telegraph*).
   - **St. Louis:** "one fifth as powerful", so 1 Mt, at 2:45 p.m. (*Dixon Evening Telegraph*).
   - **Los Angeles:** 3 x 1 Mt (hearing p.1433, primary).
   - **Pittsburgh:** a fallout-producing "blast over Pittsburgh", yield not stated (*Evening Star*).
   - **Overall ranges:** 20-600 kt atomic and 1-5 Mt hydrogen (*St. Louis Post-Dispatch* 16 Jun). "20,000 to 5 million tons" (*Lincoln Journal* 14 Jun).
   - The *Arizona Sun* (17 Jun) says that of the 50 continental cities "4 will suffer H-bomb … 'megaton-size' … hits and the others … 'Kiloton-size'". This conflicts with FCDA's 14 megaton ground bursts, so it is recorded here only.
3. **Cities that were not notified:** New Orleans ("one of the seven cities which did not know in advance … the make-believe blast killed 36,023"), plus Buffalo and Detroit (FCDA). **Portland, Maine** got the "first simulated bomb".

## Reconciling with "60 cities / 61 bombs"

- **The CSV has 59 US/territorial rows plus Montreal:**
  - 15 map-labelled US names, counting Minneapolis and St Paul separately even though they share one plume.
  - 38 further continental names.
  - 6 territorial names.
- **The territorial count of 6 matches** the newspapers ("55 cities in the continental United States … and six of the nation's territories", *St. Louis Post-Dispatch* 16 Jun) and the hearing insets (Alaska 3, Hawaii 1, Puerto Rico 1, Canal Zone 1).
- **Continental:**
  - Counts in sources: newspapers say 55, FCDA implies about 54 (60 minus 6).
  - The CSV has 53 continental names, which might fall to about 52 if Minneapolis and St Paul count as one city.
  - So **about 2-3 continental targets are still unnamed**, if every AP-listed city really was struck.
- **Bombs:** LA took 3 bombs. If every other city took 1, then 60 cities would need 62 bombs, not 61. FCDA must therefore count at least one bomb as covering a twin city (Minneapolis-St Paul is the obvious case, and possibly Chicago-Gary under one plume). The bomb count was not resolved further.
- **Number of cities by count:**
  - 61 in AP/UP stories (cities + territories).
  - 60 in FCDA.
  - 49 continental + 6 territorial in the pre-exercise UP story (*Nome Nugget* 13 Jun), described as "Washington and 48 other selected target cities … along with six more in Alaska, Hawaii, Puerto Rico and the Canal Zone".
  - "49 knew, 12 added" (*St. Louis Post-Dispatch*).
  - "42 knew + 7 surprise" (AP 15 Jun).
- **The figures do not line up exactly.** FCDA later counts 11 surprise cities, and one city that was not selected took part anyway.
- **Megaton ground bursts:** FCDA says 14 cities. The map's plumes are Houston, Atlanta, St Louis, Kansas City, Chicago (Gary), Detroit, Cleveland, Buffalo, Philadelphia (two plumes, around Philadelphia and southeast over Delaware), NYC, Minneapolis-St Paul, Los Angeles, San Francisco and Montreal. That gives about 14 US plumes plus Montreal, which matches if Chicago and Gary are one burst and Philadelphia's two plumes count separately, or Washington is counted. Washington, however, was an air burst.

## Open issues

- **Unnamed map symbols.** The FCDA map has unlabelled "other target" symbols in places that no source opened names:
  - Wisconsin (Milwaukee?)
  - Central and southern Ohio, 2 symbols (Columbus? Dayton or Cincinnati?)
  - East Tennessee (Knoxville or Oak Ridge?)
  - Possibly Indiana

  These are probably the missing 2-3 continental cities, but they are **not** in the CSV because no source names them.
- **AP names with no symbol.** Several AP-listed cities, especially in upstate New York and Connecticut, have no separate symbol on the map. They may have been supporting or participating cities rather than struck ones. All AP rows are therefore marked secondary.
- **New Orleans** is reported as hit but has no visible symbol on the map.
- **Yields:** yields for about 55 cities remain unknown. The best remaining primary source is FCDA's mimeographed "Report on Operation Alert 1955" (4 Jan 1956) or FCDA's "basic attack pattern" (developed August 1954, per the hearing exhibit p.1490). Neither was found online.
- **Better newspaper sources.** Large-city papers of 15-16 Jun 1955 (NYT, Washington Post, Chicago Tribune) probably printed per-city yields. They are not on archive.org or Chronicling America in OCR form that could be reached.
- **Inset labels.** Alaska, Hawaii, Puerto Rico and Canal Zone inset labels on hearing p.1495 cannot be read. A better scan (a GPO paper copy or HathiTrust) might confirm Anchorage, Fairbanks, Juneau, Honolulu, San Juan and Balboa.
- **Unchecked mentions.** Other city mentions in Operation Alert stories, such as Richmond (in the Washington fallout path) and Oak Ridge, were checked only by keyword search and not added.

## Files added (data/raw/civil_defence/)

| file | sha256 |
|---|---|
| `US_Congress_Hearings_1956_p1495_Appendix1_Operation_Alert_1955_attack_pattern_n464.jpg` | `30ce8eeb9494a804ae9e1af7297d093b8e6f1921a1a71d0c86e141649d5aa8fd` |
| `LOC_KeyWestCitizen_1955-06-15_p2_ocr.json` | `2128b437e3867c5514f424c51b6545cbaf2544b46c270761774982fc0a78f544` |
| `LOC_KeyWestCitizen_1955-06-17_p5_ocr.json` | `b936453683799b8080df899e76af20e2ee72fb72aea1940d0f19d0f6be9e371d` |
| `LOC_EveningStar_1955-06-15_p1_ocr.json` | `cb54151d11483584c2425eaf90b43f34035c4897715d2e53e7333fc3c2df005d` |
| `LOC_EveningStar_1955-06-16_p4_ocr.json` | `5390750fcf906071b20380af137a0c2ce7952837484534dd225c72251677dc8b` |
| `LOC_NomeNugget_1955-06-13_p3_ocr.json` | `aee197daaacbe0ffc289c79683ce032dbd144b5c9d963f747e5aa730cd71e089` |
| `LOC_NomeNugget_1955-06-15_p1_ocr.json` | `3b06536043e1edd16e332ef05f6bd757ba27f59491e82dbd7fe746914c2b865b` |
| `LOC_NomeNugget_1955-06-17_p3_ocr.json` | `48adb94692a97528b30fa053602cf939335f35cfb5fdf101bca66cd8a941bb88` |
| `LOC_ArizonaSun_1955-06-17_p1_ocr.json` | `bcf19fea923dc7d229832b0aec0cdc76e00a43d58adb302fad09fbe4a9f00078` |
| `Dixon_Evening_Telegraph_1955-06-16_djvu.txt` | `f28ca6a0046af3c8bf7cf62698f0000772ace847d31ad49722988c93eb72ab30` |
| `operation_alert_1955_fetch_manifest.tsv` | every URL fetched in this pass, with sha256 |

The `LOC_*.json` files are the raw loc.gov full-text responses, `{segment: {full_text: …}}`.

CSV sha256: `cd_1955_operation_alert_full.csv` `a6b1a95a22d531bd984cfcb8c6860ddc622cdca3fb9d5dfaaa1714e4426508a2`. The original
`cd_1955_operation_alert.csv` is unchanged (`12fc16ee…99cf`).
