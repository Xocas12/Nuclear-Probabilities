# Progress log, 3 October to 5 November 2026

Dated notes moved out of PLAN.md section 9, newest first. They are a historical record: each figure is of its
date, on the labels and code of that date, and many were later superseded. Current results are in REPORT.md and
`runs/`; where this log and REPORT disagree, REPORT holds.

**Progress (3 Nov 2026).** The sealed set was scored once under `configs/protocol_amendment_11.yaml`, committed before the scores existed (`runs/classifier/sealed/`, REPORT.md "The sealed set, scored once").

**Progress (1 Nov 2026).** The protocol is committed and M6 and part of M7 run under it: global, US and
pooled Warsaw Pact models (`REPORT.md`, `runs/classifier/`). The protocol (`configs/protocol.yaml`) replaces the
zoo of section 5.4: two candidates with fixed settings, no tuning. The sealed set waits for review.

**Progress (10 Oct 2026, evening).** M4 is done.
- **NAPB-90 Annex B** (fallout risk by county, `data/curated/napb90/fallout_counties.csv`).
  It covers 3,139 counties. Every county's population and area matches Annex A except six,
  each checked on the scan. Massachusetts' printed totals leave out Barnstable and Berkshire
  in both annexes. Fallout is a consequence, not a target label: it stays out of features.
- **Transfer universes** (`data/curated/gazetteer/TRANSFER.md`, `nucprob/transfer/`). These
  are census town tables:
  - Japan 1940, the US 1950, Canada 1956;
  - Denmark and the Netherlands 1960; Belgium, Austria and Italy 1961;
  - the UK 1981, by district.
  Every place is located, and each table has a card. Two curated military tables were added
  (Western Europe 1965, the UK 1980). The FRG was withheld until 1 Nov 2026, when
  the official table of all 583 towns of 1961 was fetched (`towns_frg_1961.md`).
- **Transfer check** (`runs/m4-transfer-check/`). The check fits on the bloc's SAC labels
  with the 20 common features and scored 16 lists then (Square Leg has since been withdrawn); the bloc lists are scored leave-country-out.
  - Read in PR-AUC, the primary metric (§5.5), with paired bootstrap intervals for
    LightGBM (common) minus the population rule (`runs/m4-transfer-check/paired.csv`).
  - On Operation Alert the bloc model ranks the top of the list clearly worse than population alone:
    PR-AUC 0.09 against 0.74,
    -0.65 [-0.81, -0.44]; precision@k 0.00 against 0.64, -0.64 [-0.86, -0.36]. The 1945
    Target Committee's 6 designated towns: -0.42 [-0.82, -0.11], precision@k -0.67 [-1.00, -0.17]. Canada 1956, from an extract of unrecorded origin,
    cannot be told apart (PR-AUC -0.04 [-0.12, +0.04]). ROC-AUC hid most of this.
  - On the mixed civil and military lists no gain is detectable (Square Leg, scored here at first, was withdrawn on
    2 Nov 2026 with its universe, tenth amendment): Lato-67, with the FRG in its universe since 1 Nov 2026, +0.02 [-0.02, +0.08] and
    +0.05 [-0.05, +0.22] (of the links as corrected on 5 Nov 2026, seventeenth amendment, and without the Dutch towns
    withdrawn on 5 Nov 2026, nineteenth amendment). These intervals include zero.
  - One exception: the Polish mirror list gains in PR-AUC, +0.14 [+0.07, +0.21], with
    precision@k +0.07 [0.00, +0.22]. It records what Polish staff expected NATO to strike.
  - This is a check, not a result.
- **Left for M4's L items:** TR-82 and the DTIC appendices (blocked), the UK lists at Kew, the
  print books, and an official FRG 1961 table.

**Progress (10 Oct 2026, later).** M4 is done for the cheap lists, the first M list and its
feature build.
- **NAPB-90, the US at scale** (`data/curated/napb90/`). FEMA's county table of direct-effects
  risk is transcribed in full: 3,142 counties with their highest blast band.
  - Two independent passes agree on every figure.
  - Counties are matched to FIPS codes and checked against the Census Bureau's 1985 estimates
    and the 1990 boundaries.
  - Slips in FEMA's own tables are documented.
- **US features as of 1985** (`nucprob/us1985/`, `data/FEATURES_US.md`). 29 features in six
  families for all 3,141 counties, including a curated, dated table of 196 military sites
  (Wikipedia, no target lists). The leakage guard covers them.
- **US check run** (`runs/m4-us-check/`), "very high" band (base rate 0.25): PR-AUC 0.65 for the
  population rule, 0.71 with population plus military, 0.74 for LightGBM on everything.
  Military is the family whose removal costs most. This is a check, not a result.
- **Small lists completed:**
  - Taiwan Strait 1958 (Halperin): 4 named targets. The plans name only target types.
  - JCS 1963 China vulnerability study: 9 targets.
  - Operation Alert 1955: 60 cities, 44 of them from the 1955 press.
