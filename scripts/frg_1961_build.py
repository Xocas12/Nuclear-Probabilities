"""Build data/curated/gazetteer/towns_frg_1961.csv from the census table's text layer.

    python scripts/frg_1961_read.py > data/interim/frg/ranked.csv
    python scripts/frg_1961_build.py data/interim/frg/ranked.csv

The table is printed in descending order of the 1961 population, so each figure is bounded by
its neighbours; the printed changes against 1939 and 1950 test it again. Rows that fail were read
on the scan and are in data/curated/gazetteer/frg_1961_corrections.csv (number, field,
value). The build fails if a row still breaks the order. The names and Land come from the same
rows; Land brackets span rows, so a row with no Land token takes the nearest token on its page.
"""

import re
import sys

import pandas as pd

from nucprob.transfer.places import Gazetteer, variants

GAZ = "data/curated/gazetteer"
LAND = {
    "SchH": "Schleswig-Holstein", "Hmb": "Hamburg", "Ndsa": "Niedersachsen", "Brm": "Bremen",
    "NrhW": "Nordrhein-Westfalen", "Hess": "Hessen", "RhPf": "Rheinland-Pfalz",
    "BaWü": "Baden-Württemberg", "Bay": "Bayern", "Saar": "Saarland", "BlnW": "Berlin (West)",
}  # fmt: skip
GN_LAND = {
    "SchH": "Schleswig-Holstein", "Hmb": "Hamburg", "Ndsa": "Lower Saxony", "Brm": "Bremen",
    "NrhW": "North Rhine-Westphalia", "Hess": "Hesse", "RhPf": "Rheinland-Pfalz",
    "BaWü": "Baden-Wurttemberg", "Bay": "Bavaria", "Saar": "Saarland", "BlnW": "Berlin",
}  # fmt: skip
# Table 1 of the volume: Gemeinden of 10,000+ and their people in thousands, Land by Land.
PRINTED = {
    "Schleswig-Holstein": (30, 1176.5), "Hamburg": (1, 1832.4), "Lower Saxony": (74, 2879.5),
    "Bremen": (2, 706.4), "North Rhine-Westphalia": (222, 12099.3), "Hesse": (42, 2178.0),
    "Rheinland-Pfalz": (26, 1111.6), "Baden-Wurttemberg": (88, 3510.4), "Bavaria": (81, 3757.1),
    "Saarland": (16, 468.9),
}  # fmt: skip
# Today's name, where the table's form does not reach GeoNames.
TODAY = {
    "Stolberg (Rhld": "Stolberg", "Bad Homburg v.d.H": "Bad Homburg vor der Höhe",
    "Rodenkirchen (Bez. Köln": "Rodenkirchen", "Gronau (Westf": "Gronau",
    "Hückelhoven-Ratheim": "Hückelhoven", "Schwandorf i.Bay": "Schwandorf",
    "Hofheim a.Ts": "Hofheim am Taunus", "Weißenburg i.Bay": "Weißenburg in Bayern",
    "Kempen-Niederrhein": "Kempen", "Ellwangen (Jagst": "Ellwangen", "Neureut (Baden": "Neureut",
    "Mühldorf a.Inn": "Mühldorf am Inn", "Schloß Neuhaus": "Schloss Neuhaus",
    "Roth b.Nürnberg": "Roth", "Immenstadt i.Allgäu": "Immenstadt im Allgäu",
    "Landsberg a.Lech": "Landsberg am Lech", "Hoengen": "Höngen",
}  # fmt: skip
# Land read on the scan or from the town's location, where the OCR lost it under a bracket.
LAND_READ: dict[str, str] = {
    "Schloß Neuhaus": "North Rhine-Westphalia", "Neureut (Baden": "Baden-Wurttemberg",
    "Duisdorf": "North Rhine-Westphalia", "Epe": "North Rhine-Westphalia",
    "Munster": "Lower Saxony",
}  # fmt: skip
SEATS = {
    "Berlin (West)", "Hamburg", "Bremen", "Kiel", "Hannover", "Düsseldorf", "Wiesbaden", "Mainz",
    "Stuttgart", "München", "Saarbrücken",
}  # fmt: skip
SOURCE = "Statistisches Bundesamt, Fachserie A, Volkszählung vom 6. Juni 1961, Vorbericht 3 (June 1962), Table 2"


