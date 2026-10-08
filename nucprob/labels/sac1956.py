"""Labels from the transcribed SAC 1956 list (PLAN section 4.2), for the place universe of
every bloc country in the place table.

    python -m nucprob.labels.sac1956 [--radius-km 10]

Coordinates first, names second (PLAN section 10): every complex and sub-complex header and
every DGZ is linked to the nearest settlement of its own country in the place table (all
settlements of at least 5,000) within the radius. A target nearest to a settlement below the
universe threshold stays with that settlement, so it does not make a larger neighbour look
targeted. The SAC name is compared with the settlement's names (1956, today's, GeoNames) as a
check, not a key.

Writes to data/processed/:
  sac1956_links.parquet   one row per complex, sub-complex and DGZ, with its place
  labels_sac1956.parquet  one row per settlement: T1 (listed; given an aim point), T2 (DGZ and
                          installation counts), T3 (best priority and tier)
  sac1956_link_report.csv unlinked targets and links whose names disagree, for review
"""

import argparse

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from nucprob.bloc import sac_country
from nucprob.gazetteer.lookup import latin_names as place_names
from nucprob.gazetteer.lookup import text
from nucprob.gazetteer.names import variants
from nucprob.gazetteer.translit import simple, to_latin
from nucprob.geo import Points, haversine_km
from nucprob.paths import CURATED, PROCESSED

RADIUS_KM = 10.0
NAME_OK = 75  # name similarity (0-100) below which a link is listed for review
# Names second: a target with no settlement within RADIUS_KM is linked to a settlement up to
# NAME_RADIUS_KM away whose name matches it closely. SAC's coordinates for remote towns can be
# tens of kilometres off (INTA is printed 72 km from Inta).
NAME_RADIUS_KM = 75.0
NAME_LINK = 88
# Stretches of the alphabet whose entries are lost from the scan (data/curated/sac1956/README.md).
# The list runs alphabetically across countries, so a settlement of any country that links to no
# target and whose name falls in one of them has no label: it may have been on the lost page.
GAPS = [
    ("ARTSIZ", "ATBASAR", "the printed page after PDF page 9 is missing"),
    ("DROGOBYCH", "DUBNICE NAD VAHOM", "the foot of PDF page 64 is cut off"),
]


def load_targets() -> tuple[pd.DataFrame, pd.DataFrame]:
    cx = pd.read_csv(CURATED / "sac1956" / "complexes.csv", dtype={"priority": str, "ref": str})
    dgz = pd.read_csv(CURATED / "sac1956" / "dgz.csv")
    cx = cx[cx["lat"].notna()].copy()
    top = cx.set_index("id")
    cx["top_id"] = np.where(cx["level"] == "complex", cx["id"], cx["parent_id"])
    cx["top_priority"] = cx["top_id"].map(top["priority"])
    cx["top_tier"] = cx["top_id"].map(top["priority_tier"])
    cx["country_1956"] = cx["country"].map(sac_country)
    dgz = dgz.merge(
        cx[["id", "top_id", "country", "country_1956"]],
        left_on="complex_id",
        right_on="id",
        suffixes=("", "_cx"),
    )
    return cx, dgz


def in_gap(place: pd.Series) -> str:
    """Why the settlement's label is unknown ("" if it is known): one of its names sorts inside
    a stretch of the alphabet lost from the scan."""
    names = [place["name_1956"], *variants(place["name_ru"], text(place.get("notes")))]
    names.append(text(place.get("gn_name")))
    keys = {simple(to_latin(n)) for n in names if n}
    for lo, hi, why in GAPS:
        if any(simple(lo) < k < simple(hi) for k in keys):
            return why
    return ""


def name_score(sac_name: str, names: list[str]) -> float:
    target = simple(sac_name)
    return max((fuzz.ratio(target, n) for n in names if n), default=0.0)


