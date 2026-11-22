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

## Playing with the data

Every modelling table is one call away, together with an algorithm zoo of 16 classifiers:
- logistic regression (L1/L2) and spline (GAM-like) logistic regression;
- naive Bayes, k-NN, an SVM and an MLP;
- a decision tree, random forest and extra trees;
- histogram gradient boosting, LightGBM, XGBoost, CatBoost and an EBM.

```
uv sync --extra playground                 # xgboost, catboost, shap, interpret, jupyter
uv run python -m nucprob.playground list   # datasets and algorithms
uv run python -m nucprob.playground run -d sac1956 -a all             # spatial-block CV leaderboard
uv run python -m nucprob.playground run -d napb90:very_high -a rf,lgbm -f population,military
uv run python -m nucprob.playground run -d pooled -a lgbm --extras     # + HYDE, Wikidata, country-year
uv run python -m nucprob.playground transfer --train sac1956 --test transfer:cd_1980_square_leg
uv run python -m nucprob.playground explain -d sac1956 -a lgbm         # permutation importance and SHAP
uv run jupyter lab notebooks/playground.ipynb
```

Datasets:
- **`sac1956`**: Soviet bloc towns in 1956, with variants `:has_dgz` and `:part2`.
- **`ussr1959`**: the USSR at the 1959 census.
- **`napb90:very_high`, `:medium_plus` and `:fallout`**: US counties in 1985.
- **`transfer:<list>`**: one dataset per smaller target list, on the towns of its countries at its date.
- **`pooled`**: everything in one table.

Cross-validation uses 300 km spatial blocks by default. `--cv random` shows how optimistic
random folds are, and `--cv country` leaves out one country at a time. The sealed test blocks
are kept out, for the single final scoring.

The data behind it (all public; sources in `data/sources.yaml`, cards next to each table):
- **Target lists** (`data/curated/labels/`, catalogued in `data/INVENTORY.md`). They cover:
  - US plans from 1945 to 1968: the 1945 Target Committee, JIC 329, the 1945
    Army Air Forces city lists, TROJAN, Korea, the Taiwan Strait and Indochina, and the SAC
    1956 study with its 1,200 complexes;
  - Warsaw Pact plans and exercises from 1961 to 1977;
  - defenders' own lists for the US, UK, Canada, Australia and China, from 1955 to 2021;
  - post-1990 leaks and state statements, from 2013 to 2025;
  - analysts' reconstructions (NRDC 2001).
- **Place universes**: census town tables for the bloc 1956, the US 1950 and 1985, Canada,
  Japan, the UK and six West European countries, plus GeoNames towns for the post-1990 lists.
- **Features**:
  - population, administration, geography, industry, military and transport, built "as of"
    each plan's date;
  - HYDE historical population grids, 1930-2017 (`nucprob/sources/hyde.py`);
  - 158,000 dated facilities from Wikidata (`nucprob/sources/wikidata_facilities.py`);
  - a 1940-2025 country-year panel of regime, economy, military capability, alliances and
    nuclear status (`nucprob/sources/country_year.py`).

Some sources refuse connections from cloud machines; `data/BLOCKED.md` lists them, with
`scripts/fetch_blocked.sh` for the four the 1956 universe needs.

## Running it

Requires [uv](https://docs.astral.sh/uv/) and GNU make.

```
make setup      # Python 3.12 environment with every dependency
make data       # download the sources of data/sources.yaml into data/raw/
make check      # places -> labels -> features -> dataset -> check run -> map
uv run python -m nucprob.us1985.places && uv run python -m nucprob.us1985.features && uv run python -m nucprob.us1985.dataset
for s in places features labels check; do uv run python -m nucprob.transfer.$s; done
uv run python -m nucprob.model.levels zoo      # M6: the zoo on every dataset (protocol: configs/protocol.yaml)
uv run python -m nucprob.model.levels levels   # M7: per country and regime, transfer matrix
uv run python -m nucprob.viz.atlas --transfer  # M9: docs/atlas/index.html
make test lint
```

`make check` writes `data/processed/` (git-ignored) and `runs/m2-check/`, including
`map.html`, a self-contained page of the results. A few sources are fetched on demand by their
modules (terrain tiles) or were transcribed by hand from scans (`data/curated/`).