- **Data cards.** Every label file has a card and a provenance tag
  (`data/curated/labels/CATALOGUE.yaml`, rendered in `data/INVENTORY.md`), enforced by a test.
- **Left for M4's L items:** Annex B (fallout) of NAPB-90, TR-82 and the DTIC appendices
  (blocked), the UK lists at Kew, and the print books.

**Progress (10 Oct 2026).** M3 is done. The three lists the Archive published only in excerpt
(the Part I airfield list, the Part II complex list with weapons, and the cross-reference list)
are transcribed through the same pipeline (`data/curated/sac1956/excerpts/`).
- **Error rate measured.**
  - Per pass, as before.
  - A blind audit of a 5% sample of the full lists found no error in 743 lines (95% bound
    0.51%).
  - The 270 airfield rows that both airfield lists print were compared line against line. This
    found 3 misreads in the Part II transcription and 1 in the Part I excerpt (BRODY), and
    corrected them. Of the other 15, 6 are coordinate differences between the two printings
    (4 of them Part II typing slips), 8 are unresolved (4 rest on a faint Part II glyph against
    a clear Part I 8 and are probably Part II misreads: AKTYUBINSK, BREST, BRIYENI, BUZAU),
    and ONEGA differs only by a period. All 19 fall on the 216 rows of the ~200-dpi pages:
    3 confirmed misreads in 216 (about 1 in 72), 7 counting the probable ones (1 in 31). The
    label rows affected say so in `notes`.
- **Anchors.** Moscow, Leningrad and East Berlin reproduce. The study's own totals (section 8)
  are redacted figure by figure, so there is nothing more to reproduce.
- **The Part II subset.** Part II keeps every excerpted complex, with its priority and
  installations, but far fewer aim points: 24 against 65 in the 33 complexes seen whole. The
  16 excerpted complexes ranked 1 to 236 all keep one, and 2 of the 13 below that do. This
  is a second, stricter label (`part2_has_dgz`). It is known for about 1,400 settlements,
  28 of them positive.
- **The cross-reference excerpt** does not reach the page lost from the Part I scan.

Data card: `data/curated/sac1956/README.md`.

**Progress (8 Oct 2026).** M2 is done: the full 1956 feature base for the whole bloc.
- **Universe.** 2,622 towns of 10,000+ near June 1956 with coordinates.
  - The USSR comes from the 1959 census, plus ten closed towns of the nuclear complex with
    imputed populations.
  - East Germany, Poland, Hungary, Czechoslovakia, Romania, Bulgaria and Albania come from
    their 1950s censuses and yearbooks, interpolated to the study date. Some had to be read from
    scans: the GDR's 1956 yearbook, Poland's 1957 yearbook and Votrubec (1959) for Slovakia.
  - China's universe is its 163 cities of the 1953 census. North Korea, North Vietnam and
    Mongolia have only the UN's estimates for their largest cities.
  - The SAC targets are linked per country, and the list's two scan gaps apply bloc-wide.
- **Features: 48 in six families.**
  - population;
  - administration: a cited table of the 1956 regional centres, with the oblasts of 1954–57;
  - geography and reach: terrain; the sea; the capitals; NATO territory, the bloc's frontier
    and SAC's overseas bases on the study date; the continental US;
  - industry: the Soviet defence industry active in 1956, from Dexter and Rodionov; WRI power
    plants;
  - military: a cited, dated table of 153 sites (district and fleet HQs, naval and Long-Range
    Aviation bases, the nuclear complex, test ranges) with a decision for June 1956; airfields;
  - transport.
- **Provenance.** Every feature names its sources and flags later knowledge
  (`data/FEATURES.md`). Every source in the manifest has a role. A guard test keeps the label
  sources out of the features.
- **Check run** (`runs/m2-check/`, regenerated on 1 Nov 2026 after the geocoding and label
  fixes). This is a check, not a result. Under spatial CV, "on the list" scores a PR-AUC of 0.77
  for the population rule and 0.85 for LightGBM on every feature. Most of that gap is between
  countries, not within them. At a given size the share of towns SAC listed differs a lot by
  country (towns of 20,000-30,000: 43% in the USSR, 79% in Czechoslovakia), and one pooled curve
  on population cannot fit that, so any family that tells the countries apart is credited with
  the difference. On the same splits, the population rule with one intercept per country already
  scores 0.82 (0.70 for "given a DGZ", against 0.65 pooled), about two thirds of the way to every
  feature. Scored inside each country (PR-AUC per country with at least ten places of each class,
  weighted by positives), every feature adds only 0.02 over the rule for "on the list" (0.82 to
  0.84) and 0.02 for "given a DGZ" (0.72 to 0.73). Over population plus country
  (`gains.csv`), transport adds +0.03 (fold spread 0.01), geography +0.02 (0.02) and military
  +0.01 (0.01); industry and administration add about 0.
  Geography's anchor distances (km to Moscow, to a SAC base) partly just say where a town is:
  over a location-only control (latitude and longitude) geography adds +0.01. Inside the USSR
  every feature beats the rule (0.78 to 0.81), and in Hungary (0.79 to 0.86); in Poland,
  Bulgaria, Romania and China the rule alone scores higher than the global model. The military
  sites add almost nothing once the rest are in (0.845 with them, 0.846 without). Dropping the
  anachronistic features costs about 0.02.
