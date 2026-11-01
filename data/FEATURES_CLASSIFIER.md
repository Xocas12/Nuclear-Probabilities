# Features of the classifier (configs/protocol.yaml)

`nucprob/classifier/table.py` builds one row per town and document, in
`data/processed/classifier_table.parquet`. The families and their columns are in
`nucprob/classifier/fit.py` (`FAMILIES`).

| Family | Columns | Source | As of the document |
|---|---|---|---|
| population, administration, geography, industry, transport | the 20 `COMMON` columns of `nucprob/transfer/features.py` | census town tables, GeoNames, Natural Earth, Copernicus DEM, WRI, OurAirports (`data/FEATURES.md`) | census at or before the document. Power plants by commissioning year. Western European towns take plants as of the document's own year |
| military | `log_km_to_naval_base`, `log_km_to_lra_base`, `log_km_to_nuclear_site` | curated site tables (`data/curated/features/`) | Sites in being in the document's year, for Western European towns; June 1956 for the bloc. NaN where no table covers the town (Japan, the US, Canada, Italy south of the Po) |
| defence | `log_km_to_sam`, `log_km_to_air_defence`, `log_air_defence_sites_50km` | the same tables' Nike, HAWK, radar and RAF defence rows; `bloc_air_defence_1956.csv`, with its S-25 positions, for the bloc | as above. NaN for a country with no row in its table |
| national power | `nmc_log_cinc`, `nmc_log_milex`, `nmc_log_milper`, `nmc_log_irst`, `nmc_log_pec`, `nmc_log_tpop`, `nmc_log_upop` | COW National Material Capabilities v7.0 (`cow_nmc_v7`) | The target state's last year at or before the document |

Limits that bear on any reading:

- **Anachronism.** The COMMON set carries the flags of `data/FEATURES.md`: railways, ports and
  airfields are today's data standing in for the document's date. Protocol: results are to be
  repeated without them. That repeat is in `runs/classifier/no_anachronisms.csv`, with all eight
  flagged columns removed: three airfield counts, two railway columns, ports, `log_power_mw_25km`
  and `log_km_to_nuclear_site`. PR-AUC falls by 0.008 to 0.019 for the US and global scopes, all
  intervals excluding zero. For the pooled Warsaw Pact exercises it rises for the logistic model,
  +0.037 [+0.014, +0.058], and does not move detectably for LightGBM, +0.002 [-0.024, +0.021].
- **The annual COW figure** for the document's year covers months after the document.
- **Military expenditure** in COW is in thousands of current US dollars, so it is not comparable
  across decades. The Soviet and Chinese figures are COW's estimates.
- **Defence tables differ in depth.** Western Europe 1965 has one row per Nike or HAWK position.
  The 1956 table has one point per S-25 position and role (protocol, third amendment; the first
  amendment's "one point" no longer holds). 22 positions count as in being in June 1956, all in the
  rings around Moscow and the bloc's only missile sites, so `log_km_to_sam` for a Soviet town is
  still close to its distance from Moscow. The family's readings are therefore made within a region.
  The 1956 reading is repeated without these points, through `log_km_to_air_defence_no_s25`, which
  is not a model feature.
- **Family names.** Airfield counts (`log_airfields_10km`, `_25km`, `_50km`) are in the *transport*
  family in `nucprob/classifier/fit.py`, while the catalogue (`data/FEATURES.md`) and the viewer call
  them *military*. The *industry* family here is the single column `log_power_mw_25km`, today's power
  plants, so a result for "industry" says nothing about factories.
- **Later sites.** No site table runs past its own date. A 1977 document on Western European towns
  sees the sites of 1965: stale, not later knowledge.
