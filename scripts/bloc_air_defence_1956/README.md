# How `bloc_air_defence_1956.csv` was made

These scripts are the record of how `data/curated/features/bloc_air_defence_1956.csv` was made. No result
depends on running them, and the table cannot be rebuilt from this repository alone:

- The saved pages they read are not committed. They are from Michael Holm's ww2.dk order of battle,
  and his site states no open licence. `fetch.py` saves them again into `$PVO_WORK/html/site/` (default
  `/tmp/pvo_fetch`, see `paths.py`), one second apart, and skips any page the host's robots.txt disallows.
- `build2.py` also reads `alias.json`, a name-alias table that was kept in the working directory and not
  committed.
- They have not been run since the table was built. They first ran with fixed paths (`/tmp/pvo_fetch` and
  this repository's path on the build machine); those paths now come from `paths.py`, `fetch.py` now asks
  robots.txt before each page, and nothing else in them was changed. Three scripts that only printed pages for reading (`an1.py`, `show.py`, `show_pvo.py`)
  were removed; they are in the git history.
- The two hand points in `hand.py` (Ravnets and Dobroslavtsi) hold the centres of their 0.5-degree cells and
  their quoted coordinates are cut, as every row of the table does (`configs/protocol_amendment_20.yaml`).
- The folder is excluded from ruff (`extend-exclude` in `pyproject.toml`), and neither the Makefile
  nor the tests run it.

Data flow: `links.py` lists unit pages, `fetch.py` saves them, `parse.py` turns them into `units.json`, `cand.py`
writes `cand.json`, `build.py` writes `step1.json`, and `build2.py` reads `step1.json` and the hand rows of
`hand.py` and writes the table. `parents.py` and `chain.py` print checks of the unit hierarchy; `dates.py` and
`gn.py` (GeoNames lookup) are helpers; `text.py` prints a saved page as text for reading.

The rerunnable check is the card's page citations. `data/curated/features/bloc_air_defence_1956.md`
gives the selection rules. The `source` column of each row gives the pages used, then the coordinate
source after `coords:`. To check a row, open its cited pages and compare them with its unit, place,
years and `in_june_1956`.
