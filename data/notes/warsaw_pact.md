# Warsaw Pact / Soviet nuclear target lists against NATO and neutral states — source notes

Worker: Warsaw Pact stream. Session 2026-10-03, 14:59–15:35 UTC. All downloads are in `data/raw/warsaw_pact/`; all label files are in `data/curated/labels/` (schema: `SCHEMA.md`).

Conventions used in the CSVs
- `quote` is verbatim from the opened document, in its original language where I read the original (HU, PL, RU). For scanned tables, cells are joined with ` | `. `"` is the source's ditto mark. `...` or `[...]` marks text I could not read or left out.
- If the only accessible text is secondary (a scholarly paraphrase, journalism, Wikipedia), every row's `notes` starts with `SECONDARY` and/or `provenance=reconstruction`.
- `target_country` for unit targets with no stated location: I filled it only where the document gives the unit's nationality or theatre, and I say so in `notes`. Otherwise it is blank.
- `weapons` and `yield_kt` are filled only when stated per target. Shared totals ("8 strikes, 173 kt" for two targets) go in `notes`.
- Host note: `www.php.isn.ethz.ch` and `php.isn.ethz.ch` serve a certificate for the wrong host, and I did not bypass it. The PHP site is mirrored with valid TLS at `https://phpisn.ethz.ch/lory1.ethz.ch/...` (an HTTrack copy, Oct 2016). Its documents are at `https://phpisn.ethz.ch/kms2.isn.ethz.ch/serviceengine/Files/PHP/<id>/...`. All PHP facsimiles below came from there.

## Summary table

| # | Source | Status | CSV (rows) |
|---|---|---|---|
| 1 | PHP dossier "Taking Lyon on the Ninth Day?" (1964 ČSLA plan) | obtained | wp_1964_csla_plan.csv (21) |
| 2 | PHP 1965 Hungarian–Soviet war game: "Easterners" plan (HU original + EN) | obtained | wp_1965_hu_wargame.csv (23) |
| 2b | PHP 1965 war game: "Westerners" plan (EN; EN+HU scan) | obtained | nato_1965_hu_wargame_mirror.csv (26) |
| 3 | PHP Lato-67 Coastal Front Directive No. 02 (RU facsimile) | obtained | wp_1967_lato67.csv (57) |
| 3b | PHP Burza 1961: Directive 002, nuclear-planning report, situation report (PL facsimiles) | obtained | wp_1961_burza.csv (23) |
| 3c | PHP list of "Westerners'" nuclear strikes, 24 Jan 1962 (PL facsimile) | obtained (new find) | nato_1962_pl_exercise_mirror.csv (76) |
| 3d | GitHub othercriteria/the-baltic-approaches (reference/php-maritime-front.md) | obtained (clone) | used to locate the primaries only |
| 4 | Pałka 2022, Kwartalnik Historyczny Eng. ed. 6 | obtained | wp_1977_zealand.csv (10); wp_1965_coastal_front_zealand.csv (5) |
| 5 | Nielsen et al. 2016, Geoforum Perspektiv 15(27) | obtained, partial content | wp_1970_coastal_front_map.csv (4) |
| 6 | Lautsch 2021 BMVg Zeitzeugenbericht | obtained, **no nuclear targets** | none (wp_1983_nva_lautsch.csv not written) |
| 7 | csla.cz plany001–003 | obtained, **counts only** | none (wp_1980s_csla.csv not written) |
| 8 | Wikipedia en/pl "Seven Days to the River Rhine" | obtained (secondary) | wp_1979_seven_days.csv (9) |
| 9 | CIA: 1977 Soviet General Staff Academy lessons | obtained via archive.org mirror | wp_1977_gsa_front_lesson.csv (19) |
| 10 | TV2 Denmark, 2 Apr 2022 (1989 Polish plan vs Denmark) | **not obtained** | none |
| 11 | R-5M "Operation Atom" 1959 (Uhl) | primary/Uhl not obtained; BBC 2012 + Wikipedia | wp_1959_r5m_operation_atom.csv (1) |

There are 274 rows in total:
- 172 rows are Warsaw Pact (attacker-side) targets in NATO and neutral states.
- 102 rows are mirror rows, where the WP simulated NATO strikes on the WP side: 76 in the 1962 Polish list and 26 in the 1965 Hungarian game.
- 143 of the 172 attacker rows come from primary documents and 29 from secondary texts.

---

