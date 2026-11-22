# Post-1990 public target lists (topic `modern`)

Collected 2026-11-22. Raw files: `data/raw/modern/` (46 files; URLs and sha256 in
`data/sources.d/modern.yaml`). Build script, which checks that every quote occurs verbatim
(whitespace-normalised) in the cited raw file: kept in the session scratchpad, not in the repo.
Rows are written to `data/curated/labels/<plan_id>.csv`, with catalogue fragments in
`data/curated/labels/catalogue.d/`.

General caveats:
- The press-based lists (1-7) are **reported**, not seen. For the leaked Russian files, the FT
  originals are paywalled. Every row cites a free outlet that reproduces or quotes the FT, and the
  outlet's date.
- `statement` is a new provenance value. `tests/test_catalogue.py` does not accept it yet, so the
  coordinator must add it to `PROVENANCE`.
- No coordinates are given in any source, so `lat`/`lon` are blank.

## 1. `ru_2024_ft_japan_korea` (5 rows, plan)

- **Story:** FT, 31 Dec 2024. 29 Russian military files from 2013-14 (an officer-training
  presentation on Kh-101 strikes) list about 160 targets in Japan and South Korea. 82 of them are
  military (HQs, radars, air and naval bases), but none of those is named in any reproduction found.
- **Named sites:**
  - Kanmon tunnel;
  - "nuclear complexes in Tokai" (one of 13 power plants);
  - Okushiri radar base (the worked Kh-101 example);
  - Pohang steelworks;
  - chemical factories in Busan.
- **Sources:**
  - Kyiv Post (quotes the FT directly);
  - Asiae (EN) and Hankyung (KO), 1 Jan 2025;
  - Mediazona and Novaya Gazeta Europe (RU), 31 Dec 2024;
  - Meduza and Kyiv Independent (context only).
- **Doubts:** the FT chose to name the civilian sites, so the sample is biased towards them. The
  plan is for conventional strikes, not nuclear ones. SCMP's version could not be fetched (403).

## 2. `ru_2024_ft_europe` (12 rows, plan)

- **Story:** FT, 13 Aug 2024. Navy files from 2008-14 contain maps with a sample of 32 NATO targets
  in Europe for nuclear-capable missiles, "for presentation rather than operational use".
