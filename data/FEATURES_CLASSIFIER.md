# Features of the classifier (configs/protocol.yaml)

`nucprob/classifier/table.py` builds one row per town and document, in
`data/processed/classifier_table.parquet`. The families and their columns are in
`nucprob/classifier/fit.py` (`FAMILIES`).

| Family | Columns | Source | As of the document |
|---|---|---|---|
| population, administration, geography, industry, transport | the 20 `COMMON` columns of `nucprob/transfer/features.py` | census town tables, GeoNames, Natural Earth, Copernicus DEM, WRI, OurAirports (`data/FEATURES.md`) | census at or before the document. Power plants by commissioning year. Western European towns take plants as of the document's own year |
| military | `log_km_to_naval_base`, `log_km_to_lra_base`, `log_km_to_nuclear_site` | curated site tables (`data/curated/features/`) | Sites in being in the document's year, for Western European towns; June 1956 for the bloc. NaN where no table covers the town (Japan, the US, Canada, Italy south of the Po) |
| defence | `log_km_to_sam`, `log_km_to_air_defence`, `log_air_defence_sites_50km` | the same tables' Nike, HAWK, radar and RAF defence rows; `bloc_air_defence_1956.csv` and the S-25 row for the bloc | as above. NaN for a country with no row in its table |
| national power | `nmc_log_cinc`, `nmc_log_milex`, `nmc_log_milper`, `nmc_log_irst`, `nmc_log_pec`, `nmc_log_tpop`, `nmc_log_upop` | COW National Material Capabilities v7.0 (`cow_nmc_v7`) | The target state's last year at or before the document |

Limits that bear on any reading:

- **Anachronism.** The COMMON set carries the flags of `data/FEATURES.md`: railways, ports and
  airfields are today's data standing in for the document's date. Protocol: results are to be
  repeated without them; that repeat has not been run.
- **The annual COW figure** for the document's year covers months after the document.
- **Military expenditure** in COW is in thousands of current US dollars, so it is not comparable
  across decades. The Soviet and Chinese figures are COW's estimates.
- **Defence tables differ in depth.** Western Europe 1965 has one row per Nike or HAWK position.
  The 1956 table has the S-25 as one point at its headquarters, so `log_km_to_sam` for a Soviet town
  is close to its distance from Moscow. The family's readings are therefore made within a region.
- **Later sites.** No site table runs past its own date. A 1977 document on Western European towns
  sees the sites of 1965: stale, not later knowledge.
