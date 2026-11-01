# nuclear-probabilities

What made a place a nuclear target? Every place in a targeted country is described as it stood
when a plan was drawn up, labelled from declassified strike plans (starting with the US
Strategic Air Command's 1956 target study), and modelled to see which characteristics drive
targeting. The full design is in [PLAN.md](PLAN.md).

## Where things stand

The classifier is built and its results are in **[REPORT.md](REPORT.md)**. The probability map is not
built, and the sealed held-out set has not been scored.

- **Main result.** Under spatial cross-validation the US model beats population plus a country term,
  +0.02 [+0.01, +0.04] in PR-AUC. It does not carry over: on a left-out document it scores below the
  rule that ranks towns by population, -0.15 [-0.17, -0.13]. Every gain the selected models show is on
  spatial blocks.
- **Evidence (`data/curated/labels/PLANS.yaml`, `runs/evidence/`).** Each list records its attacker,
  author, date, document type and grade. There is no Soviet war plan: the USSR has 64 rows, 63 from
  General Staff Academy lessons on one fictional scenario. Only the US passes the pre-committed gate for
  its own model, and 1289 of its 1314 positives are one study. Every other state is refused, with the
  reason, in `runs/classifier/state_gate.csv`. A pooled Warsaw Pact model is allowed and is always
  labelled exercise-based.
- **Protocol (`configs/protocol.yaml`).** Holdouts, metrics, gate and method were committed before any
  model it names was fitted, with dated amendments.
- **Rebuilt, 1 November 2026.** The fixes of issues #1 and #3-#11 are on this branch
  (`data/ISSUES.md`, `runs/qa/issues.csv`).

### Earlier milestones

- **Labels (milestone M3).** The SAC 1956 study's complex list and airfield list are
  transcribed in full (two independent reads, adjudication, cross-line checks). So are the
  excerpts of its Part I airfield list, Part II complex list and cross-reference list:
  `data/curated/sac1956/`, with a data card.
  - A blind audit of a 5% sample found no errors (95% bound 0.5%).
  - Part II keeps the same complexes as Part I with about a third of the aim points, kept by
    the top-priority complexes (a second label, `part2_has_dgz`).
  - Other target lists, each with a data card and provenance tag: `data/INVENTORY.md`.
- **Milestone M4, more labels (done).** FEMA's NAPB-90 county tables (the US, 1987) are
  transcribed in full: Annex A (blast) and Annex B (fallout), `data/curated/napb90/`. The US
  counties are described as of 1985 (`nucprob/us1985/`, `data/FEATURES_US.md`), with a check
  run in `runs/m4-us-check/`. Smaller lists were added for the Taiwan Strait (1958), China
  (JCS 1963) and Operation Alert (1955). The smaller lists now have place universes from
  1940-1981 censuses (Japan, the US, Canada, Denmark, the Netherlands, Belgium, Austria,
  Italy, the UK), the bloc's features built the same way, and a transfer check
  (`data/curated/gazetteer/TRANSFER.md`, `runs/m4-transfer-check/`).
- **Milestone M1, the vertical slice.** USSR only: 1,635 towns of 10,000+ in 1959 with census
  populations and coordinates, linked to the SAC targets, with population and administrative
  features, and three kinds of model under spatial cross-validation (`runs/m1-slice/`). The
  slice checks the pipeline; its numbers are not results.
- **Milestone M2, the 1956 feature base.** The whole bloc: 2,621 towns of 10,000+ near 1956
  in the USSR, Eastern Europe, China, North Korea, North Vietnam and Mongolia, from 1950s
  censuses and yearbooks (`data/curated/gazetteer/README.md`). Six feature families describe
  each town as of June 1956: population, administration (a 1956 table of regional centres),
  geography and reach (terrain, the sea, capitals, the NATO frontier and SAC's bases on the
  study date), industry (the Soviet defence industry active in 1956), military (airfields,
  curated military sites) and transport. Every feature names its sources and flags later
  knowledge (`data/FEATURES.md`); a guard test keeps the target list out of the features.
  The check run and its map are in `runs/m2-check/`; its numbers check the joins and are not
  results.

## Running it

Requires [uv](https://docs.astral.sh/uv/) and GNU make.

```
make setup      # Python 3.12 environment with every dependency
make data       # download the sources of data/sources.yaml into data/raw/
make check      # places -> labels -> features -> dataset -> check run -> map
make transfer   # the smaller lists: universes, features, links, check run
make evidence qa
make classifier # the pre-committed models and holdouts, about an hour (runs/classifier/)
uv run python -m nucprob.classifier.sensitivity  # the repeat without anachronistic features
uv run python -m nucprob.classifier.report       # REPORT.md and runs/classifier/TABLES.md
make test lint
```

`make check` writes `data/processed/` (git-ignored) and `runs/m2-check/`, including
`map.html`, a self-contained page of the results. A few sources are fetched on demand by their
modules (terrain tiles) or were transcribed by hand from scans (`data/curated/`).
