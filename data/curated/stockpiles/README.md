# Nuclear warhead inventories and delivery assumptions: data card

These tables give cited warhead inventories and stated assumptions, as inputs for a coarse area-level map of P(area struck | stockpile) at 0.5 degrees or coarser. They hold no facility-level data. All sources were retrieved on 2026-11-01. Downloads stay out of git, in data/raw/stockpiles/<source_id>/. The tables carry figures, short quotes and citations only.

## What the files hold

stockpiles.csv has one row per scenario year, state, delivery type, count basis and source. Modern rows use the 2026 figures, which is the latest edition; FAS gives them as of the beginning of 2026 and SIPRI as of January 2026. Historic rows cover the US and USSR for 1945, 1950, 1956, 1961, 1965, 1970 and 1977. A blank low and high means the source gave one number.

The count_basis stockpile_total means total inventory, including retired warheads awaiting dismantlement. military_stockpile excludes retired warheads. retired is the retired warheads alone. Extra values were added because the source categories have no match in the requested list: operationally_available (UK), military_stockpile_land_missiles and military_stockpile_sea_cruise (categories mixing ranges or cruise missiles, kept as delivery unspecified rather than relabelled icbm or slbm), and reserve_other_stored. strategic_force_loading is the NRDC measure for 1956 and 1965.

assumptions.csv has one row per stated assumption. A blank value with "no source found" means no opened document supported a number; none was estimated. Interceptor counts are counts. Fractions lost to defences are blank for the modern period and were deliberately not derived from them. Rows with a blank quote carry their source wording in notes.

## Cautions

FAS and SIPRI are not independent, because both estimates come from Kristensen and Korda. Treat their agreement as consistency, not confirmation. They differ in two places. India deployed is 0 in FAS and about 12 in SIPRI, and both rows carry low 0, high 12. US deployed is 1,670 in FAS and 1,770 in SIPRI, which is only a definition difference: FAS lists 100 nonstrategic separately.

The FAS page has internal inconsistencies, left as published. Its text gives 12,187 warheads and also "an estimated 12,321 at the beginning of 2026". Its India row does not add up (0 + 178 against 190). Its deployed strategic rows sum to 3,900 against a stated ~3,912, which the 12 Indian warheads would explain. FAS footnotes also show that some country overviews behind the table are older than 2026.

Historic totals and historic splits measure different things. The OWID series is the whole military stockpile. The NRDC tables are strategic force loadings at the end of the year, so they are much smaller and should not be subtracted from the totals without further sourcing. For example, the US in 1956 has 3,692 in total and 2,123 strategic bomber warheads.

Alert data by state dates from 2012, and US alert levels by delivery date from 2001, when forces were larger. Reliability values are analysts' assumptions of 80 to 90 percent, not measured rates. The 1953 FRUS fractions describe Soviet bombers attacking the US, so applying them to SAC in 1956 would be an extrapolation.

SIPRI's terms allow analytical use and fair-use reproduction of under 10 percent of a data set, and require authorisation above that. So the rows transcribed from SIPRI Yearbook 2026 chapter 8 are not committed; they stay in the git-ignored data/raw/stockpiles/sipri_yb2026_rows.csv. Committed from it are the 2026 rows of delivery_mix.csv, shares by delivery rounded to 0.05 for the seven states the maps use, and two short quoted counts in assumptions.csv. Every committed inventory figure is from FAS, OWID or NRDC. The 2026 mix cannot be recomputed from a clean clone without reading the chapter. Its bases differ: US and Russia are deployed forces, the others the stockpile or what is operationally available. `land_missile` is SIPRI's land-based category for China, India and Pakistan, which mixes ranges; it is not the same class as `icbm`. The 1956 US and 1965 Soviet rows come from NRDC's strategic loadings in stockpiles.csv and are exact to 0.01. No split was found for 1950, so that scenario's delivery stays unspecified.

## What could not be obtained

