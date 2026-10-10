# towns_frg_1961: West Germany (FRG incl. West Berlin), census of 6 June 1961

**File:** `towns_frg_1961.csv` (356 rows; UTF-8)
**Threshold:** 10,000 inhabitants or more at the Volkszählung of 6 June 1961.
**Coverage: incomplete.** The official count is about 583 Gemeinden of 10,000 or more (VZ 1961, Vorbericht 3, per its catalogue description). This table has 356, which is about 60%. Read the gaps below before using it as a complete list.

## Sources

The official tables could not be reached from this environment:
- Statistisches Bundesamt, *Fachserie A, Reihe 1, IV: Bevölkerung der Gemeinden mit 10 000 und mehr Einwohnern* (1962 issue; it has 6.6.1961 figures for 606 Gemeinden). It is at statistischebibliothek.de, which was in a redirect loop / down throughout.
- *VZ 1961 Vorbericht 3* (583 Gemeinden ≥10,000), same host, same failure.
- *Statistisches Jahrbuch für die BRD 1962/1963*. The Mannheim scans at digi.bib.uni-mannheim.de were blocked by the egress proxy. The GDZ copy is not yet online. The archive.org copies (1966+) are lending-only.
- A second search was also unsuccessful:
  - GDZ Göttingen lists the FRG Jahrbuch (PPN514402644, volumes 1955–1980) as "in digitisation, not yet online". Its METS/IIIF/PDF endpoints return HTTP 500, and its catalogue search finds no 1961 census volume.
  - DigiZeitschriften was discontinued on 31.12.2025.
  - archive.org has only the 1966–1974 Jahrbücher, all lending-restricted, and no 1961 census volumes.
- These attempts are logged in `data/raw/frg/urls.log`.

**What was used:** a faithful-tabulation fallback, the de.wikipedia articles' population tables ("Einwohnerentwicklung"). These mostly cite the official census results (rows "6. Juni 1961", usually with a census footnote).
- Raw wikitext was fetched for ~28,000 articles: every member of `Kategorie:Gemeinde in <Land>` and `Kategorie:Ehemalige Gemeinde in <Land>` for the 9 western territorial Länder, plus the `Einwohnerentwicklung von …` pages. The URL pattern is `https://de.wikipedia.org/w/index.php?title=<T>&action=raw`, and the title list is in `data/raw/frg/jobs.json`.
- The 1961 row was parsed automatically (scripts in `data/raw/frg/scripts/`, candidates in `data/raw/frg/cands.csv`). The wikitext of every article used is saved in `data/raw/frg/wikipedia_de/`.
- `source_page` is the article URL for each row.
- West Berlin is from the article "West-Berlin" (6.6.1961: 2,197,408).

## What the table covers / conventions

- One row per Gemeinde as it existed on 6.6.1961. This includes 28 then-independent municipalities later merged, such as Wanne-Eickel, Rheydt, Walsum, Neheim-Hüsten, Villingen, Schwenningen, Ebingen and Dudweiler. For those, `name_today` = "<today's town> (part of)" and the merger year is in `notes`.
- `admin1` = Land. West Berlin is `Berlin (West)`; its occupation status is noted in its row.
- `capital` = 1 for Bonn (provisional federal capital).
- `admin1_seat` = 1 for the 11 Land capitals (Berlin (West), Hamburg, Bremen, Kiel, Hannover, Düsseldorf, Wiesbaden, Mainz, Stuttgart, München, Saarbrücken).

## Boundary basis (main doubt)

Many Wikipedia tables give 1961 figures recomputed on *today's* territory, after the 1965–78 Gebietsreformen. Rows were handled as follows:
- **Dropped:** values the article labels as "heutiger Gebietsstand".
- **Dropped:** municipalities created after 1961 by merger, about 60 of them (e.g. Filderstadt, Ostfildern, Moormerland, Willich, Rheda-Wiedenbrück).
- **Kept, then-boundaries confirmed:** where the article says "jeweiliger/damaliger Gebietsstand", the note says so.
- **109 rows (2.04 M people) carry `BASIS_UNVERIFIED`.** The table does not state its basis, and the article mentions incorporations after 1961, so the figure may be on today's territory. This is common for Bavarian and Lower-Saxon towns, whose tables come from the Land offices' current-territory series. Treat these rows with caution; some may be below 10,000 on 1961 boundaries.
- Rows whose label is just "1961" are taken as the census figure, and the note says so. A few figures were parsed from prose, horizontal tables or timeline charts, and the note says which.

## Checks

- **Present:** the capital (Bonn 143,850), all Land capitals, and the largest cities. Examples: Berlin (West) 2,197,408; Hamburg 1,832,346; München 1,085,014; Köln 809,247; Essen 726,550.
- **Count:** 356 against about 583 official. By Land: NRW 106, BW 89, BY 59, NI 47, HE 18, RP 16, SH 12, SL 5, HB 2, HH 1, B(W) 1.
- **Sum of rows:** 27.0 M. The FRG total at the census was about 56.2 M (recalled figure; no official total could be downloaded). So this table holds about 48% of the population. The full set of ≥10,000 Gemeinden would hold roughly 30 M or more, so the missing rows are mostly towns of 10–50 k plus some larger ones.
- **Known missing (no 1961 census figure in their de.wikipedia article):**
  - **Larger towns:** Solingen, Leverkusen, Hanau, Gladbeck, Lüneburg, Fulda, Landshut, Kempten, Rosenheim, Rüsselsheim, Schweinfurt, Gütersloh, Düren, Bergisch Gladbach, Pirmasens, Neunkirchen (Saar), Völklingen, Speyer, Frankenthal, Landau, Zweibrücken, Neustadt a.d.W., Amberg, Weiden, Coburg, Ansbach, Schwabach, Cuxhaven, Stade, Soest, Kleve, Lörrach, Saarlouis, St. Ingbert, Bad Kreuznach, Bad Homburg.
  - **Merged municipalities:** Opladen, Porz, Bad Godesberg, Beuel and others.
  - **Lands:** Hessen, Rheinland-Pfalz, Schleswig-Holstein and especially Saarland are under-covered.
- No figure was taken from another year. Towns without a 6.6.1961 value were left out.

**To complete:** re-download Fachserie A/1/IV 1962 or VZ 1961 Vorbericht 3 from statistischebibliothek.de when it is back. Then replace or verify every row, especially those marked `BASIS_UNVERIFIED`.
