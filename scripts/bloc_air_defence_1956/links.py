import sys, re, os, urllib.parse

# links.py baseurl  -> prints absolute links from saved page
from paths import SITE as OUT
for base in sys.argv[1:]:
    p = os.path.join(OUT, urllib.parse.quote(base.split("://", 1)[1], safe=""))
    s = open(p, "rb").read().decode("cp1252", "replace")
    for h in re.findall(r'(?i)href="([^"#]+\.htm)"', s):
        print(urllib.parse.urljoin(base, h.replace(" ", "%20")))
