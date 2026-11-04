import json, re, sys, csv, math, collections

sys.path.insert(0, "/tmp/pvo_fetch/scripts")
import dates, gn

d = json.load(open("/tmp/pvo_fetch/units.json"))
ROOT = "/home/x280/work/Nuclear-Probabilities/"
P_RE = re.compile(r"PVO|Air Defen[cs]e")
V_RE = re.compile(r"Air Army|VVS|Fleet|Military District|Special Corps|Long-Range|\bDA\b")
UNC_TAIL = re.compile(r"reportedly|uncertain|probably|possibly|certain from|maybe|\?", re.I)
BASEH = re.compile(r"^(Bases|Base|HQ|Headquarters)\b", re.I)
SUBH = re.compile(r"^Subordinat", re.I)
COORD = re.compile(r"(\d{1,3}) (\d{1,2}) (\d{1,2})N,\s*(\d{1,3}) (\d{1,2}) (\d{1,2})E?")


def sec(x, rx):
    o = []
    for s in x["secs"]:
        if s["head"] and rx.match(s["head"]):
            o += s["items"]
    return o


def coords(t):
    m = COORD.search(t)
    if not m:
        return None
    a = [int(v) for v in m.groups()]
    if a[1] >= 60 or a[2] >= 60 or a[4] >= 60 or a[5] >= 60:
        return None
    return (round(a[0] + a[1] / 60 + a[2] / 3600, 4), round(a[3] + a[4] / 60 + a[5] / 3600, 4))


def yrs(iv):
    def y(t):
        k = dates.tok(t) if t != "?" else None
        if not k or k[0] >= 10**6:
            return ""
        return k[0] // 12

    return y(iv[0]), y(iv[1])


def splitbase(item):
    m = dates.IV.search(item)
    head = item[: m.start()].rstrip(" ,") if m else item
    tail = item[m.end() :] if m else ""
    parts = [p.strip() for p in head.split(",")]
    return parts[0], (parts[1] if len(parts) > 1 else ""), tail.strip()


def pvo_events(x):
    ev = []
    for p in x["paras"]:
        m = re.match(
            r"^(?:In\s+)?(?:Activated\s+)?(\d{1,2}\.\d{1,2}\.\d{2,4}|\d{1,2}\.\d{2,4}|\d{4})\b", p
        )
        if not m:
            continue
        if not re.search(
            r"renamed|transferred to the Air Defen|transferred to the air defen|^Activated", p
        ):
            continue
        if re.search(r"^Activated", p) and not P_RE.search(p):
            continue
        k = dates.tok(m[1])
        if k:
            ev.append((k, bool(P_RE.search(p)), p))
    ev.sort(key=lambda e: e[0][1])
    return ev


def pvo_para(x):
    """(state,para): state P/V at June 1956 from dated rename or transfer lines, or later if first PVO event follows the date"""
    ev = pvo_events(x)
    before = [e for e in ev if e[0][1] <= dates.T]
    if before:
        e = before[-1]
        return ("P" if e[1] else "V", e[2], e[0])
    later = [e for e in ev if e[1]]
    if later:
        return ("L", later[0][2], later[0][0])
    return None


def units(rx):
    return {
        u: x for u, x in d.items() if re.search(rx, u) and re.search(r"\d", u.rsplit("/", 1)[1])
    }


IAD = units(r"/iad/")
IAP = units(r"/iap/")


def classify(x, lookup=None):
    subs = []
    for s in sec(x, SUBH):
        st, iv = dates.cover(s)
        if st in ("yes", "uncertain"):
            subs.append((st, iv, s))
    title = x["title"] + " " + x["paras"][0] if x["paras"] else x["title"]
    if subs:
        kinds = []
        for st, iv, s in subs:
            name = re.split(r",\s*(?=\d|\?)", s)[0]
            if P_RE.search(name):
                kinds.append((st, "P", s))
            elif V_RE.search(name):
                kinds.append((st, "V", s))
            else:
                k = "?"
                if lookup and name.strip() in lookup:
                    k = lookup[name.strip()]
                kinds.append((st, k, s))
        if any(st == "yes" and k == "V" for st, k, s in kinds):
            return "no", [s for st, k, s in kinds if k == "V"][0]
        if all(k == "P" for st, k, s in kinds):
            return "yes", " / ".join(s for st, k, s in kinds)
        if any(st == "yes" and k == "P" for st, k, s in kinds):
            return "yes", [s for st, k, s in kinds if k == "P"][0]
        # unknown parent or mixed
        pp = pvo_para(x)
        joined = " / ".join(s_ for st, k, s_ in kinds)
        if any(k == "V" for st, k, s_ in kinds) and any(st == "uncertain" for st, k, s_ in kinds):
            return "uncertain", "subordination changes in 1956 at year precision: " + joined
        if pp and pp[0] == "P" and pp[2][0] == dates.T:
            return "uncertain", "PVO rename dated inside June 1956: " + pp[
                1
            ] + " Parent still " + joined
        if pp and pp[0] == "P":
            return "yes", "parent not labelled (" + joined + "); " + pp[1]
        if pp and pp[0] == "L":
            return "no", pp[1]
        if pp and pp[0] == "V":
            return "novvs", pp[1]
        if "PVO" in title:
            return (
                "uncertain",
                "parent not labelled PVO (" + joined + "); title says PVO, no dated transfer",
            )
        return ("uncertain" if any(k == "P" for st, k, s_ in kinds) else "novvs"), joined
    pp = pvo_para(x)
    if pp:
        if pp[0] == "P":
            return "yes", pp[1]
        if pp[0] == "L":
            return "no", pp[1]
        return "novvs", pp[1]
    if "PVO" in title:
        return (
            "uncertain",
            "title says PVO; page has no subordination line or dated transfer covering June 1956",
        )
    return "novvs", ""