Bulletin of the Atomic Scientists Nuclear Notebook entries (including Russia 2026, DOI 10.1080/00963402.2026.2659527, and US 2026, DOI 10.1080/00963402.2026.2633029) were not read. The thebulletin.org robots.txt disallows the agents anthropic-ai and ClaudeBot from the whole site. The table at thebulletin.org/wp-content/uploads/2026/05/rbul_a_2659527_t0001-full.pdf was downloaded once before that file was read, then deleted unopened; no figure comes from it and no hash was kept. Taylor & Francis returned HTTP 403 for the same articles and this was not worked around. Search-result excerpts of these articles were not used as sources. The Russia split in the table comes from SIPRI Table 8A.3 instead, and it has the same authors.

Norris and Kristensen 2010, "Global nuclear stockpiles, 1945-2010", could not be opened: SAGE and Taylor & Francis returned 403, and the Bulletin is disallowed as above. The OWID series citing FAS was used as the agreed alternative, and its agreement with the 2010 paper is unchecked. FAS revises this series, so values may differ from the 2010 print.

Rosenberg 1983 had no open copy. The RAND R-266 and DTIC AD1033589 downloads returned 403. congress.gov robots.txt disallowed the CRS PDF, so EveryCRSReport was read instead. mda.mil, nuke.fas.org and globalsecurity.org could not be reached. Consequently there is no opened figure for the following: US bomber attrition over the USSR in 1956, alert shares for the historic years, modern bomber reliability, or any modern fraction of warheads lost to defences. Those rows are blank with notes.

## Sources cited in the tables

**fas_status.** Status of World Nuclear Forces (2026 table). Publisher: Federation of American Scientists. URL: https://fas.org/initiative/status-world-nuclear-forces/. Licence or terms: Page states "Federation of American Scientists (c) 2026"; no licence on the page itself. The OWID record for this data gives CC BY 4.0. Retrieved 2026-11-01. sha256 of page.html: 50e6f6b1b234f0347149228dccd0e4f4426bbfd07c0507110fe0daf966096d96. Used for: 2026 warhead counts for all nine states; global alert count. Not obtained: Nothing missing from this page. It splits by deployed strategic and nonstrategic, reserve, stockpile and inventory, not by ICBM, SLBM and bomber.

**sipri_yb2026_ch08.** SIPRI Yearbook 2026, chapter 8, World nuclear forces. Publisher: Stockholm International Peace Research Institute. URL: https://www.sipri.org/sites/default/files/YB26%2008%20World%20Nuclear%20Forces.pdf. Licence or terms: (c) SIPRI 2026. SIPRI terms: data may be used for analysis; reproducing more than 10% of a data set needs permission. See sipri_terms. Retrieved 2026-11-01. sha256 of ch08.pdf: 026508a1d9c95a76aabb52f422bfc100517a9f07a4e65a43b57e50042c46db52. Used for: January 2026 cross-check and all delivery splits; alert range. Not obtained: Nothing missing. All nine states are covered, but North Korea has no warhead split by delivery.

**sipri_terms.** Terms and conditions. Publisher: Stockholm International Peace Research Institute. URL: https://www.sipri.org/about/terms-and-conditions. Licence or terms: As stated on the page itself. Retrieved 2026-11-01. sha256 of page.html: 4aaa3846bb516a6718648c380cec1c841e5c8f410fdc464c9c72161b02cd4791. Used for: Reuse conditions for SIPRI figures. Nothing further was needed from it.

**owid_warhead_stockpiles.** Estimated number of nuclear warheads, grapher CSV. Publisher: Our World in Data, citing Federation of American Scientists. URL: https://ourworldindata.org/grapher/nuclear-warhead-stockpiles.csv. Licence or terms: OWID indicator metadata gives CC BY 4.0 for the FAS origin (retained copy in owid_indicator_meta). Retrieved 2026-11-01. sha256 of data.csv: 5fa030e5a7e312c74884adf5d9154afef16fd2fc7fe6b33eaa6ee72401dd7a9b. Used for: US and USSR stockpile totals 1945-1977. Not obtained: The FAS source chart data was not downloaded directly; this is the OWID processed copy.

**nrdc_table_us.** Table of US Strategic Offensive Force Loadings, 1945-2002. Publisher: Natural Resources Defense Council, Wayback Machine capture of 28 March 2014. URL: https://web.archive.org/web/20140328105437/http://www.nrdc.org/nuclear/nudb/datab1.asp. Licence or terms: Page states (c) Natural Resources Defense Council. Figures only are reproduced. Retrieved 2026-11-01. sha256 of table.html: 5bc2192355281909dd4c1e999b774fc7e6937b314319cf937bef002e022fed6a. Used for: 1956 US split by delivery. Not obtained: The current nrdc.org address was not tried; the underlying 1997 Norris and Cochran databook was not opened.

