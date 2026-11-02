# Second read of the rows in soviet_search_2026-11b.md, November 2026

Output: 25 rows appended to `data/curated/labels/wp_1977_gsa_lessons.csv` (seq 45 to 69), from Lessons 27a and 24b.
The rule is the one of `second_read_2026-11.md`: a row is dropped if the document states no country and the place
cannot be identified from the name as printed, including names only a translator's bracket makes readable.

## What was read

- Lesson 27a (FIRDB-312/01472-81) pp.8 and 26, as images at 120 dpi. Lesson 24b (FIRDB-312/00726-81) pp.12 and 16, the same.
- The files were downloaded again on 2026-11-02 from archive.org. Their sha256 equal those the first reader recorded.
- Lesson 25a and the Mazowsze booklet were not read as images in this round: neither enters a list, for the reasons below.

## Result, Lesson 27a

20 rows entered of the 21 candidates.

- Dropped: TALBURG /sic -- TILBURG/ as a Pershing area. Only the bracket makes it readable. Tilburg stays positive through its other row on the same page, "in the area of TILBURG".
- Unlinked, direction with no distance, as was done for Burza's "south of Utrecht": WINTERSLAG as "north of WINTERSLAG", THE HAGUE as "east of THE HAGUE", WEERT as "southwest of WEERT".
- WEERT has selected blank. P.26 says "by employing 24 nuclear bombs and conventional means of destruction", which does not say this target gets a nuclear weapon, and p.8 does not name Weert.
- EINDHOVEN, VENLO, ST. TRUIDEN and TIENEN appear in the same p.26 sentence. They keep selected=1 on p.8's list of targets "to be destroyed by nuclear weapons".
- Offsets (18 km NW of EMMEN, 12 km SW of ENSCHEDE, 8 km N of EINDHOVEN) are placed from the town's point at the printed distance, as in `wp_1967_lato67`. The nearest town within the link radius takes the row, which need not be the named town.
- Spellings on the scan agree with the first reader's quotes on every row read.

## Result, Lesson 24b

5 rows entered of the 6 candidates.

- Dropped: BORGER (No. 64). The document states no country, and Börger (FRG) and Borger (Netherlands) both exist, with no airfield known to this reader at either.
- AURICH, VECHTA and AHLHORN carry the yield printed on p.16, 100 kt. P.16 is a student's proposed allocation. P.12 says "28 km east of AURICH" where p.16 says "in the area of AURICH"; the row follows p.16.
- WROHM and BAD MUNDER come from p.12, four warheads shared across the list, so no count per target.

## Not entered

- **Mazowsze 1963, Schemat 3-5 (65 rows).** `SCHEMA.md` asks for a quote from the document for every row. A burst symbol beside a map label has no text, and the booklet's own counts do not fix what its symbols mean (`soviet_search_2026-11b.md`, "Caveats on the Mazowsze maps"). They stay candidates in that note.
- **Mazowsze 1963, text (3 rows).** "w obszarze Szczecina, Gdańska i Warszawy" states the areas where strikes fell mainly. Three positives cannot be scored as a list. A mirror does not train in any case.
- **Lesson 25a, SWINOUJSCIE (1 row).** A mirror inside a lesson, stating a consequence ("have destroyed"), not a target. One row cannot be scored.

## What this does not change

All these lessons belong to one scenario in one document group, `su_gsa_1977`. The rows add towns and a country to one list. They add no independent plan, so the count the state gate reads for the USSR stays where it was in plans and moves only in positives.

## Where the rows land

The link rule, nearest town within 15 km, credits a neighbour where the named place is below the table's floor: Rijkevorsel goes to Turnhout (13.1 km), Zoersel to Herentals (13.2 km), Bad Münder to Springe (6.3 km), the Emmen offset to the nearest town, the Enschede offset to Haaksbergen, the Eindhoven offset to Best. Ahlhorn and Wrohm have no town within 15 km and stay unlinked. Winterslag links to Genk.

## Leads followed up on 2 November 2026

Nothing below adds a row.

- 0001197590 carries the title and date of Lesson 27a, and its OCR has the same list. It is a second copy, not a new document.
- Bariera-73 (5166d4f999326091c6a60865): the OCR is 17,710 bytes with one mention of nuclear strikes and no places. 0000237204 is a 278-byte note on Friendship-82 with none.
- Three further web searches, for East German, Bulgarian and Warsaw Pact target lists, found no document naming targets that could be opened.
- A search snippet for `digitalarchive.umd.edu/document/90470/download` describes a plan for a northern German sector, where the 4th Army is to "destroy the CP of the 1st AK (of the k) with a nuclear weapon". The host answers 403 to the fetch tool and to curl, robots.txt included, so the document was not read and nothing is taken from the snippet. Its issuer and date are unknown.
- `www.cia.gov/readingroom/node/1883385`, titled "SOVIET WAR PLAN" in search results, returned the reading room's home page, as other CIA links did. Not read.
- PHP 19619, 44997 and 21092 stay downloaded and unread; warplans.org's maps of NATO strikes on Hungary were not reached.
