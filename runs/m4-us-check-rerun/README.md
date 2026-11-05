# US 1985 county check, rerun

`make us1985` reruns the side check of `runs/m4-us-check/` (US counties against FEMA's 1987 risk bands; features in
`data/FEATURES_US.md`). It tests that those features join and is no part of the classifier's results. The pinned
record is not overwritten: the rerun is written here, and `comparison.csv` sets each metric beside the pinned one.

21 of the 36 rows have the same PR-AUC and 18 the same value on every metric. The largest PR-AUC difference is 0.002,
all in rows with OurAirports' airfield count, a live list fetched again on 1 November 2026 after the record was made.

The table of US military sites in 1985 that the check reads is not in the tree, since most of those sites are still in
use; the target reads it back from the commit that added it and checks its sha256, so a shallow clone cannot run it.
`scripts/us_military_1985_spec.py` keeps each row's name, 1985 role, unit, town and cited page. It lists features as of
1985, not targets, and ranks nothing.
