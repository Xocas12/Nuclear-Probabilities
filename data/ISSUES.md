# Open issues and pull requests: where each stands

The issues and PRs stay open on GitHub; this branch carries the fixes. `python -m nucprob.qa`
measures each criterion on the rebuilt tables and writes `runs/qa/issues.csv`; `tests/test_qa.py`
fails if a row does not pass.

| Issue | PR | Taken | Checked by | What changed beyond the PR |
|---|---|---|---|---|
| #1 letter struck for a digit | #2 | yes | `runs/qa/issues.csv` | - |
| #3 towns on same-named hamlets | #12 | yes | 11 towns within 10 km; `test_gazetteer.py` | A scan of every place against its census region found a case the PR did not cover: towns settled by rank alone, with no candidate in the region. Tushino (89,885 people, in Moscow) sat in Kaliningrad oblast. Eight towns of the universe got curated links; the rule `far_namesakes` now leaves such a match unlocated, which it did to one town of the universe (Koltsovo, 13,448) and ten smaller places. Five more were rejected by hand (`rejected_matches.csv`). Every row of the population check is fixed or explained, most by a rule (the place is the only one of its name, or lies in its census region), not row by row. |
| #4 pooled population rule | #13 | yes | `test_model.py`, `runs/m2-check/gains.csv` | Run regenerated; the PLAN note (section 6) quotes its figures: the country term closes 0.54 of the gap for `has_dgz` and 0.68 for `listed`. |
| #5 airfield verdicts | #15 | yes | `test_sac1956_crossdoc.py`; BRODY read again on the scan (`5005-02511`) | - |
| #6 closed towns' cover names | #20 | yes | `runs/qa/issues.csv`, `test_labels.py` | - |
| #7 rank floor | #14 | yes | `test_rank_floor.py`; country means of `pop_rank_pct` within 0.009 | - |
| #8 transfer read in ROC | #17 | yes | `test_transfer_paired.py` | The rerun changed two readings: PR-AUC on the Polish mirror list now gains, +0.14 [+0.07, +0.21] (`runs/m4-transfer-check/paired.csv`), and ROC-AUC on Square Leg did too until Square Leg was withdrawn with its universe (see "Robots.txt" below). The transfer card (`data/curated/gazetteer/TRANSFER.md`) names the one gain that remains, PR-AUC on the Polish mirror list, and `test_transfer_paired.py` fails on any other. |
| #9 NaN read as 0 km | #16 | yes | `runs/qa/issues.csv`, `test_transfer_military.py` | PRs #16 and #17 conflict in effect: the bootstrap sorted a NaN score as a top score. `compare` now skips a model that left towns unscored. |
| #10 district_seat tier | #19 | yes | `runs/qa/issues.csv`, `test_features.py` | - |
| #11 Austrian Land seats | #18 | yes | `runs/qa/issues.csv`, `test_transfer_places.py` | - |

Corrections with no issue of their own:
- `NAME_LINK` was raised from 88 to 90: the only two links under it were wrong (FALKENBURG to
  Eilenburg, LANY to Slaný).
- The fetcher keeps a recorded hash when a download differs, reports the difference and carries on
  past a dead host. `data/sources.yaml` marks live sources `volatile` and keeps their earlier hash in
  `previous_sha256`.
- The sealed blocks were drawn from the labels, so a label correction could move a block into the sealed set;
  they were frozen on 1 November 2026 and are no longer redrawn (`data/curated/splits/README.md`).
- SAC prints ULAAN BAATAR with the suffix CHINA; it is linked to the Mongolian capital by
  `data/curated/sac1956/same_place_links.csv`. Wakamatsu of 1940 is placed on its town, not on a hamlet.

## Name links

The 233 unsealed SAC entries whose printed name differs from the town they credit were read by name
(`data/processed/sac1956_link_report.csv`, built by `make labels`), with the 16 unlinked entries whose largest
negative town within 60 km holds 40,000 or more. Almost all are a suburb or works beside a town, which the 10 km
rule is meant to credit to that town. Their coordinates were not checked against the scan. One link was wrong:
SKURATOVO credited Skuratovskiy at Tula, 70 km away (`data/curated/sac1956/rejected_name_links.csv`). The other
name links over 25 km are in `data/curated/sac1956/far_name_links_reviewed.csv`, three of them not confirmed;
`tests/test_label_rules.py` fails on any new one. Large towns that stay negative on SAC, such as Baotou and Huainan,
have no unlinked SAC entry within 60 km, so nothing links them, and it cannot be shown whether the study meant to
leave them out.

## Robots.txt

`nucprob/sources/robots.py` makes the fetcher refuse what robots.txt disallows, and `runs/qa/robots.csv` records
the answer for every source, judged on the URL the held bytes came from. No held file came from a disallowed path:
- The 37 GeoNames dumps are held from a CC BY 4.0 mirror whose robots.txt allows them, with the recorded hashes.
- The Demoscope page and the Pałka article are held as Wayback captures with the recorded hashes (`obtained_from`
  in `data/sources.yaml`).
- Wikipedia pages are read through allowed paths, and the pages behind `frg_1961_wikipedia.csv` and
  `closed_cities_1956.csv` are registered that way in `data/curated/features/cited_pages.csv`.
- Great Britain's 1981 census district totals were available only through a disallowed Nomis path. They were
  withdrawn with the Great Britain rows built from them, the Square Leg list those rows scored and the United Kingdom
  of the 1965 map (`tests/test_robots.py`). No allowed copy was found.
