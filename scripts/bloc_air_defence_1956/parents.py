import json, re, sys, collections

sys.path.insert(0, "/tmp/pvo_fetch/scripts")
import dates

c = json.load(open("/tmp/pvo_fetch/cand.json"))
d = json.load(open("/tmp/pvo_fetch/units.json"))
names = collections.defaultdict(list)
for o in c:
    if not re.search(r"/iad/|/iap/|/pvo/", o["url"]):
        continue
    for st, iv, t in o["subs56"]:
        n = re.split(r",\s*(?=\d|\?)", t)[0].strip()
        names[n].append((st, iv, o["url"].rsplit("/", 1)[1]))
for n, v in sorted(names.items()):
    print(
        n,
        "|",
        len(v),
        "|",
        collections.Counter(x[0] for x in v).most_common(),
        "|",
        v[0][2],
        v[0][1],
    )
print("---- org lists 1953-1957 with fighter corps etc")
for u, x in sorted(d.items()):
    for s in x["secs"]:
        h = s["head"] or ""
        m = re.match(r"Organisation (19(?:5[3-7]))", h)
        if m and re.search(r"/pvo/|/iad/|/iap/|via", u):
            print(u.rsplit("/", 1)[1], h, s["items"][:12])