## 1. PHP dossier "Taking Lyon on the Ninth Day? The 1964 Warsaw Pact Plan for a Nuclear War in Europe and Related Documents" (Mastny & Luňák eds., 2005)
- URL: https://www.files.ethz.ch/isn/108642/warplan_dossier.pdf. Retrieved 2026-10-03T14:59:42Z.
- File: `php_warplan_dossier_1964_taking_lyon.pdf`. sha256 `f0241f5423dbcace69a5811f1f1d6f76f3084e9b9ebec6f4a454a336ecaa6ac6`. 36 pp, text layer.
- Status: **obtained**.
- Contents: the plan, "Plan of Actions of the Czechoslovak People's Army for War Period" (approved by Novotný; signed 11–14 Oct 1964), is on PDF pp.18–25 (printed pp.16–23). It is an English translation from the Russian original by Savranskaya & Locher. The map on PDF p.26 is a modern AtomInfo reconstruction of the advance axes and shows no nuclear targets.
- Named nuclear targets / target areas, all FRG (21 rows):
  - 184th heavy bomber regiment, first nuclear strike (16 bombs for the whole list, PDF pp.22–23): HQ 2nd Army Corps FRG; HQ 7th US Army; 2nd/40 and 2nd/82 Corporal battalions; 5th/73 Sergeant battalion; main forces of the 4th mech. and 12th tank divisions of 2nd AC FRG.
  - 10th Air Army search-and-destroy regions for means of nuclear attack and aviation C2: Weiden, Nabburg, Amberg, Grafenwöhr, Hohenfels, Regensburg, Erlangen.
  - 10th Air Army air-defence suppression regions (weapon type not stated): Roding, Kirchroth, Hohenfels, Amberg, Pfreimd, Nagel, Erbendorf.
- Counts and classes only (notes, not rows):
  - Total 131 nuclear weapons (96 missiles + 35 bombs). First strike 41, immediate task 29, subsequent 49, reserve 12.
  - Missile forces: 44 / 42 / 10 reserve. 10th Air Army bombs: 10 / 7 / 2 reserve. 184th HBR: 16.
  - Nuclear strike depth limit "up to the line Würzburg, Erlangen, Regensburg, Landshut". This is a line, not targets.
  - Missile-forces first-strike targets as classes: 7th US Army grouping, part of 2nd AC FRG, part of the air defences.
- Verified vs earlier claims:
  - Nuremberg, Stuttgart and Munich appear only as axes of advance ("advancing toward Nuremberg, Stuttgart and Munich ... immediately after the nuclear strike"). They are **not** named nuclear targets in this translation, which contradicts the Wikipedia/Telegraph 2007 framing.
  - Cross-check with csla.cz plany001 (a Czech secondary rendering of the same plan): it matches the region lists. It renders the English "command and control aviation forces" as "velitelská a naváděcí stanoviště" (command and guidance posts), so the English phrase may be a mistranslation.
- Also in the dossier: Odom's comment (PDF p.31) that East German plans foresaw "as many as 40 warheads to be dropped in the Hamburg vicinity". This is commentary, not a target list, so not extracted.

## 2. PHP collection "European Cities Targeted for Nuclear Destruction: Hungarian Documents on the Soviet Bloc War Plans, 1956–71" (Mastny, Nuenlist, Locher eds., 2001)
Collection page: https://phpisn.ethz.ch/lory1.ethz.ch/collections/colltopic429c.html?lng=en&id=16606

### 2a. "Plan of the 'Easterners'' First Massive Nuclear Strike", June 1965 (Supplement No. 8 to K-1/98/1965, HPA 1st Group Directorate, No. 023/Gyak.)
- Hungarian original (5-page scan): https://phpisn.ethz.ch/kms2.isn.ethz.ch/serviceengine/Files/PHP/19632/ipublicationdocument_singledocument/4021f42c-da63-4424-a2c8-1412ec3f02a2/hu/6506_Plan_Easterners.pdf. Retrieved 2026-10-03T15:03:44Z.
  - File: `php_1965_hu_wargame_plan_easterners_HU.pdf`. sha256 `0e8622a0c07f23e2c5cf057d0f141bc5f4a861d7c06c966d38f9bdb7fd7a2d51`.
- PHP English translation: .../19632/.../en/6506_Plan_Easterners_E.pdf. Retrieved 2026-10-03T15:03:43Z.
  - File: `php_1965_hu_wargame_plan_easterners_EN.pdf`. sha256 `80dbcefdea15bc5ed659281e13666d16babc319075cbbe327c8dc01b345b2d56`.
- Status: **obtained**. Every row was read on the Hungarian scan (PDF pp.4–5) and the quotes are Hungarian.
- CSV: `wp_1965_hu_wargame.csv`, 23 rows.
  - By country: Austria 8, Italy 7, FRG 4, blank 4. The blanks are the Pershing unit and three armoured-infantry brigade battalions whose nationality is not stated.
