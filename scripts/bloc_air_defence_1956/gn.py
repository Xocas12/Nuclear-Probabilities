import zipfile, io, csv, re, unicodedata

from paths import ROOT

RAW = ROOT + "data/raw/geonames/"


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9а-яё]+", "", s)


def load(countries, wanted):
    """wanted: set of norm names. returns name-> list of records; streams files"""
    out = {}
    for cc in countries:
        z = zipfile.ZipFile(RAW + cc + ".zip")
        with z.open(cc + ".txt") as f:
            for line in io.TextIOWrapper(f, encoding="utf8"):
                p = line.rstrip("\n").split("\t")
                if p[6] not in ("P", "S", "A"):
                    continue
                if p[6] == "A" and not p[7].startswith("PPL"):
                    continue
                if p[6] == "S" and p[7] not in ("AIRF", "AIRP", "AIRB", "AIRH"):
                    continue
                names = {norm(p[1]), norm(p[2])} | {norm(a) for a in p[3].split(",") if a}
                hit = names & wanted
                for n in hit:
                    out.setdefault(n, []).append(
                        dict(
                            gid=p[0],
                            name=p[1],
                            lat=float(p[4]),
                            lon=float(p[5]),
                            fc=p[6],
                            fcode=p[7],
                            cc=p[8],
                            adm1=p[10],
                            pop=int(p[14] or 0),
                        )
                    )
    return out
