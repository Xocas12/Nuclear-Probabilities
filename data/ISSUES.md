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
| #8 transfer read in ROC | #17 | yes | `test_transfer_paired.py` | The rerun changed two readings: PR-AUC on the Polish mirror list now gains, +0.14 [+0.07, +0.21], and ROC-AUC on Square Leg, +0.05 [+0.01, +0.10]. The card names both, and the test fails on any other. |
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