def link(
    targets: pd.DataFrame, places: pd.DataFrame, index: Points, radius_km: float
) -> pd.DataFrame:
    """Each target to a settlement within `radius_km`: the best-named one if a name matches
    (NAME_OK or better), else the nearest. Targets with names: `name` column; DGZs: none."""
    out = targets.copy()
    lat, lon = out["lat"].to_numpy(), out["lon"].to_numpy()
    dist, idx = index.nearest(lat, lon)
    nearby = index.within(lat, lon, radius_km)
    names = [place_names(places.iloc[i]) for i in range(len(places))] if "name" in out else None
    place_ids, dists, scores = [], [], []
    for row, (cands, d0, i0) in enumerate(zip(nearby, dist[:, 0], idx[:, 0], strict=True)):
        if len(cands) == 0:
            place_ids.append(None), dists.append(d0), scores.append(np.nan)
            continue
        pick = i0
        score = np.nan
        if names is not None:
            scored = {c: name_score(out["name"].iat[row], names[c]) for c in cands}
            best = max(
                scored,
                key=lambda c: (
                    scored[c],
                    -haversine_km(lat[row], lon[row], places["lat"].iat[c], places["lon"].iat[c]),
                ),
            )
            pick = best if scored[best] >= NAME_OK else i0
            score = scored[pick]
        place_ids.append(places["place_id"].iat[pick])
        dists.append(
            float(
                haversine_km(lat[row], lon[row], places["lat"].iat[pick], places["lon"].iat[pick])
            )
        )
        scores.append(score)
    out["place_id"], out["dist_km"] = place_ids, np.round(dists, 2)
    if names is not None:
        out["name_score"] = scores
    return out


def link_names(links_cx: pd.DataFrame, located: pd.DataFrame, index: Points) -> None:
    """Names second: a complex with no settlement within the radius goes to a settlement up to
    NAME_RADIUS_KM away whose name matches it closely (in place)."""
    unlinked = links_cx.index[links_cx["place_id"].isna()]
    nearby = index.within(
        links_cx.loc[unlinked, "lat"], links_cx.loc[unlinked, "lon"], NAME_RADIUS_KM
    )
    all_names = {}
    for i, cands in zip(unlinked, nearby, strict=True):
        scored = []
        for c in cands:
            if c not in all_names:
                all_names[c] = place_names(located.iloc[c])
            scored.append((name_score(links_cx.at[i, "name"], all_names[c]), c))
        if scored and max(scored)[0] >= NAME_LINK:
            score, c = max(scored)
            place = located.iloc[c]
            links_cx.loc[i, ["place_id", "name_score", "link_method"]] = [
                place["place_id"],
                score,
                "name",
            ]
            links_cx.loc[i, "dist_km"] = round(
                float(
                    haversine_km(
                        links_cx.at[i, "lat"], links_cx.at[i, "lon"], place["lat"], place["lon"]
                    )
                ),
                2,
            )


