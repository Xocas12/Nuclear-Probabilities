import sys, re, html

for f in sys.argv[1:]:
    s = open(f, "rb").read().decode("cp1252", "replace")
    print("=====", f)
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', s, re.S | re.I)
    for h, t in links:
        print(h, "|", re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", t))))
