import json, re, sys, collections, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, SITE, work  # noqa: E402
import dates

d = json.load(open(work("units.json")))
BASEH = re.compile(r"^(Bases|Base|HQ|Headquarters|Location|Locations)\b", re.I)
SUBH = re.compile(r"^Subordinat", re.I)
out = []
for u, x in sorted(d.items()):
    if not re.search(r"/pvo/[^/]+htm$|/iad/|/iap/|/army/(25|52)via|/wp/", u):
        continue
    if re.search(r"(iad|iap|okrug|oapvo|kpvo|dpvo)\.htm$", u) and not re.search(
        r"\d", u.rsplit("/", 1)[1]
    ):
        continue
    bases = []
    subs = []
    for s in x["secs"]:
        h = s["head"] or ""
        if BASEH.match(h):
            bases += s["items"]
        elif SUBH.match(h):
            subs += s["items"]
    bs = []
    for b in bases:
        st, iv = dates.cover(b)
        if st in ("yes", "uncertain"):
            bs.append((st, iv, b))
    sb = []
    for b in subs:
        st, iv = dates.cover(b)
        if st in ("yes", "uncertain"):
            sb.append((st, iv, b))
    out.append(
        dict(
            url=u,
            title=x["title"],
            paras=x["paras"][:14],
            bases_all=bases,
            bases56=bs,
            subs56=sb,
            subs_all=subs,
        )
    )
json.dump(out, open(work("cand.json"), "w"), ensure_ascii=False, indent=0)
print(len(out), sum(1 for o in out if o["bases56"]))