- **Named sites:**
  - Bergen naval base (United24 reproduces the FT map caption);
  - Barrow-in-Furness submarine shipyard (FT caption);
  - a target near Hull "marked with a smokestack" (FT caption);
  - an undisclosed target in Edinburgh (LBC; Rosyth is only LBC's guess, kept in `notes`);
  - Pärnu, Estonia (Baltic Sentinel, from the FT map);
  - Deveselu, Mihail Kogălniceanu and the Giurgiu–Ruse bridge (RFE/RL Romania; Lepetitjournal adds
    "apparemment"; Fakti.bg treats the bridge as Bulgaria's target);
  - Gölcük naval base, a nearby refinery and the command HQ in Ankara (Turkish Minute);
  - "the western coast of France" (Polskie Radio): a region, kept for audit.
- **Not named:** Germany's 5 targets (iPrima says ports, a special-forces training centre and a
  radar), 1 of Bulgaria's 2, 2 of Turkey's 5, and the Asian targets (China 5, North Korea 2,
  South Korea 1, Japan 6, per RFE/RL).
- **Shenyang:** the Maps Mania blog names it as a target in China. It is not a reputable outlet,
  so there is no row.

## 3. `ru_2019_kiselyov` (5 rows, statement)

- **Broadcast:** Rossiya-1 "Vesti Nedeli", 24 Feb 2019.
- **Targets:** the Pentagon, Camp David, Fort Ritchie, McClellan and Jim Creek.
- **Sources:** Military Times (from Reuters, 25 Feb 2019). The Bulletin (4 Mar 2019) confirms all
  five and notes that two of the sites are closed. CNBC's copy of the Reuters story returned 403.

## 4. `kp_2013_threats` (10 rows, statement)

- **"U.S. Mainland Strike Plan" map (미본토타격계획):** KCNA photo, 29 Mar 2013.
  - NK News reads San Diego, Washington D.C., Hawaii and "possibly Austin".
  - The Aviationist reads the same four, with Honolulu for Hawaii.
  - Foreign Policy reads Los Angeles instead of San Diego (recorded in `notes`).
- **KPA Supreme Command statement, 21 Mar 2013:**
  - Andersen AFB on Guam;
  - naval bases "on the Japan mainland" and on Okinawa (generic rows; neither is named).
  - Sources: Arab News/AFP; CSMonitor and IBTimes corroborate.
- **Rodong Sinmun editorial, 10 Apr 2013:** Tokyo, Osaka and Kyoto, as a conditional threat. Seen
  only in a Spanish agency report (colombia.com), not in the Korean original.

## 5. `kp_2017_guam_plan` (1 row, statement)

- **Statement:** KCNA, 9 Aug 2017. The aim is to "contain" the US bases on Guam, "including the
  Anderson Air Force Base" (Korea Times/Yonhap).
- **Aim points:** the 10 Aug plan sets impact points in the sea 30-40 km off Guam (Japan Times). The
  base is therefore the object of the threat, not an aim point.
- **Context only:** PBS, CBS and Newsweek/Yahoo (the 14 Aug "Firing Strike Plan" photo).

## 6. `kp_2023_published_maps` (2 rows, statement, audit only)

- **Gyeryongdae:** Korea JoongAng Daily, 31 Aug 2023, reading a KCNA photo.
- **Seoul and Osan Air Base areas:** Asiae, 10 Aug 2023, reading a KCNA photo.
- **Caveat:** these are journalists' readings of the maps. KCNA named only target classes.
- **Not extracted:** the 2016 "firepower strike plan" map (no places named in the coverage found)
  and the Oct 2024 map of Seoul (blurred).

## 7. `ir_2025_dimona_threats` (2 rows, statement, audit only)

- **Statements:** Dimona was named by an anonymous senior official to Al Jazeera (Ynet, 21 Jun 2025)
  and by an anonymous senior military official to Iran Nuances (Shafaq, 4 Mar 2026).
- **Excluded:** a 2019 Friday-prayer threat (JPost) has no row, because a prayer leader is not a
  state official. The search of Iranian statements was not systematic.

## 8. `rec_2001_nrdc_maonf_targets` (232 rows, reconstruction)

- **Source:** NRDC, *The U.S. Nuclear War Plan: A Time for Change* (June 2001), PDF from nrdc.org
  (sha256 `fe4ede1e…b9f9`). This is a different file from the copy cited in `civil_defence.md`
  (`ec45e72b…`). PDF page = printed page + 12.
- **Rows, from the MAO-NF chapter (184 attacked):**
  - 6 silo fields (p.54; yields from p.60);
  - 10 SS-25 bases (p.64; 2 W76 on each base and garrison, p.69);
  - 3 SS-24 bases (p.74; warheads from Table 4.6, p.77);
  - Northern Fleet, Table 4.9 (23 rows; Murmansk/Sevmorput withheld, so `selected=0`);
  - Pacific Fleet, Table 4.10 (11 rows);
  - aviation, Table 4.11 (63 rows, 19 + 54 W76);
  - nuclear warhead storage, Table 4.13 (64 rows; only the 17 national-level sites are attacked,
    with 8 W76 each, so the other 47 have `selected=0`);
  - design and production, Table 4.15 (11 rows);
  - satellite earth stations, Table 4.17 (41 rows; no per-site warheads).
- **Quotes:** verbatim excerpts of the PDF text layer. For the two-column Table 4.11, an excerpt can
  run on into the other column.
- **Not named in the report:** early-warning radars, VLF/LF stations and leadership targets, so they
  have no rows.

## Looked at, not extracted

- **Princeton SGS "Plan A" (2019):** the Arms Control Today write-up gives only target classes
  (tactical, counterforce, then city phases). The SGS page now returns 404, and no named list is
  published.
- **FAS/NRDC, *From Counterforce to Minimal Deterrence* (2009):** models 12 named Russian
  infrastructure targets, but the PDF is blocked (see below).
- **FAS/Bulletin Nuclear Notebook:** lists forces, not attack target lists. Not pursued.
- **Official government risk assessments with named hypothetical targets:** none found. US
  National Planning Scenario 1 (an improvised nuclear device in Washington) is terrorism, out of
  scope.

## Blocked (fetch from the user's machine)

- FAS PDFs, which return HTTP 202 with an empty body (bot check):
  - https://nuke.fas.org/norris/nuc_10042901a.pdf
  - https://pubs.fas.org/_docs/occasionalpaper7.pdf
  - https://programs.fas.org/ssp/nukes/publications1/Brief2009_MORS-050509.pdf
- Returned 403:
  - https://www.scmp.com/week-asia/politics/article/3293037/russias-uncovered-secret-war-plans-target-160-sites-japan-and-south-korea
  - https://www.pravda.com.ua/eng/news/2024/08/13/7470190/
  - https://www.cnbc.com/2019/02/25/after-putins-warning-russian-tv-lists-nuclear-targets-in-us.html
  - https://www.timesofisrael.com/iran-threatens-to-hit-dimona-nuclear-site-if-israel-and-us-try-to-topple-regime/
- GlobalSecurity, which returned 402 (KCNA texts):
  - https://www.globalsecurity.org/wmd/library/news/dprk/2013/dprk-130321-voa01.htm
  - https://www.globalsecurity.org/wmd/library/news/dprk/2017/dprk-170810-pdo02.htm
- The connection failed:
  - https://www.asiae.co.kr/en/article/2023041110224796934 (April 2023 map, reportedly Pyeongtaek)
- Not attempted:
  - the FT originals (paywall);
  - KCNA originals (kcna.kp).
