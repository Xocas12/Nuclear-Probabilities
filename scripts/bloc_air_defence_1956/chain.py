import csv, re, json, sys, collections, os

# coverage by top-level PVO body named on Holm's pages (stats only)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, SITE, work  # noqa: E402
import dates

d = json.load(open(work("units.json")))
TOP = [
    (
        "Moscow Air Defence District",
        r"Moscow Air Defence|Air Defence Army for Special Use|52nd Fighter Air Defence|\b37th Fighter Aviation Corps|\b56th Fighter Aviation Corps|78th Guards Fighter Aviation Corps|88th Fighter Aviation Corps|1st Air Defence Army|Special Air Defence Corps|151st Guards",
    ),
    ("Baku Air Defence District", r"Baku Air Defence|62nd Fighter Aviation Corps"),
    ("42nd Fighter Air Defence Army", r"42nd Fighter"),
    ("Leningrad Special Air Defence Army", r"Leningrad Special"),
    ("North Caucasus Air Defence Army", r"Caucasus Air Defence"),
    ("32nd Fighter Air Defence Army", r"32nd Fighter Air Defence"),
    ("Minsk Air Defence Corps", r"Minsk Air Defence"),
    ("49th Fighter Aviation Corps PVO", r"49th Fighter Aviation Corps"),
    ("72nd Guards Corps / Turkmenistan Corps", r"72nd Guards Fighter|Turkmenistan Air Defence"),
    ("Turkestan Air Defence Region", r"Turkestan Air Defence"),
    ("36th Fighter Aviation Corps PVO", r"36th Fighter Aviation Corps"),
    ("Belomorskiy Air Defence Corps", r"Belomorskiy"),
    ("Amurskaya Air Defence Army", r"Amurskaya"),
    ("Sakhalinskaya Air Defence Division", r"Sakhalinskaya"),
    ("Carpathian Air Defence Zone", r"Lvov Air Defence"),
    ("GK PVO direct", r"GK PVO|Odessa Air Defence"),
]


def top(text):
    for n, rx in TOP:
        if re.search(rx, text):
            return n
    return None


title = {}
for u, x in d.items():
    if "/iad/" in u and x["paras"]:
        subs = [
            i
            for s in x["secs"]
            if s["head"] and s["head"].startswith("Subordinat")
            for i in s["items"]
        ]
        m0 = re.search(r"^(\d+)\w*( Guards)?", x["title"])
        if m0 and (m0[1] + (m0[2] or "") not in title or "PVO" in x["title"]):
            title[m0[1] + (m0[2] or "")] = " / ".join(
                i for i in subs if dates.cover(i)[0] in ("yes", "uncertain")
            )
rows = list(csv.DictReader(open(sys.argv[1])))
C = collections.defaultdict(collections.Counter)
NM = []
for r in rows:
    if r["in_june_1956"] == "no":
        continue
    m = re.search(r'PVO evidence: "(.*?)"\.', r["note"])
    ev = m[1] if m else r["unit"] + " " + r["note"][:300]
    if r["note"].startswith("No regiment page"):
        u = r["source"].split("; ")[0]
        subs = [
            i
            for sx in d[u]["secs"]
            if sx["head"] and sx["head"].startswith("Subordinat")
            for i in sx["items"]
            if dates.cover(i)[0] in ("yes", "uncertain")
        ]
        ev = " / ".join(subs)
    if r["role"] == "sam_system":
        t = "Moscow Air Defence District"
    elif r["role"] == "radar":
        t = "radar rows, parent not read"
    else:
        t = top(ev)
        if not t:
            md = re.search(r"(\d+)\w*( Guards)? Fighter Aviation Division", ev)
            if md:
                k = md[1] + (md[2] or "")
                t = top(title.get(k, ""))
    if r["country_1956"] not in ("USSR",):
        t = "Satellite: " + r["country_1956"]
    if not t:
        NM.append((r["role"], r["unit"][:30], r["town"], ev[:60]))
    C[t or "parent not named or not mapped"][r["role"]] += 1
    C[t or "parent not named or not mapped"]["u" if r["in_june_1956"] == "uncertain" else "y"] += 1
for k, v in sorted(
    C.items(),
    key=lambda kv: -sum(kv[1][a] for a in ("pvo_hq", "pvo_fighter_base", "sam_system", "radar")),
):
    print(k, dict(v))
hq = {
    re.match(r"\d+", r["unit"])[0]
    for r in rows
    if r["role"] == "pvo_hq" and re.match(r"\d+", r["unit"])
}
par = collections.Counter()
for r in rows:
    if r["role"] == "pvo_fighter_base" and r["in_june_1956"] != "no":
        m = re.search(r'PVO evidence: "(.*?)"\.', r["note"])
        md = re.search(r"(\d+)\w* ?(Guards )?Fighter Aviation Division", m[1]) if m else None
        if md and md[1] not in hq:
            par[md[0]] += 1
print("parent divisions named by regiment rows, no HQ row:", par.most_common())
print("NM", NM)
