import sys, time, os, urllib.request, urllib.parse, re

# usage: fetch.py urlfile ; saves to $PVO_WORK/html/site/<quoted path> (paths.py)
from paths import SITE as OUT
os.makedirs(OUT, exist_ok=True)


def path(u):
    return os.path.join(OUT, urllib.parse.quote(u.split("://", 1)[1], safe=""))


AGENT = "academic-curation-research/1.0"
_robots = {}


def allowed(u):
    """The host's robots.txt answer for this agent; a page it disallows is not fetched."""
    import urllib.robotparser

    host = u.split("://", 1)[0] + "://" + u.split("://", 1)[1].split("/", 1)[0]
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser(host + "/robots.txt")
        rp.read()
        _robots[host] = rp
    return _robots[host].can_fetch(AGENT, u)


def get(u):
    p = path(u)
    if os.path.exists(p):
        return "cached"
    if not allowed(u):
        return "DISALLOWED by robots.txt"
    time.sleep(1.2)
    req = urllib.request.Request(u, headers={"User-Agent": AGENT})
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
