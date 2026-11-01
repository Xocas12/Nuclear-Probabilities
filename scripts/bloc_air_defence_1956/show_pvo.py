import json, re

c = json.load(open("/tmp/pvo_fetch/cand.json"))
for o in c:
    if "/pvo/" in o["url"] and o["bases56"]:
        print(
            o["url"].rsplit("/", 1)[1],
            "|",
            o["title"],
            "|",
            o["bases56"],
            "|SUB",
            [s[2] for s in o["subs56"]],
        )
        print("   P:", [p for p in o["paras"][2:] if re.search(r"19[45]\d|\.[45]\d\b", p)][:4])
print("--no 1956 base:")
for o in c:
    if "/pvo/" in o["url"] and not o["bases56"]:
        print(
            o["url"].rsplit("/", 1)[1],
            "|",
            o["title"],
            "|",
            [p for p in o["paras"] if p.startswith("Activated")][:1],
            o["bases_all"][:2],
        )
