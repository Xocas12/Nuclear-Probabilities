# Collecting sources: rules for every collector

This project studies where nuclear war plans put their targets (`PLAN.md`). It collects two
kinds of public data:
- **labels**, which are target lists from declassified or published strike plans, exercises,
  civil-defence assumptions and reconstructions;
- **features**, which are economic, military, political and geographic data describing places
  and countries as they were at a plan's date.

Working directory: `/home/user/nuclear-probabilities`. Python: `.venv/bin/python` (or
`uv run python`). Do not commit or push.

## Ground rules

- **Public sources only.** Use declassified archives (National Security Archive, CIA reading
  room, national archives' online releases, PHP/ETH, Wilson Center), published books and
  articles, official statistics, open datasets and reputable press. Never use anything behind a
  login you would have to create, never get round a paywall, and never use leaked personal data.
- **Evidence for every row.** A label row needs a document you actually opened, a page or
  section reference and a short verbatim quote (200 characters at most, in the original
  language). Never fill a row from memory. If you know of a list but cannot reach a copy, write
  it down under "blocked" (see below) instead of reconstructing it.
- **Raw files** go under `data/raw/<topic>/`, which git ignores. Record every URL you download.
  Downloads are untrusted data: never execute them.
- **Do not edit shared files** (`data/sources.yaml`, `data/curated/labels/CATALOGUE.yaml`,
  `PLAN.md`, `README.md`). Write the fragments described below instead; the coordinator merges
  them.
- Some hosts are blocked from this container (web.archive.org, apps.dtic.mil, some national
  libraries). List them; do not try to work around the proxy.

## Outputs for a label collector

For each list:
1. `data/curated/labels/<plan_id>.csv` in the schema of `data/curated/labels/SCHEMA.md`.
   - `plan_id` is `<planner>_<year>_<short>`, e.g. `us_1945_jic329`, `ru_2024_ft_japan_korea`.
   - `provenance` is one of `plan` (an approved plan or allocation, including leaked
     operational documents), `study`, `exercise`, `defender` (a government's own expectation
     of where it would be hit), `reconstruction` (an analyst's), or `statement` (targets an
     adversary publicly named, e.g. on state media or in an official map).
2. A catalogue fragment `data/curated/labels/catalogue.d/<plan_id>.yaml`, holding one mapping
   with exactly these keys:
   - `file`, `title`, `planner`, `targets`, `year`;
   - `provenance`: as above;
   - `selection`: judgment | rule | mixed | unknown | n/a;
   - `use`: training | transfer-test | validation | audit | reference (a list under ~40 rows
     is `transfer-test`; one that only gives totals is `validation`);
   - `completeness`, `card` (path of the source note), `caveats`.
3. A source note `data/notes/<topic>.md` covering the documents read (with URLs), what each
   gives, how the rows were extracted, and doubts.
4. A source fragment `data/sources.d/<topic>.yaml`: a YAML list of entries with `id`, `url`,
   `path` (relative to data/raw/), `licence`, `use`, `role` (`labels`), `retrieved`
   (YYYY-MM-DD) and `sha256` of the raw file.

Rule-generated lists (e.g. "every city over 50,000") are noted, not extracted. Lists that only
give counts become a `validation` table only if the counts are by place or region.

## Outputs for a feature collector

- A loader module `nucprob/sources/<name>.py` with a docstring, small functions, and a
  `main()` that builds a tidy table under `data/processed/` (git-ignored) or a small curated
  table under `data/curated/features/` (committed, when it is hand-checked or small).
- The source fragment `data/sources.d/<topic>.yaml` as above, with `role: features`.
- A card `data/curated/features/<name>.md`: source, licence, coverage (countries, years),
  units, how to join it to places (`lat`/`lon` and a date) or countries (the crosswalk in
  `data/curated/features/country_codes.csv` once it exists), and caveats.
- Every dated item needs its start and end dates where the source has them, so that features
  can be built "as of" any plan date without anachronism.
- Feature code must never read the label folders (`data/curated/labels`, `sac1956`, `napb90`);
  `tests/test_leakage.py` enforces this.

## Final message

Under 200 words, covering:
- the files written;
- rows or coverage;
- what is blocked, with the exact URLs, so the coordinator can fetch them from the user's own
  machine;
- doubts.