**nrdc_table_ussr.** Table of USSR/Russian Strategic Offensive Force Loadings, 1945-2002. Publisher: Natural Resources Defense Council, Wayback Machine capture of 28 March 2014. URL: https://web.archive.org/web/20140328104322/http://www.nrdc.org/nuclear/nudb/datab2.asp. Licence or terms: Page states (c) Natural Resources Defense Council. Figures only are reproduced. Retrieved 2026-11-01. sha256 of table.html: d119f6f4ed81dd96f11d1670186b9fce1ff75da49ff27919bc4978b377e5e6f3. Used for: 1965 USSR split by delivery. Not obtained: As for nrdc_table_us. The USSR table starts in 1956.

**nrdc_war_plan_2001.** The U.S. Nuclear War Plan: A Time for Change (2001). Publisher: Natural Resources Defense Council. URL: https://www.nrdc.org/sites/default/files/us-nuclear-war-plan-report.pdf. Licence or terms: No licence statement checked in the extracted text; figures only are reproduced. Retrieved 2026-11-01. sha256 of report.pdf: fe4ede1eb13cc6e9d6f0669a29198f666e6f2ce520d67e2d7b4f5649b40ab9f9. Used for: US alert shares by level (Table 3.1); reliability (Table 5.3). Not obtained: The CBO 1986 and CRS 1991 sources it cites for reliability were not opened.

**unidir_alert_2012.** Reducing Alert Rates of Nuclear Weapons (Kristensen and McKinzie, 2012). Publisher: United Nations Institute for Disarmament Research. URL: https://unidir.org/wp-content/uploads/2023/05/reducing-alert-rates-of-nuclear-weapons-en-307.pdf. Licence or terms: Copyright (c) United Nations, 2012. All rights reserved. Figures and short quotes only. Retrieved 2026-11-01. sha256 of report.pdf: 5182d4bd94ea1ebf49f6de050149635eff9d21377c5e8481a7b1e52748c3165e. Used for: Alert counts and shares by state and delivery. Not obtained: Data are from 2012; no newer openly available split by state was found.

**ucs_hair_trigger_faq.** Frequently Asked Questions about Taking Nuclear Weapons off Hair-Trigger Alert. Publisher: Union of Concerned Scientists. URL: https://www.ucs.org/sites/default/files/attach/2015/01/Hair-Trigger%20FAQ.pdf. Licence or terms: (c) January 2015 Union of Concerned Scientists. Retrieved 2026-11-01. sha256 of faq.pdf: a7d286ac3b14289c7d9e4cc1457e1eb3a0fe30695109a3ef46d7309afb3488d8. Used for: Cross-check on alert counts. Nothing further was needed from it.

**sgs_hobson_1991.** The ICBM Basing Question (Hobson, Science & Global Security 2, 1991). Publisher: Science & Global Security. URL: https://scienceandglobalsecurity.org/archive/sgs02hobson.pdf. Licence or terms: (c) 1991 Gordon and Breach; "Photocopying permitted by license only". Scalar with citation only. Retrieved 2026-11-01. sha256 of paper.pdf: 971c8799d3872e09537035d9e2654de722d62d5bb41533550a5b56cb55c7eac1. Used for: Reliability assumption. Nothing further was needed from it.

**frus_1952_54v02p1_d66.** FRUS 1952-1954, vol. II part 1, document 66: Report of the Special Evaluation Subcommittee of the NSC, 18 May 1953. Publisher: US Department of State, Office of the Historian. URL: https://history.state.gov/historicaldocuments/frus1952-54v02p1/d66. Licence or terms: US government record; no licence statement in the extracted text. Treated as public domain, which you may want to confirm. Retrieved 2026-11-01. sha256 of page.html: 151999485c7e0a51fea9b598da7947ef866aa08b171c508da2dd168aca5fe405. Used for: 1953-55 bomber aborts, operational losses, duds, attrition by defences. Not obtained: It covers Soviet bombers attacking the US, not SAC bombers attacking the USSR.