def num(s) -> float:
    t = re.sub(r"[^\d,.]", "", str(s)).replace(".", ",")
    try:
        return float(t.replace(",", "."))
    except ValueError:
        return float("nan")


def short(name: str) -> str:
    n = re.sub(r"\s+\.\s+", " ", name)
    n = re.sub(
        r"\s*[|\^]?\s*[|fiI^{]?(saar|NrhW|ß?ay|Bay|Hess|Ndsa|SchH|RhPf|BaWü)\s*$", "", n, flags=re.I
    )
    n = re.sub(r"[„»«.,:;|>)\]}\s]+$", lambda k: ")" if ")" in k.group() else "", n)
    n = re.sub(r"\s*[|>)\]]+$", "", n)
    n = re.sub(
        r",?\s*(\.\s*)?(Freie und Hansestadt|Hansestadt|Stadt|Landeshauptstadt|Universitätsstadt"
        r"|Domstadt|Kreisstadt|Markt|Staat|Stach|Stadt[.,:\s]*)\.?\s*$",
        "",
        n,
    )
    n = re.sub(r"\s+", " ", n).strip(" ,.")
    return re.sub(r"^(.+), (Bad|Sankt)$", r"\2 \1", n)


def read_order(raw: list[str]) -> tuple[list[int], list[int]]:
    """The figures, cut to 5-7 digits (the percent column sometimes runs into them), and the rows
    outside the longest non-increasing run: those break the table's printed order."""
    vals = []
    for s in raw:
        v = int(s) if s.isdigit() else 0
        if v > 2_500_000 and s[:5].isdigit():
            v = int(s[:5])
        vals.append(v)
    best = [1] * len(vals)
    back = [-1] * len(vals)
    for i in range(len(vals)):
        for j in range(max(0, i - 40), i):
            if vals[j] >= vals[i] and best[j] + 1 > best[i]:
                best[i], back[i] = best[j] + 1, j
    keep, i = set(), max(range(len(vals)), key=best.__getitem__)
    while i >= 0:
        keep.add(i)
        i = back[i]
    return vals, [i for i in range(len(vals)) if i not in keep or vals[i] < 10_000]


def assign_land(m: pd.DataFrame) -> pd.Series:
    """A printed token where the OCR kept one. Under a bracket: the Land among the name's
    GeoNames hits, with the nearest printed token breaking a tie, then the town with most people."""
    gz = Gazetteer("DE")
    g = gz.g
    tokens = m["land"].map(GN_LAND)
    over = m["name_clean"].map(LAND_READ)
    out = []
    for i in m.index:
        if pd.notna(over.at[i]):
            out.append(over.at[i])
            continue
        if pd.notna(tokens.at[i]):
            out.append(tokens.at[i])
            continue
        hits = {
            j
            for k in variants(m.at[i, "name_clean"], m.at[i, "name_today"])
            for j in gz.index.get(k, [])
        }
        west = [j for j in hits if g.at[j, "admin1_name"] in set(GN_LAND.values())]
        known = tokens[tokens.notna()]
        near = known.iloc[abs(known.index.to_numpy() - i).argsort()[:6]].tolist()
        big = max(west, key=lambda j: g.at[j, "population"], default=None)
        if big is not None and g.at[big, "population"] >= 0.4 * m.at[i, "pop"]:
            out.append(g.at[big, "admin1_name"])
            continue
        pick = [x for x in near if x in {g.at[j, "admin1_name"] for j in west}]
        out.append(pick[0] if pick else near[0])
    return pd.Series(out, index=m.index)


