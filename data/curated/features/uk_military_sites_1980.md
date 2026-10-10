## The UK military sites of 1980 (`uk_military_sites_1980.csv`)

- **What it is.** 148 rows: military installations, command centres, nuclear-weapons plants and
  government war headquarters in the United Kingdom as they stood in mid-1980 (study date
  30 June 1980). Each row is one role at one site. A base with two roles has two rows: Marham,
  for example, has a Victor tanker row (in) and a Tornado row (out), and Lossiemouth has three.
  - Columns: `site`, `role`, `unit`, `country` (England, Scotland, Wales, Northern Ireland),
    `town`, `lat`/`lon`, `from_year`/`until_year`, `in_role_1980`, `decision`, `note` and
    `source`.
  - `from_year`/`until_year` are the years of the role at the site, not of the site. A blank
    `until_year` means the role lasted beyond 1991 or continues today, except for the
    government war HQs (see below). A blank `from_year` means the cited articles do not date the
    role's start (ROF Cardiff, Mount Wise, Molesworth).
- **How it was built.** Every row cites English Wikipedia articles, and their URLs are in
  `source`:
  - each station's, base's or establishment's own article;
  - *V bomber*, *Third Air Force*, *Linesman/Mediator*, *UKADGE* (Improved United Kingdom Air
    Defence Ground Environment) and *Atomic Weapons Establishment* for context rows;
  - *Regional seat of government* for the government war HQs.

  The wikitext was saved under `data/raw/uk_military/wikipedia/`, one JSON file per page, with
  the URL it was fetched from (`index.php?action=raw`, following redirects; the API was
  rate-limited). `scripts/uk_military_1980_fetch.py` downloads them.
  `scripts/uk_military_1980_spec.py` holds the rows, years and decisions. Each row also has a
  regex that has to match its article or one of its extra pages; for the rows whose role began
  or ended near 1980 the regex is the dating sentence itself (for example "first arriving in
  November 1980", "staffed radar station in October 1980", "in June 1980, RAF Greenham Common
  was selected"). Every match was read by hand (`-v` prints them). The CSV is rebuilt with
  `.venv/bin/python scripts/uk_military_1980_build.py`.

  No nuclear target list or strike analysis was used: not Square Leg, Hard Rock, the New
  Statesman bomb plots, the target maps in Campbell's *War Plan UK*, or Openshaw and Steadman.
  The CGWHQ article mentions *War Plan UK* only as the source of the nickname "Hawthorn".
- **Coordinates.** Each point is the article's `{{coord}}`, taken from the title or infobox and
  rounded to 3 decimals. There are these exceptions:
  - Four articles fill their title coordinates from Wikidata: HMNB Devonport, HMNB Portsmouth,
    RAF Wethersfield (now *MDP Wethersfield*) and Belfast. Their points come from the rendered
    page, saved in `data/raw/uk_military/html/`, and `source` says so.
  - Mount Wise has no coordinates in its article, so the row uses HMNB Devonport's, about 1 km
    away.
  - Stirling Lines' article point is the regiment's later site at Credenhill, so the row uses
    Hereford's (Bradbury Lines, the 1980 site, was in Hereford).
  - Some articles are about the place, not the site, and the point is the place's: Burghfield
    (village; the ROF lies about 1.5 km away), Llanishen (ROF Cardiff), Ernesettle, Capenhurst
    nuclear site (its own point), and the town or village of 14 government war HQs that have no
    site article. Their notes say so.
  - RAF Benbecula's point is the radar head on North Uist (*RRH Benbecula*), about 20 km from
    the airfield.

### Rows per role (in role at mid-1980 / all)

| role | in 1980 | rows | role | in 1980 | rows |
|---|---|---|---|---|---|
| raf_vbomber (Vulcan) | 2 | 2 | usaf_strike (F-111) | 2 | 2 |
| raf_strike_attack | 4 | 7 | usaf_attack (A-10) | 2 | 2 |
| raf_tanker (Victor) | 1 | 1 | usaf_command_transport (Mildenhall) | 1 | 1 |
| raf_aew (Shackleton) | 1 | 1 | usaf_reconnaissance (Alconbury) | 1 | 1 |
| raf_maritime (Nimrod) | 2 | 2 | usaf_tanker (Fairford) | 1 | 1 |
| raf_reconnaissance (Wyton) | 1 | 1 | usaf_standby (Sculthorpe, Wethersfield) | 2 | 2 |
| raf_air_defence (Phantom, Lightning) | 4 | 4 | usaf_support (Greenham Common) | 1 | 1 |
| raf_sam (Bloodhound) | 3 | 3 | usaf_glcm | 0 | 2 |
| raf_transport | 6 | 6 | usaf_munitions (Welford) | 1 | 1 |
| command_hq | 8 | 8 | us_army_depot | 2 | 2 |
| army_hq | 5 | 5 | ssbn_base (Faslane, Holy Loch) | 2 | 2 |
| early_warning_radar (Fylingdales) | 1 | 1 | nuclear_weapons_store (Coulport) | 1 | 1 |
| air_defence_radar | 8 | 9 | naval_base | 3 | 3 |
| comms_intel | 15 | 15 | naval_shipyard | 4 | 4 |
| nuclear_weapons_establishment | 3 | 3 | naval_air | 4 | 4 |
| nuclear_materials | 4 | 4 | naval_munitions | 4 | 4 |
| army_garrison | 9 | 9 | royal_marines | 3 | 3 |
| army_training_area | 4 | 4 | military_depot | 3 | 3 |
| military_port (Marchwood) | 1 | 1 | government_war_hq | 23 | 23 |

The table has 142 rows in role and 6 out. By country: England 111, Scotland 26, Wales 7,
Northern Ireland 4.

### Decisions (`in_role_1980`)

- **Out:**
  - Lossiemouth's Buccaneers: the first (No. 12 Squadron, from Honington) arrived in November
    1980. Honington's row, which has No. 12 Squadron, is in.
  - Marham's Tornados arrived in 1982-83.
  - Cottesmore's Tri-National Tornado Training Establishment moved in from July 1980 and opened
    on 29 January 1981.
  - RAF Portreath was re-opened as a staffed radar station in October 1980.
  - Greenham Common's 501st Tactical Missile Wing was activated on 1 July 1982. Its support row
    is in: in 1980 the base was a USAF mail sorting and storage site, and it was chosen as a
    cruise missile base in June 1980.
  - Molesworth: its flight line closed in 1973 and the cruise missile facilities were built in
    the early 1980s.
- **In, with a note:**
  - RAF Benbecula: the Linesman article lists it among the northern radars feeding L1, but *RRH
    Benbecula* gives only "built 1980" with no month.
  - Scampton's Vulcans (to 1982), Waddington's (to 1984), Chatham Dockyard (closed 1984), RAF
    Bawtry as HQ No. 1 Group (to 1984) and Barnton Quarry (to the early 1980s) were all still
    in role in mid-1980.
  - The government war HQs are the sub-regional network as it stood after the Civil Defence
    Corps was run down in 1968. The source says it was kept on care and maintenance in the 1970s,
    and that a 1980 review called for it to be recast as Regional Government Headquarters. All
    23 rows are in. Those in the final (late-1980s) network have `until_year` 1992, when the
    network began to be run down. Those not in the final network have a blank `until_year`,
    because the source gives no end date: Bempton, Conisbrough, Basingstoke, Dover Castle,
    Guildford, Ullenwood, Southport, Kirknewton and East Kilbride.

### Uncertainties and gaps

- **Rows whose 1980 role is not fully dated by the cited text:**
  - Dover Castle: the castle's article says the RSG plan there was abandoned, but the network
    list puts it in the 1968 network.
  - RAF Daws Hill: the article dates its nuclear command bunker (for bombers and cruise
    missiles) to the 1980s.
  - RAF Digby: the article does not date the signals role, so 1955 (No. 399 Signals Unit) is
    from general knowledge.
  - Thiepval Barracks: the article names HQ Northern Ireland but does not date its move to
    Lisburn; the cited fact is 39 Infantry Brigade from 1970.
  - Kirknewton (East Zone): the RAF Kirknewton article does not mention the bunker; only the
    RSG article does.
  - RAF Aldergrove: the article does not name the 1980 helicopter units (No. 72 Squadron came
    in November 1981).
- **Facts from general knowledge rather than the cited text:**
  - the Molesworth wing's number (303rd TMW);
  - several unit lists: Waddington's and Scampton's squadrons in 1980, Leuchars' and
    Coningsby's Phantom squadrons, Binbrook's Lightning squadrons, Kinloss's Nimrod squadrons,
    Lyneham's Hercules squadrons, Alconbury's 527th Aggressor Squadron and Prestwick's role
    with the Clyde submarines;
  - a few founding years (Brize Norton's transport role, Benson's Queen's Flight, Pitreavie,
    Boulmer, Saxa Vord, GCHQ Scarborough).

  Units are the main ones in 1980, not a full order of battle.
- **Not covered:**
  - RAF Germany and the overseas bases (Cyprus, Gibraltar, Belize, Hong Kong);
  - training stations (Valley, Cranwell, Finningley, Linton-on-Ouse) and maintenance units
    (St Athan, Abingdon, Kemble);
  - Royal Observer Corps group HQs and UKWMO sector controls;
  - Rapier squadrons, TA centres and most barracks;
  - the US Navy communication station at Thurso (no Wikipedia article was found);
  - AWRE Foulness (no cited article mentions AWRE there);
  - civil ports used for reinforcement (only Marchwood, the Army's own port, is in);
  - Pindar and the Whitehall citadels beyond the MoD Main Building.
- **Anachronism.** Sites are curated from present-day articles and dated to 1980. Several
  titles are today's (Remote Radar Head, MDP Wethersfield, BAE Systems Submarines for the
  Vickers yard at Barrow, Atomic Weapons Establishment for AWRE Aldermaston). The `site` column
  uses the 1980 names.