- Verified facts:
  - Strategic missiles, 500 kt each: BÉCS (Vienna) 2×; ERDING airfield; MÜNCHEN; "PERSHING" o.; nuclear-ammunition depot OBERAMERGAU (sic); AVIANO airfield; VERONA; GHEDI airfield; PIACSENZA airfield; VICSENZA.
  - Long-range aviation: CENTAURO 2×200 kt; ARIETE 3×200 kt.
  - 25th Army missile brigade (R-170): Austrian brigade groups and tank battalions (20–40 kt); GRÁC (Graz) depot of *conventional* ammunition, 40 kt.
  - 20th Air Army: FRG 12th armoured div. 3×50 kt; armoured-infantry brigade tank battalions; LINC (Linz) and KLAGENFURT airfields, 20 kt.
- Corrections to earlier claims:
  - "30 weapons" is the document's own summary, but the itemised strikes add up to **29**. The 500-kt rows add up to **11** against the summary's "10 × 500 kt" and 10 strategic missiles. The 20-kt rows add up to 7 against a summary of 9. Total yield as stated is 7,450 kt.
  - The PHP English renders "Vezetési pontok ellen" (against command posts) as "Points of deploxment". That is a mistranslation.
  - Padua is **not** a target in this plan (see source 8).
  - The 1965 game is an *exercise* (command-staff war game), not a war plan.

### 2b. "Plan of the 'Westerners'' First Massive Nuclear Strike" (No. 0022/Gyak.), mirror against Hungary
- EN: .../19630/ipublicationdocument_singledocument/25b6323f-c328-4f25-9143-a335a21c354e/en/6506_Plan_Westerners_E.pdf. Retrieved 2026-10-03T15:03:43Z.
  - File: `php_1965_hu_wargame_plan_westerners_EN.pdf`. sha256 `810f238972fa92fef9086e14d3dfd7e23d4b7488458b163dd2c2d303d700ee69`. 16 pp.
- EN+HU: .../19630/.../hu/6506_Plan_Westerners_E%2bHU.pdf. Retrieved 2026-10-03T15:03:43Z.
  - File: `php_1965_hu_wargame_plan_westerners_EN_HU.pdf`. sha256 `8509705aea29856b2f670dae7ab340dc40e0b5dc47e6075e6b936c3c0df071ae`. 10-page scan, not transcribed.
- Status: **obtained**. Quotes come from the PHP English text, which is flagged in source_doc.
- CSV: `nato_1965_hu_wargame_mirror.csv`, 26 rows: Hungary 23, Czechoslovakia 2, USSR 1. The 30 plan weapons are complete, totalling 7,405 kt:
  - Polaris 3×800 kt: Csap/Chop (USSR), Miskolc, Debrecen.
  - Pershing 4×1 Mt from SE of Landsberg: Budapest ×3, Székesfehérvár.
  - F-100D, F-104 (Ghedi, Piacenza) and carrier aviation 47 or 28 kt: bridges (Komárom, Dunaföldvár, Baja), airfields (Pápa, Sármellék, Tököl, Kecskemét), SAM units (Sárbogárd, Madocsa), missile units and tank regiments.
  - Plus Brno and Gottwaldov, 2×300 kt, reported for the neighbouring Western Front and outside the 30-weapon plan.
- Other docs in this collection, not opened: war game exercise record, arbitrator summaries, the plan of the two-stage war game, Balló's German analysis.

## 3. PHP collection "A Landing Operation in Denmark: New Evidence from Polish Archives" (Locher & Nuenlist eds., 2002)
Collection page: https://phpisn.ethz.ch/lory1.ethz.ch/collections/colltopic4241.html?lng=en&id=16446

### 3a. Lato-67: "Excerpt of Operational Directive No. 2 of the Maritime Front", 31 May 1967 (Russian; AIC MON Modlin, GISB, spis 18/91/227)
- URL: .../20318/ipublicationdocument_singledocument/61cd99c8-8388-466c-bbd5-f454fda05a53/ru/OperationalDirective_310567.pdf. Retrieved 2026-10-03T15:03:43Z.
- File: `php_1967_lato67_coastal_front_directive02_RU.pdf`. sha256 `a970ff094f1efc0bb73a3e5b641a87fa7dc3f490709dc058c32b32a43f88a605`. 6 pp, 1-bit scan at 200 dpi.
- Status: **obtained**. Read at native resolution.
- CSV: `wp_1967_lato67.csv`, 57 rows: FRG 28, Denmark 18, Netherlands 9, Belgium 2.
- Verified (PDF p.3 = facsimile p.2): "57 ядерных ударов стратегическими средствами – общей мощности 3200 КТ" are delivered **by the UAF Supreme Command in favour of** the Coastal Front. The front does not fire them. The named aim points are:
  - 15 communication junctions. "АРНХЕНАМСТЕРДАМ" is typed run-together and split as Arnhem + Amsterdam.
  - 19 ports.
  - 11 airfields.
  - 5 Nike/Hawk batteries on Zealand.
  - 2 ammunition depots and 4 WMD depots.
  - 1 reactor (W of Lingen).
  - These add up to exactly 57 aim points, or 49 distinct place names.
  - Pałka 2022 (p.108), citing the same Polish file (18/91/227, fols 135–36), counts "fifteen transport hubs, nineteen seaports and eleven airfields", which corroborates the split.
