"""The place universes of the transfer regions: census town tables given coordinates.

    python -m nucprob.transfer.places

Every town of a region's tables (data/curated/gazetteer/towns_<country>_<year>.csv, or a pop-stat
page) is found in its country's GeoNames dump by name: the printed name, today's name and the
name without its qualifiers ("Frankfurt am Main" -> also "Frankfurt"), against GeoNames' name,
ASCII name and alternate names. A town is only ever matched inside its own first-order unit:
data/curated/gazetteer/admin1_crosswalk.csv says which GeoNames units a table's unit may lie in
today, and a table unit it does not list stops the build. Among several hits in the unit the
town's own province (where the crosswalk gives one) wins, then a place with at least a fifth of
the town's census people (one carrying the name as its main name before one holding it as an
alternate), then a seat or capital, then the place with the most people today. Names with no exact hit get a close fuzzy match (rapidfuzz ratio of at least
90) among the unit's places of 5,000 or more today. A town found nowhere keeps no coordinates
and is listed: a same-named place in another unit is a different town.

Writes data/processed/transfer_places.parquet: region, country, name, pop, pop_date, capital,
admin1_seat, admin1, lat, lon, match_method, gn_admin1 (the first-order unit of the GeoNames
entry used, blank for a hand-placed town).
"""

import re

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from nucprob.gazetteer.lookup import fold
from nucprob.paths import CURATED, PROCESSED, RAW
from nucprob.sources import geonames, popstat
from nucprob.transfer.regions import REGIONS

GAZ = CURATED / "gazetteer"
SEATS = {"PPLC": 0, "PPLA": 1, "PPLA2": 2, "PPL": 3}
CREDIBLE = 0.2  # a GeoNames place with under this share of a town's census people is not it
QUALIFIER = re.compile(
    r"\s*(\(.*?\)|,.*$|/.*$|\b(am|an der|a\. ?d\.|i\. ?d\.|im|in|bei|ob der|sur|en|aan|on|upon|"
    r"-on-|-upon-)\b.*$)",
    re.I,
)


def key(name: str) -> str:
    return re.sub(r"[^a-z]", "", fold(str(name)).lower())


def variants(*names: str) -> list[str]:
    out = []
    for n in names:
        if not isinstance(n, str) or not n.strip():
            continue
        out += [
            n,
            QUALIFIER.sub("", n),
            n.split(" - ")[0],
            n.replace("St.", "Saint"),
            n.replace("Sankt", "St."),
            n.replace("Saint", "St."),
        ]
    return [k for k in dict.fromkeys(key(v) for v in out) if k]


# The seat of each first-order unit at the census date, for the pop-stat pages (Land: seat
# town, as the page spells it). The pages underline today's seats, which are not the 1961
# ones: St. Pölten was made Lower Austria's capital in 1986 (until then, and in practice until
# 1997, the Land was governed from Vienna), and the page underlines Dornbirn for Vorarlberg,
# whose seat is Bregenz.
# Eisenstadt (Burgenland) is listed but had fewer than 10,000 people in 1961.
POPSTAT_SEATS = {
    "austria": {
        "Wien": "Wien",
        "Burgenland": "Eisenstadt",
        "Kärnten": "Klagenfurt am Wörthersee",
        "Niederösterreich": "Wien",
        "Oberösterreich": "Linz",
        "Salzburg": "Salzburg",
        "Steiermark": "Graz",
        "Tirol": "Innsbruck",
        "Vorarlberg": "Bregenz",
    },
}


def popstat_seats(d: pd.DataFrame, page: str) -> pd.Series:
    """1 for the towns of a parsed pop-stat page that were the seat of a first-order unit.

    Checked against the whole page, before any population cut: every unit of the page must
    have a seat in POPSTAT_SEATS, and every seat must name exactly one town of the page, so a
    renamed town or a new page fails here instead of leaving the column silently at 0."""
    if page not in POPSTAT_SEATS:
        raise ValueError(f"pop-stat page {page!r} has no first-order seats in POPSTAT_SEATS")
    seats = POPSTAT_SEATS[page]
    unknown = sorted(set(d["region"]) - set(seats))
    if unknown:
        raise ValueError(f"pop-stat {page}: no seat given for {unknown}")
    for unit, town in seats.items():
        n = int((d["name_ru"] == town).sum())
        if n != 1:
            raise ValueError(f"pop-stat {page}: seat of {unit}, {town!r}, found {n} times")
    return d["name_ru"].isin(set(seats.values())).astype(int)


