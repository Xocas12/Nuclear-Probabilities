# Curated feature tables (as of June 1956)

Small hand-built tables that feed the features (`nucprob/features/`). None of them is derived
from a US target list: the leakage guard (`tests/test_leakage.py`) checks that no feature reads
the SAC transcription, and these tables cite independent sources (Wikipedia, base histories,
official administrative histories).

| File | Rows | What it is | Used by |
|---|---|---|---|
| `capitals_1956.csv` | 29 | National capitals of the bloc, the 16 union-republic capitals of June 1956 (the Karelo-Finnish SSR still among them) and Bratislava as Slovakia's seat | `national_capital`, `republic_capital`, `log_km_to_moscow`, `log_km_to_capital` |
| `admin_centres_1956.csv` | ~300 | First-order units and their centres in June 1956: RSFSR krais, oblasts and ASSRs (with the oblasts of 1954–57: Arzamas, Balashov, Velikiye Luki, Kamensk, Grozny), autonomous oblasts and national okrugs; the oblasts of the other republics; Polish voivodeships, East German Bezirke, Czechoslovak kraje, Hungarian counties, Romanian regions, Bulgarian okrugs, Chinese provinces, North Korean provinces | `regional_centre`, `autonomy_centre` |
| `sac_bases_1956.csv` | 15 | SAC's overseas bomber, tanker and forward bases in service in 1956, with their years (the Spanish bases opened in 1957–59 and are excluded) | `log_km_to_sac_base` |

## Conventions

- **Names.** `centre` is the name in use in June 1956 (Сталино, Молотов, Чкалов, Stalinogród,
  Karl-Marx-Stadt, Gottwaldov, Orașul Stalin, Сталин for Varna); `centre_today` is today's,
  so either can find the place in the place table.
- **Dates.** A unit is in the table if it existed in June 1956. The notes give the years of
  units created or abolished near the study date.
- **Coordinates** of capitals are GeoNames' (checked against CShapes 2.0's capital points in
  `tests/test_features.py`; all agree within 4 km).

## Known uncertainties

- Kyrgyzstan: the Talas oblast was abolished in 1956 (ru.wikipedia, "Административно-
  территориальное деление Киргизии"); the month is not checked, so it is kept for June 1956.
  Dzhalal-Abad, Issyk-Kul and Frunze oblasts lasted until 1959.
- North Vietnam's and Mongolia's first-order units are not in the table yet.
- Varna was named Stalin from 1949 to 20 October 1956. pop-stat's note says "Stalin in
  1949-1956", and the name helper treats the end year as exclusive, so the place table gives
  Varna's 1956 name as Варна. The administrative table finds it by either name.

## Sources

- Administrative history of the USSR: the "Административно-территориальное деление" articles
  of each oblast and republic on ru.wikipedia.org; Wikipedia's lists of the oblasts abolished
  in 1957 (Arzamas, Balashov, Velikiye Luki, Kamensk, Grozny oblasts) and of the Karelo-Finnish
  SSR (ended 16 July 1956).
- Bulgaria: the 12 okrugs of 1951–59 and Sofia city (bg.wikipedia, "Административно деление на
  България": the Vidin and Yambol okrugs were merged into others in 1951).
- Eastern Europe: the Wikipedia articles on the administrative divisions of the Polish People's
  Republic (1950–1975), the Bezirke of the GDR (1952–1990), the regions of Czechoslovakia
  (1949–1960), the counties of Hungary (1950 reform), the regions of Romania (1952–1956) and the
  okrugs of Bulgaria (1949–1959).
- China: the provincial-level divisions of 1955–56 (Rehe and Xikang abolished in 1955;
  Xinjiang an autonomous region from October 1955; Henan's capital at Zhengzhou from 1954).
- SAC bases: each base's history (the `basis` column).
