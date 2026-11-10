# Hand rows: every statement quoted or closely paraphrased from the page(s) in source
H(
    "High Command PVO, Balashikha",
    "High Command Air Defence Forces (GK PVO)",
    "Balashikha",
    "Moscow Oblast",
    None,
    1954,
    1998,
    "yes",
    "",
    'Holm: "Activated 5.54 in Balashika, Moscow Oblast, as the Air Defence Forces of the Nation (PVO Strany)"; HQ "Balashika, Moscow Oblast, 1954 - 2.98". Command post location, not a fighter or SAM unit.',
    PV + "pvostrany.htm",
)
H(
    "Moscow Air Defence District HQ",
    "Moscow Air Defence District",
    "Moscow",
    "Moscow Oblast",
    None,
    1948,
    "",
    "yes",
    "",
    'Holm: HQ "Moscow, Moscow Oblast, 1948 - today", Organisation 1955 listed. ru-Wikipedia: district formed by order of 20 August 1954 from the Moscow Air Defence Region; Holm says the district name dates from 1950. The two disagree on the name date, not on June 1956.',
    PV + "mopvo.htm; " + WIKI_MO,
)
H(
    "Baku Air Defence District HQ",
    "Baku Air Defence District",
    "Baku",
    "Azerbaizhan SSR",
    None,
    1945,
    1980,
    "yes",
    "",
    'Holm: "1954 renamed Baku Air Defence District"; HQ "Baku, Azerbaizhan SSR, 1945 - 1980". ru-Wikipedia: formed June 1954 from the Baku Air Defence Region, disbanded 30 May 1980.',
    PV + "bapvo.htm; " + WIKI_BA,
)
H(
    "1st Special Purpose Air Defence Army HQ",
    "1st Red Banner Air Defence Army for Special Use",
    "Balashikha",
    "Moscow Oblast",
    None,
    1953,
    1994,
    "yes",
    "",
    'Holm: "Activated 1.12.53 in Balashikha"; HQ "Balashikha, Moscow Oblast, 1953 - today". ru-Wikipedia: created 24 October 1952, formation complete December 1953, HQ Balashikha; ru district article has the army HQ order of 15 July 1955. All before June 1956.',
    PV + "1apvo.htm; " + WIKI_1A + "; " + WIKI_MO,
)
for k, o, t, sec_, loc in (
    ("1kpvo", "1st Special Air Defence Corps", "Vidnoye", "2nd", ""),
    (
        "6kpvo",
        "6th Special Air Defence Corps",
        "Balashikha",
        "1st",
        " ru-Wikipedia's Moscow district article places the 6th at Chernoye; Holm lists its Radio-Technical Center at Chernoye in 1960.",
    ),
    (
        "10kpvo",
        "10th Special Air Defence Corps",
        "Dolgoprudnyy",
        "3rd",
        " ru-Wikipedia's Moscow district article swaps the 10th and 17th towns; its 1st Army article agrees with Holm.",
    ),
    (
        "17kpvo",
        "17th Special Air Defence Corps",
        "Odintsovo",
        "4th",
        " ru-Wikipedia's Moscow district article swaps the 10th and 17th towns; its 1st Army article agrees with Holm.",
    ),
):
    H(
        o + " HQ",
        o,
        t,
        "Moscow Oblast",
        None,
        1953,
        "",
        "yes",
        "",
        "Holm: activated 1953 in "
        + t
        + " as the Administration "
        + sec_
        + " Sector, renamed in 12.53; subordination to the 1st Army 12.53 - 1.12.94."
        + loc,
        PV + k + ".htm; " + WIKI_1A + ("; " + WIKI_MO if loc else ""),
    )
