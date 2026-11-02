# Extracted target lists: shared CSV schema

One CSV per source list: `data/curated/labels/<plan_id>.csv`, UTF-8, header row, one row per
named target (or per candidate, for lists that record rejected candidates too).

| column | meaning |
|---|---|
| plan_id | short slug, e.g. `us_1956_sac_complexes`, `wp_1965_hu_wargame` |
| planner | who drew up / assumed the list, e.g. `US`, `UK`, `France`, `Poland/USSR`, `FEMA (defender)` |
| target_country | country containing the target, as at the plan date (e.g. `USSR`, `FRG`) |
| plan_year | year of the document |
| provenance | a row-level tag: `plan` / `disputed` (sources disagree whether plan or exercise) / `study` / `exercise` / `training` (a staff-academy lesson) / `mirror` (one side's exercise assumption of the other's strikes) / `defender` / `reconstruction`. It is coarser than the document type in `PLANS.yaml`, which governs: in `us_1945_target_committee.csv`, `plan` marks the rows of the committee's selections and the orders that followed, a document the registry types as `target_selection`, not as a war plan |
| seq | row order in the source |
| name_source | spelling exactly as in the source |
| name_modern | modern name, only if certain; else blank |
| target_class | class as stated (city, airfield, port, HQ, ...) or blank |
| selected | 1 = designated target; 0 = explicitly considered and rejected; blank = n/a |
| priority | as stated, else blank |
| weapons | number of weapons as stated, else blank |
| yield_kt | yield in kt as stated, else blank |
| lat, lon | decimal degrees ONLY if the source gives coordinates; else blank (geocoding is a later step) |
| source_doc | citation |
| source_url | URL actually downloaded |
| source_page | page(s) in the PDF/document where the row appears |
| quote | short verbatim excerpt (<= 200 chars, original language) supporting the row |
| notes | anything uncertain |

Rules: no row without a page reference and a quote from a document actually opened.
Rule-generated lists (e.g. "all cities over 50,000") are recorded in notes, not extracted.
