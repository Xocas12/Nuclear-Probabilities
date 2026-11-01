import sys, time, os, urllib.request, urllib.parse, re

# usage: fetch.py urlfile ; saves to /tmp/pvo_fetch/html/<quoted path>
OUT = "/tmp/pvo_fetch/html/site"
os.makedirs(OUT, exist_ok=True)


def path(u):
    return os.path.join(OUT, urllib.parse.quote(u.split("://", 1)[1], safe=""))


def get(u):
    p = path(u)
    if os.path.exists(p):
        return "cached"
    time.sleep(1.2)
    req = urllib.request.Request(u, headers={"User-Agent": "academic-curation-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = r.read()
        if not d:
            return "EMPTY"
        open(p, "wb").write(d)
        return r.status
    except urllib.error.HTTPError as e:
        open(p + ".err", "w").write(str(e.code))
        return e.code
    except Exception as e:
        return "ERR " + str(e)


for u in open(sys.argv[1]):
    u = u.strip()
    if u:
        print(get(u), u, flush=True)
