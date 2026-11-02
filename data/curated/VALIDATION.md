# Validation tables

Two tables in this folder are checks against other documents, not labels or features. Neither is read by
the classifier or the map.

## `validation_sac1956_nsa_city_sheets.csv`

**Rows:** 175 category counts from the National Security Archive's city sheets of the SAC 1956 study
(Moscow, Leningrad, Beijing, Warsaw), one row per sheet, block and installation category. **Columns:**
`sheet`, `location`, `block` (the name as printed), `category_name`, `category_code`, `count`.
**Made by** `scripts/sac1956_nsa_sheets.py`; `scripts/sac1956_assemble.py` compares the counts with the
transcribed installations. **Source and licence:** National Security Archive Electronic Briefing Book
No. 538 (2015), a US government record in the public domain; see `sac1956/README.md`.

## `validation_siop62.csv`

**Rows:** 8 totals from the history of the Joint Strategic Target Planning Staff's preparation of
SIOP-62 (HQ SAC History & Research Division, n.d., excised; National Security Archive Electronic
Briefing Books 130 and 236): the size of the national target database of August 1960, DGZs of the
completed list (all and USSR), alert and follow-on forces, and execution options. **Columns:** `item`,
`category`, `country`, `count`, `source_doc`, `source_url`, `page`, `quote`; each row quotes its page.
**Provenance, retrieval and hashes:** `data/notes/western.md`, section 8. Only totals are transcribed;
no target or place is named. **Use:** none in any result. It records the scale of the 1960 plan
beside the 1956 study, and figures often cited for SIOP-62 that were not found on the pages read are
listed in the note, not here.
