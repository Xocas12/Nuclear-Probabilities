"""The map of a run: one self-contained HTML page.

    python -m nucprob.viz.map [--run m2-check]

Reads the run (runs/<run>/), the dataset and the SAC links, and writes runs/<run>/map.html:
every settlement of the universe coloured by its out-of-fold P(target) (or by SAC's own list,
or by where the two disagree), the SAC entries themselves, and a card per settlement with its
features. Land and lake outlines come from Natural Earth; there are no borders, so no modern
ones. The page loads deck.gl from a CDN and carries its data inline.
"""

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.gazetteer.translit import to_latin
from nucprob.paths import PROCESSED, RAW, RUNS

TEMPLATE = Path(__file__).with_name("map.html")
BBOX = (5.0, 196.0, 10.0, 82.0)  # lon min, lon max (east of 180 for Chukotka), lat min, lat max
TARGETS = {"listed": "On the list", "has_dgz": "Given an aim point"}
MODELS = [
    "population rule",
    "logistic, all features",
    "LightGBM, all features",
    "LightGBM, no anachronisms",
]
# Features shown on a place's card: (feature, label, how to show it). "count" and "km" undo
# log10(1 + x); "flag" is yes/no; "m" is metres.
CARD = [
    ("regional_centre", "Regional centre (1956)", "flag"),
    ("republic_capital", "Republic capital", "flag"),
    ("log_vpk_total", "Defence establishments active in 1956", "count"),
    ("log_vpk_factories", "… of them factories", "count"),
    ("log_vpk_design", "… design bureaux and institutes", "count"),
    ("log_vpk_within_25km", "Defence establishments within 25 km", "count"),
    ("log_power_mw_25km", "Power (MW) commissioned by 1956, 25 km", "count"),
    ("military_district_hq", "Military district HQ (1956)", "flag"),
    ("log_km_to_lra_base", "To a long-range bomber base", "km"),
    ("log_km_to_naval_base", "To a naval base", "km"),
    ("log_km_to_nuclear_site", "To a nuclear-complex site", "km"),
    ("log_airfields_25km", "Airfields within 25 km (today's list)", "count"),
    ("rail_lines_5km", "Rail lines within 5 km", "raw"),
    ("log_km_to_rail", "To a railway", "km"),
    ("log_km_to_port", "To a seaport", "km"),
    ("log_km_to_major_river", "To a major river", "km"),
    ("log_km_to_coast", "To the sea", "km"),
    ("log_km_to_nato", "To NATO territory (1956)", "km"),
    ("log_km_to_frontier", "To the bloc's frontier", "km"),
    ("log_km_to_sac_base", "To the nearest SAC base", "km"),
    ("elevation_m", "Elevation", "m"),
]


def east(lon: float) -> float:
    """Longitudes west of -100 (Chukotka) continue east of 180, so the map does not split."""
    return lon + 360 if lon < -100 else lon


def outline(path: Path, decimals: int = 2) -> list[list[list[float]]]:
    """Polygon rings of a Natural Earth layer inside BBOX, rounded and thinned."""
    rings = []
    for feature in json.loads(path.read_text())["features"]:
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly[:1]:  # outer rings only
                # Natural Earth splits rings at 180°; a ring wholly west of -100° (Chukotka) moves
                # east of 180°, any other ring stays where it is.
                shift = 360 if max(x for x, _ in ring) < -100 else 0
                pts = [(round(x + shift, decimals), round(y, decimals)) for x, y in ring]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if max(xs) < BBOX[0] or min(xs) > BBOX[1] or max(ys) < BBOX[2] or min(ys) > BBOX[3]:
                    continue
                thin = [pts[0]] + [p for a, p in itertools.pairwise(pts) if p != a]
                if len(thin) >= 4:
                    rings.append([list(p) for p in thin])
    return rings


