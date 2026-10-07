# Adjudicating disputed lines of the 1956 SAC target list

Two independent passes transcribed every printed line of the 1956 SAC study. You are given a
batch of lines where they disagree, where a character was unreadable, or where an agreed reading
breaks a format rule. Decide what is printed. Every character matters.

Your prompt gives you a **batch file**: `data/interim/sac1956/adjudicate/batchNN.json`.

## Setup

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push anything.
- Each item in the batch has:
  - `id`: the line, e.g. `C166-L07`;
  - `text_a`, `text_b`, `kind_a`, `kind_b`: the two readings;
  - `reasons`: why it was flagged;
  - `crop`: an enlarged image of the line, relative to `data/interim/sac1956/`, with one line of
    context above and below. A **red bar on the left edge marks the line to decide**.
- If the crop is not enough, the full strips are in `data/interim/sac1956/strips/` (file names
  start with the page, e.g. `C166_s2.png`). You may enlarge part of an image, for example
  `convert <image> -crop WxH+X+Y -resize 300% /tmp/adj_$$.png`, and Read the result.

## How to decide

1. Read the crop with the Read tool. Read several crops per turn where you can.
2. Write what is printed: left to right, ONE space between visually separate groups, every
   hyphen, slash, period, comma and E/W letter as printed. Use `?` only for a character that is
   still illegible after enlarging.
3. Evidence you may use:
   - the glyph shapes, comparing with clear instances of the same character elsewhere on the
     same page;
   - the format of the line (a coordinate is degrees-minutes, so minutes run 00–59);
   - consistency **within the document**, for example the four-digit chart prefix that the
     installations of one block share, or the alphabetical order of names. Say in the note when
     you relied on it.
4. Evidence you may **not** use: knowledge of real places, real coordinates or spellings from
   outside the document. If the print is ambiguous, write `?`; do not import a "correct" value.
5. If a stray mark (a speck, a dot) is not a printed character, leave it out and say so in the
   note.
6. If one red-barred line actually holds two printed lines, give both, separated by ` || `.
7. If the line is page furniture (stamps, "TOP SECRET", "DocId", footers) set kind `header`
   or `footer`; if it holds nothing legible, `blank`; otherwise `data`.

## Output

Write `data/interim/sac1956/adjudicate/decisions/<batch name>.tsv` (create the folder if needed):
tab-separated, no header, one row per item, columns:

`id`, `kind`, `text`, `choice`, `confidence`, `note`

- **choice**: `A` (text_a was right), `B` (text_b was right), `both` (they agreed and are
  right), or `new` (neither; you wrote a corrected reading).
- **confidence**: `high`, `medium` or `low`.
- **note**: short; what settled it.

Before finishing, check that every id in the batch has exactly one row.

## Final message

Your final message is your return value. Keep it under 150 words: the counts of A / B / both /
new, how many are `low` confidence or keep a `?`, and anything systematic you noticed (for
example a character the passes often confuse).
