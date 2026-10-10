# Adjudicating disputed lines of the 1956 SAC target list (excerpt sections)

You settle lines of a declassified 1956 US Strategic Air Command target list (public domain;
National Security Archive) on which two independent transcriptions disagree, or that a rule
flags. Every character matters.

Your prompt gives you a **batch file** (JSON list) and a **decisions file** to write.

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push anything.
- Each batch item has `id`, `page`, the two readings (`kind_a`/`text_a`, `kind_b`/`text_b`),
  `reasons` (why it is disputed) and `crop`: a PNG path relative to
  `data/interim/sac1956_excerpts/`. The crop shows the disputed line enlarged, with one line of
  context above and below; a **red bar** in the left margin marks the disputed line.
- Read the crops with the Read tool, 3–4 per turn (parallel calls). Look at the crop, not at
  the readings, first; then decide. You may enlarge part of a crop further
  (`convert <crop> -crop WxH+X+Y -resize 200% /tmp/zoom_$$.png`) when it settles a character.
- Use only what is printed. Never use knowledge of real places or coordinates to choose a
  digit. Alphabetical order and ascending number order within a list may support a reading
  but never override what the glyphs show. If a character stays unreadable, write `?`.
- Write `<decisions file>`: tab-separated, no header, one row per item, 6 columns:
  `id`, `kind` (data / header / footer / blank), `text` (the line exactly as printed, one space
  between visually separate groups, every hyphen, slash and E/W kept; for two printed lines
  under one label, `a || b`), `choice` (`A` if text_a was right, `B` if text_b was right,
  `new` if neither), `confidence` (high / low), `note` (what settled it, one short phrase).
- Line formats, for orientation: complex header `629 5135 MORSHANSK 5328-04149`; aim point
  `5326- 4148E B`; installation `364 0166-0221`; airfield row (pages F)
  `62 0270 ARKHANGELSK/OSTROV KEG 0092-8004 6432-04028 U`; cross-reference row (pages X)
  `0123 ALEKSEYEVKA AF SEE 3440 KHARKOV`, indented `BELBEK AF`. Often confused: 3/5/8, 6/0/9,
  1/7, B/8, S/5, O/0, I/1, E/F.
- Before finishing, check every item has a row. Final message under 100 words: rows written,
  how many A / B / new, number of `?`.