H(
    "52nd Fighter Air Defence Army HQ",
    "52nd Fighter Air Defence Army",
    "Moscow",
    "Moscow Oblast",
    None,
    1943,
    1960,
    "yes",
    "",
    'Holm: bases "Moscow, Moscow Oblast, 6.43 - 3.60"; "2.52 renamed 52nd Fighter Air Defence Army"; "Disbanded 3.60"; Organisation 1955 listed. Commander Podgornyy 6.54 - 1.58.',
    B + "air%20force/army/52via.htm",
)
for n, t, reg, succ, div in (
    ("56th Fighter Aviation Corps PVO", "Yaroslavl", "Yaroslavl Oblast", "3kpvo", "133iad"),
    ("78th Guards Fighter Aviation Corps PVO", "Bryansk", "Bryansk Oblast", "7kpvo", "15gviad"),
    ("88th Fighter Aviation Corps PVO", "Rzhev", "Tver Oblast", "2kpvo", "129iad"),
):
    H(
        n + " HQ",
        n,
        t,
        reg,
        None,
        "",
        1960,
        "yes",
        "",
        "Town bracketed by two dated statements: Holm's Moscow district Organisation 1955 lists the corps at "
        + t
        + ", and the 1960 successor corps is activated at "
        + t
        + " from it. Holm subordination on the division page runs through 1956.",
        PV
        + "mopvo.htm; "
        + B
        + "air%20force/army/52via.htm; "
        + PV
        + succ
        + ".htm; "
        + B
        + "air%20force/division/iad/"
        + div
        + ".htm",
    )
