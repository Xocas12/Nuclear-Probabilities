"""The place universes of the transfer regions: census town tables given coordinates.

    python -m nucprob.transfer.places

Every town of a region's tables (data/curated/gazetteer/towns_<country>_<year>.csv, or a pop-stat
page) is found in its country's GeoNames dump by name: the printed name, today's name and the
name without its qualifiers ("Frankfurt am Main" -> also "Frankfurt"), against GeoNames' name,
ASCII name and alternate names. Among several hits the seat or capital wins, then the place
with the most people today. Names with no exact hit get a close fuzzy match (rapidfuzz ratio
of at least 90) among the country's places of 5,000 or more today. A town found nowhere keeps
no coordinates and is listed.

Writes data/processed/transfer_places.parquet: region, country, name, pop, pop_date, capital,
admin1_seat, admin1, lat, lon, match_method.
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


def load_table(spec: str) -> pd.DataFrame:
    if spec.startswith("popstat:"):
        _, page, col = spec.split(":", 2)
        d = popstat.parse(RAW / "popstat" / f"{page}-cities.htm", page)
        d = d[d[col].notna() & (d[col] >= 10_000)]
        return pd.DataFrame(
            {
                "name": d["name_ru"],
                "name_today": "",
                "admin1": d["region"],
                "pop": d[col].astype(int),
                "pop_date": col.removeprefix("pop_"),
                "capital": (d["region"] == "Wien") & (d["name_ru"] == "Wien"),
                "admin1_seat": 0,
                "source": f"pop-stat {page}",
            }
        )
    d = pd.read_csv(GAZ / f"{spec}.csv", dtype={"name_today": str}, keep_default_na=False)
    d["pop"] = pd.to_numeric(d["pop"], errors="coerce")
    return d[d["pop"].notna()]


class Gazetteer:
    """Name keys of a country's populated places in GeoNames."""

    def __init__(self, code: str):
        g = geonames.load_country(code).reset_index(drop=True)
        a1 = geonames.load_admin1()
        a1 = a1[a1["country"] == code].set_index("admin1")["asciiname"]
        g["admin1_name"] = g["admin1"].map(a1).fillna("")
        self.g = g
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

    def best(self, rows: list[int], admin1: str = "") -> int:
        """A hit in the town's own first-order unit first (when today's unit has the same
        name), then a seat, then the most people today."""
        g = self.g
        a = key(admin1)

        def same_unit(i: int) -> bool:
            b = key(g.at[i, "admin1_name"])
            return bool(a and b) and (a in b or b in a)

        return min(
            set(rows),
            key=lambda i: (
                not same_unit(i),
                SEATS.get(g.at[i, "feature_code"], 4) > 1,
                -g.at[i, "population"],
            ),
        )

    def find(self, *names: str, admin1: str = "") -> tuple[int | None, str]:
        for k in variants(*names):
            if k in self.index:
                return self.best(self.index[k], admin1), "name"
        # A fuzzy hit must lie in the town's own first-order unit, where the table gives one.
        a = key(admin1)
        for k in variants(*names):
            for _, _, j in process.extract(
                k, self.fuzzy_keys, scorer=fuzz.ratio, score_cutoff=90, limit=10
            ):
                i = int(self.fuzzy_rows[j])
                b = key(self.g.at[i, "admin1_name"])
                if not a or (b and (a in b or b in a)):
                    return i, "fuzzy"
        return None, "not found"


# Tables whose rows are districts, not towns, with a file giving each district's
# headquarters town and its point; the seat stands for the district.
SEATS_FILES = {"UK": "uk_districts_1981_seats.csv"}


def manual_links(country: str) -> dict[str, tuple[dict, str]]:
    """Hand-checked coordinates for towns GeoNames does not know by their old name
    (data/curated/gazetteer/transfer_links.csv), and district seats (SEATS_FILES)."""
    out: dict[str, tuple[dict, str]] = {}
    seats = GAZ / SEATS_FILES.get(country, "-")
    if seats.exists():
        d = pd.read_csv(seats)
        for _, r in d[d["lat"].notna()].iterrows():
            out[r["name"]] = ({"lat": r["lat"], "lon": r["lon"], "gn": r["seat"]}, "district seat")
    path = GAZ / "transfer_links.csv"
    if path.exists():
        d = pd.read_csv(path)
        for _, r in d[d["country"] == country].iterrows():
            out[r["name"]] = ({"lat": r["lat"], "lon": r["lon"], "gn": r["located_as"]}, "manual")
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
            gaz = Gazetteer(code)
            links = manual_links(country)
            found = []
            for n, t, a in zip(towns["name"], towns["name_today"], towns["admin1"], strict=True):
                found.append(links[n] if n in links else gaz.find(n, t, admin1=str(a)))
            g = gaz.g

            def coord(hit, col, g=g):
                i, method = hit
                if method in ("manual", "district seat"):
                    return i[col]
                return (
                    g.at[i, {"lat": "lat", "lon": "lon", "gn": "name"}[col]]
                    if i is not None
                    else (np.nan if col != "gn" else "")
                )

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