- Corrections to earlier claims and to the Baltic repo transcription:
  - The repo lists 14 junctions (missing Amsterdam) and 17 ports (missing КЕЛЬ, probably Kiel, and Harlingen).
  - The repo's airfield list misses ЭЙНТ..ВЕ (probably Eindhoven) and АСПЕРЕ (25 km S of Utrecht).
  - "~45 named places" is about right: there are 49 distinct names.
- Uncertain readings, flagged in notes:
  - "...РСТЕР" (probably Münster)
  - "КЕЛЬ" (probably Kiel)
  - "ЭЙНТ..ВЕ" (probably Eindhoven)
  - "АСПЕРЕ" (not identified)
  - the battery "10 км юж.(?) КОПЕНГАГЕН"
  - a struck-through first battery entry
- Counts (PDF p.5, facsimile p.4): one army (61, 63, 64, 65 tank divisions) uses the results of 6 strategic strikes plus 46 of its own nuclear strikes, 2,065 kt in total, plus 30 chemical strikes. Of these, 17 nuclear strikes at 729 kt are in the first strike. No targets are named there. The text mentions bypassing NATO "ядерные заграждения" (nuclear barriers) S and W of Hannover.

### 3b. Burza 1961 (Front Nadmorski; AIC MON Modlin, GISB, spis 18/91/30)
- Operational Directive No. 002, 4 Oct 1961 (PL): .../20316/ipublicationdocument_singledocument/5bc8ce55-ee20-44c5-a30c-632f879be2b2/pl/OperationalDirective_041061.pdf. Retrieved 2026-10-03T15:03:44Z.
  - File: `php_1961_burza_maritime_front_directive002_PL.pdf`. sha256 `7c9ce212db0d845fb73ca08425643ce25bd611c0762c7c1d18e44334a5d30c67`.
  - **No named nuclear targets.** The "Wojska rakietowe" section on PDF p.3 gives classes only: enemy nuclear stocks and delivery means, Northern Army Group main forces, German–Danish border fortifications, western Baltic and North Sea naval bases, support of air and sea landings.
  - Allotment of 93 missiles: tactical 3 kt×10, 10 kt×21, 20 kt×12; operational 10 kt×9, 20 kt×9, 40 kt×21; front 200 kt×6, 500 kt×5.
- "Meldunek dotyczący planowania uderzeń jądrowych wojsk rakietowych" (data as of 7.00 7.10 [1961]): .../20314/ipublicationdocument_singledocument/83b161b9-8ba1-4603-b32a-a0cfbab3cc73/pl/Report_001061.pdf. Retrieved 2026-10-03T15:03:43Z.
  - File: `php_1961_report_planning_nuclear_strikes_missile_forces_PL.pdf`. sha256 `2ab2c4403a9c6d7635b23e933320784881f363530bfe81521cd0b23ceed8cb4b`.
  - **16 numbered targets**:
    - Zealand Nike and coastal-artillery targets: BLOWSTER, SEWANG, 4 km SE of ROSKILDE, KEGE, STEWNS. These support the airborne and sea landing.
    - HAGENOW (GDR; NATO forces assumed on GDR soil).
    - DEHENBERG (1st British Corps HQ).
    - ILCEN (11th Div., 3 strikes).
    - Honest John batteries at DALMIN, SZREPKO, NICOW.
    - Nuclear depot S of SZLEZWIG; airfield N of HAMBURG; 3rd Armoured Div.
    - Strategic strikes *requested* from the Unified Command on WEZERMUNDE and WILHELMSHAFEN.
  - Counts: 31 strikes "to commit the main grouping" (14 tactical, 14 army, 3 front), plus one 500-kt target "to be specified later".
- Situation report of the Maritime Front commander, 20.00 10.10.1961: .../20317/ipublicationdocument_singledocument/a15dc579-3ce6-4fe4-839d-31e14cd92837/pl/SituationReport_101061.pdf. Retrieved 2026-10-03T15:03:43Z.
  - File: `php_1961_situation_report_maritime_front_PL.pdf`. sha256 `a05e6e950c70a2f73149500ed6d50298db2e7acd2f207691602e817f63501ef7`.
  - 7 target rows:
    - Bremen pocket + 3rd Armoured Div. S of Wilhelmshaven: 8 strikes, 173 kt.
    - Ports of Wilhelmshaven + Emden: 2 strategic strikes, 700 kt.
    - South of Utrecht: readiness for 3 strategic strikes, 2,000 kt.
    - 1st German Div. on the Dortmund–Ems canal: 5 strikes, 90 kt.
    - Danish 3rd + German 6th Div.: 73 kt.
