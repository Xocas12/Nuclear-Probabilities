import json, re, sys, collections

sys.path.insert(0, "/tmp/pvo_fetch/scripts")
import dates

d = json.load(open("/tmp/pvo_fetch/units.json"))
pat = sys.argv[1]
c = collections.Counter()
heads = collections.Counter()
for u, x in sorted(d.items()):
    if not re.search(pat, u):
        continue
    c["pages"] += 1
    for s in x["secs"]:
        if s["head"] and not s["head"].startswith("Organisation"):
            heads[s["head"][:30]] += 1
print(c)
print(heads.most_common(25))
