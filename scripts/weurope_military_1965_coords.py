"""Coordinate extraction from saved Wikipedia wikitext (en/de/nl/da/it) for
weurope_military_sites_1965. Used by scripts/weurope_military_1965_build.py.

Recognised templates: {{coord}} (en/it/da), {{Coordinate|NS=|EW=}} (de),
{{Coördinaten|..._N_..._E_}} / {{Coor title dms|...}} / {{Coor dms}} (nl),
{{Koordinater}} (da), plus infobox latd/longd and Breitengrad/Längengrad parameters.
The title/infobox coordinate (display=title, article=/, or the first one) is preferred.
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/weurope_military/wikipedia"


def fname(title):
    return re.sub(r'[/\\:*?"<>|]', "_", title.replace(" ", "_")) + ".json"


def load(ref):
    lang, title = ref.split(":", 1)
    p = RAW / lang / fname(title.replace("_", " "))
    return json.load(open(p))


def _templates(w, names):
    out = []
    pat = r"\{\{\s*(?:" + "|".join(names) + r")\s*\|"
    for m in re.finditer(pat, w, re.I):
        i = m.end()
        depth, j = 1, i
        while j < len(w) and depth:
            if w.startswith("{{", j):
                depth += 1
                j += 2
            elif w.startswith("}}", j):
                depth -= 1
                j += 2
            else:
                j += 1
        body = w[i : j - 2]
        while re.search(r"\{\{[^{}]*\}\}", body):
            body = re.sub(r"\{\{[^{}]*\}\}", "", body)
        out.append((m.start(), m.group(0), body))
    return out


def _num(x):
    x = x.strip().replace(",", ".")
    return float(x) if x else 0.0


def _dms(parts):
    v = 0.0
    for n, x in enumerate(parts):
        if x.strip():
            v += _num(x) / 60**n
    return v


def _parse_coord(body):
    parts = [p for p in body.split("|")]
    named = {
        p.split("=", 1)[0].strip().lower(): p.split("=", 1)[1].strip() for p in parts if "=" in p
    }
    pos = [p.strip() for p in parts if "=" not in p]
    for k, p in enumerate(pos):
        if p.upper() in ("N", "S"):
            for jj, q in enumerate(pos[k + 1 :]):
                if q.upper() in ("E", "W", "O"):
                    lat = _dms(pos[:k]) * (1 if p.upper() == "N" else -1)
                    lon = _dms(pos[k + 1 : k + 1 + jj]) * (-1 if q.upper() == "W" else 1)
                    return lat, lon, named
            return None
    try:
        return _num(pos[0]), _num(pos[1]), named
    except Exception:
        return None


def _de_part(s):
    s = s.strip()
    m = re.match(r"^([\d.,/]+)/?([NSEWO])?$", s.replace(" ", ""))
    if not m:
        return None
    nums = [x for x in m.group(1).split("/") if x != ""]
    v = _dms(nums)
    if m.group(2) in ("S", "W"):
        v = -v
    return v


def _parse_de(body):
    named = {
        p.split("=", 1)[0].strip(): p.split("=", 1)[1].strip() for p in body.split("|") if "=" in p
    }
    if "NS" in named and "EW" in named:
        a, b = _de_part(named["NS"]), _de_part(named["EW"])
        if a is not None and b is not None:
            return a, b, named
    return None


def _parse_nl(body):
    # geohack-style 52_5_30_N_5_7_20_E_type:...
    first = body.split("|")[0]
    m = re.match(r"\s*([\d._]+?)_([NS])_([\d._]+?)_([EWO])", first)
    if m:
        lat = _dms(m.group(1).split("_")) * (1 if m.group(2) == "N" else -1)
        lon = _dms(m.group(3).split("_")) * (-1 if m.group(4) == "W" else 1)
        return lat, lon, {}
    return _parse_coord(body)


def coords(w):
    """All coordinates in a wikitext, in order: list of (pos, lat, lon, kind, is_title)."""
    out = []
    for s, head, body in _templates(
        w,
        [
            "coord",
            "koordinater",
            "coor title dms",
            "coor title dm",
            "coor title d",
            "coor dms",
            "coor dm",
            "coor d",
        ],
    ):
        r = _parse_coord(body)
        if r:
            lat, lon, named = r
            title = (
                "title" in named.get("display", "")
                or named.get("display", "") in ("t", "it,t", "inline,title")
                or "title" in head.lower()
            )
            out.append((s, lat, lon, "coord", title))
    for s, _head, body in _templates(w, ["coordinate"]):
        r = _parse_de(body)
        if r:
            lat, lon, named = r
            title = named.get("article", "") != "" or (
                named.get("type", "") and "text" not in named and "name" not in named
            )
            out.append((s, lat, lon, "Coordinate", title))
    for s, _head, body in _templates(w, ["coördinaten", "coordinaten"]):
        r = _parse_nl(body)
        if r:
            out.append((s, r[0], r[1], "Coördinaten", True))

    # infobox degree parameters
    def g(keys):
        for k in keys:
            m = re.search(r"\|\s*" + k + r"\s*=\s*([-\d.,]+)", w)
            if m and m.group(1).strip(".,-"):
                return _num(m.group(1))
        return None

    for (d, mi, se, ns), (D, MI, SE, ew) in [
        (("latd", "latm", "lats", "latns"), ("longd", "longm", "longs", "longew")),
        (
            ("lat_deg", "lat_min", "lat_sec", "lat_dir"),
            ("lon_deg", "lon_min", "lon_sec", "lon_dir"),
        ),
        (
            ("lat_gradi", "lat_primi", "lat_secondi", "lat_NS"),
            ("long_gradi", "long_primi", "long_secondi", "long_EW"),
        ),
        (
            ("latitudine_gradi", "latitudine_primi", "latitudine_secondi", "latitudine_NS"),
            ("longitudine_gradi", "longitudine_primi", "longitudine_secondi", "longitudine_EW"),
        ),
        (("breddegrad", "_x", "_x", "_x"), ("længdegrad", "_x", "_x", "_x")),
        (("latitude", "_x", "_x", "_x"), ("longitude", "_x", "_x", "_x")),
        (("Latitudine decimale", "_x", "_x", "_x"), ("Longitudine decimale", "_x", "_x", "_x")),
    ]:
        a = g([d])
        b = g([D])
        if a is not None and b is not None:
            lat = a + (g([mi]) or 0) / 60 + (g([se]) or 0) / 3600
            lon = b + (g([MI]) or 0) / 60 + (g([SE]) or 0) / 3600
            m = re.search(r"\|\s*" + ns + r"\s*=\s*([NS])", w)
            if m and m.group(1) == "S":
                lat = -lat
            m = re.search(r"\|\s*" + ew + r"\s*=\s*([EWO])", w)
            if m and m.group(1) == "W":
                lon = -lon
            out.append((w.find(d), lat, lon, "infobox", True))
            break
    for k1, k2 in (
        ("Breitengrad", "Längengrad"),
        ("BREITENGRAD", "LÄNGENGRAD"),
        ("Breite", "Länge"),
        ("lat", "lon"),
    ):
        m1 = re.search(r"\|\s*" + k1 + r"\s*=\s*([\d./,]+(?:/[NS])?)\s*(?:\||\n|<)", w)
        m2 = re.search(r"\|\s*" + k2 + r"\s*=\s*([\d./,]+(?:/[EWO])?)\s*(?:\||\n|<)", w)
        if m1 and m2:
            a, b = _de_part(m1.group(1)), _de_part(m2.group(1))
            if a is not None and b is not None:
                out.append((m1.start(), a, b, "infobox", True))
                break
    out.sort(key=lambda x: x[0])
    return out


def title_coord(ref):
    """Coordinate of the article's subject: title/infobox one if marked, else the first."""
    d = load(ref)
    cs = [c for c in coords(d["wikitext"]) if -90 <= c[1] <= 90 and -30 <= c[2] <= 40 and c[1] != 0]
    if not cs:
        return None
    for c in cs:
        if c[4]:
            return c[1], c[2], c[3]
    return cs[0][1], cs[0][2], cs[0][3] + "(first)"


def named_coord(ref, name_regex):
    """Coordinate of the template whose own text (e.g. name=...) matches name_regex; failing that,
    the first coordinate on the first line matching name_regex."""
    w = load(ref)["wikitext"]
    for _s, head, body in _templates(w, ["coord", "coordinate"]):
        if re.search(name_regex, head + body + "}}"):
            r = (
                _parse_de(body)
                if head.lower().strip("{ |").startswith("coordinate")
                else _parse_coord(body)
            )
            if r:
                return r[0], r[1], "named"
    for line in w.split("\n"):
        if re.search(name_regex, line):
            cs = coords(line)
            if cs:
                return cs[0][1], cs[0][2], cs[0][3]
    return None
