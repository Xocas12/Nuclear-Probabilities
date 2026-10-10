# Building a town table for a country and census year

You build the place universe of one country at one census date for a historical research
dataset (where nuclear war plans put their targets). Your prompt names the country, the
census and the output file. Working directory: `/home/user/nuclear-probabilities`. Do not
commit or push.

## What to produce

`data/curated/gazetteer/<file>.csv`, UTF-8, one row per town (municipality, city, urban area
as the source counts it) with **10,000 or more inhabitants at that census** (if the best source
you can reach only lists a higher threshold, use it and say so). Columns:

| column | content |
|---|---|
| `name` | the name as printed in the source |
| `name_today` | today's name, if different (else empty) |
| `admin1` | the first-order unit (Land, province, county, prefecture...) it lay in at that date |
| `pop` | population at the census, persons (integer) |
| `pop_date` | census date (YYYY-MM-DD, or YYYY) |
| `capital` | 1 for the national capital, else 0 |
| `admin1_seat` | 1 if the town was the seat of its first-order unit at that date, else 0 |
| `source` | short citation of the table (publication, table number) |
| `source_page` | page or table reference where the row appears |
| `notes` | boundary basis (municipality as of that date, or today's), merged or renamed towns, doubts |

## Rules

- **Census figures from that date only**, from an official statistical publication (a yearbook,
  a census volume) or a faithful tabulation of it (e.g. a Wikipedia table that cites the census,
  or citypopulation.de where it states the census date). Prefer the original publication. Never
  fill a missing figure from another year or by interpolation; leave the town out and say so.
- Record every URL you download, and save the raw files under `data/raw/<country>/`. Use curl
  (Wikipedia: https://en.wikipedia.org/w/api.php?action=parse&page=...&prop=wikitext&format=json
  or the same on de./da./nl./fr./it./ja. wikipedia). Many statistics offices block scripts;
  try them, then fall back to good tabulations.
- **Do not use any nuclear target list, war plan, civil-defence target list or analysis of where
  bombs would fall** (Square Leg, Hard Rock, Operation Alert, NAPB-90, the Warsaw Pact plans,
  the Target Committee papers...). This table describes places, independent of any targeting.
- Municipal boundaries change; the census figure belongs to the municipality as it then was.
  Note big mergers (e.g. German or Danish municipal reforms) in `notes` where a figure covers a
  unit unlike today's.
- Check: the national capital and the largest cities are present; the count of towns is
  plausible for the country (state it); the sum of your rows is a plausible share of the national
  urban population (state the national total if the source gives it).

## Also write

`data/curated/gazetteer/<file stem>.md`: a short card: source(s) with URLs, what the table
covers, threshold, count of towns, checks done, doubts.

Final message (under 150 words): rows, source, threshold, doubts.