- CSV: `wp_1961_burza.csv`, 23 rows: FRG 9, Denmark 5, Netherlands 1, GDR 1, blank 7. The blanks are unidentified places and unit targets.
- Correction: the named targets come from the report and the situation report, **not** from the directive.

### 3c. "Wykaz uderzeń jądrowych 'Zachodnich'" (Annex 6), 24 Jan 1962 (spis 18/91/20). New find, mirror against Poland
- URL: .../20315/ipublicationdocument_singledocument/8aab042c-853a-4c70-8054-7b239ae71b27/pl/ListNuclear_240162.pdf. Retrieved 2026-10-03T15:03:43Z.
- File: `php_1962_list_nuclear_strikes_westerners_PL.pdf`. sha256 `60bd07aaa9799808191f3850e8a95c8e99e46e6ec1232a0d282b4a69f2c81137`.
- Status: **obtained**.
- What it is: an annex to a Polish command-staff map exercise ("Organizacja i prowadzenie operacji zaczepnej Frontu z marszu..."). It is a different file and date from Burza, although PHP files it in the same collection.
- CSV: `nato_1962_pl_exercise_mirror.csv`, 76 rows (one strike each): Poland 70, USSR 3 (Brest, Grodno, Rawa Ruska), GDR 2 (Gartz, Schwedt), illegible 1. Total 5,173 kt; 37 ground bursts (N) and 39 air bursts (P).
- Naming: I used the `wp_` prefix to stay inside my write permission. It could be renamed `nato_1962_pl_exercise_mirror.csv` to match the 1965 mirror.
- Uncertain readings: first row (illegible), [D]EBRZNO, [Ł]OMY, KOŻUCHÓW (listed among northern towns).

### 3d. GitHub othercriteria/the-baltic-approaches
- Cloned at commit `ca07850239b73781559bd673c7afcf3bbbec7c3b` (2026-08-05) into the scratchpad. Not kept, because it is not a source document.
- Used `reference/php-maritime-front.md`, and the transcripts for the Pałka, Nielsen and Lautsch URLs. Its transcriptions are secondary, and corrections are listed under 3a. The PDFs it describes are not committed in the repo.
- Not opened: "Message by the Commander of the Berlin Front (Siwicki)... Hannover" (28 Apr 1971) and the "Related Documents" page.

## 4. Pałka, "Planning for a Landing Operation of the Polish People's Army on the Danish Isles during the Cold War", Kwartalnik Historyczny CXXIX (2022) Eng. ed. 6, pp.95–126
- URL: https://rcin.org.pl/Content/238081/WA303_274302_A52-KH-129-EE-6_Palka.pdf. Retrieved 2026-10-03T15:02:26Z.
- File: `palka_2022_kh_ee6_landing_danish_isles.pdf`. sha256 `040015ff3479aa53c1cf4140bd8466b1e0bf3992ffae05452504aee8793a4991`.
- Status: **obtained**. Secondary (scholarly table and paraphrase of AIPN files, which are not online).
- `wp_1977_zealand.csv`, 10 rows, all Denmark:
  - Table 3 (PDF p.21) is from "Legenda do planu operacji desantowej Frontu Nadmorskiego", 9 Sept 1977.
  - Verified: 15 weapons, 2,095 kt in total, the first strike 5.5 h before G-hour.
  - Targets: Fort Dragør, Amager (fort, Hawk, Nike-Hercules), Tune, Store Heddinge, 4 company strongpoints in Køge/Fakse bays (2×300), Fort Stevns 200, Bas-Mosede 15, Honest John battalion 2×15, Danish tank battalion 2×10, Royal Marine Brigade 3×10.
- `wp_1965_coastal_front_zealand.csv`, 5 rows:
  - From p.108 (PDF p.14), paraphrasing "Plan operacji zaczepnej Frontu Nadmorskiego", 28 Feb 1965.
  - 4 strikes on anti-landing defences near Roskilde, Slagelse, Næstved and Vordingborg; 11 on reserves in N Zealand. In total 15 missiles, ~340 kt, plus 5 aerial strikes of unstated yield.
  - Pałka says no Polish weapon was aimed at Copenhagen itself.

