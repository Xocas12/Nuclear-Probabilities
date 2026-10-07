# Transcribing the 1956 SAC target list

You are transcribing a declassified 1956 US Strategic Air Command target list (public domain;
National Security Archive) for a historical research dataset. Every character matters.

Your prompt gives you a **chunk file** and a **pass directory**.

## Setup

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push anything.
  Create the pass directory if needed.
- The chunk file lists pages. Each page has strips (PNG files; paths are relative to
  `data/interim/sac1956/`) and, for each strip, the ids of its lines, top to bottom.
- Each strip shows part of one scanned page, enlarged. Every printed line has a red label (e.g.
  `L07`) in the left margin; faint blue rules separate the lines. Only the labelled lines of a
  strip belong to it. The right part of each page is redacted and not shown.
- **Independence.** Other workers transcribe the same pages separately. Open only: this file,
  your chunk file, the strips, `data/interim/sac1956/manifest.json` (for the completeness
  check), and your own pass directory. Do not open or list any other pass directory
  (`passA`, `passB`, `trial*`) or any other transcription (e.g. `data/curated/labels/sac1956_*`).

## Work page by page

1. Read the page's strips with the Read tool. **Read 3–4 strips per turn** (parallel Read calls
   in one message) to save time.
2. For every line id listed for the page, write exactly one row to
   `<pass directory>/<page>.tsv` (e.g. `.../C166.tsv`): tab-separated, 4 columns, no header:
   `id`, `kind`, `text`, `note`. Write each page's file as soon as the page is done.
   - **id**: the line id exactly as listed (e.g. `C166-L07`).
   - **kind**:
     - `data` for a row of the target table;
     - `header` for page furniture above the table (stamps, "TOP SECRET", the column heading
       "DGZ BA", control numbers);
     - `footer` for page furniture below it ("NW#", "DocId", "TOP SECRET - RESTRICTED DATA",
       page numbers);
     - `blank` when the label marks only specks or nothing legible.
   - **text**: the printed characters exactly as printed, left to right, with ONE space between
     visually separate groups (columns or words).
     - Keep every hyphen, slash, period and comma, and the E/W letters.
     - Write `?` for each character you cannot read with confidence.
     - Never correct, expand or normalise anything.
     - Never use knowledge of real places or coordinates to guess a digit. If it is not
       legible, write `?`.
     - Leave text empty for blank rows.
   - **note**: normally empty. Otherwise one of:
     - `merged`: one label covers two printed lines. Put both in text, separated by ` || `.
     - `cut`: the line is partly outside the strip.
     - `unsure`: you made a judgment call on a character.
     - a short remark.
3. If a printed table line has **no label**, add a row with id = the label above it plus `+`
   (e.g. `C166-L07+`), kind `data`, note `unlabelled`.
4. After writing a page, re-read your TSV once against the strips.
5. If a character is genuinely ambiguous, you may enlarge part of a strip and Read the result,
   e.g. `convert data/interim/sac1956/strips/C166_s2.png -crop 900x120+170+300 -resize 200% /tmp/zoom_$$.png`.
   Do this only when it can settle the character; otherwise write `?`.
6. If you lose track (for example after a long run), run the completeness check below and carry
   on with the pages that are not complete.

## What rows look like

These are for orientation only; always transcribe what is printed.

- **Complex header**: priority, reference number, name (with a country suffix outside the
  USSR, e.g. CZECH or POL), reference coordinates: `629 5135 MORSHANSK 5328-04149`
- **Aim point (DGZ) line**: coordinates with a hemisphere letter, then a letter label:
  `5326- 4148E B`
- **Installation line**: category code, Bombing Encyclopedia number (the part after the hyphen
  may be missing): `364 0166-0221`, `227 0166-`
- **Sub-complex header** (indented): a name and coordinates.
- **Airfield row** (pages `A...`): priority, reference, name, BE number, coordinates, letter:
  `62 0270 ARKHANGELSK/OSTROV KEG 0092-8004 6432-04028 U`
- **Often confused**: 3/5/8, 6/0/9, 1/7, B/8, S/5, O/0, I/1, E/F. Look closely.

## Completeness check (run before finishing)

```
.venv/bin/python - <<'PY'
import json, sys
from pathlib import Path
chunk, pass_dir = sys.argv[1], sys.argv[2]
m = json.load(open("data/interim/sac1956/manifest.json"))
for p in json.load(open(chunk))["pages"]:
    want = {l["id"] for l in m[p["page"]]["lines"]}
    f = Path(pass_dir) / f"{p['page']}.tsv"
    have = {r.split("\t")[0].rstrip("+") for r in f.read_text().splitlines() if r.strip()} if f.exists() else set()
    print(p["page"], "OK" if want <= have else f"MISSING {sorted(want - have)}")
PY
```

Run it with your chunk file and pass directory as the two arguments (put them after `-` on
the python command line, e.g. `.venv/bin/python - CHUNK PASSDIR <<'PY'`). Fix any gaps.

## Final message

Your final message is your return value. Keep it under 200 words: one line per page (rows
written, number of `?`, anything unusual such as merged, unlabelled or blank lines, or damage),
then the time taken.
