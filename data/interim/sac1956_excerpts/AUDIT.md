# Audit reading of the 1956 SAC target list

You are re-reading a random sample of lines of a declassified 1956 US Strategic Air Command
target list (public domain; National Security Archive) to measure transcription accuracy.
Every character matters.

Your prompt gives you an **audit file** and an **output file**.

- Working directory: `/home/user/nuclear-probabilities`. Do not commit or push anything.
- The audit file lists pages. For each page: `ids`, the line ids to read, and `strips`, the
  PNG strips (paths relative to `data/interim/sac1956_excerpts/`) that contain them. Each strip
  shows part of a scanned page, enlarged, with a red label (e.g. `L07`) in the left margin for
  every printed line. Read only the listed ids; ignore the other lines of a strip.
- **Independence.** Open only this file, your audit file, the strips and your output file. Do
  not open any transcription: nothing under `data/curated/`, no `pass*`, `compare`,
  `adjudicate` or `audit*` output other than your own, no `lines.csv`.
- Write `<output file>`: tab-separated, columns `id`, `text`, `note`, no header, one row per
  listed id. Text is the printed characters exactly as printed, one space between visually
  separate groups, every hyphen, slash and E/W letter kept, `?` for any character you cannot
  read with confidence. Never correct or guess from knowledge of real places. Note is normally
  empty (`unsure` for a judgment call). Append rows as you go.
- Rows look like: complex header `629 5135 MORSHANSK 5328-04149`; aim point
  `5326- 4148E B`; installation `364 0166-0221` or `227 0166-`; airfield (pages `A`)
  `62 0270 ARKHANGELSK/OSTROV KEG 0092-8004 6432-04028 U`. Often confused: 3/5/8, 6/0/9, 1/7,
  B/8, S/5, O/0, I/1, E/F. You may enlarge part of a strip
  (`convert <strip> -crop WxH+X+Y -resize 200% /tmp/zoom_$$.png`) when it settles a character.
- Read 3-4 strips per turn (parallel Read calls). Before finishing, check that every listed id
  has a row.
- Final message (under 100 words): rows written, number of `?`, time taken.
