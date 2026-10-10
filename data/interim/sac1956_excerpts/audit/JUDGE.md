# Judging audit disagreements in the 1956 SAC target list

You decide which of two readings of a line of a declassified 1956 US Strategic Air Command
target list (public domain; National Security Archive) matches the scan. Every character
matters.

Your prompt gives you a **batch file** (JSON list) and a **decisions file** to write.

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push anything.
- Open only this file, your batch file, the crops it names and your decisions file. Do not open
  `key.json`, any transcription, `lines.csv`, or anything under `data/curated/`.
- Each item has `id`, two readings `X` and `Y` (in no particular order; neither is privileged)
  and `crop`, a PNG path relative to the working directory: the line enlarged, with a line of
  context above and below and a **red bar** in the left margin marking the line to judge.
- Read the crops with the Read tool, 3–4 per turn (parallel calls). Look at the crop first,
  then compare with X and Y. You may enlarge part of a crop
  (`convert <crop> -crop WxH+X+Y -resize 200% /tmp/zoom_$$.png`) when it settles a character.
- Spacing differences do not matter; characters do (a `?` counts as a character that
  differs). Use only what is printed, never knowledge of real places or coordinates.
- Write `<decisions file>`: tab-separated, no header, one row per item, 5 columns: `id`,
  `verdict` (`X` if X matches the printed line character for character, `Y` if Y does,
  `neither` otherwise), `text` (the line as printed, `?` for a character that stays
  unreadable), `confidence` (high / low), `note` (which characters differ and what settled
  it, one short phrase).
- Formats, for orientation: complex header `629 5135 MORSHANSK 5328-04149`; aim point
  `5326- 4148E B`; installation `364 0166-0221`; airfield row
  `62 0270 ARKHANGELSK/OSTROV KEG 0092-8004 6432-04028 U`. Often confused: 3/5/8, 6/0/9, 1/7,
  B/8, S/5, O/0, I/1, E/F.
- Final message under 100 words: rows written, how many X / Y / neither.
