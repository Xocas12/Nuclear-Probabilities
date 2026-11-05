import json, re, sys, csv, math, collections, zipfile, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, SITE, work  # noqa: E402
import dates, gn

d = json.load(open(work("units.json")))
s1 = json.load(open(work("step1.json")))
rows = s1["rows"]
B = "https://www.ww2.dk/new/"
PV = B + "pvo/"
WIKI_S25 = "https://en.wikipedia.org/wiki/S-25_Berkut"
WIKI_1A = "https://ru.wikipedia.org/wiki/1-я_армия_ПВО_особого_назначения"
WIKI_MO = "https://ru.wikipedia.org/wiki/Московский_округ_ПВО"
WIKI_BA = "https://ru.wikipedia.org/wiki/Бакинский_округ_ПВО"
COORD = re.compile(r"(\d{1,3}) (\d{1,2}) (\d{1,2})N,\s*(\d{1,3}) (\d{1,2}) (\d{1,2})E?")


def co(t):
    m = COORD.search(t)
    if not m:
        return None
    a = [int(v) for v in m.groups()]
    if a[1] >= 60 or a[2] >= 60 or a[4] >= 60 or a[5] >= 60:
        return None
    return [round(a[0] + a[1] / 60 + a[2] / 3600, 4), round(a[3] + a[4] / 60 + a[5] / 3600, 4)]


def H(site, unit, town, reg, hc, y0, y1, st, dec, note, src, cc="USSR", role="pvo_hq"):
    rows.append(
        dict(
            site=site,
            role=role,
            unit=unit,
            country_1956=cc,
            town=town,
            reg=reg,
            hc=hc,
            y0=y0,
            y1=y1,
            in_june_1956=st,
            decision=dec,
            note=note,
            source=src,
        )
    )


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand.py"), encoding="utf8").read())
# ---- S-25 regiments
s25 = []
for u, x in sorted(d.items()):
    if "/pvo/sam/" not in u:
        continue
    la = [i for s in x["secs"] for i in s["items"] if i.startswith("Launch area")]
    eq = [p for p in x["paras"] if re.search(r"equipped with .*S-25", p)]
    if not la or not eq:
        continue
    act = [p for p in x["paras"] if p.startswith("Activated")][0]
    m = re.match(r"Activated (?:([\d.]+) )?in (.+?), ([A-Z][a-z]+ Oblast)", act)
    date, town, reg = (m[1], m[2], m[3]) if m else (None, None, None)
    eqm = re.match(r"(\d{4}) to (\d{4})", eq[0])
    hc = co(la[0])
    sid = re.search(r"site ([A-Z]\d+-\d)", la[0])
    sid = sid[1] if sid else ""
    outer = sid.startswith("E")
    y0 = ""
    if date:
        k = dates.tok(date)
        y0 = k[0] // 12
    base = (
        'Holm: "'
        + act
        + " "
        + eq[0].rstrip(":")
        + '" Launch area quoted from the page: "'
        + la[0]
        + '".'
    )
    kd = dates.tok(date) if date else None
    if kd and kd[0] > dates.T:
        st = "no"
        dec = "OUT: activated after the study date."
    elif kd and kd[1] >= dates.T:
        st = "uncertain"
        dec = "UNCERTAIN: activation date touches 1956 at year or month precision."
    elif not sid:
        st = "uncertain"
        dec = "UNCERTAIN: no site code on the page, so the ring cannot be read."
    elif not date:
        st = "uncertain"
        dec = "UNCERTAIN: Holm gives no activation date for this regiment; only the equipment line dates it."
    elif outer:
        st = "uncertain"
        dec = "UNCERTAIN: regiment at the site by Holm, but ru-Wikipedia has second-echelon regiments starting combat duty in July 1956 and en-Wikipedia has site construction running to 1958; the E designation is read as the outer ring from Holm's 1284zrp page, and outer ring = second echelon is an inference."
    else:
        st = "yes"
        dec = ""
    note = (
        base
        + " Regiment and position documented; ring assignment read from the site code. Launch-area coordinates carry a US designation on Holm's page, i.e. later intelligence knowledge (see card)."
    )
    rows.append(
        dict(
            site="S-25 position " + town,
            role="sam_system",
            unit=x["paras"][0],
            country_1956="USSR",
            town=town,
            reg=reg,
            hc=hc,
            y0=y0 or (int(eqm[1]) if eqm else ""),
            y1=int(eqm[2]) if eqm else "",
            in_june_1956=st,
            decision=dec,
            note=note,
            source=u
            + "; "
            + WIKI_1A
            + "; "
            + WIKI_S25
            + ("; " + PV + "sam/1284zrp.htm" if outer else ""),
            coord_force="Holm launch area on the cited page",
        )
    )
    s25.append((u, town, sid, st))