H(
    "37th Fighter Aviation Corps PVO HQ",
    "37th Fighter Aviation Corps PVO",
    "Morshansk",
    "Tambov Oblast",
    None,
    "",
    "",
    "uncertain",
    "UNCERTAIN: Morshansk is stated only up to Organisation 1955; no later page dates the HQ town, so a move before June 1956 cannot be excluded.",
    'Holm: Organisation 1949, 1950 and 1955 list the corps at Morshansk ("Morsansk" on the district page). Subordinate 103rd division line "37th Fighter Aviation Corps PVO, 1950 - 1960" shows the corps through June 1956.',
    PV
    + "mopvo.htm; "
    + B
    + "air%20force/army/52via.htm; "
    + B
    + "air%20force/division/iad/103iad.htm",
)
H(
    "Odessa Air Defence Corps HQ",
    "Odessa Air Defence Corps (later 21st Air Defence Division)",
    "Odessa",
    "Odessa Oblast",
    None,
    1954,
    1960,
    "yes",
    "",
    'Holm: "Activated 7.54 in Odessa, Odessa Oblast, as the Odessa Air Defence Corps"; "1.3.60 renamed 21st Air Defence Division"; HQ "Odessa, 7.54 - 6.89".',
    PV + "21dpvo.htm",
)
H(
    "Lvov Air Defence Corps HQ",
    "Lvov Air Defence Corps (later 28th Air Defence Corps)",
    "Lvov",
    "Lvov Oblast",
    None,
    1954,
    1960,
    "uncertain",
    "UNCERTAIN: the activation line places the corps in Lvov from 9.54, but the same page's HQ line starts only in 1957.",
    'Holm: "Activated 22.9.54 in Lvov, Lvov Oblast, as the Lvov Air Defence Corps"; "5.60 renamed 28th Air Defence Corps"; HQ "Lvov, Lvov Oblast, 1957 - 1992"; subordination "Carpathian Air Defence Zone, 1954 - 1960".',
    PV + "28kpvo.htm",
)
H(
    "Minsk Air Defence Corps HQ",
    "Minsk Air Defence Corps",
    "Minsk",
    "Minsk Oblast",
    None,
    1954,
    1960,
    "uncertain",
    "UNCERTAIN: the corps is dated 1954 - 1960 by a subordinate division, but its HQ town is taken from its name and from the 2nd Army activated from it in 1960.",
    'Holm: 39th division subordination "Minsk Air Defence Corps, 1954 - 1960"; 2nd Army "Activated 1.7.60 in Minsk, Minsk Oblast, from the Minsk Air Defence Corps".',
    B + "air%20force/division/iad/39iad.htm; " + PV + "2oapvo.htm",
)
H(
    "Leningrad Special Air Defence Army HQ",
    "Leningrad Special Air Defence Army",
    "Leningrad",
    "Leningrad Oblast",
    None,
    1954,
    "",
    "uncertain",
    "UNCERTAIN: the army is dated from 9.54 by a subordinate division, but its HQ town is taken from its name and from the 6th Army activated from it in 2.61.",
    'Holm: 20th division subordination "Leningrad Special Air Defence Army, 9.54 - 4.60"; 6th Army "Activated 2.61 in Leningrad, Leningrad Oblast, from Leningradskaya Special Air Defence Army".',
    B + "air%20force/division/iad/20iadpvo.htm; " + PV + "6oapvo.htm",
)
H(
    "49th Fighter Aviation Corps PVO HQ",
    "49th Fighter Aviation Corps PVO",
    "Perm",
    "Perm Oblast",
    None,
    1953,
    1960,
    "uncertain",
    "UNCERTAIN: the corps is dated through June 1956, but its HQ town comes only from the 1960 successor.",
    'Holm: 86th, 87th and 101st division subordination "49th Fighter Aviation Corps PVO, 4.53 - 4.60"; 20th Corps "Activated 10.4.60 in Perm, Perm Oblast, from the 49th Fighter Aviation Corps PVO".',
    B + "air%20force/division/iad/87iad.htm; " + PV + "20kpvo.htm",
)
H(
    "72nd Guards Fighter Aviation Corps PVO HQ",
    "72nd Guards Fighter Aviation Corps PVO",
    "Krasnovodsk",
    "Ashkhabad Oblast",
    None,
    "",
    1960,
    "uncertain",
    "UNCERTAIN: HQ town comes only from the 1960 successor; the 92nd Guards division page moves to a Turkmenistan Air Defence Corps in 1955 while the 38th and 238th stay under the 72nd until 1960.",
    'Holm: 38th and 238th division subordination runs to 1960; 16th Guards Division "Activated 4.60 in Krasnovodsk, Ashkhabad Oblast, from the 72nd Guards Fighter Aviation Corps".',
    B
    + "air%20force/division/iad/38iad.htm; "
    + B
    + "air%20force/division/iad/238iad.htm; "
    + B
    + "air%20force/division/iad/92gviad.htm; "
    + PV
    + "16gvdpvo.htm",
)
H(
    "Primorskiy Air Defence Corps HQ",
    "Primorskiy Air Defence Corps (later 23rd Air Defence Corps)",
    "Vladivostok",
    "Primorskiy Kray",
    None,
    1956,
    1960,
    "uncertain",
    "UNCERTAIN: activated in 1956, month not given; the HQ town is that of the 1960 successor.",
    'Holm: "Activated 4.60 in Vladivostok, Primorskiy Kray, from the Primorskiy Air Defence Corps (activated 1956)".',
    PV + "23kpvo.htm",
)
# near-date activations, kept as out rows
for k, u, t, reg, y, q in (
    (
        "14dpvo",
        "Tallin Air Defence Division (later 14th)",
        "Tallin",
        "Estonian SSR",
        1957,
        "Activated 30.1.57 in Tallin, Estonian SSR, as the Tallin Air Defence Division.",
    ),
    (
        "1dpvo",
        "Krymskaya Air Defence Division (later 1st)",
        "Sevastopol",
        "Crimean Oblast",
        1957,
        "Activated 1.57 in Sevastopol, Crimean Oblast, as the Krymskaya Air Defence Division.",
    ),
    (
        "3dpvo",
        "Baltiysk Air Defence Division",
        "Baltiysk",
        "Kaliningrad Oblast",
        1957,
        "Activated 1.57 in Baltiysk, Kaliningrad Oblast, as the Baltiysk Air Defence Division.",
    ),
    (
        "21kpvo",
        "Northern Air Defence Corps (later 21st)",
        "Severomorsk",
        "Murmansk Oblast",
        1957,
        "Activated 2.57 in Severomorsk, Murmansk Oblast, as the Northern Air Defence Corps.",
    ),
    (
        "27kpvo",
        "Baltic Air Defence Corps (later 27th)",
        "Riga",
        "Latvian SSR",
        1957,
        "Activated 2.57 in Riga, Latvian SSR, as the Baltic Air Defence Corps.",
    ),
    (
        "4dpvo",
        "Polyarnyy Air Defence Division (later 4th)",
        "Belushya Guba",
        "Novaya Zemlya",
        1957,
        "Activated 1.3.57 in Belushya Guba, Novaya Zemlya, as the Polyarnyy Air Defence Division.",
    ),
    (
        "6dpvo",
        "Kamchatskaya Air Defence Division (later 6th)",
        "Petropavlovsk-Kamchatka",
        "Kamchatskaya Oblast",
        1957,
        "Activated 15.3.57 in Petropavlovsk-Kamchatka, Kamchatskaya Oblast, as the Kamchatskaya Air Defence Division, from the 222nd Fighter Aviation Division PVO.",
    ),
    (
        "8kpvo",
        "Komsomolskaya Air Defence Corps (later 8th)",
        "Komsomolsk-na-Amure",
        "Khabarovsk Kray",
        1957,
        "Activated 4.60 in Komsomolsk-na-Amure, Khabarovsk Kray, from the Komsomolskaya Air Defence Corps (activated 1957).",
    ),
):
    H(
        u + " HQ",
        u,
        t,
        reg,
        None,
        y,
        "",
        "no",
        "OUT: activated after the study date.",
        'Holm: "' + q + '"',
        PV + k + ".htm",
    )
