# How the protocol changed

`configs/protocol.yaml` was committed before any model it names was fitted. Every later change is a dated
amendment: four inside that file (`amendments:`), and the fifth onwards in their own files. Each amendment's
header says what had been read when it was written. This page gives one line each; the files are the record,
and the git log the order. Reviews are named by the commit they read. They were outside reviews held by the owner
and are not in this repository, so they cannot be checked here: what each one found that led to a change is stated
in the `reasons` field of that amendment, and the commit it read can be checked out. The amendment files and the
comments of `configs/protocol.yaml` and `data/curated/labels/` are left as committed, since the runs pin their
sha256.

| Amendment | Date | What it changed | What had been read before it |
|---|---|---|---|
| 1 (protocol.yaml) | 2026-11-01 | Defences and military sites as features; the FRG's towns; scopes; selection on spatial blocks; sealed set waits for review | The transfer and M2 checks |
| 2 (protocol.yaml) | 2026-11-01 | Gate counts sealed positives too; comparisons on every holdout and on lists other than SAC | A 3-bag code check |
| 3 (protocol.yaml) | 2026-11-01 | Two lesson and exercise lists added; defence table repeated without S-25 points | The 3-bag check |
| 4 (protocol.yaml) | 2026-11-01 | After the review of e1ed40e: rejected rows are negatives, sector boxes, a left-out document's towns leave training, the training floor, block intervals, column-removal repeats | Every holdout of the earlier labels, and the review |
| 5 | 2026-11-01 | Adds economic and political columns as separate readings; changes nothing in the primary analysis | Primary results and national power |
| 6 | 2026-11-01 | Label and link corrections after the review of 59a35e6 | Primary results, the map, the review |
| 7 | 2026-11-02 | Lesson rows from a second read of the scan; three link corrections | All primary results |
| 8 | 2026-11-02 | Corrections after the review of c840f88, including derived sector boxes whose effect that review had shown | All primary results; two uncommitted quick runs on the final table (disclosed in 9) |
| 9 | 2026-11-02 | Discloses the quick runs and that Burza's sector box was drawn with its scores seen; the rule that a block interval needs positives in 5 blocks; no label, model or holdout change | The run pinned at 110174e, the review of 1e98ebc |
| 10 | 2026-11-02 | Withdraws Great Britain's 1981 districts (fetched through a path robots.txt disallows), Square Leg 1980 and the UK of the 1965 map; full refit | The runs pinned at 110174e and de8a502, the review of 46021d7 |
| 11 | 2026-11-03 | Fixes how the sealed set is read, before any sealed score existed | Every result except the sealed set |
| 12 | 2026-11-03 | Restricts the sealed reading to places no committed run had scored (the blind places); refits and rescores nothing | The sealed reading under 11 |
| 13 | 2026-11-03 | Intervals and a split spread for the document identification check, and a stated test of one explanation for its rise; no primary result is read again | document_identification.csv without intervals |
| 14 | 2026-11-03 | Post hoc: tests whether the identification classifier diverged and reads the check again with it regularised | The thirteenth amendment's capacity probe and one fold inspected by hand |
| 15 | 2026-11-03 | Tests the primary fits (every bag of the four models on the whole scope, the first spatial grid, leave-one-document-out and temporal fits) for divergence; changes no result | The fourteenth amendment's finding; no figure of this check |
| 16 | 2026-11-03 | Cites, corrects or drops the 29 West European site rows that rested on general knowledge; full classifier refit on the corrected table; the sealed and blind readings stay those of the earlier fit | The review of c27c1b8; a check of which table cells change, no fit |
| 17 | 2026-11-05 | Places Lato-67's German offset rows, unlinks two Burza rows that print a direction but no distance, and gives reasons for two Lato-67 rows already unlinked; full classifier refit on the corrected links | The in-build review of c39684a, which rescored committed held-out scores with five Lato-67 towns positive; a rebuild of the links, no fit |
| 18 | 2026-11-05 | Repeats the primary comparisons' bootstraps under seeds 1-20 and reports which verdicts depend on the seed; refits nothing | The review of 736fdb5, which reran one comparison's block bootstrap under seeds 1-20 |
| 19 | 2026-11-05 | Withdraws the Dutch 1960 towns (fetched through a path robots.txt disallows) and the Netherlands of the 1965 map; holds every site with no recorded end year at its 0.5-degree cell centre; drops two site rows whose only source refuses this project; full refit | Every result at 12a720f and the review of that commit |
| 20 | 2026-11-10 | Holds every row of the site tables at its 0.5-degree cell centre whatever its end year (an end year dates the role, not the facility), and places three hand-checked label links at the resolution their documents print instead of at air bases and an airport; full refit (pending: its outputs are not yet committed) | Every result at 7bbd5b0 and the review of 1bf6e6a |

After the tenth amendment's refit (930a164; its main step run again at a776225 after a quoting fault in
`data/sources.yaml` was fixed) every classifier table had the same content as the run of 110174e, except that
`lists.csv` lost Square Leg's rows.

The word "brief" in the protocol means the owner's instructions for this project, which are not in this
repository.
