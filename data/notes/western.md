# Western target lists (US / UK / France / NATO): source cards

Worker: western lists. Session date: 2026-10-03 (all retrievals 2026-10-03, between 14:59 and 15:25 UTC).
Downloads are in `data/raw/western/`. The sha256 values below were computed after download.
Rule used throughout: no CSV row without a page reference and a verbatim quote from a document I opened.
All PDFs below are image scans unless stated. I read them as rendered PNGs; no OCR was used.

Outputs written:

| file | rows |
|---|---|
| `data/curated/labels/us_1945_target_committee.csv` | 42 |
| `data/curated/labels/us_1964_china_nuclear.csv` | 2 |
| `data/curated/validation_siop62.csv` | 8 |

No CSV for: JIC 329/1, Norstad 1945, France 1959, Taiwan Strait 1958, MacArthur 1950, UK, WINTEX 89 (see the cards).

---

## 1. NSA, "The Atomic Bomb and the End of World War II" (2020 update) + 2025 "80 Years Later" posting

- URLs: https://nsarchive.gwu.edu/briefing-book/nuclear-vault/2020-08-04/atomic-bomb-end-world-war-ii (fetched as /node/3393;
  the `/japan-nuclear-vault/` path returns 404); 2025 posting:
  https://nsarchive.gwu.edu/briefing-book/nuclear-vault/2025-08-05/atomic-bombings-japan-and-end-world-war-ii-80-years-later
  (/node/4683). Documents: https://nsarchive.gwu.edu/documents/atomic-bomb-end-world-war-ii/NNN.pdf