## 5. Nielsen, Svenningsen, Tinning & Clemmesen, "An operational map of the Polish Coastal Front 1970", Geoforum Perspektiv 15(27):48–60 (2016)
- URL: https://rucforsk.ruc.dk/ws/portalfiles/portal/59080015/1404_5312_1_PB.pdf. Retrieved 2026-10-03T15:02:26Z.
- File: `nielsen_2016_geoforum_coastal_front_1970_map.pdf`. sha256 `ddef89e8ba8386e7247753144f934d5c3ff8659481c3737a4411e2a8212c4786`.
- Status: **obtained, partial content**.
- The map ("Plan Operacji Zaczepnej Frontu Nadmorskiego", signed by Jaruzelski on 25 Feb 1970) shows 17 *operational* nuclear weapons. The text names only the 5 on Zealand: Stevns fort, Greve, Holbæk, Copenhagen ×2 (PDF p.12).
- The other 12 are "the large ports along the German and Dutch coastlines", which are unnamed. Tactical strikes (small red dots; inset 6) are not itemised. The full-map figure (PDF p.7, 1301 px wide) is too small to read the bomb symbols. The Zealand detail (Fig. 5) is consistent with the text.
- The authors note **Esbjerg is not a target**.
- CSV: `wp_1970_coastal_front_map.csv`, 4 rows (5 weapons), Denmark, SECONDARY.
- Correction: "named cities and strike counts" exist only for Zealand.

## 6. Lautsch, "Kämpfen können, um nicht kämpfen zu müssen" — Zeitzeugenbericht (BMVg, Gespräche am Ehrenmal, 2021)
- URL: https://www.bmvg.de/resource/blob/5109026/3795b6876878de7ebe1f5ed5aec1ca71/zeitzeugenbericht-lautsch-data.pdf. Retrieved 2026-10-03T15:02:28Z.
- Files:
  - Raw download, which the server sent gzip-encoded: `lautsch_2021_bmvg_zeitzeugenbericht.pdf.gz`, sha256 `d75138f0659e37fdc151766f08c3f80a50f0a1b5f5d722da76808d13c8c8780b`.
  - Decompressed: `lautsch_2021_bmvg_zeitzeugenbericht.pdf`, sha256 `3b959b673027f4932bd6bb19394386e7412336590fd4208cb826694719802c1a`, 22 pp.
- Status: **obtained, no nuclear targets**.
- The text describes the 1983 5th Army offensive idea (S of Hamburg towards Ahaus/the Dutch border in 5–7 days) and the 1985 defensive turn. The reconstructed maps (PDF pp.15–17) show axes and units only, with no nuclear strike symbols.
- **Correction**: this document contains no NVA 5th Army nuclear target list, so `wp_1983_nva_lautsch.csv` was not written.
- The relevant piece is Lautsch, "Nuklearkräfte in Europa in den 1980er Jahren. Einsatz der Raketentruppen der 5. Armee der NVA", *Military Power Revue* 2/2014 (ASMZ 180/12, pp.58–73). It was not obtained: archive.org has nothing, and I had no other search route.
- de.wikipedia "5. Armee (Nationale Volksarmee)" (revid 267707290; `wiki_de_5_armee_nva.json`, sha256 `6826839ef4bdb281d5b39c646f6f3b14710e611876660f0b4dd12ce940bdb3a7`) names no targets.

## 7. csla.cz "Válečné plány" pages
- URLs: https://www.csla.cz/armada/taktika/plany001.htm, plany002.htm, plany003.htm. Retrieved 2026-10-03T15:24:20–34Z. plany004.htm returned 404.
- sha256:
  - plany001 `7a0db5cf4e4b8d47863d32ac3fc0d26bf26b31dfa6faeccd3dd7d884149fea1e`
  - plany002 `8edb5970982acf0b6bfcf129f854b76cd2e871bde9d64e3bf82d14f4089470ce`
  - plany003 `d589c1f0b3a214d49b65272b7584b612d3575885144f56409841141eeb63efd8`
- Status: **obtained, counts only** (secondary, by a former ČSLA officer). There are no named target areas for 1977 or 1989, so `wp_1980s_csla.csv` was not written.
- 1977 plan (plany003):
  - 258 nuclear charges: 162 for rocket troops, 96 for aviation.
  - First strike 124 (28 OTR, 56 TR, 40 aviation); immediate task 71 (16/24/31); subsequent task 45 (8/22/15).
  - Reserve is written "8 kusy" but its components are 8 rocket + 10 aviation = 18. 124+71+45+18 = 258, so "8" is a typo.
  - The page also says "Dokument z roku 1974", which is an unresolved date inconsistency.
- 1989 plan (plany003):
  - Defensive. Up to 546 munitions, including the Central Group of Forces.
  - First strike 328 (270 missiles/artillery + 58 aviation); subsequent 169 (137 + 32); reserve 49 (43 + 3, as printed).
  - Warheads from "Časlav" objects per annex 6, which is not available.
  - Signed by Husák in July 1989 and by Havel on 30 Jan 1990, with operations outside ČSSR blacked out.
