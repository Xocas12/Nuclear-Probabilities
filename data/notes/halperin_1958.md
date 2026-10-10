# Source card: Halperin, RAND RM-4900-ISA (1966), Taiwan Strait 1958 (unabridged pages)

- File: `data/raw/western/halperin_rm4900/Halperin_RM-4900_1966_unabridged_ellsberg2021.pdf`
  (sha256 `f89b93d7e49e0082aaaae0a2194290c077f125b231c8c256871bc17691170914`; see `western.md` section 5)
- URL: https://www.ellsberg.net/wp-content/uploads/2021/05/Quemoy_Study_The_1958_Taiwan_Straits_Crisis_Partial_Plus_Total_Redactions_December_1966.pdf
- Output: `data/curated/labels/us_1958_taiwan_strait.csv` (4 rows)
- Method: all 237 pages were skimmed as 90-dpi two-page spreads. Pages with target content were then read at 140-150 dpi.
  Rotated tables were rotated and cropped at about 200 dpi. No OCR was used. The working notes are in the session scratchpad and are not kept.

## What the document is

This is not the whole study. Ellsberg compiled the pages of Halperin's 1966 Top Secret history that were partly or
entirely withheld from the declassified version, and he marked them up by hand: brackets show the withheld passages, and "PW"
means partially withheld. PDF p.1 is the cover. PDF pp.2-3 are lists of the withheld pages. One note reads "Our copy of the study is missing pp. 451 and 468".
The rest is the deleted pages in order, covering printed pp. vii-562, with large gaps in the printed page numbers. For example, printed
p.75 and p.285 are not in the PDF. Printed p.123 appears twice (PDF pp.52-53), once as an email printout. The PDF is
therefore **not** a continuous text. Context on pages outside the PDF has to come from the released abridged version,
which was not consulted.

Page key (PDF -> printed) for the pages that matter: 9-10 -> 48-49; 16-17 -> 55-56; 23 -> 77; 28-30 -> 84-86;
31-34 -> 87-90; 37-40 -> 106-109; 42-43 -> 113-114; 44 -> 115; 56 -> 126; 60 -> 130; 67-68 -> 141-142;
81-83 -> 197-199; 86 -> 208; 101-104 -> 261-264; 120-121 -> 281-282; 123 -> 286; 126 -> 293;
134-140 -> 379-385; 179 -> 460; 203-204 -> 519-520; 211-213 -> 527-529; 228 -> 544.

## Named targets (CSV rows)

All 4 rows are `study`. None comes from the text of an approved plan, because the approved directives quoted in the
document name only classes of targets (see below).

| seq | name as printed | class | who / when | page (PDF/printed) |
|---|---|---|---|---|
| 1 | "the fields in the Amoy area" | airfields, 10-15 kt | Twining, mid-Aug 1958 meeting | 23 / 77 |
| 2 | Shanghai ("as far north as Shanghai") | northern limit of follow-on strikes | Twining, same meeting | 23 / 77 |
| 3 | "the military control center at Ching Yang" | control center, first increment | Kuter (CINCPACAF) estimate, 26 Aug | 68 / 142 |
| 4 | artillery "opposite Quemoy ... in the Amoy area" | coastal batteries | Dulles query 7 Nov; JCS reply 8 Dec 1958 | 228 / 544 (also 212/528, 101/261) |

No named target was explicitly considered and then rejected, so there are no `selected=0` rows. Rejections in the document
concern *how* and *when* nuclear weapons would be used, not which places would be hit.

## Target sets named only by class (not extracted as rows)

- **CINCPAC OPS PLAN 25-58** (16 May 1958, approved by the JCS): in Phase II, US forces would defeat the attack using atomic
  weapons. In Phase III, SAC would "destroy the war-making capability of Communist China". On 16 Aug the plan was altered
  so that atomic weapons would be used only "when authorized by the President" (pp.9-10 / 48-49). Its **Annex E (Atomic
  Annex)** target list is referred to but never reproduced. Halperin writes: "I have not seen this Annex" (p.68/142).
- **PACAF interim OPS PLAN 25-58** (7 Aug), with an interim atomic annex two days later: 13th AF "pre-planned strikes
  against enemy air bases. No conventional operations ... planned" (pp.16-17 / 55-56).
- **LeMay to Kuter**: "simultaneous strikes against the coastal airfields using Guam-based SAC B-47's". SAC was
  alerted for this. The 15-aircraft Guam B-47 squadron was "available on Guam for atomic attacks against the mainland" and
  had "no conventional capability" (pp.28 / 84; 42-43 / 113-114).
- **Kuter, 25 Aug**: SAC "would strike first against the newly reoccupied fields, followed by attacks on other airfields"
  (p.67/141). In his increments (row 3) he also proposed "selected targets within a 400-mile radius of Taiwan, including
  Beagle bases and control centers" (p.68/142).
- **Joint Staff answer to Gray**, JCS DM 280-58, 20 Aug (Table 10): attack mainland air bases. "Effective attack would
  require nuclear weapons." It also mentions coastal airfields and, in situation D, SAC (pp.31-34 / 87-90).
- **Burke to Felt, 24 Aug**: the JCS would "press for the use of atomic weapons on Chinese Communist local air fields from the
  outset". CINCPAC was to prepare "a list of proposed atomic targets". That list is not in the document (pp.37-39 / 106-108).
- **CINCPAC, 26 Aug**: "targets on the mainland would include airfields deep enough to neutralize Chinese Communist planes,
  but the attacks might be nonnuclear or nuclear" (p.60/130).