**airforcemag_early_war_plans.** The Early War Plans (1 December 2012). Publisher: Air & Space Forces Magazine. URL: https://www.airandspaceforces.com/article/1212war/. Licence or terms: No licence located in the extracted page. Short quote only. Retrieved 2026-11-01. sha256 of page.html: 3d6ff30d8494723be1fbc6ed06bb12234bbf1fa655ddee218aa4a59314a27c3e. Used for: 1946 plan attrition upper value. Not obtained: It is a secondary account; the 1946 plan itself was not opened.

**csis_gmd.** Ground-based Midcourse Defense (GMD) System, last updated 17 September 2026. Publisher: Center for Strategic and International Studies, Missile Threat. URL: https://missilethreat.csis.org/system/gmd/. Licence or terms: (c) 2026 CSIS. All rights reserved. Count and short quote only. Retrieved 2026-11-01. sha256 of page.html: 184ed2ed25cd10735dd45cf85f995046f32d146e3c9acecb7104e4b1e72c0f9d. Used for: GMD interceptor count. Nothing further was needed from it.

**cacnp_bmd_factsheet.** Fact sheet: U.S. Ballistic Missile Defense, updated 21 May 2025. Publisher: Center for Arms Control and Non-Proliferation. URL: https://armscontrolcenter.org/fact-sheet-u-s-ballistic-missile-defense/. Licence or terms: (c) 2026 Center for Arms Control and Non-Proliferation. Retrieved 2026-11-01. sha256 of page.html: b242187a81aabefd72e93dad0dd478e09f40fa30c3a4ea68412021ce42d78db6. Used for: GMD count cross-check. Nothing further was needed from it.

**wiki_a135.** A-135 anti-ballistic missile system. Publisher: Wikipedia. URL: https://en.wikipedia.org/wiki/A-135_anti-ballistic_missile_system. Licence or terms: CC BY-SA 4.0, as stated on the page. Retrieved 2026-11-01. sha256 of page.html: 5163ec595371fc83553669e2ab5073db9fe9f9189722cd51600fb74ca2cef710. Used for: A-135 interceptor count, weak. Not obtained: A primary or think-tank count was not obtained. The GlobalSecurity page could not be reached and the CSIS Russian system page was not tried.

**acp_toon_2007.** Atmospheric effects and societal consequences of regional scale nuclear conflicts (Toon et al., ACP 7, 2007). Publisher: Copernicus / Atmospheric Chemistry and Physics. URL: https://acp.copernicus.org/articles/7/1973/2007/acp-7-1973-2007.pdf. Licence or terms: "Under a Creative Commons License", as printed on the first page. Retrieved 2026-11-01. sha256 of toon.pdf: fc2506b8b4b6b984f1ae0c5288056bd4be34ff51d43264b73ab9900a348efbdc. Used for: Searched for a reliability figure; none used. Not obtained: No delivery reliability is stated.

**sgs_plan_a.** PLAN A. Publisher: Princeton Science & Global Security. URL: https://sgs.princeton.edu/the-lab/plan. Licence or terms: Copyright (c) The Trustees of Princeton University. Retrieved 2026-11-01. sha256 of page.html: 1c177d39892cde13b32e1529c318b776ac11907c4e3c19da78db6e139aa88f7e. Used for: Searched for a reliability figure; none used. Not obtained: No figure on this page or on the Simulating Nuclear War page (sgs_simulating). No separate Glaser et al. 2020 paper was located.

## Opened but not used for any figure, kept for provenance

**sipri_wnf_2026_pr.** SIPRI French press release of 8 June 2026; its table agrees with Table 8A.1. Retrieved 2026-11-01. sha256 of WNF_2026_PR_FRE.pdf: f435095ea570510332ac5f8a49e20236b06a9d65e5a21cf726cb329edf47e1ff.

**sipri_press_2026_en.** SIPRI English press release page; the totals agree. Retrieved 2026-11-01. sha256 of page.html: 2bb27812252ae95b3c889dd128610c7c07ef12245c3b5e8ec6a81fbdab748ea1.

**sipri_yb2026_summary.** SIPRI Yearbook 2026 English summary, (c) SIPRI 2026; totals agree. Retrieved 2026-11-01. sha256 of summary.pdf: 14f57dbf83cb3c56f8a1e7964b8495f872cbb98e4a0fbe44d80dfc72bdc05cf0.

