# nuclear-probabilities

What made a place a nuclear target? Every place in a targeted country is described as it stood
when a plan was drawn up, labelled from declassified strike plans (starting with the US
Strategic Air Command's 1956 target study), and modelled to see which characteristics drive
targeting. The full design is in [PLAN.md](PLAN.md).

## Where things stand

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
- **Milestone M2, the 1956 feature base.** The whole bloc: 2,600 towns of 10,000+ near 1956
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
make test lint
```

`make check` writes `data/processed/` (git-ignored) and `runs/m2-check/`, including
`map.html`, a self-contained page of the results. A few sources are fetched on demand by their
modules (terrain tiles) or were transcribed by hand from scans (`data/curated/`).