- Status: **obtained**.
- Files (`nsa_atomic_bomb_end_ww2/`), sha256:
  - briefing_book_page.html `67abe0636e8f41bc78dbf7042ed995da88515a6257ad96f4e3130ae9f8679ed4`
  - doc009.pdf (Target Cttee notes, 27 Apr meeting, dated 2 May 1945) `d5b481060dbfa822750b9d26ea82b1aeddd23e22e520d96ca5288578e3f66755`
  - doc011.pdf (Derry/Ramsey summary of 10-11 May meetings, 12 May 1945) `07bd94cf39b661a075b68ae99f955a4c899b34bd4ae2bc76c10be4bc4f60ccc3`
  - doc012.pdf (Stimson diary 14-15 May; downloaded, not read) `f1b9e3b3c028f261b8d9feff5c85668494f6abc42fba822aef046b05d083a69c`
  - doc015.pdf (minutes, 3rd Target Cttee meeting, 28 May 1945) `d06f000895322de7915a8413e043cdb8fb16cb3a411638ccd06999cbd38785ef`
  - doc016.pdf (Norstad to CG XXI Bomber Command, 29 May 1945) `7749d7725177b96505b47581689e69f53e1fd9feb12168d312a2ccea66f6807d`
  - doc046e_2025.pdf (Groves, "Plan of Operations - Atomic Fission Bomb", 24 Jul 1945; has OCR text layer; from
    https://nsarchive.gwu.edu/sites/default/files/documents/Doc%2046E%201945-07-24%20%20RG%20319%20JONES%20MANHATTAN%20BX%2016%20MANHATTAN%20BOMB%20ORGANIZATION%20AND%20MATERIALS%20PROCUREMENT-ocr.pdf)
    `cf40e32b6f41f98fd7306a3dffa0f2a9287f03fcd0b2f8ab0bb8344955c330d6`
  - doc047.pdf (Truman Potsdam diary, Bernstein transcription, FSJ 1980) `c8ca3ee14508e964ddbe33a0e51b508b825507f1150fb16aa6d28b54af45186a`
  - doc048.pdf (Stimson diary 16-25 Jul; 17 pp.; downloaded, **not read**) `552f71c108904b6e8d374cf080f69e3b0deb90e9935e0e35ca699fb724df7596`
  - doc059.pdf (MAGIC diplomatic summary 5 Aug 1945; downloaded by mistake, irrelevant) `503cb8c4f0450b63bb847e0f8de404965bc3b5ebe5c40fa2ce53c3a13fd3df65`
  - doc060a.pdf `a2ec4f04531ae7607a996e3be3bc76f62bb6008dcc082448b698fbde3cee3263`; doc060b.pdf (Stone to Arnold 24 Jul) `cccd42e79fced2f747597d56f8552cbb2de3cca26e2dbd049409ba814b9c1b29`;
    doc060c.pdf (WAR 37683, 24 Jul) `e2057f7f0805c4d5fc59377a2a8b41a23992b3e7148e69da86d178855afca2e0`; doc060d.pdf `a704986ee52c3917dcfe585a75865dfe78bba8cb38623b6e75bcf173b262a99b`;
    doc060e.pdf (Handy to Spaatz, dated 25 Jul 1945) `4c70b1ce5de29fe3d8b88613930b8cc0f5a5d2ea70714336221b32993ad86ce1`
  - doc072a.pdf `4468e86d122184857fd88f88af96f9236577d56520234637e3172e69012d9902`; doc072b.pdf `e0631b2c188e9bc087349de96dbf56363409bc97409b71a5eb6118591a692b17`; doc072c.pdf `074c70812859bfacd63fa18077301f941d372455a4965792cc5a446fb51a1764`
  - doc082.pdf (Groves to Marshall 10 Aug 1945) `f623350073c2dbf9fa8fa62de9eb78a47bfda3c6dfd2c89d5b87d1590f6ccafe`
  - doc087.pdf (Hull-Seeman phone transcript 13 Aug 1945) `d0b0c66d0b85040a82f70fd93e73694fd476af1d676455c2358ca9168c60eaa0`
- What the documents establish:
  - 27 Apr 1945 (Doc 9, PDF p5): 17 "areas ... considered appropriate for study": Tokyo Bay, Kawasaki, Yokohama, Nagoya,
    Osaka, Kobe, Kyoto, Hiroshima, Kure, Yawata, Kokura, "Shimosedka" [sic, = Shimonoseki], Yamaguchi, Kumamoto, Fukuoka,
    Nagasaki, Sasebo. No selection was made at this meeting. Criteria: urban areas at least 3 miles in diameter, between
    Tokyo and Nagasaki, high strategic value. Note: the PDF pages are out of order (PDF p3 is the document's p4, and PDF p4 is its p3).
  - 10-11 May (Doc 11, PDF pp4-6): five targets the Air Forces would reserve: Kyoto (AA), Hiroshima (AA), Yokohama (A),
    Kokura Arsenal (A), Niigata (B). The Emperor's palace was discussed and "not recommend[ed]". The "first four choices" were
    Kyoto, Hiroshima, Yokohama and Kokura Arsenal (Niigata was left out at this stage). The document gives reasons for each.
  - 28 May (Doc 15, PDF p3): "the 3 reserved targets ... were announced". Stearns presented data on Kyoto, Hiroshima and Niigata.
  - 29 May (Doc 16, PDF p3): "Kyoto, Hiroshima, and Niigato have been reserved".
  - 24 Jul (Doc 46E): "Hiroshima, Kokura and Niigata have been reserved"; the draft directive lists them "in the priority listed".
  - 24 Jul (Doc 60B): four targets selected, Hiroshima, Kokura, Niigata and Nagasaki, with populations and reasons.
  - 25 Jul directive (Doc 60E): "Hiroshima, Kokura, Nigata and Nagasaki". "Additional bombs will be delivered on the above
    targets as soon as made ready".
  - Kyoto and Tokyo rejection: Truman diary, 25 Jul (Doc 47, Bernstein transcription): "cannot drop that terrible bomb on the
    old Capital [Kyoto] or the new [Tokyo]". This is a secondary transcription; the brackets are Bernstein's.
- Checked against earlier claims:
  - "25 July 1945 directive": confirmed. The document is dated 25 July 1945 on its face, but NSA lists it as "July 26, 1945".
  - **"Third shot" documents: no target named.** Doc 82 gives only readiness (the bomb ready "after 17 or 18 August") and
    Marshall's note that it "is not to be released over Japan without express authority from the President". Doc 87 discusses
    tactical use in support of an invasion, but names no city. I found no third-shot target list in the NSA sets.
    Wellerstein's "Neglected Niigata" (blog) was not consulted because the blog has a cookie challenge and Wayback was unreachable.
  - The 2025 posting (text, not a document) says Groves's 24 July list was "Hiroshima, Kokura, and Niigata, in that order",
    and the Doc 46E text confirms this.
- CSV: `us_1945_target_committee.csv`, 42 rows: 17 study areas (selected blank) + 6 (10-11 May) + 3 (28 May) + 3 (29 May)
  + 3 (Groves 24 Jul) + 4 (Stone 24 Jul) + 4 (directive 25 Jul) + 2 (Truman diary, selected=0).
  The CSV has one row per candidate per document, so the same city repeats across stages. `selected` refers to that stage only:
  Niigata is 0 on 11 May and 1 later.
- Open issues: Stimson diary (Doc 48) should be read for a primary Kyoto-rejection quote. The Nagasaki strike cable (Doc 72C)
  gives an aim point "500 feet south end of Mitsubishi Steel Works"; it was not extracted because it reports a strike, not a list.
  Kokura as the primary target for 9 August appears only in NSA editorial text on the pages I read.

## 2. JIC 329/1 (Nov 1945) / Valero, Studies in Intelligence 44:3 (2000)

- Status: **not obtained**.
- Attempts:
  - cia.gov (new site): returns a JavaScript shell with no article text.
  - Old CSI URL https://www.cia.gov/library/center-for-the-study-of-intelligence/csi-publications/csi-studies/studies/summer00/art06.html:
    the archive.org availability API reports Wayback snapshot 20201017151038. However, web.archive.org connections were reset
    throughout the session (proxy log: `ws_closed_mid_exchange`), and http:// gives a proxy 403.
  - CIA reading-room search page: no parseable results.
  - archive.org advancedsearch for "JIC 329" / "strategic vulnerability of russia": 0 hits.
- No sha256 (nothing downloaded). No CSV.

## 3. Norstad to Groves, "Atomic Bomb Production", 15 Sep 1945 (+ 30 Aug 1945 map)

- Status: **not obtained**. The NSA 2020 and 2025 atomic-bomb postings and the 2024 "Manhattan Project Director's Files" posting
  (/node/4496) contain no "Norstad"/"Soviet cities"/"Atomic Bomb Production" document (text search of the pages).
  blog.nuclearsecrecy.com was not visited (cookie challenge). A Wayback CDX query for the May 2012 blog posts failed
  (connection reset, retried about 20 times in a background loop).
- The figures in the brief (66 cities, 204 bombs, 15 first-priority cities, 21 Manchurian cities) remain **unverified**. No CSV.

## 4. Pelopidas & Philippe, "Unfit for purpose ...", Cold War History 21(3), 2021 (doi 10.1080/14682745.2020.1832472)

- Status: **not obtained (blocked)**.
  - hal.science (hal-03384910, file 2020-pelopidas-unfit-for-purpose-cold-war-history.pdf) and Sciences Po SPIRE (which
    redirects to sciencespo.hal.science) both serve an **Anubis anti-bot proof-of-work challenge**. It was not bypassed, and
    the challenge page I received was deleted (it is not the document).
  - tandfonline PDF: HTTP 403.
  - OpenAlex lists the Routledge chapter reprint (10.4324/9781003448983-1) as closed.
  - scholar.archive.org: rate-limited.
- The 20-city list with air-defence grades is **unverified**. No CSV.

## 5. Taiwan Strait 1958: Halperin, RAND RM-4900 (unabridged), and NSA doc 21083 (Van Staaveren 1962)

- URL: https://www.ellsberg.net/wp-content/uploads/2021/05/Quemoy_Study_The_1958_Taiwan_Straits_Crisis_Partial_Plus_Total_Redactions_December_1966.pdf
- Status: **obtained, not extracted**. 237 scanned pages with no text layer; I did not read them within the time-box.
- File: `halperin_rm4900/Halperin_RM-4900_1966_unabridged_ellsberg2021.pdf` sha256 `f89b93d7e49e0082aaaae0a2194290c077f125b231c8c256871bc17691170914`
- Also listed on ellsberg.net (not downloaded): /wp-content/uploads/2017/11/1958-Taiwan-Straits-Crisis-Halperin.pdf,
  /wp-content/uploads/2021/05/DE_Notes_PACAF_Report_on_Taiwan_Quemoy_Operation_date_unknown.pdf,
  /wp-content/uploads/2021/05/DE_Notes_Draft_Notes_on_Offshore_Islands_Feb_1963.pdf.
- NSA doc 21083 (Van Staaveren): not attempted. No CSV.

## 6. Chinese nuclear facilities 1963-64: NSA EBB 38 and EBB 488

- URLs: https://nsarchive2.gwu.edu/NSAEBB/NSAEBB38/ ; https://nsarchive2.gwu.edu/nukevault/ebb488/
- Status: **obtained (partial reading)**.
- Files and sha256:
  - EBB 38 index.html `55c9c70ce0a162c644da6439d508d8d415495a819ab7ca943ce2c3ec1c0b4b88`
  - document3.pdf (NIE 13-2-62) `075012a2704cffd8de1b8ec8340cd58d5e8e59f812afd3488768b639acd615e0`, not read
  - document6.pdf (JCS "Chinese Communist Vulnerability" 1963) `11ae79d3ae87072e7bb11ee926a4aab32d8ff1a8b2a56425356692119f6445be`, not read
  - document8.pdf (ACDA, Jul 1963) `85e410f1070b6da8f8c8812a3608226bbca8050e870e78d11510d15872092d56`, not read
  - document11.pdf `0a376c50da42404073268991e0f9975b861743bdbf706fb9a4470dbcb4154dc2`; document12.pdf `abe77e958298b19db8df5242ea40b16528d5a190bd0353ac1ec0366438f24c54`; document13.pdf `eeb086e1003085346f07deebd8e23a5aa622fa0a5a8b6b88ef036793a9fa5723`, not read
  - document15.pdf (Johnson 2 Sep 1964) `70470f76153cce578162476c311b3284e7c6d13cf68591405fd05e3607e7f6fe`, read: no facility named
  - document16.pdf (Bundy MFR 15 Sep 1964) `7f734f780df1a2185775e2ad80691cfbce898368db21d94bffd4157ba58ca357`, read: no facility named
  - document21.pdf (Rathjens 14 Dec 1964) `21e9fe0ea04e6b9e4c55d478fe3e4c1dd277b8b3d71dcaf4a92ddfedbfa3d2a4`, read: no facility named
  - EBB 488 index.html `8b345c9db4a48c0e17a374781792a0b21d55a325f233b50aa11af0df967d3907`
  - EBB 488 Doc 16 (Rostow to Bundy 22 Apr 1964, enclosing R. H. Johnson, 14 Apr 1964, 35 pp.)
    `79392217174f9af3b62c74c4b8785f191b71d96946138e88372b530a2c333f26`. All pages read: only two facilities are named.
- Correction: the named 1964 targets come from **EBB 488 Doc 16**, not EBB 38. The Rathjens paper in EBB 38 summarises the
  same Johnson paper without naming facilities. Johnson also mentions "two other areas" that may hold plutonium facilities,
  but does not name them.
- CSV: `us_1964_china_nuclear.csv`, 2 rows (Pao-T'ou plutonium production reactor; Lan-Chou incomplete gaseous diffusion plant).
  Provenance is `study`; `selected` is blank because the study recommends against action.
- Open issues: NIE 13-2-62 and the JCS 1963 vulnerability study were not read and may name more installations.

## 7. MacArthur, December 1950 "retardation targets"

- Status: **not attempted** (time-box). No CSV.

## 8. SIOP-62 / NSTL 1960 totals: NSA EBB 130 and EBB 236

- URLs: https://nsarchive2.gwu.edu/NSAEBB/NSAEBB130/ ; https://nsarchive2.gwu.edu/nukevault/ebb236/ ;
  history PDF https://nsarchive.gwu.edu/nukevault/ebb285/sidebar/SIOP-62_history.pdf (linked from EBB 236 as Doc. 1).
- Status: **obtained (partial reading)**. I read PDF pp. 18-28 of the history.
- Files (`nsa_ebb130_ebb236/`), sha256:
  - ebb130_index.html `ef4c47dc908e1b598ec73baf2e2bf7035a9a3160f46f4de1ef756cad026e23e3`
  - ebb236_index.html `169f19600ff5a616c4e27d709bfff78d02b3c70a83112131abc1ee87772aa88f`
  - ebb236_doc1_SIOP-62_history.pdf `c1caba36758a90571c5b389039cd0c5cf8a92dc4646d2a28aa89a8a21566e812` (the OCR layer is unusable)
  - ebb130_SIOP-28.pdf (same history, older excision; not read) `a4aa7467b93c42d9e4086ac56b1fc356b1628eda47f585ab7a9e16c9b9554fc1`
- Verified figures:
  - NSTDB working list of "about 4,000 targets" (Aug 1960)
  - "1043 DGZs (706 in the USSR, ...)"; the counts for China and the European satellites are excised
  - alert force: 874 delivery systems, 1447 weapons
  - follow-on force: 1464 aircraft and missiles, 1976 weapons
  - 16 execution options
- Derived, not stated on the pages read: 1447 + 1976 = 3423 weapons. Commonly cited figures (about 2,600 installations,
  151 urban-industrial DGZs, about 1,060 DGZs) were **not found** on the pages read and are not in the CSV.
- CSV: `data/curated/validation_siop62.csv`, 8 rows.
- Open issues: EBB 130 Docs 12, 18, 19, 22, 24B and 25 (JCS reviews; the McNamara JSTPS visit) were not read and probably
  contain DGZ, urban-industrial and country breakdowns.

## 9. UK (TNA Discovery API)

- API: https://discovery.nationalarchives.gov.uk/API/search/records and /API/records/v1/details/{id}
- Status: **references found; not digitised; nothing extracted**.

| reference | dates | title | status |
|---|---|---|---|
| AIR 2/13716 (id C2641584; former ref AF/CMS262/64 Part 1) | 1956-1957 | Bomber Command strategic target policy and capability | open (closure 30), digitised: false, TNA Kew |
| AIR 2/13717 (id C2641585; AF/CMS262/64 Part 2) | 1957-1963 | same title | open, not digitised |
| DEFE 5/77/208 (id C13517031) | 19 Sep 1957 | Strategic Target Policy for Bomber Command: note by the Chief of Air Staff | open, not digitised |
| DEFE 5/78/224 (id C13517047) | 16 Oct 1957 | Strategic Target Policy for Bomber Command: memorandum by the Chiefs of Staff | open, not digitised |
| DEFE 4/100/72 (23 Sep 1957), DEFE 4/100/78 (15 Oct 1957) | 1957 | COS minutes, returned by the same search (agenda items not fully shown) | open, not digitised |

- Which file holds the 1957 grading (131 cities, 98 in range, 44 selected) is **unverified**. The likely candidates are
  DEFE 5/77/208 and AIR 2/13716-13717.
- (b) Joint SAC-Bomber Command target lists 1958-63: no catalogue hit. Queries tried: "SAC Bomber Command coordination
  targets", "joint strike plan SAC", "Strategic Air Command co-ordination", and "Strategic Air Command" in AIR 1957-64, which
  returned only bombing-competition files. AIR 2/13717 (1957-63) is the best lead. Not digitised; a visit to Kew is needed.

## 10. WINTEX-CIMEX 89

- Status: **not attempted** (time-box). No CSV.

---

## Environment notes

- web.archive.org was unreachable for the whole session (TLS tunnel reset; the proxy logs `ws_closed_mid_exchange`). Items 2 and 3 depend on it.
- hal.science and SPIRE are behind Anubis; tandfonline gives 403. All were respected and not bypassed.
- The NSA site search parameter is `s=` (https://nsarchive.gwu.edu/search?s=...); results link to /node/NNNN.