def load_table(spec: str) -> pd.DataFrame:
    if spec.startswith("popstat:"):
        _, page, col = spec.split(":", 2)
        d = popstat.parse(RAW / "popstat" / f"{page}-cities.htm", page)
        d = d.assign(admin1_seat=popstat_seats(d, page))
        d = d[d[col].notna() & (d[col] >= 10_000)]
        return pd.DataFrame(
            {
                "name": d["name_ru"],
                "name_today": "",
                "admin1": d["region"],
                "pop": d[col].astype(int),
                "pop_date": col.removeprefix("pop_"),
                "capital": (d["region"] == "Wien") & (d["name_ru"] == "Wien"),
                "admin1_seat": d["admin1_seat"],
                "source": f"pop-stat {page}",
            }
        )
    d = pd.read_csv(GAZ / f"{spec}.csv", dtype={"name_today": str}, keep_default_na=False)
    d["pop"] = pd.to_numeric(d["pop"], errors="coerce")
    return d[d["pop"].notna()]


def admin1_crosswalk(country: str) -> dict[str, tuple[set[str], set[str]]]:
    """A table's first-order unit -> (the GeoNames admin1 codes, and admin2 codes where given,
    it may lie in today)."""
    d = pd.read_csv(GAZ / "admin1_crosswalk.csv", dtype=str, keep_default_na=False)
    return {
        r["admin1"]: (set(r["gn_admin1"].split(";")), set(filter(None, r["gn_admin2"].split(";"))))
        for _, r in d[d["country"] == country].iterrows()
    }


class Gazetteer:
    """Name keys of a country's populated places in GeoNames. With `units` (admin1_crosswalk)
    a lookup that gives its admin1 is confined to that unit."""

    def __init__(self, code: str, units: dict[str, tuple[set[str], set[str]]] | None = None):
        g = geonames.load_country(code).reset_index(drop=True)
        self.g = g
        self.units = units
        self.index: dict[str, list[int]] = {}
        for i, (name, ascii_name, alt) in enumerate(
            zip(g["name"], g["asciiname"], g["alternatenames"], strict=True)
        ):
            for n in {name, ascii_name, *str(alt).split(",")}:
                k = key(n)
                if k:
                    self.index.setdefault(k, []).append(i)
        big = g[g["population"] >= 5000]
        self.fuzzy_keys = [key(n) for n in big["name"]]
        self.fuzzy_rows = big.index.to_numpy()

    def unit(self, admin1: str) -> tuple[set[str], set[str]] | None:
        if not admin1 or self.units is None:
            return None
        if admin1 not in self.units:
            raise ValueError(f"table unit {admin1!r} is not in admin1_crosswalk.csv")
        return self.units[admin1]

    def best(
        self, rows: list[int], k: str = "", admin2: frozenset | set = frozenset(), pop: float = 0
    ) -> int:
        """The town's own province first, where known. Then, when the lookup gives the town's
        census population, a place big enough to be it: first one with the name as its main name,
        then one holding it as an alternate (the alternate names hold old and foreign spellings,
        "Mirano" among Milan's, while "München" is also a hamlet's main name). Then a seat, then
        the most people today."""
        g = self.g

        def tier(i: int) -> int:
            if not pop:
                return 0
            if g.at[i, "population"] < CREDIBLE * pop:
                return 2
            return int(k not in (key(g.at[i, "name"]), key(g.at[i, "asciiname"])))

        return min(
            set(rows),
            key=lambda i: (
                bool(admin2) and g.at[i, "admin2"] not in admin2,
                tier(i),
                SEATS.get(g.at[i, "feature_code"], 4) > 1,
                -g.at[i, "population"],
            ),
        )

    def find(self, *names: str, admin1: str = "", pop: float = 0) -> tuple[int | None, str]:
        unit = self.unit(admin1)
        g = self.g
        for k in variants(*names):
            rows = self.index.get(k, [])
            if unit:
                rows = [i for i in rows if g.at[i, "admin1"] in unit[0]]
                if rows:
                    return self.best(rows, k, unit[1], pop), "name"
            elif rows:
                return self.best(rows), "name"
        # A fuzzy hit must lie in the town's own first-order unit, where the table gives one.
        for k in variants(*names):
            for _, _, j in process.extract(
                k, self.fuzzy_keys, scorer=fuzz.ratio, score_cutoff=90, limit=10
            ):
                i = int(self.fuzzy_rows[j])
                if not unit or g.at[i, "admin1"] in unit[0]:
                    return i, "fuzzy"
        return None, "not found"


# Tables whose rows are districts, not towns, with a file giving each district's
# headquarters town and its point; the seat stands for the district.
SEATS_FILES = {"UK": "uk_districts_1981_seats.csv"}