def build(radius_km: float = RADIUS_KM) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    cx_all, dgz_all = load_targets()
    parts_cx, parts_dgz = [], []
    for country in places["country_1956"].unique():
        located = places[places["has_coords"] & (places["country_1956"] == country)]
        located = located.reset_index(drop=True)
        index = Points(located["lat"].to_numpy(), located["lon"].to_numpy())
        cx = cx_all[cx_all["country_1956"] == country]
        links_cx = link(cx, located, index, radius_km)
        links_cx["link_method"] = np.where(links_cx["place_id"].notna(), "coordinates", "")
        link_names(links_cx, located, index)
        parts_cx.append(links_cx)
        parts_dgz.append(
            link(dgz_all[dgz_all["country_1956"] == country], located, index, radius_km)
        )
    links_cx = pd.concat(parts_cx)
    links_dgz = pd.concat(parts_dgz)
    located = places[places["has_coords"]]

    # Labels per settlement.
    g = links_cx[links_cx["place_id"].notna()].groupby("place_id")
    top = links_cx[(links_cx["level"] == "complex") & links_cx["place_id"].notna()]
    top_prio = top.assign(p=top["priority"].str.rstrip("A").astype(float)).groupby("place_id")
    labels = pd.DataFrame(index=places["place_id"])
    labels["n_complexes"] = g.apply(lambda d: (d["level"] == "complex").sum())
    labels["n_subcomplexes"] = g.apply(lambda d: (d["level"] == "subcomplex").sum())
    labels["n_installations"] = g["n_installations"].sum()
    labels["n_population_lines"] = g["n_population"].sum()
    labels["n_dgz"] = g["n_dgz"].sum()  # the DGZs of the settlement's own complexes (T2)
    labels["n_dgz_points_near"] = (
        links_dgz[links_dgz["place_id"].notna()].groupby("place_id").size()
    )
    labels["best_priority"] = top_prio["p"].min()
    labels["best_tier"] = top_prio["priority_tier"].min()
    labels["parent_priority"] = g["top_priority"].apply(
        lambda s: pd.to_numeric(s.str.rstrip("A"), errors="coerce").min()
    )
    labels["sac_names"] = g["name_printed"].apply(lambda s: "; ".join(sorted(set(s))))
    labels = labels.fillna(
        {
            c: 0
            for c in [
                "n_complexes",
                "n_subcomplexes",
                "n_installations",
                "n_population_lines",
                "n_dgz",
                "n_dgz_points_near",
            ]
        }
    )
    # T1, main: the settlement has an entry of its own, a complex or a sub-complex. A DGZ of a
    # big complex that happens to lie nearer a suburb (Zaton by Barnaul) does not make the suburb
    # a target; it stays with its complex.
    labels["listed"] = (labels["n_complexes"] + labels["n_subcomplexes"]) > 0
    labels["label_gap"] = [
        "" if listed else in_gap(place)
        for listed, (_, place) in zip(labels["listed"], places.iterrows(), strict=True)
    ]
    labels["has_dgz"] = labels["n_dgz"] > 0  # T1, variant: given at least one aim point
    labels = labels.reset_index()

    report = pd.concat(
        [
            links_cx[links_cx["place_id"].isna()].assign(issue="no settlement within the radius"),
            links_cx[links_cx["name_score"] < NAME_OK].assign(issue="names disagree"),
            links_cx[links_cx["link_method"] == "name"].assign(
                issue="linked by name, coordinates far"
            ),
        ]
    )
    report = report.merge(
        located[["place_id", "name_1956", "name_ru", "gn_name", "pop"]],
        on="place_id",
        how="left",
    )
    cols = [
        "issue",
        "id",
        "country_1956",
        "level",
        "name_printed",
        "top_priority",
        "n_dgz",
        "n_installations",
        "lat",
        "lon",
        "dist_km",
        "link_method",
        "place_id",
        "name_1956",
        "gn_name",
        "pop",
        "name_score",
    ]
    report = report[cols].sort_values(
        ["issue", "top_priority"],
        key=lambda s: (
            pd.to_numeric(s.str.rstrip("A"), errors="coerce") if s.name == "top_priority" else s
        ),
    )
    links = pd.concat(
        [links_cx.assign(kind=links_cx["level"]), links_dgz.assign(kind="dgz")], ignore_index=True
    )
    return links, labels, report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Link SAC 1956 targets to places; write labels.")
    parser.add_argument("--radius-km", type=float, default=RADIUS_KM)
    args = parser.parse_args(argv)
    links, labels, report = build(args.radius_km)
    links.to_parquet(PROCESSED / "sac1956_links.parquet", index=False)
    labels.to_parquet(PROCESSED / "labels_sac1956.parquet", index=False)
    report.to_csv(PROCESSED / "sac1956_link_report.csv", index=False)
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    u = labels.merge(places[["place_id", "country_1956", "in_universe"]], on="place_id")
    u = u[u["in_universe"]]
    cx = links[links["kind"].isin(["complex", "subcomplex"])]
    dgz = links[links["kind"] == "dgz"]
    for country, c in cx.groupby("country_1956"):
        uc = u[u["country_1956"] == country]
        print(
            f"{country}: {len(c)} complexes and sub-complexes, "
            f"{(dgz['country_1956'] == country).sum()} DGZs; linked within {args.radius_km:g} km: "
            f"{c['place_id'].notna().mean():.1%} of complexes, "
            f"{dgz.loc[dgz['country_1956'] == country, 'place_id'].notna().mean():.1%} of DGZs; "
            f"universe {len(uc)}, listed {int(uc['listed'].sum())}, with a DGZ {int(uc['has_dgz'].sum())}"
        )
    print(
        f"review: {(report['issue'] == 'no settlement within the radius').sum()} unlinked, "
        f"{(report['issue'] == 'names disagree').sum()} name disagreements (sac1956_link_report.csv)"
    )


if __name__ == "__main__":
    main()