**sipri_yb2026_page.** SIPRI Yearbook 2026 chapter page; no figures used. Retrieved 2026-11-01. sha256 of page.html: 3f1aad6fb9cd085300a7ddf20f5692e4fbcef26406d247990c025fffd5e3bdd5.

**owid_indicator_meta.** OWID indicator metadata, source of the CC BY 4.0 statement. Retrieved 2026-11-01. sha256 of meta.json: af4290f230a78951ee6f85daa7941986645f809f1276956bb61af67fad4a5657.

**crs_if12672_russia.** CRS In Focus IF12672 via EveryCRSReport, updated 27 May 2026; repeats the FAS figure of 1,796 deployed, no row taken. Retrieved 2026-11-01. sha256 of page.html: 8c913527de3081229d170399096ca5b01984256917c322ab2e533e3781ac49f6.

**fas_reducealert_2012.** FAS post on the UNIDIR report; repeats its 1,800 total. Retrieved 2026-11-01. sha256 of page.html: ad85bca4cb8bfd2d6a1ed9d360ec2b7924cee5fbe906d4ba43c9e1f906c5beef.

**cacnp_stockpile_history.** CACNP stockpile history fact sheet, which cites Norris and Kristensen 2010 but carries its figures only in charts, so nothing was used. Retrieved 2026-11-01. sha256 of page.html: 619f28ecdf5526bd779dd0c0a6ff4ec16c143497d52ee7c629259adc82b7af33.

**unidir_alert_2012_landing.** UNIDIR landing page, source of the PDF link. Retrieved 2026-11-01. sha256 of page.html: cb81bc3699c7de647b03d5dd4a841eac1449e54511e2b0ca344f8c391a64d0fc.

**sgs_simulating.** Princeton Simulating Nuclear War page; no reliability figure. Retrieved 2026-11-01. sha256 of page.html: a81323d4fd2c997d91f75969f12bb82cca2f25bca42e63ef6764eef44cf56451.

**wiki_us_war_plans.** Wikipedia, United States war plans 1945-1950; no attrition figure used. Retrieved 2026-11-01. sha256 of page.html: 1bdbe123ffc40af2be8cfb99bb96f371d09d14b0f78a321e4e10eaf4b5aa075f.

**restricteddata_1956.** Restricted Data post on the 1956 plan; no figure used. Retrieved 2026-11-01. sha256 of page.html: 9d54bedc7e1cd8e243e6ee18b140c747f5995c400562b31ce636ad5a082f487c.

**nsa_ebb197.** National Security Archive EBB 197; no figure used. Retrieved 2026-11-01. sha256 of page.html: d8a323d072ab32ee126a23ced7ffd52894ca57e35d580ef257c6697fc4f7ba1c.

**nas_future_policy_ch.** National Academies, Future of U.S. Nuclear Weapons Policy, chapter; no figure used. Retrieved 2026-11-01. sha256 of page.html: b7523e57885c14b0c0a107c86fc201376f3c3255c0f3e1d0f81a304d1bb310c0.

**crs_rl33640.** CRS RL33640, 2006 version hosted by bits.de; no figure used. Retrieved 2026-11-01. sha256 of rl33640.pdf: cefb2a454f0cd9b606987f55d6dfb5cfc016465e7c943860c679639947e72ac0.

**sipri_yb2001_6a.** SIPRI Yearbook 2001 appendix 6A; no figure used. Retrieved 2026-11-01. sha256 of yb.pdf: 0f423ddf3b32c03913792e72ed78860c5f3e8493e9182663cd51799ab131e983.

**fas_us_notebook_2025.** FAS release on the US 2025 Notebook; no delivery split in the release. Retrieved 2026-11-01. sha256 of page.html: 4c0f0becf6de8cebafdfdf2bac864016e708c5ac2146d957ef81619f3cbd4d46.

**russianforces_defense.** Russian Strategic Nuclear Forces blog, 2015 interceptor test; no count given. Retrieved 2026-11-01. sha256 of page.html: f4edd500a7a7a06197d4f5fbc64b77ea215ddbd3cf7b005fc237aaba611f9737.
