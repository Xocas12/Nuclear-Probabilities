# Open issues and pull requests: what was done

The issues and PRs stay open on GitHub; this branch carries the fixes. `python -m nucprob.qa`
measures each criterion on the rebuilt tables and writes `runs/qa/issues.csv`; `tests/test_qa.py`
fails if a row does not pass.

| Issue | PR | Taken | Checked by | What changed beyond the PR |
|---|---|---|---|---|
| #1 letter struck for a digit | #2 | yes | `runs/qa/issues.csv` | - |
| #3 towns on same-named hamlets | #12 | yes | 11 towns within 10 km; `test_gazetteer.py` | A scan of every place against its census region found a case the PR did not cover: towns settled by rank alone, with no candidate in the region. Tushino (89,885 people, in Moscow) sat in Kaliningrad oblast. Eight towns of the universe got curated links; the rule `far_namesakes` now leaves such a match unlocated, which it did to one town of the universe (Koltsovo, 13,448) and ten smaller places. Five more were rejected by hand (`rejected_matches.csv`). Every row of the population check is fixed or explained, most by a rule (the place is the only one of its name, or lies in its census region), not row by row. |
| #4 pooled population rule | #13 | yes | `test_model.py`, `runs/m2-check/gains.csv` | Run regenerated; the PLAN note now quotes its figures. |
| #5 airfield verdicts | #15 | yes | `test_sac1956_crossdoc.py`; BRODY read again on the scan (`5005-02511`) | - |
| #6 closed towns' cover names | #20 | yes | `runs/qa/issues.csv`, `test_labels.py` | - |
| #7 rank floor | #14 | yes | `test_rank_floor.py`; country means of `pop_rank_pct` within 0.009 | - |
| #8 transfer read in ROC | #17 | yes | `test_transfer_paired.py` | The rerun changed two readings: PR-AUC on the Polish mirror list now gains, +0.14 [+0.07, +0.21] (`runs/m4-transfer-check/paired.csv`), and ROC-AUC on Square Leg did too until Square Leg was withdrawn with its universe (tenth amendment). The card names the remaining one, and the test fails on any other. |
| #9 NaN read as 0 km | #16 | yes | `runs/qa/issues.csv`, `test_transfer_military.py` | PRs #16 and #17 conflict in effect: the bootstrap sorted a NaN score as a top score. `compare` now skips a model that left towns unscored. |
| #10 district_seat tier | #19 | yes | `runs/qa/issues.csv`, `test_features.py` | - |
| #11 Austrian Land seats | #18 | yes | `runs/qa/issues.csv`, `test_transfer_places.py` | - |

Found while rebuilding, with no issue of their own:
- `NAME_LINK` raised from 88 to 90: the only two links under it were wrong (FALKENBURG to
  Eilenburg, LANY to Slaný).
- The fetcher overwrote a recorded hash on download and stopped at the first dead host. It now
  keeps the record, reports the difference and carries on. `data/sources.yaml` marks live sources
  `volatile` and keeps their earlier hash in `previous_sha256`.
- The sealed set depended on the labels (`data/curated/splits/README.md`).

The independent review of e1ed40e (findings 2-22) is answered in `configs/protocol.yaml`, fourth amendment, and in
`tests/test_label_rules.py`, `tests/test_classifier_report.py`, `tests/test_provenance.py` and `tests/test_probmap.py`.

Added after the independent review:
- `nucprob/sources/robots.py` makes the fetcher refuse what robots.txt disallows, and `runs/qa/robots.csv` records the answer
  for every source. Files already fetched from disallowed paths are named in `README.md` and stay until the owner decides.
- `runs/classifier/extended.csv` holds the economic and political readings fixed by `configs/protocol_amendment_5.yaml`, and
  `runs/probmap/by_delivery.csv` holds warheads by state and delivery for every scenario.

The independent review of 59a35e6 (findings 1-33) is answered by `configs/protocol_amendment_6.yaml`, the rerun it describes,
`tests/test_committed_outputs.py`, the end-to-end map tests in `tests/test_probmap.py`, and `data/curated/features/cited_pages.csv`.
One is not answered: finding 4, files fetched against robots.txt. That needs the owner (README, "Robots").

Found while answering it, with no finding of its own: SAC's ULAAN BAATAR is printed with the suffix CHINA, so it stayed unlinked and
the Mongolian capital read as a negative. `data/curated/sac1956/same_place_links.csv`. Wakamatsu of 1940 sat on a hamlet like Kokura.

Link audit of 2 November 2026, after that answer (`configs/protocol_amendment_7.yaml`). The 233 unsealed entries of `data/processed/sac1956_link_report.csv`
whose printed name disagrees with their town were read by name, with the 16 unlinked entries whose largest negative town within 60 km holds 40,000 or more. Almost all are a suburb or works beside a
town, which is how the 10 km rule is meant to work. Their coordinates were not checked against the scan. One error: SKURATOVO credited Skuratovskiy at Tula, 70 km away (`data/curated/sac1956/rejected_name_links.csv`).
The other name links over 25 km are in `data/curated/sac1956/far_name_links_reviewed.csv`, three of them not confirmed, and a new one fails `tests/test_label_rules.py`.
Square Leg's Gatwick and "Tay Bridge / Dundee" were wrong too. Large towns that stay negative on SAC, such as Baotou and Huainan, have no unlinked SAC entry within 60 km:
the audit found nothing to link them to, and it cannot show whether the study meant to leave them out.

The independent review of c840f88 (a file held by the owner, not in this repository, findings 1-29) is answered by `configs/protocol_amendment_8.yaml`, the rerun it
describes, `tests/test_holdouts_bite.py`, and the new tests in `tests/test_label_rules.py` and `tests/test_probmap.py`. One is not answered: finding 1, files fetched against robots.txt, which needs the owner. "Review finding" numbers cited here and in tests refer to those review files, which are not in the repository.

The robots finding, answered on 2 November 2026 except for one source. The 37 GeoNames dumps were fetched again from a CC BY 4.0
mirror whose robots.txt allows them, with the recorded hashes; the Demoscope page and the Pałka article are held as Wayback
captures with the recorded hashes (`obtained_from` in `data/sources.yaml`). The Wikipedia fetch scripts and the transcription instructions
now use an allowed path, and the pages of `uk_districts_1981_seats.csv` (since removed from the tree), `frg_1961_wikipedia.csv` and `closed_cities_1956.csv`
are registered through allowed paths in `data/curated/features/cited_pages.csv`. Those three tables, and the use of
`Special:Export` and `/w/api.php`, were not in the earlier audit. The last source, the UK 1981 census district totals from
Nomis's disallowed API path, was withdrawn after the review of 46021d7 with the Great Britain rows built from it, the Square Leg
list they scored and the UK of the 1965 map (`configs/protocol_amendment_10.yaml`; `tests/test_robots.py`). No allowed copy was found.