- plany002: a 1960 ČSLA estimate of the NATO first strike on ČSSR: 40–45 objects, 63–75 weapons (10 kt–5 Mt), and 200–250 more strikes by day 5. This is classes and counts only. It could seed a future defender-perspective file.
- plany001: a Czech rendering of the 1964 plan, matching source 1.

## 8. Wikipedia "Seven Days to the River Rhine" (en) / "W siedem dni do rzeki Ren" (pl)
- en API (revid 1369632420): https://en.wikipedia.org/w/api.php?action=parse&page=Seven+Days+to+the+River+Rhine&prop=wikitext|revid&format=json&formatversion=2. Retrieved 2026-10-03T15:22:10Z.
  - File: `wiki_en_seven_days_to_the_river_rhine.json`, sha256 `1ea9ebc20bd8174701587c09c4f94230e6184eb74ad20fcfb09593ca8d7d4471`.
- pl (revid 77709939). Retrieved 2026-10-03T15:23:02Z.
  - File: `wiki_pl_w_siedem_dni_do_rzeki_ren.json`, sha256 `ac41ad8591b81f78b0c48eea5250d0ff56e004acffc2aa5ec4798a4458fbd323`.
- Status: **obtained (secondary)**. No primary images were obtained.
- CSV: `wp_1979_seven_days.csv`, 9 rows, provenance=reconstruction.
- **Imported details.** None of the en "Known targets" is sourced to the 1979 document:
  - Vienna 2×500 kt, Vicenza, Verona, Padua (500 kt) and "7.5 megatons" are cited to the Telegraph, 1 Dec 2001. That is the 1965 Hungarian war game (source 2a). Padua is not in that primary and looks like an error.
  - Stuttgart, Munich and Nuremberg, and "Lyon by day nine", are cited to the Telegraph, 20 Sep 2007. That is the 1964 ČSLA plan, whose text has these cities as axes of advance, not nuclear targets.
  - Roskilde and Esbjerg are cited to Jyllands-Posten, 18 Jan 2003, which predates the 2005 Polish release and names no plan. Nielsen 2016 contradicts Esbjerg for 1970.
- The pl article repeats Vienna, Vicenza, Verona, Stuttgart, Munich and Nuremberg, without Padua or Danish towns and without inline citations.
- The only 1979-specific claims are from Guardian/Telegraph 2005 (not opened): NATO strikes in the Vistula valley, ~2 million Polish dead, and Soviet counter-strikes on the FRG, Benelux, Denmark and NE Italy. These are classes only.

## 9. CIA: USSR General Staff Academy lessons (1977 lesson set, translated 1980–81)
- The URL in the brief, https://www.cia.gov/readingroom/docs/1980-07-03.pdf, **does not exist**: cia.gov redirects it to the reading-room home page. DOC_0001197534/45.pdf and the site search also redirect, because search needs JavaScript. The redirect pages were deleted.
- Obtained from the archive.org mirror:
  - 0001197534 ("Work of the Nuclear Planning Group Using the Calculations Performed on Electronic Computers...", FIRDB-312/00987-80, 1 May 1980): https://archive.org/download/cia-readingroom-document-0001197534/0001197534.pdf. Retrieved 2026-10-03T15:25:36Z.
    - File: `cia_0001197534.pdf`, sha256 `54eddb0bde648b4ec8732ef383c706fabdd2d2889b906f6a06ffb7ffca416296`. Scan without a text layer; read via archive.org OCR (`_djvu.txt`).
  - 0001197545 ("Study and Critique of the Decision of the Commander of the Combined Baltic Fleet...", FIRDB-312/02033-80, dated 1980-07-04 in the archive.org metadata). This is probably the "1980-07-03" document in the brief. https://archive.org/download/cia-readingroom-document-0001197545/0001197545.pdf. Retrieved 2026-10-03T15:25:41Z.
    - File: `cia_0001197545.pdf`, sha256 `b28c6e4f26028fad58cc2cd1ba73a1fa5eb090db8fd654b10027cacc129ada35`.
- Are targets named? **Partly.** In the front lesson (PDF p.8), the initial nuclear strike names:
  - control and warning posts "in the areas of WROHM, EYTIN, BADMUNDEN, FALLINGBOSTEL, AHRENSBURG" (FRG);
  - real NATO units: 2nd Pershing Squadron, Lance 650th/150th battalions and 24th/50th regiments, Sergeant 450th, 2ATAF CP, NORTHAG forward CP, 8 Hawk battalions, Nike-Hercules 24th/25th, 36th Thunderbird regiment;
  - 14 airfields by number only;
  - corps HQs under colour codes (Brown/Blue/Lilac/Green).