H(
    "S-25 Berkut system, Moscow area",
    "S-25 system under the 1st Air Defence Army for Special Use",
    "Moscow",
    "Moscow Oblast",
    None,
    1955,
    1988,
    "yes",
    "",
    "Area row, point is Moscow and not a site. en-Wikipedia: deployed in rings around Moscow from 1955, combat ready June 1956, 24 inner and 32 outer sites, construction through 1958. ru-Wikipedia: accepted into service 7 May 1955; second-echelon regiments began combat duty July 1956. Holm: last S-25 withdrawn 4.88.",
    WIKI_S25 + "; " + WIKI_1A + "; " + WIKI_MO + "; " + PV + "1apvo.htm",
    role="sam_system",
)
H(
    "Budaörs radar regiment",
    "45th independent Radio-Technical Regiment",
    "Budaörs",
    "Hungary",
    None,
    1954,
    1960,
    "yes",
    "",
    'Holm: "Activated 7.10.54 in Budaörs, Hungary, as the 45th independent Radio-Technical Regiment"; base "Budaörs, Hungary, 7.10.54 - 30.11.60". Hungarian unit; no pages found for other satellite radar units in June 1956.',
    B + "wp/Hungary/45rtp.htm",
    cc="Hungary",
    role="radar",
)
for k, u, t, hc, y, q in (
    (
        "15iap",
        "15th Fighter Aviation Regiment (Bulgaria)",
        "Ravnets",
        [42.75, 27.25],
        1952,
        "Ravnets, Bulgaria, 8.52 - 1992",
    ),
    (
        "18iap",
        "18th Fighter Aviation Regiment (Bulgaria)",
        "Dobroslavtsi",
        [42.75, 23.25],
        1952,
        "Dobroslavtsi, Bulgaria, 20.4.52 - 1992",
    ),
):
    H(
        t + " airfield",
        u,
        t,
        "Bulgaria",
        hc,
        y,
        1992,
        "uncertain",
        'UNCERTAIN: Holm lists the regiment under the Bulgarian "Air Defence" heading, but dates an air-defence subordination only from 1968 or not at all.',
        'Holm base line: "' + q + '". Index page heading "Air Defence".',
        B + "wp/Bulgaria/" + k + ".htm; " + B + "wp/Bulgaria/bulaf.htm",
        cc="Bulgaria",
        role="pvo_fighter_base",
    )