# parent lookup by title, two passes
lookup = {}
for u, x in IAD.items():
    st, ev = classify(x)
    t = re.sub(r"\s+", " ", x["title"])
    lookup[re.sub(" PVO$", "", t)] = {"yes": "P", "no": "V", "novvs": "V"}.get(st, "?")
    lookup[t] = lookup[re.sub(" PVO$", "", t)]
ROWS = []
DROP = collections.Counter()
NOBASE = []


def first_pvo_start(x):
    for s in sec(x, SUBH):
        if P_RE.search(s):
            iv = dates.intervals(s)
            if iv:
                k = dates.tok(iv[0][0]) if iv[0][0] != "?" else None
                return k[0] // 12 if k else None
    pp = pvo_para(x)
    return pp[2][0] // 12 if pp else None


def row_unit(u, x, role):
    st, ev = classify(x, lookup)
    if st == "novvs":
        DROP["not PVO in June 1956 (no PVO label)"] += 1
        return
    bases = []
    for b in sec(x, BASEH):
        s2, iv = dates.cover(b)
        if s2 in ("yes", "uncertain"):
            bases.append((s2, iv, b))
    if not bases:
        if "PVO" in x["title"] or st != "novvs":
            NOBASE.append((u, x["title"], sec(x, BASEH)[:4], st))
        DROP["no base line covering June 1956"] += 1
        return
    fy = first_pvo_start(x)
    if st == "no" and not ("PVO" in x["title"] and fy and fy <= 1957):
        DROP["PVO only from after 1957"] += 1
        return
    aircraft = [
        a
        for a in sec(x, re.compile("^Aircraft", re.I))
        if dates.cover(a)[0] in ("yes", "uncertain")
    ]
    for s2, iv, b in bases:
        town, reg, tail = splitbase(b)
        y0, y1 = yrs(iv)
        tailunc = bool(
            UNC_TAIL.search(tail) or UNC_TAIL.search(b.split("]")[0] if "]" in b else "")
        )
        final = (
            "no"
            if st == "no"
            else ("uncertain" if (s2 == "uncertain" or st == "uncertain" or tailunc) else "yes")
        )
        late = None
        for p_ in x["paras"]:
            m_ = re.match(r"^Activated (\d{1,2}\.\d{1,2}\.\d{2,4}|\d{1,2}\.\d{2,4}|\d{4})\b", p_)
            if m_:
                k_ = dates.tok(m_[1])
                if k_ and k_[0] > dates.T:
                    late = p_
                break
        if late and final != "no":
            final = "uncertain"
        dec = ""
        if final == "no":
            dec = "OUT: not under PVO in June 1956 (" + ev + ")."
        elif final == "uncertain":
            bits = []
            if s2 == "uncertain":
                bits.append("base dates touch 1956 at year or month precision")
            if st == "uncertain":
                bits.append("PVO status in June 1956 not dated (" + ev[:120] + ")")
            if tailunc:
                bits.append("source qualifies the location")
            if late:
                bits.append("activation line post-dates June 1956 (" + late[:90] + ")")
            dec = "UNCERTAIN: " + "; ".join(bits) + "."
        note = 'Holm base line: "' + b + '". PVO evidence: "' + ev + '".'
        if aircraft:
            note += " Aircraft: " + "; ".join(aircraft) + "."
        ROWS.append(
            dict(
                site=town,
                role=role,
                unit=x["paras"][0] if x["paras"] else x["title"],
                country_1956="",
                town=town,
                reg=reg,
                hc=coords(b),
                y0=y0,
                y1=y1,
                in_june_1956=final,
                decision=dec,
                note=note,
                source=u,
            )
        )


for u, x in sorted(IAD.items()):
    row_unit(u, x, "pvo_hq")
for u, x in sorted(IAP.items()):
    row_unit(u, x, "pvo_fighter_base")
json.dump(
    dict(rows=ROWS, drop=DROP, nobase=NOBASE),
    open("/tmp/pvo_fetch/step1.json", "w"),
    ensure_ascii=False,
    indent=0,
)
print(collections.Counter((r["role"], r["in_june_1956"]) for r in ROWS))
print(DROP)
print(len(NOBASE))
