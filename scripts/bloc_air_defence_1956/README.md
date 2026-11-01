# How `bloc_air_defence_1956.csv` was made

These scripts are the record of how `data/curated/features/bloc_air_defence_1956.csv` was made. They
are not a rerunnable step, and the table cannot be rebuilt from this repository:

- Ten of the 15 scripts read or write paths under `/tmp` that no longer exist: `an1.py`, `build.py`,
  `build2.py`, `cand.py`, `chain.py`, `fetch.py`, `links.py`, `parents.py`, `parse.py`, `show_pvo.py`.
- The saved pages they read are not committed. They are from Michael Holm's ww2.dk order of battle,
  and his site states no open licence.
- The folder is excluded from ruff (`extend-exclude` in `pyproject.toml`), and neither the Makefile
  nor the tests run it.

They are kept as they ran, and no result depends on running them.

The rerunnable check is the card's page citations. `data/curated/features/bloc_air_defence_1956.md`
gives the selection rules. The `source` column of each row gives the pages used, then the coordinate
source after `coords:`. To check a row, open its cited pages and compare them with its unit, place,
years and `in_june_1956`.
