import sys, re, html

for f in sys.argv[1:]:
    s = open(f, "rb").read().decode("cp1252", "replace")
    s = re.sub(r"(?is)<(script|style|head).*?</\1>", "", s)
    s = re.sub(r"(?i)<li[^>]*>", "- ", s)
    s = re.sub(
        r'(?i)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        lambda m: m.group(2) + " {" + m.group(1) + "}",
        s,
        flags=re.S,
    )
    s = re.sub(r"(?i)</(p|tr|li|ul|h\d)>|<br[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\r\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    s = re.sub(r"(?<=[^\n])\n(?=[a-zA-Z(])", " ", s) if False else s
    print("=====", f.split("%2F", 1)[-1])
    print(s)
