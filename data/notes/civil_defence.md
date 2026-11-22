# Civil-defence (defender) target assumptions: source cards

Worker: civil-defence sources. Retrieved 2026-10-03 (UTC) unless noted. All raw files are in
`data/raw/civil_defence/`. The SHA-256 of each file used is given on its card. Label CSVs are in
`data/curated/labels/` (`cd_*` = defender lists, `rec_*` = outside reconstructions).
Provenance in the label CSVs is `defender` for government or exercise assumptions. Lat/lon are always blank.

---

## 1. FEMA, *Nuclear Attack Planning Base - 1990 (NAPB-90), Final Project Report* (April 1987)

- **Files**
  - `FEMA_1990_Nuclear_attack_planning_base_(NAPB-90).pdf`, sha256 `3e884fd8…36bb0`, 510 pp.,
    1-bit 200-ppi JBIG2 scans. This is a compilation (created 2021-04-01). Its layout:

    | PDF pages | Content |
    |---|---|
    | p.1 | cover |
    | p.2 | FEMA FOIA release letter (27 Apr 2005) |
    | pp.3-12 | front matter + executive summary (FAS) |
    | pp.13-18 | Part 1 (FAS part1.pdf) |
    | pp.19-60 | Parts 2 + 3 (printed pp.7-48) |
    | pp.61-292 | **Annex A**, Direct Effects & Fire Risk (FAS annexa.pdf) |
    | pp.293-508 | **Annex B**, Fallout Risk |

    Annex B (pp.293-508) comes from the archive.org item
    `1990FEMADirectEffectsFireRiskStatisticsMapsNAPB90Annexa216p`. That item is *mislabelled*
    "Annex A": its cover page (PDF p.293) reads "Annex B Fallout Risk Statistics & Maps".
  - `NAPB90_FAS_execsum.html` (https://nuke.fas.org/guide/usa/napb-90/execsum.html), sha256 `0fd20598…c142d`.
  - `NAPB90_archiveorg_504pg_djvu.txt`, sha256 `852a65ab…0cc397`. This is the OCR of archive.org item
    `nuclearattackplanningbase1990finalreport504pg` (504 pp., full report).
- **Not obtained:** FAS PDFs (front/part1-3/annexa/annexb.pdf). nuke.fas.org answers HTTP 202 with
  `x-amzn-waf-action: challenge` (a bot challenge, not bypassed). Their content is in the compilation above.
- **Status:** obtained.

### 1a. Target classes (`cd_1987_napb90_classes.csv`, 12 rows = 10 classes + 1 subtotal + 1 total)

- **Source:** PDF p.21 (printed p.9, Part 2.B) and PDF p.22 (printed p.10). Read from the page image.
  Matches the archive.org OCR.
- **Verified:**
  - "Ten target classes containing 6,139 aim points were included in an **initial** target set."
  - ICBM silos + LCCs 1,228; Air Force 199; Army 159; Navy 110 (subtotal "(468)"); key
    military-support industries 325; political infrastructure 44; ports 106; refineries 242;
    electric power 1,632; chemical 2,094.
- **Correction to earlier claim:**
  - 6,139 is the **pre-editing initial set**, not the final aimpoint list. "Other military 468" is
    three printed classes. There are ten classes, not eight.
  - Parts 1-3 print **no post-edit aimpoint or weapon total**. The only aggregate is "average assumed
    yield ... slightly less than 1 megaton" (PDF p.16).
- **Editing rules:**
  - Titan complexes deleted (Little Rock AFB, McConnell AFB, Davis-Monthan AFB).
  - Refineries: those under 75,000 bbl/day dropped, rank-order degradation to 75%. *Rule-based.*
  - Power plants: rank-ordered by capacity, attacked until 75% degradation is assured. *Rule-based.*
  - Chemical class: replaced by SIC-281 "basic chemicals" producers (1968 SRI study). *Rule-based on
    the industry code.*
  - Military, political and port classes: no rule printed. *Judgment / unknown.*
- **Context (PDF p.17, printed p.5):**
  - TR-82 classes, in priority order: US military installations; military-support industry,
    transportation and logistics; other basic industries; **"Population concentrations of 50,000 or
    more (Bureau of Census urbanized areas) not otherwise targeted"**. The last is a rule-based
    population class. It is not extracted.
  - NAPB-90 adds ports, refineries, political, electric power and chemicals. It has no population class.

### 1b. County tables

- **Annex A, Part 2 "Highest Direct Effects Risk by County":**
  - Location: PDF pp.135-292 (printed A-85 to ~A-301). National summary at pp.135-136, regional
    summaries interleaved, state tables from p.138 (Connecticut, A-89). Georgia starts at p.173 (A-145).
    Pages are scanned rotated 90°.
  - Layout: one row per county. Columns: COUNTY | VERY HIGH (GT 10 psi) pop, area | HIGH (5-10) pop,
    area | MEDIUM (2-5) pop, area | LOW/NO* (0.5-2) pop, area. The **whole county** population (1985
    est.) and land area (sq mi) are printed in the single column of the highest risk level reached
    anywhere in the county. An asterisk on the area means "<0.5 psi", i.e. NO risk.
  - Puerto Rico and Virgin Islands pages read "DATA WILL BE FURNISHED SEPARATELY".
- **Annex B fallout tables:**
  - Location: PDF pp.298-508. Each state has a map page plus a table page (not rotated).
  - Columns: VERY HIGH [GT 15000R], HIGH [6000-15000R], MEDIUM [3000-6000R], LOW [LT 3000R], each
    pop/area. Whole county in one column.
  - The TOC marks AR, LA, OK, TX, MS, KS and the Region IV/VI/VII summaries as "*Interim data; to be
    corrected".
- **Counties:** about 3,100-3,200 rows per annex. This is an estimate (~145 state pages × ≤25 rows),
  not counted.
- **Pilot (`cd_1987_napb90_county_pilot.csv`, 33 rows):**
  - Connecticut, PDF p.138 (A-89), 8 counties. Rows sum exactly to the printed state totals
    (VH 2,775,954 / 3,062 sq mi; LOW 389,507 / 1,810).
  - Georgia, PDF p.173 (A-145), first 25 counties.
  - The derived class column comes from the filled column plus the asterisk.
- **Sample renders:** p.138 and p.173 (Annex A), p.301 (Annex B, CT fallout).
- **Effort estimate:**
  - The archive.org OCR of the rotated tables is garbage. Vision transcription needs about 3-5 min per
    page with verification: Annex A ≈ 145 pages ≈ 8-12 h, Annex B ≈ 100-110 pages ≈ 6-9 h.
  - With a real OCR engine (Tesseract on 300-dpi rotated crops; the typeface is clean monospace) plus
    total-checks against the printed state totals: about 3-5 h.

### 1c. State maps

- **Location and layout:**
  - Annex A Part 1, A-7 to A-79 (PDF pp.67-~133). One "DIRECT EFFECTS RISK AREAS" map per state or
    territory, interleaved with regional tables.
  - Legend: black area ≥5.0 psi; ringed ≥2.0 psi; unringed (stippled) ≥0.5 psi.
  - Scale varies by state (Georgia 1:2,600,000). Albers Equal Area projection. County boundaries drawn.
  - DC, Puerto Rico and Virgin Islands read "MAP WILL BE FURNISHED SEPARATELY".
- **Georeferencing:** feasible with county corners as control points (the projection is stated). Blob
  centres give approximate DGZs. Overlapping envelopes merge (e.g. Atlanta), so counts per blob are
  lower bounds. Individual aimpoints are not marked.
- **Annex B maps:** show fallout-risk county shading only.

### 1d. Other volumes

- archive.org searches for "NAPB-90", "nuclear attack planning base", "aimpoint list" and "aim point
  list" AND FEMA, plus the OSTI API, found **no "National Aimpoint List" volume**.
- The only NAPB items are the two archive.org scans named above.
- Status of the aimpoint list: not obtained (no public copy located).

---

## 2. UK "Probable nuclear targets in the United Kingdom" (1972)

- **Discovery API:** `HO 322/785` "Probable nuclear targets in the United Kingdom: assumptions for
  planning", 1969-1972, former ref CDP 67 237/10/4. closureStatus **D**, held by "Creating government
  department or its successor", i.e. **retained**, not at Kew, not digitised.
- **Related files, also retained:**
  - `AIR 2/18143` "Nuclear targets in the UK" (1967-74)
  - `ADM 1/27615` "Nuclear targets" (1957-69)
  - `HO 322/1248` "home defence planning assumptions; attack patterns" (1981-84)
- **Open:** `DEFE 69/585` "Targets for Allied nuclear offensive: probable nuclear targets in UK"
  (1957-69), opened 31/03/2016, not digitised.
- **2014 coverage:** BBC/Guardian coverage could not be located. The BBC search renders by JS; the
  Guardian API requires a key. The Arnold 2014 PhD thesis (London Met, 341 pp., sha256 `4f4f0264…5a71`)
  does not reproduce the list.
- **Status:** not obtained. **No CSV written.** The "106 sites / 38 towns / 37 air bases…" figures
  remain unverified.

---

## 3. Square Leg (1980) and Hard Rock (1982)

- **Files:**
  - `Campbell_1980_NewStatesman_WW3_exclusive_preview.pdf`: D. Campbell, *New Statesman* 3 Oct 1980,
    map "POST WAR BRITAIN", p.5. https://www.duncancampbell.org/menu/journalism/newstatesman/newstatesman-1980/WW3.pdf,
    sha256 `d3c43a63…c0ea`.
  - `Campbell_1981_NewStatesman_Scotlands_nuclear_targets.pdf`: *NS* 6 Mar 1981, map "POST WAR
    SCOTLAND", p.11, sha256 `a155d304…927e`.
  - Also used: `Campbell_Edwards_1980_NewStatesman_Square_Leg_caught_out.pdf` (`3366f02e…6ffa`) and
    Wikipedia wikitext of "Square Leg" (rev 1369733924, `fb18530f…c33b`) and "Hard Rock (exercise)"
    (rev 1341149254, `5345f707…5af1`).
- **CSV:** `cd_1980_square_leg.csv`, **95 rows** (England & Wales 76 map labels, Scotland 19).
  - **SECONDARY:** a journalist's reproduction of the official bomb plot ("copied from a variety of
    official sources including maps on display at the Basingstoke and Wanstead bunkers"). This is
    flagged on every row.
  - Weapons are filled only where "(n)" is printed or the text states it. Yields are filled only where
    stated: Faslane 5 Mt; Gareloch, Coulport and Clyde 1 Mt; Canvey Island 5 Mt.
  - Burst type is noted for Scotland only. England & Wales markers are ambiguous in the halftone.
  - Northern Ireland: never released (NS 6 Mar 1981).
- **Totals:** NS 1981 gives "125 weapons with a total yield of around 200 Megatons". Wikipedia cites
  150 weapons / 280.5 Mt (South Yorkshire CC 1984) and a 127-strike partial plot (Openshaw & Steadman).
  The earlier claim of "~131 weapons, 205 Mt" is not confirmed by any document opened.
- **Hard Rock:**
  - TNA files HO 322/983-1020 are open (1981-82) but not digitised.
  - Wikipedia records Campbell's statement that London, Manchester, Edinburgh, Liverpool, Bristol,
    Cardiff, Holy Loch and Faslane were omitted ("politically undesirable" targets removed).
  - No target list was obtained. No CSV written.
- **Selection:** judgment-based (exercise directing staff), with acknowledged political editing.

---

## 4. Operation Alert 1955 (FCDA)

- **Primary sources:**
  - `FCDA_1956_Annual_report_for_1955.pdf` (archive.org `fcda1955annualreportfor1955`, folkscanomy,
    not lending-restricted), sha256 `06132cd4…fa57930`. Its OCR is `…_djvu.txt` (`87f13a21…50a0`).
  - Congressional hearings "Civil Defense for National Survival" (Apr-May 1956), Exhibit 5 "Report on
    Operation Alert, 1955", pp.1490-1492. OCR is
    `US_Congress_Hearings_1956-04_05_Operation_Alert_exhibit_djvu.txt`, `ae4f3769…07db1e7`.
- **Verified:**
  - "60 cities in the United States, Hawaii, Puerto Rico, the Canal Zone, and Alaska were struck by
    61 bombs, ranging in size from 20 kilotons to 5 megatons"; 11 cities not told in advance
    (report p.32).
  - "14 of the attacked cities were struck by megaton bombs bursting at ground level".
  - LA: "3, 1-megaton bombs" (hearing p.1433).
  - Newspapers say "61 cities" (55 continental + 6 territories) and "49 knew, 12 added": *St. Louis
    Post-Dispatch* 16 Jun 1955 (`6a7ee5d8…db1e7`). The *Lincoln Star* 16 Jun 1955 (`1263f7e5…5af5`)
    has no list.
- **Correction:** 61 is the number of **bombs**. FCDA counts **60 cities**. No document opened gives
  a per-city yield list. The "5 Mt on New York" claim is unverified.
- **CSV:** `cd_1955_operation_alert.csv`, **16 rows**.
  - These are the cities *labelled* on the official map "ATTACK PATTERN OPERATION ALERT-1955" (printed
    p.31, PDF p.39): 15 US labels + Montreal. These are the megaton ground-burst cities with fallout
    plumes.
  - The ~45 "OTHER TARGETS BOMBED" symbols are unlabelled and were not transcribed.
  - Appendix 1 of the hearing report (the attack pattern) is not in the OCR.
- **Selection:** judgment (FCDA "basic attack pattern", Aug 1954).
- **Open issue:** the full 60-city list probably sits in FCDA "Report on Operation Alert 1955" (mimeo,
  4 Jan 1956) or the hearing PDF's Appendix 1 (142 MB, not downloaded).

---

## 5. Canada 1956 evacuation (target) areas

- **Files:**
  - `Canada_HoC_Debates_1956_22-3_vol7_extract_1956_1.txt`: a copy of the session-supplied extract,
    origin not recorded. sha256 `d036cd97…7fd57930`.
  - `Canadiana_search_1956_evacuation_areas.html` (`53bbfc99…77e8`). Full-text search on
    parl.canadiana.ca matches the passage only in **House of Commons Debates, 22nd Parl., 3rd Sess.,
    Vol. 7** (`oop.debates_CDC2203_07`).
- **CSV:** `cd_1956_canada_target_areas.csv`, **13 rows**: Montreal, Toronto, Ottawa-Hull, Windsor,
  Niagara Falls, Halifax, Vancouver, Hamilton, Winnipeg, Edmonton, Quebec city, Saint John (N.B.),
  Victoria. Source: extract lines 265-266, "Supply—Civil Defence".
- **Open issue:** exact sitting date and printed page are **not verified**. The extract has no
  date/page. Suez questions in the same extract put it after 26 Jul 1956 (the session ended mid-Aug
  1956). The Canadiana page-level lookup returned HTTP 503. The speaker is not named in the extract.
- **Selection:** judgment (largest urban areas).

---

## 6. TR-82 / CRP-2B / high-risk area reports

- **OSTI ids differ from earlier claims:**
  - **OSTI 5736224 is not TR-82.** It is Sager, Hulburt & Sullivan, *High Risk Areas of the United
    States Identified by Congressional District*, SPC 444, May 1979 (AD-A069521). Files:
    `OSTI_biblio_5736224.html` (`dd241f93…02faf`) and `DTIC_ADA069521_djvu.txt` (`6230f166…0d89`).
    It maps the TR-82 blast areas by congressional district (cross-hatched state maps, 43 pp.). No
    aimpoint list.
  - **OSTI 7361159 = ORNL-5041** (Haaland, Chester & Wigner, June 1976). File
    `ORNL-5041_…OSTI7361159.pdf` (`ebaa8cf6…f9d70`).
- **CRP-2B, from ORNL-5041 Table 3.1 (printed p.21, PDF p.37):**
  - The DCPA attack: 1,444 weapons, 6,559 Mt, of which 5,051 Mt are ground bursts. Classes:

    | Target type | Weapons | Yield each | Burst | Total |
    |---|---|---|---|---|
    | ICBM fields | 127 | 20 Mt | ground | 2,540 Mt |
    | SAC AFB/SSBN support | 46 + 1 | 1 Mt / 2 Mt | ground | 48 Mt |
    | CRP/OHVM ("Other High Value Military") | 183 + 1 | 1 Mt / 20 Mt | ground | 203 Mt |
    | CRP/UI ("Urban-Industrial") | 113 | 20 Mt | ground | 2,260 Mt |
    | CRP/UI | 614 | 1 Mt | air | 614 Mt |
    | CRP/UI | 183 + 1 | 2 Mt / 3 Mt | air | 369 Mt |
    | CRP/UI | 175 | 3 Mt | air | 525 Mt |

  - ICBM aim points deliberately "do not designate actual locations of silos".
  - Priority list = the TR-82 four classes, including **population concentrations of 50,000 or
    greater** (rule-based).
  - Not extracted as a CSV (no per-target list).
- **TR-82 itself:** not obtained. DTIC ADA067231 (SPC 409, *Civil-Defense Needs of High-Risk Areas*,
  1979; OCR `82955528…7e74e`) states the DCPA counterforce set: "six MINUTEMAN missile fields, the
  three TITAN missile fields, the 36 Strategic Air Command bases, and the two strategic submarine
  bases" + ~80 research facilities. A named list may be in its appendices (PDF not downloaded).
- **Rule-based vs judgment:** UI/population classes are rule-based (urbanized areas ≥50,000).
  Military classes are an installation inventory.

---

## 7. Reconstructions (class counts only)

- **`rec_2002_helfand_classes.csv` (15 rows):**
  - Source: Helfand et al. 2002 (`667f0dfe…ce5b`), Table 1, PDF p.3. Fourteen classes, 1,249 targets,
    2,000 × 550-kt warheads.
  - Electric power: 342 plants ≈ 68% of capacity (rule).
  - The 500-warhead population-maximising NMD scenario is excluded.
- **`rec_2001_nrdc_classes.csv` (9 rows):**
  - Source: NRDC 2001 (`ec45e72b…bfc0`), Figure 4.83, PDF p.123 (printed p.111). Warheads by category
    for MAO-NF: silo ICBM 720, road-mobile 100, rail-mobile 5, SSBN/naval 137, aviation 73, warhead
    storage 128, design/production 29, L-C3 97; total 1,289.
  - The counts are **warheads, not aimpoints**, so the `aimpoints` column is blank.
  - Chapter 5 countervalue attacks are excluded.

## Other files fetched (sha256)

- `wikipedia_Square_Leg.json` `082ba536…815a`; `wikipedia_Hard_Rock_(exercise).json` `8d3aa254…a5d25e`
- `OSTI_biblio_7361159.html` `ee8cfa68…98067`
- FEMA-196 PDF `9ddf7911…2828`: not used in this pass.

---

# Second pass (2026-11-22): defenders' lists

Raw files are in `data/raw/civil_defence/p2/`; SHA-256 of each file used is in
`data/sources.d/civil_defence.yaml`. Lat/lon are always blank.

## 8. Canada 1962: sixteen designated possible target areas (`cd_1962_canada_target_areas.csv`, 16 rows)

- **Primary source:** Lt.-Col. B. W. Lee, "The Organization and Role of the Target Area Headquarters",
  *EMO National Digest* 2(3), June 1962, PDF p.12 (printed p.9),
  https://www.publicsafety.gc.ca/lbrr/archives/emo%202-3-1962-eng.pdf. "One has been established in the
  vicinity of each of the sixteen Canadian cities which have been designated as possible target areas",
  then a list of city—interim TAHQ location (St. John's—Holyrood ... Victoria—Duncan). The same article
  says DSO&P assumed "an all out nuclear attack on Canada would affect at least sixteen of our
  large populated centers".
- **Corroboration:** EMO *Blueprint for Survival No. 5, Survival in Likely Target Areas* (Queen's Printer,
  1962, Cat. No. S83-1/6), PDF p.5 (checked on the page image): the same 16 cities, "the more likely target
  areas". https://archive.org/download/31761117081935/31761117081935.pdf. Hansard 23 Mar 1962 p.2137
  (canadiana `oop.debates_HOC2405_03`, image 91) confirms the booklet was issued that month.
- **Extraction:** one row per city in the Digest's order; Blueprint spelling in `notes`.
- **Doubts:** the TAHQ A/B/C size bands (≥750k / 250–750k / <250k) are a sizing rule, not a selection rule;
  the per-city type is not printed. Compared with 1956 (13 areas) the list adds Calgary, London, St. John's.

## Exercise Tocsin B (Canada, 13–14 Nov 1961): no list found

- Hansard 29 Jan 1962 p.301 (image 303 of `oop.debates_HOC2405_01`): Mr Pitman's Question No. 35 asks
  "What centres in Canada were supposedly hit by bombs?"; it was **passed as an order for return**, so the
  answer is a sessional paper, not in the Debates. Not found online.
- Hansard 23 Mar 1962 p.2126 (image 80 of `oop.debates_HOC2405_03`), Pitman: "there were only 17 weapons
  dropped with a total megatonnage of some 75. All the bombs were from one to five megatons or only one
  was of 10 megatons"; "Only six bombs were delivered by I.C.B.M.'s"; "only 350 individual aircraft
  attacking". Totals only, not by place, so no validation table.
- Hansard 29 Jan 1962 p.291: of 828 federal buildings, "281 in areas listed as possible target areas";
  214 "destroyed under the circumstances assumed in exercise Tocsin B".
- *EMO National Digest* 1(6), Dec 1961 (Tocsin B issue) has photos and the PM's address, no target list.
- Canadiana gives page-level search (`/search/page?q0.0=…&pkey=…`) but no OCR text, so pages were read from
  IIIF images.

## 9. UK 1963: dispersal areas (`cd_1963_uk_dispersal_areas.csv`, 19 rows)

- **Source:** HC Deb 28 March 1963 vol 674 cc179-80W (Corfield to Noel-Baker),
  https://api.parliament.uk/historic-hansard/written-answers/1963/mar/28/civil-defence-evacuation:
  "a list of the 19 areas from which dispersal would take place if the scheme were put into effect.
  Dispersal Areas (Named mostly after the main Town or City they contain)", followed by the 19 names.
- **Context:** the scheme was for about 9½ million people in the priority classes "from certain towns in
  England and Wales" (HC Deb 2 May 1963 cc1299-300), under the MHLG circular of 16 Oct 1962 (Circular
  15/62 of 28 Mar 1962 is also cited). Earlier answers (1957–61) speak of 12 million and a review.
- **Doubts:** an evacuation area is a danger expectation, not an aim point. Scotland (Glasgow, Clyde,
  Edinburgh, etc.) was planned separately and is not in the list. Selection criterion not stated.

## 10. New South Wales 1968: assumed target zones (`cd_1968_nsw_target_zones.csv`, 3 rows)

- **Source:** R. Bale (Director of Civil Defence, Canberra), "Civil Defence in Australia", *EMO National
  Digest* 8(6), Dec 1968–Jan 1969, PDF p.16 (printed p.13),
  https://publicsafety.gc.ca/lbrr/archives/emo%208-6-1968-69-eng.pdf: "Planning was to proceed on the
  assumption of three possible target zones - the cities of Sydney, Newcastle and Wollongong"; "The zones
  are the assumed target areas of Sydney, Newcastle and Wollongong".
- The same article (PDF pp.14–20) names no target areas for Victoria, Queensland, SA, WA, Tasmania, NT or
  ACT, and quotes the 1959 Commonwealth policy that "it is unlikely that Australia would be a primary target".

## 11. Exercise Hard Rock 1982 (`cd_1982_hard_rock_partial.csv`, 12 rows: 3 hit, 9 not attacked)

- **Source:** D. Campbell, "Bad day at Hard Rock", *New Statesman* 17 Sep 1982 (author's 1-page PDF),
  https://www.duncancampbell.org/menu/journalism/newstatesman/newstatesman-1982/hard%20rock.pdf.
  Planning (June 1981) began with 105 targets; after deletions the attack was "scaled down to only 54
  weapons, delivering about 48 Megatons". Named hits: Mallaig, Builth Wells, "near Bideford". Not
  attacked: London, Manchester, Edinburgh, Liverpool, Bristol, Cardiff, Sheffield; Holy Loch and Faslane.
- "Armageddon postponed" (NS, Sep 1982) gives "Fifty nuclear targets".
- **Not obtained:** the "complete 'bomb plots' ... shown overleaf" were printed on the following magazine
  pages, which are not in the author's PDF. Campbell's *War Plan UK* (1982/83) is not publicly online: the
  archive.org item `WarPlanUK` is a compilation of other government files despite its name, and
  `warplanuk0000camp` is a lending-library copy (not used).
- `use: reference` because the rows are a fragment and the selected=0 rows are scenario omissions.

## 12. China: national key civil-air-defence cities (`cd_2021_china_key_cad_cities.csv`, 4 rows)

- The national classification (国家一类/二类/三类人民防空重点城市, set by the State Council and CMC under
  人民防空法 art. 11) is not published. Rows are cities whose own official pages state a class:
  - Nanjing, class 1: 解放军报 article on mod.gov.cn, 2021-06-02.
  - Yantai, class 1: Yantai civil-air-defence office page dated 2004-01-01.
  - Weihai, class 1: Weihai defence-mobilisation office glossary, 2014-08-11.
  - Quanzhou, class 2: Quanzhou government news, 2018-09-21.
- **Found in search but could not be opened** (503/404/empty from this container): Chongqing (class 1,
  cq.gov.cn 2020-11-02 and 2023-06-05), Hangzhou (class 1, rf.hangzhou.gov.cn 2022-06-15), Xinxiang
  (class 3, rfb.xinxiang.gov.cn/lylb/info/16288). A Baidu Q&A list of all three classes exists but is
  unsourced and contradicts official pages (e.g. Chongqing, Nanjing, Yantai); not used.
- Doubts: the date of each designation is unknown; classes may have changed. Very partial.

## 13. Noted, not extracted

- **FCDA Critical Target Areas (1956–58 annual reports):** 72 CTAs and 116 other Target Areas. Rule-based:
  "Critical Target Areas are those Standard Metropolitan Areas having 40,000 or more manufacturing
  employees" plus Washington DC; Target Areas = all SMAs and state capitals (FCDA Annual Report 1957,
  pp.7-8). Not extracted (rule). The 1957 report also prints FCDA's eight target categories (pp.4-5).
- **Operation Alert 1956–1961:** no per-city list reached. FCDA annual reports for 1956–58 give no
  attack pattern. Newspapers (Chronicling America): 1956, "76 U.S cities" (*Milford Chronicle* 20 Jul
  1956 p.1) or "73 areas in the United States and 25 in Canada" (*Key West Citizen* 20 Jul 1956 p.1,
  AP; names only Tampa/MacDill and Tallahassee); 1957, "166 H-bombs were dropped on 155 targets", "191
  vital U.S. targets" (*Nome Nugget* 15 Jul 1957 p.1). CIA Reading Room items on archive.org (OA 1956
  briefing, OA 1957 report, OA 1959 concept) are agency-participation memos without target lists (one
  says the 1956 pattern embraced "over 70 critical target areas").
- **DCPA TR-82 / high-risk areas:** DTIC ADA067231 (SPC 409, 1979, full PDF from archive.org) gives the
  counterforce set by type (six Minuteman fields, three Titan, 36 SAC bases, two SSBN bases) and county
  CRP status for missile fields, but no national named list. TR-82 itself not found on OSTI or archive.org.
- **Sweden / Norway:** Prop. 1956:185 discusses *utrymningsorter* but no named list was found in what
  search returned; Norwegian evacuation lists not found. Netherlands, FRG, Switzerland, Japan, New
  Zealand: not found in the time available.
