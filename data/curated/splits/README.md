# The frozen held-out set of the 1956 bloc

`scripts/freeze_seal.py` wrote these once, on 1 November 2026, and they are not regenerated.

- `scored_before_freeze.csv`: every place the M1 slice (1,294 rows) or the M2 check (2,127 rows)
  scored, read from their outputs at commit `de2e54a`, with its 1956 name, because a corrected
  match changes a place's id.
- `sealed_blocks.csv`: the 300 km blocks (`nucprob/model/splits.py`) that held a place and no place
  the M2 check scored, on the coordinates of 1 November. Coordinates corrected since then put 11 places
  the M2 check had scored inside these blocks. They are not sealed, since a place the M2 check scored
  never is (below), and they stay scored (`tests/test_classifier_report.py` allows exactly those).

`nucprob/dataset.py` reads them. A place is `sealed` if its block is listed and the M2 check did
not score it, and `never_scored` if the M1 slice did not score it either. No label is read.

Before the freeze the sealed blocks were drawn from the labels, so correcting a label could move
a block a check run had read into the sealed set. The M1 slice also drew its blocks before the
other countries existed, so M2 sealed towns M1 had scored: of the 467 sealed places, 194 are such
towns, all in the USSR. Only the 273 `never_scored` places are blind. Issue #3 also names
Meuselwitz, Schmölln and Liaoyang, sealed towns, in describing a geocoding error; they stay in.

## What the freeze missed (twelfth amendment)

`freeze_seal.py` read what earlier runs scored from one commit, `de2e54a`. The M2 check had been
run and committed three times before that, on 8 October (`b094d1d`, `e599d9c`, `e80681b`), on a
place table since rebuilt, and those versions scored places that `de2e54a`'s version did not; the
map of each showed the scores. `scripts/scored_history.py` walks every commit before the sealed
scoring (`6258036`), reads every committed `oof_predictions.csv` and every map under `runs/` that
shows a score, and writes `scored_in_history.csv` (place_id, path, first and last commit), matching
by id or by 1956 name and country as `nucprob/dataset.py` does. It finds 316 of the 467 sealed
places, 123 of them among the 273 `never_scored` ones. So `never_scored` is not blind; the 150
`never_scored` places the scan does not find are, and `configs/protocol_amendment_12.yaml` reads
the committed sealed scores on them (`python -m nucprob.classifier.sealed_reread`). `sealed` and
`never_scored` keep their meanings in the table.
