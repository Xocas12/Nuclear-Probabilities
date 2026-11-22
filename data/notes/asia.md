# Source note: US nuclear target lists in Asia, 1950-1975 (topic `asia`)

Collector pass of 2026-11-22. Lists already done elsewhere and not redone: `us_1945_target_committee`,
`us_1958_taiwan_strait` (Halperin, unabridged pages), `us_1963_jcs_china_vulnerability`, `us_1964_china_nuclear`.

## Method

FRUS volumes were downloaded as TEI XML from the Office of the Historian's public repository
(`https://raw.githubusercontent.com/HistoryAtState/frus/master/volumes/<volume>.xml`; the same text as
`https://history.state.gov/historicaldocuments/<volume>/<doc>`). Each document was split out, and the sentences that
mention atomic/nuclear weapons were searched for place names (Chinese, Korean, Vietnamese and Soviet place names, old
spellings) and for "target", "airfield" and "air base". Every hit was read in context, and printed page numbers
come from the TEI `<pb>` markers. All FRUS quotes in the CSVs were checked by script against the downloaded text.
The ORO report was read as a scanned PDF (its OCR text layer checked against the page image).

Volumes searched: 1950 VII; 1951 VII (pts 1-2); 1952-54 XII pt 1, XIII (pts 1-2), XIV pt 1, XV (pts 1-2);
1955-57 II, III, XIX; 1958-60 XIX; 1961-63 XXII; 1964-68 I, VI, VII, XXIX pt 1, XXX; 1969-76 XVII, XIX pt 1, XXXIV.

