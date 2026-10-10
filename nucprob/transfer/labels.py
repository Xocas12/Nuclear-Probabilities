"""Link the targets of the transfer lists to the places of their region.

    python -m nucprob.transfer.labels

A target is located by its name in its own country: today's name (`name_modern`) first, then the
printed name with its prefixes and qualifiers removed ("m. BLOWSTER" -> "Blowster", "vicinity of
Roskilde" -> "Roskilde", "Newcastle (2)" -> "Newcastle"). A name that is a town of the region's
table is that town. Otherwise it is looked up in the country's GeoNames dump
(nucprob.transfer.places.Gazetteer) and linked to the nearest town of the table within LINK_KM.
Hand-checked points in data/curated/gazetteer/transfer_target_links.csv (plan_id, seq, lat, lon,
located_as) take precedence. A target with no point, or with no town within LINK_KM (an airfield
or missile site in the country), stays unlinked; the link report lists both.

Writes data/processed/transfer_links.csv (one row per target in a region) and
data/processed/labels_transfer.parquet (one row per place and list: n_targets, listed).
"""

import re

import numpy as np
import pandas as pd

from nucprob.geo import Points
from nucprob.paths import CURATED, PROCESSED
from nucprob.transfer.places import GAZ, Gazetteer, variants
from nucprob.transfer.regions import REGIONS

LINK_KM = 15.0
LABELS = CURATED / "labels"
PREFIX = re.compile(
    r"^\s*(m\.|g\.|vicinity of|area of|the|fort(ification)?( in)?|headquarters of( the)?)\s+",
    re.I,
)
# Target-country spellings of the lists, by the region's country names.
COUNTRY = {
    "USA (Territory of Alaska)": "",
    "USA (Territory of Hawaii)": "",
    "USA (Puerto Rico)": "",
}


def clean(name: str) -> str:
    n = str(name)
    n = re.sub(r"\(.*?\)|\[.*?\]", " ", n)
    n = re.split(r",| - | south | north | east | west ", n)[0]
    n = PREFIX.sub("", n)
    n = re.sub(r"\b(re\.?tér|airfield|air base|city)\b", "", n, flags=re.I)
    return n.strip(" .").title() if n.isupper() else n.strip(" .")


def hand_links() -> dict[tuple[str, int], tuple[float, float, str]]:
    path = GAZ / "transfer_target_links.csv"
    if not path.exists():
        return {}
    d = pd.read_csv(path)
    return {
        (r["plan_id"], int(r["seq"])): (r["lat"], r["lon"], r["located_as"])
        for _, r in d.iterrows()
    }


def link() -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    places = places[places["lat"].notna()]
    hand = hand_links()
    gaz: dict[str, Gazetteer] = {}
    rows = []
    for region_id, region in REGIONS.items():
        codes = {c: g for c, g, _ in region.countries}
        towns = places[places["region"] == region_id]
        for plan in region.lists:
            lst = pd.read_csv(LABELS / f"{plan}.csv", dtype=str, keep_default_na=False)
            for _, t in lst.iterrows():
                country = COUNTRY.get(t["target_country"], t["target_country"])
                if country not in codes:
                    continue
                code = codes[country]
                own = towns[towns["country"] == country]
                names = [t["name_modern"], clean(t["name_source"])]
                out = {
                    "region": region_id,
                    "plan_id": plan,
                    "seq": int(t["seq"]),
                    "target_country": country,
                    "name_source": t["name_source"],
                    "target_class": t["target_class"],
                    "lat": np.nan,
                    "lon": np.nan,
                    "located_as": "",
                    "method": "",
                    "place_id": "",
                    "town": "",
                    "dist_km": np.nan,
                }
                key = (plan, int(t["seq"]))
                if key in hand:
                    out["lat"], out["lon"], out["located_as"] = hand[key]
                    out["method"] = "hand"
                else:
                    keys = set(variants(*names))
                    hit = [
                        bool(keys & set(variants(n, m)))
                        for n, m in zip(own["name"], own["name_today"], strict=True)
                    ]
                    town_hit = own[np.array(hit, dtype=bool)]
                    if len(town_hit):
                        h = town_hit.sort_values("pop", ascending=False).iloc[0]
                        out.update(lat=h["lat"], lon=h["lon"], located_as=h["name"])
                        out["method"] = "town name"
                    else:
                        if code not in gaz:
                            gaz[code] = Gazetteer(code)
                        i, method = gaz[code].find(*names)
                        if i is not None:
                            g = gaz[code].g
                            out.update(lat=g.at[i, "lat"], lon=g.at[i, "lon"])
                            out["located_as"] = g.at[i, "name"]
                            out["method"] = f"geonames {method}"
                if out["located_as"] and len(own):
                    dist, idx = Points(own["lat"].to_numpy(), own["lon"].to_numpy()).nearest(
                        [out["lat"]], [out["lon"]]
                    )
                    d, j = float(np.ravel(dist)[0]), int(np.ravel(idx)[0])
                    out["dist_km"] = round(d, 1)
                    if d <= LINK_KM:
                        out["place_id"] = own["place_id"].iloc[j]
                        out["town"] = own["name"].iloc[j]
                rows.append(out)
    return pd.DataFrame(rows)


def labels(links: pd.DataFrame) -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    places = places[places["lat"].notna()]
    out = []
    for region_id, region in REGIONS.items():
        for plan in region.lists:
            sub = links[(links["plan_id"] == plan) & (links["place_id"] != "")]
            countries = set(links.loc[links["plan_id"] == plan, "target_country"])
            own = places.loc[
                (places["region"] == region_id) & places["country"].isin(countries), "place_id"
            ]
            n = sub["place_id"].value_counts()
            out.append(
                pd.DataFrame(
                    {
                        "place_id": own,
                        "region": region_id,
                        "plan_id": plan,
                        "n_targets": own.map(n).fillna(0).astype(int),
                    }
                )
            )
    lab = pd.concat(out, ignore_index=True)
    lab["listed"] = (lab["n_targets"] > 0).astype(int)
    return lab


def main() -> None:
    links = link()
    links.to_csv(PROCESSED / "transfer_links.csv", index=False)
    lab = labels(links)
    lab.to_parquet(PROCESSED / "labels_transfer.parquet", index=False)
    s = links.groupby("plan_id").agg(
        targets=("seq", "size"),
        located=("located_as", lambda x: int((x != "").sum())),
        linked=("place_id", lambda x: int((x != "").sum())),
    )
    s["towns_listed"] = lab.groupby("plan_id")["listed"].sum()
    s["towns"] = lab.groupby("plan_id").size()
    print(s.to_string())


if __name__ == "__main__":
    main()