json.dump(s25, open(work("s25.json"), "w"), ensure_ascii=False)
# ---- radar
for u, x in sorted(d.items()):
    if "/pvo/radar/" not in u or not re.search(r"\d", u.rsplit("/", 1)[1]):
        continue
    bs = [s for s in x["secs"] if s["head"] and re.match(r"(HQ|Headq|Bases)", s["head"])]
    items = [i for s in bs for i in s["items"]]
    for b in items:
        st, iv = dates.cover(b)
        if st in ("yes", "uncertain"):
            act = [p for p in x["paras"] if p.startswith("Activated")][:1]
            ops = [p for p in x["paras"] if "operational" in p][:1]
            m = dates.IV.search(b)
            head = b[: m.start()].rstrip(" ,")
            parts = [q.strip() for q in head.split(",")]
            k0 = dates.tok(iv[0]) if iv[0] != "?" else None
            k1 = dates.tok(iv[1]) if iv[1] != "?" else None
            dec = (
                ""
                if st == "yes"
                else "UNCERTAIN: base dates touch 1956 at year or month precision."
            )
            ma = (
                re.match(r"^Activated (\d{1,2}\.\d{1,2}\.\d{2,4}|\d{1,2}\.\d{2,4}|\d{4})\b", act[0])
                if act
                else None
            )
            ka = dates.tok(ma[1]) if ma else None
            if ka and ka[0] > dates.T:
                st = "uncertain"
                dec = "UNCERTAIN: Holm's base line starts before June 1956 but the activation line post-dates it; the unit may be a predecessor battalion at the site, or absent."
            hcb = None if "possibly" in b else co(b)
            rows.append(
                dict(
                    site=parts[0] + " radar unit",
                    role="radar",
                    unit=x["paras"][0],
                    country_1956="USSR",
                    town=parts[0],
                    reg=parts[1] if len(parts) > 1 else "",
                    hc=hcb,
                    y0=(k0[0] // 12 if k0 else ""),
                    y1=(k1[0] // 12 if k1 and k1[0] < 10**6 else ""),
                    in_june_1956=st,
                    decision=dec,
                    note='Holm base line: "' + b + '". ' + " ".join(act + ops),
                    source=u,
                    coord_force="Holm point on the cited page" if hcb else None,
                )
            )
# satellites
for u, x in sorted(d.items()):
    if "/wp/" in u and re.search(r"\d", u.rsplit("/", 1)[1]):
        pass
# ---- regiments named in dated Organisation lists of PVO divisions, with no page of their own
pages = {}
for u, x in d.items():
    if "/iap/" in u and x["paras"]:
        m = re.match(r"(\d+)(?:st|nd|rd|th)( Guards)?", x["paras"][0])
        if m:
            pages[(m[1], bool(m[2]))] = u
org_gap = []
seen_div = set()
for r in list(rows):
    if (
        r["role"] != "pvo_hq"
        or r["in_june_1956"] == "no"
        or "/iad/" not in r["source"]
        or r["source"] not in d
        or r["source"] in seen_div
    ):
        continue
    seen_div.add(r["source"])
    x = d[r["source"]]
    regs = {}
    for s_ in x["secs"]:
        m = re.match(r"Organisation (19\d\d)", s_["head"] or "")
        if not m:
            continue
        y = int(m[1])
        for i in s_["items"]:
            mm = re.match(
                r"(\d+)(?:st|nd|rd|th)( Guards)? Fighter Aviation Regiment( PVO)?\s*\(", i
            )
            if not mm:
                continue
            # balanced parenthesis scan
            st_ = mm.end()
            dep = 1
            j = st_
            while j < len(i) and dep:
                dep += {"(": 1, ")": -1}.get(i[j], 0)
                j += 1
            inner = i[st_ : j - 1] if dep == 0 else i[st_:]
            bits = [q.strip() for q in inner.rsplit(",", 1)]
            regs.setdefault((mm[1], bool(mm[2])), []).append(
                (y, bits[0], bits[1] if len(bits) > 1 else "", i, i[: mm.end() - 1].strip())
            )
    for k, v in regs.items():
        if k in pages:
            continue
        pre = [e for e in v if 1950 <= e[0] <= 1956]
        post = [e for e in v if 1956 <= e[0] <= 1960]
        same = [(a, b) for a in pre for b in post if a[1] == b[1]]
        name = v[0][4]
        if same:
            a, b = same[-1]
            if a[0] >= 1952 and b[0] <= 1958:
                st, dec = "yes", ""
            else:
                st, dec = (
                    "uncertain",
                    f"UNCERTAIN: same town in the division's Organisation {a[0]} and {b[0]} lists, but no statement closer to June 1956.",
                )
            q = f'Division page Organisation {a[0]} and {b[0]} both list "{a[3]}".'
            town, reg = a[1], a[2]
        else:
            use = [e for e in v if e[0] in (1955, 1957, 1958)]
            if not use:
                org_gap.append((name, [(e[0], e[1]) for e in v], r["source"]))
                continue
            e = use[-1]
            st = "uncertain"
            dec = f"UNCERTAIN: known only from the division's Organisation {e[0]} list; no own page, no base line covering June 1956."
            q = f'Division page Organisation {e[0]} lists "{e[3]}".'
            town, reg = e[1], e[2]
        rows.append(
            dict(
                site=town + " airfield",
                role="pvo_fighter_base",
                unit=name,
                country_1956="USSR",
                town=town,
                reg=reg,
                hc=None,
                y0="",
                y1="",
                in_june_1956=st,
                decision=dec,
                note="No regiment page on Holm. " + q,
                source=r["source"],
            )
        )
added = {r["unit"] for r in rows if r["note"].startswith("No regiment page")}
org_gap = [g for g in org_gap if g[0] not in added]
json.dump(org_gap, open(work("org_gap.json"), "w"), ensure_ascii=False)
# ---- country
CC = {
    "Germany": "East Germany",
    "East Germany": "East Germany",
    "Poland": "Poland",
    "Hungary": "Hungary",
    "Romania": "Romania",
    "Bulgaria": "Bulgaria",
    "Czechoslovakia": "Czechoslovakia",
    "China": "China",
    "Austria": "Austria",
    "Mongolia": "Mongolia",
    "North Korea": "North Korea",
}
for r in rows:
    if not r["country_1956"]:
        r["country_1956"] = CC.get(r["reg"], "USSR")
    if (
        r["country_1956"]
        in (
            "East Germany",
            "Poland",
            "Romania",
            "China",
            "Austria",
            "Mongolia",
            "North Korea",
            "Czechoslovakia",
        )
        and r["role"] == "pvo_fighter_base"
        and r["in_june_1956"] != "no"
    ):
        print("CHECK", r["unit"], r["town"], r["reg"])


# ---- GeoNames + OurAirports
def hav(a, b, c, e):
    R = 6371
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(e - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


oa = []
for r in csv.DictReader(open(ROOT + "data/raw/ourairports/airports.csv", encoding="utf8")):
    if r["type"] in ("small_airport", "medium_airport", "large_airport", "closed"):
        try:
            oa.append(
                (
                    float(r["latitude_deg"]),
                    float(r["longitude_deg"]),
                    r["ident"],
                    r["name"],
                    r["municipality"] or "",
                    r["iso_country"],
                    r["type"],
                )
            )
        except:
            pass
oa_sov = [
    a
    for a in oa
    if a[5]
    in "RU UA BY KZ LT LV EE GE AZ AM UZ TM TJ KG MD BG HU DE PL RO CZ SK CN KP MN AT".split()
]


def cands(t):
    t = t.strip()
    out = []
    m = re.match(r"(.+?)\s*\((.+?)\)", t)
    if m:
        out += [m[1], m[2]]
    out.append(t)
    b = re.sub(r"\s*\(.*\)", "", t)
    if "-" in b:
        out += b.split("-") + [b.replace("-", " ")]
    return list(dict.fromkeys(x.strip() for x in out if x.strip()))


wanted = set()
ALIAS = json.load(open(work("alias.json"), encoding="utf8"))
for r in rows:
    towns = cands(r["town"])
    for t in towns:
        wanted.add(gn.norm(t))
        if t in ALIAS:
            wanted.add(gn.norm(ALIAS[t]))
GN = gn.load(
    "RU UA BY KZ LT LV EE GE AZ AM UZ TM TJ KG MD BG HU DE PL RO CZ SK CN KP MN AT".split(), wanted
)
print("gn names", len(GN), "wanted", len(wanted))
adm = {}
for l in open(ROOT + "data/raw/geonames/admin1CodesASCII.txt", encoding="utf8"):
    k, n, a, g = l.rstrip("\n").split("\t")
    adm[k] = a
REGALIAS = {
    "Kuybyshev Oblast": "Samara",
    "Gorkiy Oblast": "Nizhny",
    "Kalinin Oblast": "Tver",
    "Stalino Oblast": "Donetsk",
    "Ashkhabad Oblast": "Balkan",
    "Azerbaizhan SSR": "Baki",
    "Leningrad Oblast": "Leningrad",
    "Moscow Oblast": "Moscow",
    "Primorskiy Kray": "Primorye",
    "Khabarovsk Kray": "Khabarovsk",
    "Kamchatskaya Oblast": "Kamchatka",
    "Checheno Ingushskaya ASSR": "Chechnya",
    "Tatarskaya ASSR": "Tatarstan",
    "Adygeyskaya Autonomous Oblast": "Adygeya",
}


def stem(x):
    return re.sub(r"[^a-z]", "", x.lower())[:5]


def gnpick(town, reg, hc):
    best = None
    for t in cands(town):
        for name in (t, ALIAS.get(t)):
            if not name:
                continue
            cs = GN.get(gn.norm(name), [])
            cs = [c for c in cs if c["fc"] in ("P", "A")] or cs
            if hc:
                cs = [c for c in cs if hav(hc[0], hc[1], c["lat"], c["lon"]) <= 40]
            if not cs:
                continue

            # score
            def sc(c):
                a = adm.get(c["cc"] + "." + c["adm1"], "")
                rs = stem(
                    REGALIAS.get(reg, reg)
                    .replace(" Oblast", "")
                    .replace(" Kray", "")
                    .replace(" ASSR", "")
                    .replace(" SSR", "")
                )
                return ((rs and rs in stem(a)) or stem(a)[:4] == rs[:4], c["pop"])

            cs.sort(key=sc, reverse=True)
            top = cs[0]
            if hc:
                return top, "", name
            rs = stem(
                REGALIAS.get(reg, reg)
                .replace(" Oblast", "")
                .replace(" Kray", "")
                .replace(" ASSR", "")
                .replace(" SSR", "")
            )
            a = adm.get(top["cc"] + "." + top["adm1"], "")
            matched = (rs and rs in stem(a)) or stem(a)[:4] == rs[:4]
            spread = max(hav(top["lat"], top["lon"], c["lat"], c["lon"]) for c in cs)
            flag = "" if matched or len(cs) == 1 or spread < 40 or top["pop"] > 100000 else "ambig"
            return top, flag, name
    return None, "", None


stats = collections.Counter()
review = []
anchor = {}
for r in rows:
    if r["hc"] and not r.get("coord_force"):
        anchor.setdefault((r["town"], r["reg"]), r["hc"])
for r in rows:
    hc = r["hc"] or anchor.get((r["town"], r["reg"]))
    if r.get("coord_force"):
        r["lat"], r["lon"] = hc
        r["cs"] = "coords: " + r["coord_force"]
        stats["holm_site"] += 1
        continue
    if r.get("fix"):
        r["lat"], r["lon"], r["cs"] = r["fix"]
        stats["fixed"] += 1
        continue
    done = False
    if r["role"] == "pvo_fighter_base":
        if hc:
            near = sorted(
                (hav(hc[0], hc[1], a[0], a[1]), a)
                for a in oa_sov
                if abs(a[0] - hc[0]) < 0.2 and abs(a[1] - hc[1]) < 0.4
            )
            if near and near[0][0] <= 5:
                km, a = near[0]
                r["lat"], r["lon"] = round(a[0], 4), round(a[1], 4)
                r["cs"] = f"coords: OurAirports {a[2]} ({km:.1f} km from Holm's point)"
                stats["oa_holmcheck"] += 1
                done = True
        if not done and not hc:
            top, flag, name = gnpick(r["town"], r["reg"], hc)
            if top:
                near = sorted(
                    (hav(top["lat"], top["lon"], a[0], a[1]), a)
                    for a in oa_sov
                    if abs(a[0] - top["lat"]) < 0.3 and abs(a[1] - top["lon"]) < 0.5
                )
                st = gn.norm(name)
                near = [
                    n
                    for n in near
                    if n[0] <= 15 and (st in gn.norm(n[1][3]) or st in gn.norm(n[1][4]))
                ]
                if near:
                    km, a = near[0]
                    r["lat"], r["lon"] = round(a[0], 4), round(a[1], 4)
                    r["cs"] = (
                        f"coords: OurAirports {a[2]} (name match via GeoNames {top['gid']}, {km:.1f} km)"
                    )
                    stats["oa_name"] += 1
                    done = True
    if done:
        continue
    top, flag, name = gnpick(r["town"], r["reg"], hc)
    if top:
        r["lat"], r["lon"] = round(top["lat"], 4), round(top["lon"], 4)
        extra = ""
        if hc:
            extra = f", {hav(hc[0], hc[1], top['lat'], top['lon']):.1f} km from Holm's point"
        r["cs"] = f"coords: GeoNames {top['gid']} town {top['name']}{extra}"
        if flag:
            r["cs"] += " (namesake choice not confirmed by region)"
            review.append(
                (
                    r["town"],
                    r["reg"],
                    top["name"],
                    adm.get(top["cc"] + "." + top["adm1"]),
                    top["pop"],
                )
            )
        stats["gn_ambig" if flag else "gn"] += 1
    elif hc:
        r["lat"], r["lon"] = hc
        r["cs"] = "coords: Holm's point on the cited page (no GeoNames or OurAirports match)"
        stats["holm"] += 1
    else:
        r["lat"], r["lon"] = "", ""
        r["cs"] = "coords: none (place not found in GeoNames or OurAirports)"
        stats["none"] += 1
        review.append((r["town"], r["reg"], "NONE", "", 0))
print(stats)
print("REVIEW", review)
# ---- write
OUT = sys.argv[1]
cols = "site,role,unit,country_1956,town,lat,lon,from_year,until_year,in_june_1956,decision,note,source".split(
    ","
)
order = {"pvo_hq": 0, "sam_system": 1, "pvo_fighter_base": 2, "radar": 3}
rows.sort(key=lambda r: (order[r["role"]], r["site"], r["unit"]))
seen = set()
with open(OUT, "w", newline="", encoding="utf8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        k = (r["role"], r["unit"], r["town"], r["y0"], r["y1"])
        if k in seen:
            print("DUP", k)
            continue
        seen.add(k)
        site = r["site"] if r["role"] != "pvo_fighter_base" else r["town"] + " airfield"
        src = r["source"]
        src = src + "; " + r["cs"]
        w.writerow(
            [
                site,
                r["role"],
                r["unit"],
                r["country_1956"],
                r["town"],
                r["lat"],
                r["lon"],
                r["y0"],
                r["y1"],
                r["in_june_1956"],
                r["decision"],
                r["note"],
                src,
            ]
        )
print(collections.Counter((r["role"], r["in_june_1956"]) for r in rows))