- **Closed towns and cover names.** None of the ten closed towns appears on the 1956 list under
  its own name, but SAC did list the plants of three of them under the open town next door:
  Mayak (Ozersk) under KYSHTYM, with a 040 A/E line and an aim point 6 km from Ozersk; the
  gaseous-diffusion plant (Novouralsk) under the sub-complex VERKHNE NEYVINSKIY, with a 044
  line; and the Kapustin Yar range (Znamensk) under KAPUSTIN YAR, with a 210 guided-missile
  line. The labels now credit those entries to the closed town as well as to the open one
  (`data/curated/sac1956/cover_names.csv`), so Ozersk, Novouralsk and Znamensk count as
  listed with an aim point. Seversk, Snezhinsk, Sarov, Zheleznogorsk and the rest have no such entry nearby.
- **Gaps.**
  - Slovakia's towns that passed 10,000 after 1953 are missing.
  - China's towns below city rank are missing.
  - Ullman's 1958 figures for China need a manual download.
  - District HQs for Hungary, Albania, North Korea and North Vietnam are unverified.

**Progress (7 Oct 2026, later).** M0 and M1 are done. The scaffold (uv, Python 3.12, ruff,
pytest, Make, CI) and the provenance manifest are in place. The USSR slice runs end to end:
1,635 towns of 10,000+ in 1959 from pop-stat and Demoscope, 99% given coordinates by a
gazetteer over GeoNames; the SAC 1956 targets linked to them (coordinates first, names second);
population and administrative features; the population rule, logistic regression and LightGBM
under spatial-block CV, with the sealed test blocks set aside; and a map (`runs/m1-slice/`).
First read, not a result: population alone ranks the towns nearly as well as every slice model
(PR-AUC 0.79 vs 0.80 for "on the list"), so industry, military and transport must carry what is
left. Building the slice exposed a page missing from the SAC scan (Astrakhan, Ashgabat, Arzamas;
see the data card). Next: M2, the full 1956 feature base.

**Progress (7 Oct 2026).** M3 is done for the two complete lists: the Part I complex list and
the Part II airfield list are transcribed (two passes by different models, every disagreement
adjudicated on the scan, a second look at every line a consistency check flags), with an error
rate measured per pass and a data card. Outstanding for M3: the Part II complex excerpts.

**Progress (3 Oct 2026).** The first pass of M4 is done: 24 lists extracted, every row with a
page reference and a quote (see `data/INVENTORY.md`). For the 1956 list, everything is
downloaded and piloted, and the category codes are transcribed. Feature sources are confirmed
downloadable: pop-stat's 1939/1959 census series, the Dexter–Rodionov guide (v24, July
2026), GeoNames. The code scaffold (pyproject, tests, CI) is not started.

| # | Milestone | Size | Done when |
|---|---|---|---|
| M0 | Scaffold; network access working; ask for the 1,154-target CSV | S | `make setup test lint` green in CI; every source is listed in `data/sources.yaml` |
| M1 | **Vertical slice**: USSR only; 1959 universe; population and administrative features only; city-level labels from the fastest source; population rule vs. logistic regression vs. LightGBM; a quick lonboard map | M | Every join works end to end on real data. The slice's numbers are not results |
| M2 | Full 1956 feature base: all families, whole bloc, curated military and administrative tables, leakage guard | L | Feature table with provenance and anachronism flags; tests green |
| M3 | Full 1956 labels: the Part I table of DGZs, the Part II subset, the airfield list | L | Error rate measured; published anchors reproduced; data card written |
| M4 | **More labels, cheapest first.** The S-effort lists of §4.5, then the M lists, plus as-of feature builds for each new country and year. L items (archives, print books) only if someone can fetch them | M → L | Each list has a data card and provenance tag |
| M5 | Freeze the protocol (including the regime coding); seal the test blocks | S | `configs/protocol.yaml` committed with its hash |
| M6 | **Level G**: the global model zoo across T1–T5 | M | Leaderboard with cross-validation spreads |
| M7 | **Levels C, R, H**: per-country, per-regime-type and hierarchical models; transfer matrix | M | Specialisation gains with CIs, for every country and regime group that has enough data |
| M8 | Explanations and findings memo, including driver profiles by country and regime type | M | Ablation, SHAP and ALE agree, or the disagreement is reported; sealed test scored once |
| M9 | Interactive map on GitHub Pages, with the level selector and transfer-matrix panel | M | All views and place cards work, including at phone width |
| M10 | Stretch: L-effort archive lists; optional present-day counterfactual | L | — |

The slice (M1) comes early on purpose. It tests the risky joins (transliteration, historical
renames, linking DGZs to places) on real data before anything is scaled up. It also gives an
early read on how much population alone explains.

---
