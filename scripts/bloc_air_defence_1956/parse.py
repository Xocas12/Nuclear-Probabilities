import re, html, os, json, urllib.parse, sys

from paths import SITE as OUT


def clean(t):
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def parse(path):
    raw = open(path, "rb").read().decode("cp1252", "replace")
    m = re.search(r"(?is)<title>(.*?)</title>", raw)
    title = clean(m.group(1)) if m else ""
    body = re.sub(r"(?is)^.*?<body[^>]*>", "", raw)
    toks = re.split(r"(?is)(<ul[^>]*>.*?</ul>)", body)
    secs = []
    paras = []
    cur = None
    for t in toks:
        if re.match(r"(?is)<ul", t):
            items = [clean(x) for x in re.findall(r"(?is)<li[^>]*>(.*?)(?=<li|</ul>)", t)]
            secs.append({"head": cur, "items": items})
        else:
            ps = [clean(x) for x in re.findall(r"(?is)<p[^>]*>(.*?)</p>", t)]
            ps = [p for p in ps if p]
            paras += ps
            if ps:
                cur = ps[-1]
    return dict(title=title, paras=paras, secs=secs)


res = {}
for f in os.listdir(OUT):
    if f.endswith(".err"):
        continue
    u = "https://" + urllib.parse.unquote(f)
    res[u] = parse(os.path.join(OUT, f))
json.dump(res, open(work("units.json"), "w"), ensure_ascii=False, indent=0)
print(len(res))