General finding: in FRUS the Korean War and Taiwan Strait atomic plans are almost always described by
**target class** (Manchurian air bases, coastal airfields, troop concentrations, "targets in China, Manchuria and
Korea"). Named places are rare. On 3 Dec 1953 Radford told the NSC the JCS "had not" yet laid out their target system
(1952-54 XV, doc. 811). The rows below are every named place I found. Nothing named was found for the 1960s-70s
beyond the facilities already extracted. FRUS 1964-68 XXX names Lop Nor, Lanchou and Pao-t'ou only as intelligence
subjects, and 1964-68 XXIX and 1969-76 XIX (the Pueblo and EC-121 crises) give no named nuclear targets.

## (1) `us_1950_korea_atomic_options.csv`, 7 rows, study
- FRUS 1950 VII doc. 745 (Nitze, 4 Nov 1950, after a talk with Brig. Gen. Loper): "such Manchurian cities as Mukden,
  Fushun, Anshan, Harbin and Dairen" as examples of strategic use. The memo argues *against* that use, so `selected` is blank.
- Doc. 927 (Clubb, 1 Dec 1950): destruction "by A-bombs if need be" of the Yalu River Dam and the other North Korean power
  installations. Row 7 is the unnamed class and can be dropped.
- Doc. 787 (Emmerson, 8 Nov 1950) lists only target types (cities, industrial complexes, concentrations), so no rows.

## (2) `us_1951_oro_fec_tactical.csv`, 4 rows, study
- ORO-R-2 (FEC), "Tactical Employment of Atomic Weapons", Operations Research Office for GHQ Far East Command, dated 1 March
  1951 (covering letters 20 Jul and 7 Sep 1951). 338-page scan:
  https://archive.org/download/DnaEm1CapabilitiesOfNuclearWeapons/1951%20proposal%20for%20use%20of%20tactical%20nuclear%20weapons%20to%20end%20Korean%20War.pdf
- PDF p.33 (printed p.18, para 39) has four cases, 15 weapons of 40 kt in all: Taechon (1), the Pyonggang-Chorwon-Kumhwa
  triangle (6), the line north of the Imjin (6) and Wonju (2). Appendix B (printed pp.153-155 and following) has
  aiming-point schemes. It calls Pyonggang the most important aiming point, with Chorwon second.
- Doubt: these are *hindsight* exercises on Nov 1950-Jan 1951 situations, not forward targeting. Appendix G covers the
  vulnerability of UN targets (Pusan, ASCOM City), which are not US targets and were not extracted.

## (3) `us_1953_korea_nsc_jcs.csv`, 4 rows (1 plan, 3 study)
- 1952-54 XV doc. 391: Eisenhower in the NSC (11 Feb 1953), "tactical atomic weapons on the Kaesong area".
- Doc. 605 (17 Jun 1953): Dulles to ROK Prime Minister Paek, saying retaliation "could mean atomic attacks on Vladivostok and Port
  Arthur". This is deterrent talk, so the evidence is weak.
- Doc. 807, JCS to SecDef (27 Nov 1953), NSC 170 series, Appendix B para 7: "Provision for attacks on targets in the Dairen-Port
  Arthur area will be included in the plans", with JCS approval needed. This is the only `plan` row.
- Bowie's comment in doc. 810 (p.1635) is noted in the row but not duplicated.
- Not extracted (class only): NSC 147 and the JCS memo of 19 May 1953 (docs. 437, 535: "Communist air complexes and other targets north of the Yalu"), the 179th NSC
  meeting (doc. 841: "at least 22 enemy airfields"), SNIE doc. 877, and Bradley's "four airfields in North Korea" (doc. 500).

## (4) `us_1954_dien_bien_phu.csv`, 1 row, study
1952-54 XIII doc. 711: the JCS advanced study group's estimate of "three tactical A-weapons" against the Vietminh around Dien
Bien Phu. The name "Vulture" comes only from the editors' footnote quoting Nixon.

## (5) `us_1955_taiwan_strait_cincpac.csv`, 6 rows, study
1955-57 II doc. 199, Stump to Carney (9 Apr 1955), pp.472-473: atomic retaliation limited to "Luchiao, Fouchow and Swatow
airfields", possibly extended to the "Ningpo Canton Nanchang air complexes". Doc. 58 shows that CINCPAC OPLAN 51-Z-55 had an
atomic annex (Annex A), but the annex is not printed.

## (6) `us_1958_taiwan_strait_jcs_contingency.csv`, 3 rows, plan (second-hand)
1958-60 XIX doc. 63 (G. Smith to Dulles, 3 Sep 1958), p.123: JCS contingency planning includes "targets in the Shanghai,
Nanking, and Canton areas" within a 500-mile radius. Shanghai is also in `us_1958_taiwan_strait`. Doc. 34 (Herter) repeats the
Twining "as far north as Shanghai" statement already extracted.

**Halperin RM-4900, re-checked.** The released 691-page version, with an OCR text layer, is on archive.org (item
`The1958TaiwanStraitsCrisisADocumentedHistory_201712`). Its full text was searched for airfield and base names
(Lungtien, Luchiao, Chenghai, Chuchow, Swatow, Foochow, Chienou, Nanchang, Ningpo, Canton and others). The only hits are
operational or intelligence mentions, such as MIGs at Swatow, air battles near Foochow, and the blockade of Amoy and Foochow. None is a nuclear target.
Together with the earlier full read of the unabridged withheld pages (`halperin_1958.md`), this means RM-4900 names no airfields beyond the four rows
already extracted. rand.org returned HTTP 403 (CloudFront block), so the RAND copy was not used.

## (7) `us_1968_khe_sanh.csv`, 1 row, study (selected = 0)
1964-68 VI doc. 51, editorial footnote (p.120): Wheeler asked about "the feasibility of nuclear strikes at Khe Sanh" (JCS 1154,
1 Feb), and planning was terminated on 11 Feb 1968 (JCS 1690). The Fracture Jaw documents themselves were not obtained.

## Not found / blocked
- **MacArthur's "retardation targets" (24 Dec 1950, 26 bombs plus 8 more) and Operation Hudson Harbor**: neither is in FRUS (no
  "retardation" or "Hudson Harbor" anywhere in the volumes searched). The Truman Library site search returned nothing usable. The documents are in
  RG 218 (JCS) and the MacArthur Memorial Archives, which are not online.
- **Wilson Center Digital Archive** (digitalarchive.wilsoncenter.org): the connection failed from this container.
- **RAND RM-4900**: https://www.rand.org/pubs/research_memoranda/RM4900.html and
  https://www.rand.org/content/dam/rand/pubs/research_memoranda/2006/RM4900.pdf both returned 403.
- **Fracture Jaw cables (Feb 1968)**: released in 2016-18 and reported in the press. No NSArchive copy was found. The 1958 NSArchive briefing
  book (nuclear-vault, 2021-05-28) links only an interview PDF.