def check_land(m: pd.DataFrame) -> None:
    """Against the volume's Table 1 (p. 6): towns and thousands of people per Land."""
    got = m.groupby("admin1")["pop"].agg(["size", "sum"])
    for land, (n, thousands) in PRINTED.items():
        a, b = int(got.at[land, "size"]), got.at[land, "sum"] / 1000
        flag = "" if a == n and abs(b - thousands) < 0.5 else "  <-- differs"
        print(f"{land:26} {a:4} {n:4} {b:10.1f} {thousands:10.1f}{flag}", file=sys.stderr)


def main(path: str) -> None:
    m = pd.read_csv(path, dtype=str, keep_default_na=False)
    fixes = pd.read_csv(f"{GAZ}/frg_1961_corrections.csv", dtype=str, keep_default_na=False)
    # The OCR lost one printed row; its values are in the corrections file as `row` entries.
    for _, f in fixes[fixes["field"].eq("row")].iterrows():
        name, land, pop = f["value"].split("|")
        at = int(f["seq"]) - 1
        new = dict.fromkeys(m.columns, "") | {
            "page": f["page"], "name": name, "land": land, "pop61": pop,
        }  # fmt: skip
        m = pd.concat([m.iloc[:at], pd.DataFrame([new]), m.iloc[at:]], ignore_index=True)
    m["seq"] = range(1, len(m) + 1)
    for _, f in fixes[fixes["field"].ne("row")].iterrows():
        m.loc[m["seq"].eq(int(f["seq"])), f["field"]] = f["value"]
    p, bad = read_order(m["pop61"].tolist())
    m["pop"] = p
    m["p39"] = pd.to_numeric(m["pop39"], errors="coerce")
    m["p50"] = pd.to_numeric(m["pop50"], errors="coerce")
    m["pct39n"], m["pct50n"] = m["pct39"].map(num), m["pct50"].map(num)
    c39 = (m["pop"] / m["p39"] - 1) * 100
    c50 = (m["pop"] / m["p50"] - 1) * 100
    m["ok39"] = (c39.abs() - m["pct39n"]).abs() < 0.11
    m["ok50"] = (c50.abs() - m["pct50n"]).abs() < 0.11
    # A jump bigger than the neighbours allow: an ordering a misread high digit could pass.
    gap = m["pop"].shift(1) - m["pop"]
    jump = gap > m["pop"] * 0.08
    fail = m[~m["ok39"] & ~m["ok50"]]
    print(
        "rows",
        len(m),
        "order breaks",
        len(bad),
        "no pct support",
        len(fail),
        "jumps",
        int(jump.sum()),
        file=sys.stderr,
    )
    for i in bad:
        print("ORDER", dict(m.loc[i, ["seq", "page", "name", "pop61"]]), file=sys.stderr)
    for _, r in fail.iterrows():
        print(
            "PCT",
            r["seq"],
            r["page"],
            r["name"],
            r["pop61"],
            r["pop39"],
            r["pop50"],
            r["pct39"],
            r["pct50"],
            sep=" | ",
            file=sys.stderr,
        )
    for _, r in m[jump].iterrows():
        print("JUMP", r["seq"], r["page"], r["name"], r["pop"], file=sys.stderr)
    m["name_clean"] = m["name"].map(short)
    old = pd.read_csv(f"{GAZ}/frg_1961_wikipedia.csv", dtype=str, keep_default_na=False)
    today = dict(zip(old["name"], old["name_today"], strict=True))
    today |= {k: v for k, v in TODAY.items()}
    m["name_today"] = m["name_clean"].map(today).fillna("")
    m["admin1"] = assign_land(m)
    check_land(m)
    out = pd.DataFrame(
        {
            "name": m["name_clean"],
            "name_today": m["name_today"],
            "admin1": m["admin1"],
            "pop": m["pop"],
            "pop_date": "1961-06-06",
            "capital": m["name_clean"].eq("Bonn").astype(int),
            "admin1_seat": m["name_clean"].isin(SEATS).astype(int),
            "source": SOURCE,
            "source_page": "p. " + m["page"].astype(str),
            "notes": "preliminary census result; Gebietsstand 6.6.1961",
        }
    )
    out.to_csv(f"{GAZ}/towns_frg_1961.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1])