- Counts for the front lesson: 680 warheads (360 rocket troops and artillery + 320 air army); initial strike 376 (176 + 200); immediate task 166 (94 + 72).
- CSV: `wp_1977_gsa_front_lesson.csv`, 19 rows (FRG 5, blank 14).
- Baltic Fleet lesson: classes and counts only (carrier strike groups, naval aviation at airfields, mine depots, C3/EW; 222 munitions, 8,220 kt; 95 in the initial strike; 90 for D to D6). Nations are colour-coded, so no rows were written.
- Not opened: 27 other lessons in the series (e.g. 0001197591 front rocket troops, 0001197491 rocket troops lecture 1976).

## 10. TV2 Denmark, 2 April 2022 (1989 Polish plan against Denmark)
- Status: **not obtained**. nyheder.tv2.dk has no usable sitemap (sitemap.xml returned 404 as HTML) and the site is rendered by JavaScript. Wayback CDX prefix queries (nyheder.tv2.dk/{udland,samfund,politik}/2022-04-0*) returned nothing. WebSearch was unavailable. No targets extracted.

## 11. R-5M "Operation Atom" 1959 (Uhl)
- Uhl & Ivkin, "'Operation Atom'...", CWIHP Bulletin 12/13 (2001). Status: **not obtained**.
  - archive.org item `coldwarinternati0000unse` is lending-only (access-restricted; I did not borrow or log in). wilsoncenter.org returned 404 and the digital archive returned 502.
  - Uhl, *Stalins V-2* (2001) is a book and was not obtained.
- Secondary texts fetched:
  - de.wikipedia "R-5 (Rakete)" (revid 261773610; `wiki_de_r5_rakete.json`, sha256 `b1ded75045594b94b257a5ccb0ccf92cc9479ee2ed00ae3223372373d93136e9`), citing Uhl 2001 pp.236–245. It gives classes only: air bases and ports in the FRG, NL and BE, and US missile sites in the UK.
  - en "R-5 Pobeda" (revid 1330642838; `wiki_en_r5_pobeda.json`, sha256 `7b2e88e710abd84e8608fbbcaeec038b86574cde666d6d8afa1fd3c5637cc42e`) gives no targets.
  - de "Vogelsang (Zehdenick)" (revid 269350436; sha256 `cfb834e80677fbb4383f812f669ea60571ca3ec1837f3539b0cd978371447538`) gives no targets.
  - BBC News, S. Evans, 26 Oct 2012: https://www.bbc.co.uk/news/magazine-20079147. Retrieved 2026-10-03T15:29:46Z. File `bbc_2012_soviet_missile_base_germany.html`, sha256 `a6edb6d873ebb9dcdeff2b34feeb09f68a220b8209727c13fc41b55548c297dc`. It says "targets including London and nuclear bases in eastern England", with 2 bases × 6 missiles.
- CSV: `wp_1959_r5m_operation_atom.csv`, 1 row (London, UK), reconstruction/SECONDARY.

---

## Open issues / next steps
1. **Lato-67 uncertain readings**: "...РСТЕР", КЕЛЬ, ЭЙНТ..ВЕ, АСПЕРЕ, and the Copenhagen battery direction. A better scan, or the Polish General Staff list "Wykaz obiektów uderzeń jądrowych środkami strategicznymi" (CAW-WBH 18/91/227, fols 135–36, cited by Pałka), would resolve them.
2. **Burza place names**: BLOWSTER, SEWANG, DEHENBERG, ILCEN, DALMIN, SZREPKO and NICOW are not identified. They may be exercise-garbled or fictional. Candidates (Blovstrød, Uelzen, Dannenberg) are given in notes as unconfirmed.
3. **1965 Westerners mirror**: quotes are from the PHP English. The Hungarian scan (`..._EN_HU.pdf`) should be checked for spellings.
4. **1970 map**: the remaining 12 operational strikes (ports) and the tactical strikes need a high-resolution copy of the map (Danish Royal Library holding).
5. **NVA 5th Army** nuclear targets: Lautsch, Military Power Revue 2/2014. Wenzke (ed.) 2010 is also a candidate.
6. **ČSLA 1977/1989 named targets**: still none. The VHA operational plans or the "Časlav" annex 6 would be needed.
7. **TV2 2022** and **CWIHP Bulletin 12/13 (Operation Atom)** need a working search or library access.
8. **Seven Days 1979** primary (IPN 2005 release; map images): not located. The Guardian/Telegraph 2005 articles were not opened.
9. **CIA lesson series**: 27 more lessons to scan (e.g. 0001197591, 0001197581). Some may name places like 0001197534 does.
10. Further PHP items noticed but not processed: "List of Nuclear Strikes" companion annexes; 1971 Siwicki/Hannover message; Balló's "Die Ungarische Volksarmee im Warschauer Pakt" (German PDF on the PHP mirror); and the Hungarian collection's other 1965 documents (arbitrator reports).
