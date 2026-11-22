# Sources this cloud container cannot reach

These sources are public, but the sites refuse or reset connections from the cloud container
(bot checks, regional blocks, rate limits). Fetch them from an ordinary machine and put the
files where the third column says (`data/raw/` is git-ignored). Then rerun
`make data` (it checks the hashes recorded in `data/sources.yaml`) and the build.

## Needed to rebuild the 1956 universe (the core training data)

Until these two are fetched, `make check` needs `NUCPROB_SKIP_MISSING=1`. That builds a
universe without Uzbekistan and East Germany and records it in
`data/processed/INCOMPLETE_BUILD.txt`.

| What | URL | Save as |
|---|---|---|
| Demoscope, 1959 census by region (Uzbekistan's towns) | https://www.demoscope.ru/weekly/ssp/ussr59_reg2.php | `data/raw/demoscope/ussr59_reg2.html` |
| GDR Statistisches Jahrbuch 1956, p. 41 | https://digi.bib.uni-mannheim.de/fileadmin/statjahrb/514402644_1956/pdf/514402644_0041.pdf | `data/raw/ddr/514402644_0041.pdf` |
| same, p. 42 | https://digi.bib.uni-mannheim.de/fileadmin/statjahrb/514402644_1956/pdf/514402644_0042.pdf | `data/raw/ddr/514402644_0042.pdf` |
| same, p. 43 | https://digi.bib.uni-mannheim.de/fileadmin/statjahrb/514402644_1956/pdf/514402644_0043.pdf | `data/raw/ddr/514402644_0043.pdf` |

## Target lists known but not yet read (labels)

| List | URL | Note |
|---|---|---|
| Norstad memo to Groves, Sep 1945 (66 cities) | http://blog.nuclearsecrecy.com/wp-content/uploads/2012/05/1945-Atomic-Bomb-Production.pdf | `data/notes/early_western.md` |
| AAF map of Soviet and Manchurian urban areas, 1945 (full size, about 66 cities) | https://upload.wikimedia.org/wikipedia/commons/9/95/1945_Russian_and_Manchurian_Strategic_Urban_Areas.jpg | rate-limited (429) |
| French Air Force staff study, 1959 (20 cities) | https://hal.science/hal-03384910/document | anti-bot challenge |
| same, journal version | https://www.tandfonline.com/doi/pdf/10.1080/14682745.2020.1832472 | 403 |
| UK Air Ministry grading 1957; SAC-Bomber Command coordination | https://www.raf.mod.uk/what-we-do/centre-for-air-and-space-power-studies/aspr/apr-vol7-iss1-7-pdf/ | 403 |
| Halperin, RAND RM-4900 (Taiwan Strait 1958), original | https://www.rand.org/content/dam/rand/pubs/research_memoranda/2006/RM4900.pdf | 403; the released text was read |
| Budapest war game against Turkey and Greece, 1975 | https://www.cia.gov/readingroom/docs/1975-06-13.pdf | best lead for Bulgarian/southern targets |
| CIA reading room, war game | https://www.cia.gov/readingroom/docs/1975-08-26.pdf | |
| Wilson Center Digital Archive (Warsaw Pact documents) | https://digitalarchive.wilsoncenter.org/ | 502 from here |
| UMD digital archive documents | https://digitalarchive.umd.edu/document/89847/download, https://digitalarchive.umd.edu/document/92175/download | 403 |
| FAS minimal-deterrence target list (2009) | https://nuke.fas.org/norris/nuc_10042901a.pdf, https://pubs.fas.org/_docs/occasionalpaper7.pdf | bot check |
| Russian TV targets 2019 (CNBC) | https://www.cnbc.com/2019/02/25/after-putins-warning-russian-tv-lists-nuclear-targets-in-us.html | 403 |
| FT 2024 Japan/Korea leak (SCMP) | https://www.scmp.com/week-asia/politics/article/3293037/russias-uncovered-secret-war-plans-target-160-sites-japan-and-south-korea | 403 |
| China key civil-air-defence cities | https://cq.gov.cn/ywdt/jrcq/202306/t20230605_12027007.html, https://rf.hangzhou.gov.cn/art/2022/6/15/art_1588071_58826986.html, http://rfb.xinxiang.gov.cn/lylb/info/16288 | |
| Anything on web.archive.org or apps.dtic.mil | | both refuse connections from here |

## Feature data

| What | URL | Note |
|---|---|---|
| HYDE 3.3 population grids (1940-2020) | https://geo.public.data.uu.nl/vault-hyde/HYDE%203.3%5B1701183392%5D/original/hyde33_c7_base_mrt2023/zip/ (`<year>AD_pop.zip`) | bot check; HYDE 3.2.1 is used instead |
| FRG 1961 census by municipality (Statistisches Jahrbuch 1962/63; Statistische Bibliothek) | https://www.statistischebibliothek.de/ | timed out; the FRG is withheld from the transfer universe |
| democracyData regime codings (Geddes-Wright-Frantz, Kailitz) | https://github.com/xmarquez/democracyData/tree/master/data | .rda files, not yet parsed |

## Archives and print only (not online)

These need an archive visit or a print book, not just a different network:
- Kew: AIR 2/13716-7, DEFE 5/77/208, DEFE 5/78/224 (UK 1957 grading), HO 322/985-1020 (Hard
  Rock);
- War Plan UK (Campbell 1982); the New Statesman, 17 Sep 1982 (Hard Rock bomb plot);
- the Ross & Rosenberg facsimiles (Broiler to Dropshot);
- the JCS records in RG 218 and the MacArthur Memorial (Korea 1950-51 "retardation targets");
- Andersen 2026 (Polish plans against Denmark) and Luňák 2007 (Czechoslovak plans).