- **Taylor, 2 Sep**, citing "current operations plans": "seven to ten Kt. air-burst weapons". "The initial attack would be on
  five coastal airfields with one bomb per field", followed by a pause. Runways would not be cratered. Twining said the US would "strike at Chinese
  Communist airfields and shore batteries with small atomic weapons" (pp.101-104 / 261-264). The five fields are not named.
- **JCS 2118/110** (approved 6-7 Sep, Table 16): "it is most probable that we will have to use atomic weapons against air
  bases and perhaps against other targets in the Chinese mainland". The Joint Staff draft said "inevitable". The Army's
  "last resort" wording was rejected (pp.120-121 / 281-282).
- **Paper initialled by the President, 6 Sep**: 3a, approve the CHINAT Air Force "striking enemy forces and mainland targets". 4,
  "Use of atomic weapons and U.S. air attack in support of CHINAT Air Force ... only as approved by the President"
  (p.123/286).

### Conventional-only alternative (the nuclear plan's substitute)

- **JCS #947046 (25 Aug, approved at the White House)**: "prepare to assist the GRC including attacks on coastal air bases. It is
  probable that initially only conventional weapons will be authorized, but prepare to use atomic weapons to extend deeper
  into Chinese Communist territory if necessary" (p.42/113). Table 11 (Navy message, 25 Aug) lists the conventional
  responses: artillery pieces, supporting air and navy bases, staging areas, mainland bases, assault forces (p.59/129).
- **JCS #947298 (29 Aug)**: in Phase II the US would assist "including attack on enemy artillery and local airfields. During Phase
  II, it is anticipated that atomic weapons would not be used". In all phases, use requires the "specific authority of
  the President", and the GRC was not to be told (p.83/199). PACAF ordered its units to prepare "to use HE against coastal air bases
  and other targets which posed an invasion threat". The commanders were "assured that expansion [dee]per into China would involve the use of nuclear
  wea[pon]s" (p.86/208).
- **Annex H to CINCPAC OPS PLAN 25-58** (issued 11 Sep), "Without Using Nuclear Weapons". If nuclear weapons
  were to be used, "Phase II of OPS PLAN 25-58 would be implemented with a new atomic strike plan" (p.134/380). Table 22
  and the footnote on p.140/385 give the Annex H Appendix II target groups:
  - Group I: targets of opportunity, meaning forces intensifying supply of Quemoy and Matsu, invading forces, artillery positions, and staging areas.
  - Group II: coastal airfields and military control centers. A word such as "(seven ..." is cut off.
  - Group III: inland fields, GCI sites and control centers, "starting with eighteen targets and following with
    twenty-two additional targets", in "a gradually expanding arc until destruction complete in an 800-mile radius of
    Taiwan".

  These are conventional groups with no place names, so they are not extracted as rows. The footnote's lines are
  garbled in the scan, and the counts (18 + 22) are legible but their exact context is not.

## Nuclear use: yields, restrictions, "conventional first"

- Yields stated: 10-15 kt (Twining, p.77). 7-10 kt air burst with a 3-4 mile lethal area and no fallout (Taylor, p.264). "Small
  air-burst atomic weapons without fallout" (Dulles to Macmillan, p.460). Air burst is enough for the Amoy batteries (JCS, 8 Dec,
  p.544). Dulles to Chiang: only ground bursts would take out the guns, with heavy fallout on Quemoy (p.529); he cited Hiroshima at 20 kt (p.527).
- Decision sequence:
  1. OPS PLAN 25-58 assumed atomic operations.
  2. On 25 Aug the President inserted the clause that initial operations would probably be conventional (pp.113, 120, 126).
  3. On 29 Aug Eisenhower decided to "defer the use of nuclear weapons even in the event of an assault" (p.197).
  4. On 2-3 Sep Dulles and the JCS agreed: conventional first, then nuclear weapons quickly if the PRC persisted (p.263).
  5. JCS 2118/110 put this as "most probable" (p.281).
  6. The 6 Sep presidential paper reserved atomic use to the President (p.286).

  Halperin's footnote on p.293 says the conventional pause would be "measured in hours and not days".
- Field reaction: Kuter and PACAF protested that SAC B-47s had no HE capability (pp.144-145, 538). Felt questioned whether
  the islands could be defended non-nuclear (p.140). Taiwan Defense Command (TDC), 21 Oct: the PRC airfields "could not be cratered without atomic
  weapons" (pp.519-520).

## Redactions and gaps

- The PDF consists *only* of formerly withheld pages, many with bracketed passages. A few passages still have black redaction marks
  (for example PDF pp.98-104). Hole punches and over-inking hide some words, for example on p.140/385 and p.141/386.
- Annex E (the atomic target list) and the CINCPAC "list of proposed atomic targets" (Burke, 24 Aug) are not reproduced.
- Printed p.75 (the date of the Twining meeting) and p.285 are not in the PDF. The "north general war (GEOP) targets" assigned to the
  carrier *Midway* (p.141/386) are SIOP-type targets and are not named.

## Open issues

- Identify "Ching Yang" (Wade-Giles). It might be a Fujian command center, but this is unverified.
- Check the Twining meeting date (probably 14 or 15 Aug 1958) against the abridged release or FRUS 1958-60 vol. XIX.
- Read the released abridged version (ellsberg.net 2017 PDF) for context, and the PACAF report and Ellsberg's notes listed in `western.md`
  section 5. Annex E might be found in the CINCPAC Command History for 1958.
- Not used as US targets: "junks observed at Amoy Harbor" (GRC conventional strikes, p.258), and Chiang's "supply lines to the
  Amoy area" (GRC, p.528).
