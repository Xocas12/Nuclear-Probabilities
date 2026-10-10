# NSA EBB 38, "The United States and the Chinese Nuclear Program, 1960-1964": source cards

Source: https://nsarchive2.gwu.edu/NSAEBB/NSAEBB38/ (files in `data/raw/western/nsa_ebb38/`). This file continues
`western.md` section 6. Section 6 covered documents 15, 16 and 21 (none names a facility) and EBB 488 Doc 16
(`us_1964_china_nuclear.csv`).

None of the PDFs has a text layer. I rendered every page to PNG (110 dpi) and read each one as an image. Where a
table needed it, I also read a zoomed crop. "Printed p" is the page number on the document; "PDF p" is the page in
the file.

Test used for a CSV row: the place must be named, and the document must present it as something US (or
US-backed) military action could strike or interdict. Places named only as intelligence findings, without any
strike context, are recorded below but not extracted.

## Summary

| doc | what | pages read | names targets? | CSV rows |
|---|---|---|---|---|
| 3 | NIE 13-2-62, 25 Apr 1962 | 29/29 | no (intelligence only) | 0 |
| 6 | JCSM-343-63 + appendix "Chinese Communist Vulnerability", 29 Apr 1963 | 36/36 | yes | 9 |
| 8 | ACDA appraisal, 10 Jul 1963 | 25/25 | no (intelligence only) | 0 |
| 11 | CM-1024-63, Taylor, 18 Nov 1963 | 1/1 | no | 0 |
| 12 | Rusk evening reading, 1 May 1964 + Rostow summary, 30 Apr 1964 | 4/4 | no | 0 |
| 13 | R. H. Johnson, "Unorthodox approaches", 1 Jun 1964 | 13/13 | no | 0 |
| EBB 236 Doc 1 / EBB 130 | JSTPS history of SIOP-62 (two excision versions) | partial (see card) | no | 0 |

## Doc 6: JCS, "Study of Chinese Communist Vulnerability" (1963)

- Gen. Curtis LeMay (Acting CJCS) to SecDef, JCSM-343-63, 29 Apr 1963, Top Secret. Appendix "Chinese Communist
  Vulnerability" (31 pp). Declassification NND 989569. sha256 `11ae79d3...6445be` (in full in `western.md`). 36 PDF pages:
  PDF pp1-4 are the cover memo (printed 1-4); PDF p5 is the appendix cover; PDF p6 onward is the appendix.
  Appendix page = PDF page - 5. Some page numbers are not printed and are inferred from that offset.
- Purpose: answers Nitze's request for ways to "persuade or compel" China to accept a test ban. Lists indirect
  actions (diplomacy, propaganda, severance, embargo) and direct actions: (1) overt aerial reconnaissance;
  (2) support infiltration, subversion and sabotage by Chinese Nationalists; (3) maritime control up to blockade;
  (4) a CHINAT invasion; (5) a ROK invasion of North Korea; (6) "small scale conventional air attacks against CHICOM
  nuclear or other facilities"; (7) "Deliver a tactical nuclear weapon on a selected CHICOM target" (App p11).
- Conclusion (cover memo, printed p4): "unrealistic to use overt military force to obtain CHICOM acceptance of any
  agreement". It favours joint US/Soviet measures.
- **Named targets**, `us_1963_jcs_china_vulnerability.csv`, 9 rows:
  - App p10 (PDF p15), para 7b, "Chinese Communist nuclear activities are located as follows": a 6-row table. The rows
    are the Institute of Atomic Energy 20 mi SW of Peiping; a small research reactor "On railroad 18 miles north on
    Canton"; a separation plant at Changsha; a missile propulsion vertical test stand 13 mi WSW of Peiping; the
    missile test range at Shuangcheng Tzu; and a probable gaseous diffusion plant at Lanchou. Para 7c: "These
    activities are vulnerable to sabotage as well as to overt aircraft attack." The paper also says "No plutonium
    production reactor has been identified."
  - App p7 (PDF p12), para 4d: rail transloading points for petroleum at Chining, Man-chou-li and Sui-fen-ho are
    "serious bootle-necks" [sic; hyphenated across a line break in the original]. They are identified as
    vulnerabilities and are not explicitly proposed for attack. They are included as the only named
    transport/POL target system; the notes column flags this.
- `selected` is blank in all rows. The study analyses the options and makes no decision about individual targets.
  Options (6) and (7) are discussed without naming a facility: para 18, App p25, says air attack could eliminate
  ChiCom nuclear capability "provided target locations are known"; para 19, App p26, says "Any CHICOM nuclear
  facility could be effectively demolished".
- Considered and **not extracted**:
  - "extensive railroad complex in Manchuria" and the "Only one railroad" to the USSR: not named places.
  - Generic phrases such as "bomb out the enemy's airfields" (App p20) and "interdiction of vulnerable
    transportation facilities" (App p16): no place named.
  - Hong Kong, the Offshore Islands, Taiwan, the Pescadores, South Korea, India, Sikkim, Bhutan, Nepal, South
    Vietnam, Cambodia, Laos, Burma and Thailand (App pp29-31): places where the **Chinese** might retaliate, not
    US targets.
  - North Korea: named only as a country, under option (5).
- Quote convention: in the table rows, the two columns are joined with three spaces.
- Redactions: none visible in the text.
- Open issues: the Canton reactor and the WSW-of-Peiping test stand are given only as distances from a city.
  Chining is probably Jining, Inner Mongolia, but this is unconfirmed, so `name_modern` is blank.

