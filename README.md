# nuclear-probabilities

What made a place a nuclear target? Every place in a targeted country is described as it stood
when a plan was drawn up, labelled from declassified strike plans (starting with the US
Strategic Air Command's 1956 target study), and modelled to see which characteristics drive
targeting. The full design is in [PLAN.md](PLAN.md).

## Where things stand

- **Labels.** The SAC 1956 study's complex list and airfield list are transcribed in full
  (two independent reads, adjudication, cross-line checks): `data/curated/sac1956/`, with a data
  card. 24 other target lists are extracted: `data/INVENTORY.md`.
- **Milestone M1, the vertical slice.** USSR only: 1,635 towns of 10,000+ in 1959 with census
  populations and coordinates, linked to the SAC targets, with population and administrative
  features, and three kinds of model under spatial cross-validation (`runs/m1-slice/`). The
  slice checks the pipeline; its numbers are not results.

## Running it

Requires [uv](https://docs.astral.sh/uv/) and GNU make.

```
make setup      # Python 3.12 environment with every dependency
make data       # download the sources of data/sources.yaml into data/raw/
make slice      # places -> labels -> features -> dataset -> models -> map
make test lint
```

`make slice` writes `data/processed/` (git-ignored) and `runs/m1-slice/`, including
`map.html`, a self-contained page of the results.