def manual_links(country: str) -> dict[tuple[str, str], tuple[dict, str]]:
    """Hand-checked coordinates for towns GeoNames does not know by their old name
    (data/curated/gazetteer/transfer_links.csv), and district seats (SEATS_FILES), keyed by
    (name, admin1); admin1 is blank where the name alone is unique in the country. A row with
    no lat stays unplaced: the notes say why no point could be fixed."""
    out: dict[tuple[str, str], tuple[dict, str]] = {}
    seats = GAZ / SEATS_FILES.get(country, "-")
    if seats.exists():
        d = pd.read_csv(seats)
        for _, r in d[d["lat"].notna()].iterrows():
            hit = {"lat": r["lat"], "lon": r["lon"], "gn": r["seat"]}
            out[(r["name"], "")] = (hit, "district seat")
    path = GAZ / "transfer_links.csv"
    if path.exists():
        d = pd.read_csv(path, dtype={"admin1": str}, keep_default_na=False)
        d["lat"] = pd.to_numeric(d["lat"], errors="coerce")
        d["lon"] = pd.to_numeric(d["lon"], errors="coerce")
        for _, r in d[d["country"] == country].iterrows():
            hit = {"lat": r["lat"], "lon": r["lon"], "gn": r["located_as"]}
            method = "manual" if pd.notna(r["lat"]) else "not found"
            out[(r["name"], r["admin1"])] = (hit, method)
    return out


def build() -> pd.DataFrame:
    parts = []
    for region_id, region in REGIONS.items():
        for country, code, spec in region.countries:
            if not spec.startswith("popstat:") and not (GAZ / f"{spec}.csv").exists():
                print(f"{region_id}: {spec} missing, skipped")
                continue
            towns = load_table(spec)
            # Summary rows (metropolitan areas) are not towns of the universe.
            notes = towns.get("notes", pd.Series("", index=towns.index)).astype(str)
            towns = towns[
                ~towns["name"].str.contains(r"\((?:CMA|metropolitan)", case=False)
                & ~notes.str.contains("^CMA|census metropolitan area row", case=False)
                # The US table's territories lie outside the 1955 universe (the 48 states, DC).
                & ~notes.str.contains("Territory, outside", case=False)
            ]
            towns = towns.reset_index(drop=True)
            gaz = Gazetteer(code, admin1_crosswalk(country))
            links = manual_links(country)
            found = []
            for n, t, a, p in zip(
                towns["name"], towns["name_today"], towns["admin1"], towns["pop"], strict=True
            ):
                a = str(a)
                hit = links.get((n, a)) or links.get((n, ""))
                found.append(hit if hit else gaz.find(n, t, admin1=a, pop=p))
            g = gaz.g

            def coord(hit, col, g=g):
                i, _ = hit
                if isinstance(i, dict):
                    return i.get(col, "" if col == "a1" else np.nan)
                blank = "" if col in ("gn", "a1") else np.nan
                columns = {
                    "lat": "lat",
                    "lon": "lon",
                    "gn": "name",
                    "a1": "admin1",
                    "pop": "population",
                }
                return g.at[i, columns[col]] if i is not None else blank

            towns["gn_admin1"] = [coord(h, "a1") for h in found]
            towns["gn_population"] = [coord(h, "pop") for h in found]
            towns["lat"] = [coord(h, "lat") for h in found]
            towns["lon"] = [coord(h, "lon") for h in found]
            towns["gn_name"] = [coord(h, "gn") for h in found]
            towns["match_method"] = [m for _, m in found]
            towns["region"], towns["country"] = region_id, country
            parts.append(towns)
    out = pd.concat(parts, ignore_index=True)
    out["place_id"] = (
        out["region"]
        + ":"
        + out["country"]
        + ":"
        + out.groupby(["region", "country"]).cumcount().astype(str)
    )
    for c in ("capital", "admin1_seat"):
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype(int)
    return out


def main() -> None:
    out = build()
    cols = [
        "place_id",
        "region",
        "country",
        "name",
        "name_today",
        "gn_name",
        "admin1",
        "pop",
        "pop_date",
        "capital",
        "admin1_seat",
        "lat",
        "lon",
        "match_method",
        "gn_admin1",
    ]
    out[cols].to_parquet(PROCESSED / "transfer_places.parquet", index=False)
    summary = out.groupby(["region", "country"]).agg(
        towns=("name", "size"),
        located=("lat", lambda s: int(s.notna().sum())),
        fuzzy=("match_method", lambda s: int((s == "fuzzy").sum())),
    )
    print(summary.to_string())
    missing = out[out["lat"].isna()]
    if len(missing):
        print("not found:", "; ".join(missing["country"] + " " + missing["name"])[:2000])


if __name__ == "__main__":
    main()