## Doc 3: NIE 13-2-62, "Chinese Communist Advanced Weapons Capabilities" (25 Apr 1962)

- CIA FOIA release, MORI DocID 278410, stamped "Release as Sanitized", copy No. 374. 29 PDF pages. Printed pages
  2 and 8 are not in the scan: PDF p5 is printed 1, PDF p6 is printed 3, and PDF p19 is printed 9.
- An intelligence estimate. It contains no discussion of US strikes and **names no targets**.
- Places named only as intelligence findings:
  - the Shuang-cheng-tzu missile test centre and rangehead, about 50 nm NE of Shuang-cheng-tzu on a rail spur off
    the Urumchi-Lanchou line along the Etsin River, with SSM launch complexes A, B and C and an SA-2 area;
  - photo captions with coordinates: support base 41-05N 100-17E; Shuang-cheng-tzu airfield 40-21N 99-47E;
  - Lanchou, a suspected gaseous diffusion plant (paras 7 and 40);
  - the Institute of Mechanics and the Peiping Aeronautical College;
  - "a few SAM sites at Peiping" (printed p15).
- The map on PDF p26, "Potential Target Coverage of Surface-To-Surface Missiles From Communist China's Borders",
  shows **Chinese** missile reach over other countries. It is not a list of US targets.
- Redactions: bracketed excisions on printed pp6-7 (paras 15 and 17-21).

## Doc 8: ACDA, "Summary and Appraisal of Latest Evidence on Chinese Communist Advanced Weapon Capabilities" (10 Jul 1963)

- Harriman's copy, marked "For Moscow". ACDA-957. Declassification NND 979572. 25 PDF pages: a cover sheet plus 24 pp.
  It contains a summary, Annex 1 (missiles and aircraft), Annex 2 (France and Israel comparison) and Annex 3,
  "Suspected Communist Chinese Advanced Weapons Facilities" (10 numbered facilities with map and NPIC photographs).
- **Names no targets.** Annex 3 is an intelligence inventory. Nothing in the document frames any facility as a
  strike option.
- Facilities in Annex 3 (useful later for geocoding the doc 6 rows):
  1. Lan Chou gaseous diffusion plant
  2. Pao T'ou
  3. Hsi-an nuclear research
  4. Peiping Institute of Atomic Energy (two locations)
  5. Chang Hsien Tien missile R&D, about 16 nm SW of Peiping
  6. Shuang-Cheng-Tzu
  7. Tu-Ko-Ma-Ching
  8. Nan-King Radar Plant 720
  9. Cheng-Tu airframe plant
  10. Shen-Yang aircraft engine plant, arsenal and airframe plant

  Annex 1 also names cruise-missile sites at Port Arthur, Darien and Lienshan; SAM sites, including Chung-Wei
  37-54N 105-17E; and a CW depot near Lu-Hsien.
- Redactions: none noticed.

## Doc 11: CM-1024-63, Gen. Maxwell Taylor to the Joint Chiefs, "Chinese Nuclear Development" (18 Nov 1963)

- 1 page. Declassification NND 941071. It covers a paper on covert action to delay the Chinese programme,
  "Unconventional Warfare Program BRAVO". The paper is **not attached**.
- **Names no places.**

## Doc 12: Rusk to President, "Items for Evening Reading" (1 May 1964), enclosing Rostow (30 Apr 1964)

- 4 pages. Declassification NND 979533. Issue 4b, pre-emptive military action against ChiCom nuclear facilities:
  "Would be undesirable except possibly as part of general action against the mainland in response to major ChiCom
  aggression."
- Mentions "one known plutonium reactor", unnamed. **Names no targets.** Wheelus Base and the other places on p1
  are unrelated items.

## Doc 13: R. H. Johnson (S/P), "The Chinese Communist Nuclear Capability and Some 'Unorthodox' Approaches..." (1 Jun 1964)

- 13 pages. Declassification NND 979524. Section I summarises Johnson's TS paper on direct action against ChiCom
  nuclear facilities, which is EBB 488 Doc 16, already extracted.
- Refers only to "the one known plutonium reactor" (covert ChiNat attack) and "the incomplete and possibly
  incompleteable gaseous diffusion plant". **Names no facilities.** These are the Pao-T'ou and Lan-Chou rows of
  `us_1964_china_nuclear.csv`; no duplicate rows were added.
- "Bases in Taiwan" appear only as targets of ChiCom retaliation. "French facilities" are mentioned only in general
  terms.

## EBB 236 Doc 1 / EBB 130: JSTPS history of SIOP-62

- `ebb236_doc1_SIOP-62_history.pdf` (37 pp, poor OCR layer) and `ebb130_SIOP-28.pdf` (38 pp, an older and more heavily
  excised release of the same history).
- Read as images this session: EBB 236 PDF pp21-23 and EBB 130 PDF pp22-23. `western.md` section 8 covers EBB 236
  PDF pp18-28. I also searched the OCR text of all 37 EBB 236 pages for place names. The only geographic references
  are general ones: "Sino-Soviet Bloc", "USSR", "China", "European satellites", and the split of the target system at
  100 deg E longitude.
- **Names no targets.** The history gives only totals: "1043 DGZs (706 in the USSR, [excised] China, [excised]
  European satellites ...)". The China count is excised. EBB 130 excises the whole sentence.
- Open issue: EBB 130 PDF pp1-21 and 24-38 and EBB 236 PDF pp1-17 and 29-37 were not checked page by page as
  images. Their OCR text and section 8 of `western.md` show they are about organisation, administration and
  footnotes.
