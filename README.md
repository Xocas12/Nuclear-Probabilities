# nuclear-probabilities

What made a place a nuclear target, as far as declassified lists can show? And given a stated stockpile,
how likely is it that an area is struck? This is historical analysis on public sources. Towns are described
as they stood at a document's date and labelled from target lists of US and Warsaw Pact documents, 1945-1977.
The largest list, SAC's 1956 study, is a requirements study, not a war plan, and no Soviet war plan has been
declassified. The results are in **[REPORT.md](REPORT.md)**. [PLAN.md](PLAN.md) is the original design.

## What was found

PR-AUC, the area under the precision-recall curve, measures how many of a model's top-ranked towns are on a
list. A list's base rate is what no information scores: 0.48 for SAC, 0.06 for the other lists. Each interval is 95%.

- **Inside SAC's list**, under spatial cross-validation, the selected model beats population plus a country term by
  +0.02 [+0.01, +0.03]. Without features that use data from after the document it is +0.01 [0.00, +0.02], and its interval
  reaches zero.
- **On a plan the model has not seen**, the richer model against ranking towns by population is -0.13 [-0.15, -0.11]
  over all lists. On a left-out plan nothing beats population.
- **No state gets its own model.** The US has 1,296 linked positives, but only 7 outside one document and the
  pre-committed gate asks for 15. Counting them used to reach 25, until rows the documents reject stopped counting.
  The USSR has 0 positives in a plan document, and 33 towns from staff-academy lessons. A pooled Warsaw Pact model is allowed
  and is always labelled exercise-based. Refusals: `runs/classifier/state_gate.csv`.
- **The map.** Because of that transfer result the rule chose population as the score, so the map shows where
  people live in towns, given a number of warheads. Stockpile assumptions drive most of its intervals.
  Modern scenarios are extrapolation: a classifier told their towns from the training towns at ROC-AUC 0.97,
  where 0.5 would mean no shift, and no modern label exists to test them.

Sealed places have not been scored. They are held for after an independent review.

## Layout

- `data/curated/labels/`: target lists, the registry `PLANS.yaml` (attacker, date, type, grade), `SECTORS.yaml`.
- `data/curated/stockpiles/`: cited inventories and assumptions. `data/sources.yaml`: every source's provenance.
- `configs/protocol.yaml`: pre-committed analysis and its dated amendments. `configs/scenarios.yaml`: scenarios.
- `runs/classifier/`, `runs/probmap/`: committed outputs. `REPORT.md` is generated from them.

## Running it

Requires [uv](https://docs.astral.sh/uv/) and GNU make.

```
make setup
make data       # sources of data/sources.yaml into data/raw/; see "Not all rebuildable" below
make places labels features dataset
make transfer evidence qa
make classifier # table, models, repeats, report; about 1.5 hours on 3 cores
make probmap    # about 10 minutes
make viewer     # one self-contained page: runs/probmap/viewer/index.html
make test lint
```

`make viewer` builds from the committed outputs alone. A clean clone's tests run without data; those that need
built tables skip.

**Not all rebuildable.** COW's data is not committed (no licence stated), so rebuilding needs its download. SIPRI's
tables are not redistributed (its terms), so `data/curated/stockpiles/delivery_mix.csv` holds rounded shares only.
`data/curated/features/bloc_air_defence_1956.csv` was made by hand from cited pages
(`scripts/bloc_air_defence_1956/README.md`). `download.geonames.org` has a robots.txt that disallows all paths, and
the GeoNames dumps in `data/raw/geonames/` came from it in earlier work; `make data` would fetch them again.
