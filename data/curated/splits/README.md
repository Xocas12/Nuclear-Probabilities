# The frozen held-out set of the 1956 bloc

`scripts/freeze_seal.py` wrote these once, on 1 November 2026, and they are not regenerated.

- `scored_before_freeze.csv`: every place the M1 slice (1,294 rows) or the M2 check (2,127 rows)
  scored, read from their outputs at commit `de2e54a`, with its 1956 name, because a corrected
  match changes a place's id.
- `sealed_blocks.csv`: the 300 km blocks (`nucprob/model/splits.py`) that hold a place today and
  held no place the M2 check scored.

`nucprob/dataset.py` reads them. A place is `sealed` if its block is listed and the M2 check did
not score it, and `never_scored` if the M1 slice did not score it either. No label is read.

Before the freeze the sealed blocks were drawn from the labels, so correcting a label could move
a block a check run had read into the sealed set. The M1 slice also drew its blocks before the
other countries existed, so M2 sealed towns M1 had scored: of the 467 sealed places, 194 are such
towns, all in the USSR. Only the 273 `never_scored` places are blind. Issue #3 also names
Meuselwitz, Schmölln and Liaoyang, sealed towns, in describing a geocoding error; they stay in.