def clean(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def latin(name: str) -> str:
    """A readable Latin form of a Cyrillic name (other scripts are kept as they are)."""
    if any("а" <= ch.lower() <= "я" or ch in "іїєґўәғқңөұүһҷӣӯҳ" for ch in name):
        return to_latin(name).title()
    return name


def shown(value, how: str):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if how in ("count", "km"):
        return round(10**value - 1, 0 if how == "count" else 1)
    if how == "flag":
        return bool(value)
    return round(float(value), 0)


def payload(run: Path) -> dict:
    preds = pd.read_csv(run / "oof_predictions.csv")
    data = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    links = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    metrics = pd.read_csv(run / "metrics.csv")
    by_country = pd.read_csv(run / "by_country.csv")
    by_place = preds.set_index("place_id")
    entries = links[links["kind"].isin(["complex", "subcomplex"])]
    own = {pid: g for pid, g in entries.groupby("place_id")}
    places = []
    for _, r in data.iterrows():
        pid = r["place_id"]
        p = by_place.loc[pid] if pid in by_place.index else None
        mine = own.get(pid, entries.iloc[:0])
        places.append(
            {
                "id": pid,
                "name": r["name_1956"],
                "latin": latin(r["name_1956"]),
                "now": clean(r["gn_name"]),
                "country": r["country_1956"],
                "unit": str(r["unit_1956"]).title(),
                "lon": round(east(r["lon"]), 4),
                "lat": round(r["lat"], 4),
                "pop": int(r["pop"]),
                "year": int(r["pop_year"]),
                "listed": clean(r["listed"]),
                "has_dgz": clean(r["has_dgz"]),
                "p2": clean(r["part2_has_dgz"]),
                "sealed": bool(r["sealed"]),
                "gap": r["label_gap"] or None,
                "p": None
                if p is None
                else {t: [clean(round(float(p[f"{t}: {m}"]), 3)) for m in MODELS] for t in TARGETS},
                "f": [clean(shown(r[f], how)) for f, _, how in CARD],
                "sac": [
                    {
                        "name": e["name_printed"],
                        "level": e["level"],
                        "prio": clean(e["top_priority"]),
                        "dgz": int(e["n_dgz"]),
                        "inst": int(e["n_installations"]),
                        "km": clean(float(e["dist_km"])),
                        "how": e["link_method"],
                    }
                    for _, e in mine.iterrows()
                ],
            }
        )
    targets = [
        {
            "name": e["name_printed"],
            "level": e["level"],
            "prio": clean(e["top_priority"]),
            "dgz": int(e["n_dgz"]),
            "lon": round(east(e["lon"]), 4),
            "lat": round(e["lat"], 4),
            "linked": clean(e["place_id"]),
        }
        for _, e in entries.iterrows()
    ]
    spatial = metrics[metrics["scheme"] == "spatial blocks"].set_index(["target", "model"])
    random = metrics[metrics["scheme"] == "random"].set_index(["target", "model"])
    table = [
        {
            "target": t,
            "model": m,
            "pr_auc": round(spatial.at[(t, m), "pr_auc_mean"], 3),
            "pr_auc_sd": round(spatial.at[(t, m), "pr_auc_std"], 3),
            "roc_auc": round(spatial.at[(t, m), "roc_auc_mean"], 3),
            "p_at_k": round(spatial.at[(t, m), "precision_at_k_mean"], 3),
            "pr_auc_random": round(random.at[(t, m), "pr_auc_mean"], 3)
            if (t, m) in random.index
            else None,
            "base": round(spatial.at[(t, m), "base_rate"], 3),
        }
        for t in TARGETS
        for m in MODELS
    ]
    families = sorted(
        {
            m.split("population + ")[1]
            for m in spatial.index.get_level_values(1)
            if "population + " in m
        }
    )
    ablation = [
        {
            "target": t,
            "family": fam,
            "added": round(spatial.at[(t, f"LightGBM, population + {fam}"), "pr_auc_mean"], 3),
            "dropped": round(spatial.at[(t, f"LightGBM, all but {fam}"), "pr_auc_mean"], 3),
        }
        for t in TARGETS
        for fam in families
    ]
    reference = {
        t: {
            "population": round(spatial.at[(t, "LightGBM, population family"), "pr_auc_mean"], 3),
            "all": round(spatial.at[(t, "LightGBM, all features"), "pr_auc_mean"], 3),
        }
        for t in TARGETS
    }
    countries = [
        {
            "target": r["target"],
            "country": r["country"],
            "model": r["model"],
            "pr_auc": round(r["pr_auc"], 3),
            "base": round(r["base_rate"], 3),
            "n": int(r["n"]),
        }
        for _, r in by_country[by_country["model"].isin(MODELS)].iterrows()
    ]
    lon = data["lon"].map(east)
    return {
        "models": MODELS,
        "targets": TARGETS,
        "card": [label for _, label, _ in CARD],
        "card_how": [how for _, _, how in CARD],
        "places": places,
        "sac": targets,
        "metrics": table,
        "ablation": ablation,
        "reference": reference,
        "countries": countries,
        "bounds": [
            [float(lon.quantile(0.002)), float(data["lat"].quantile(0.002))],
            [float(lon.max()), float(data["lat"].quantile(0.998))],
        ],
        "land": outline(RAW / "naturalearth" / "ne_50m_land.geojson"),
        "lakes": [r for r in outline(RAW / "naturalearth" / "ne_50m_lakes.geojson") if len(r) > 12],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write the map of a run.")
    parser.add_argument("--run", default="m2-check")
    args = parser.parse_args(argv)
    run = RUNS / args.run
    data = json.dumps(payload(run), ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*DATA*/null", data)
    out = run / "map.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
