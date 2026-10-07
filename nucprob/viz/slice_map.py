"""The quick map of the slice (milestone M1): one self-contained HTML page.

    python -m nucprob.viz.slice_map

Reads the slice run (runs/m1-slice/), the dataset and the SAC links, and writes
runs/m1-slice/map.html: every settlement of the universe coloured by its out-of-fold
P(target) (or by SAC's own list, or by where the two disagree), the SAC entries themselves, and
a card per settlement. Land and lake outlines come from Natural Earth; there are no borders,
so no modern ones. The page loads deck.gl from a CDN and carries its data inline.
"""

import itertools
import json
import math
from pathlib import Path

import pandas as pd

from nucprob.gazetteer.translit import to_latin
from nucprob.model.zoo import MODELS
from nucprob.paths import PROCESSED, RAW, RUNS

RUN = RUNS / "m1-slice"
TEMPLATE = Path(__file__).with_name("slice_map.html")
BBOX = (12.0, 196.0, 30.0, 82.0)  # lon min, lon max (east of 180 for Chukotka), lat min, lat max
TARGETS = {"listed": "On the list", "has_dgz": "Given an aim point"}


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
    return value


def latin(name: str) -> str:
    """A readable Latin form of a Cyrillic name (other scripts are kept as they are)."""
    if any("а" <= ch.lower() <= "я" or ch in "іїєґўәғқңөұүһҷӣӯҳ" for ch in name):
        return to_latin(name).title()
    return name


def payload() -> dict:
    preds = pd.read_csv(RUN / "oof_predictions.csv", dtype={"label_gap": str})
    data = pd.read_parquet(PROCESSED / "dataset_ussr1959.parquet")
    links = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    metrics = pd.read_csv(RUN / "metrics.csv")
    models = list(MODELS)
    by_place = preds.set_index("place_id")
    entries = links[links["kind"].isin(["complex", "subcomplex"])]
    places = []
    for _, r in data.iterrows():
        pid = r["place_id"]
        p = by_place.loc[pid] if pid in by_place.index else None
        own = entries[entries["place_id"] == pid]
        places.append(
            {
                "id": pid,
                "name": r["name_1956"],
                "latin": latin(r["name_1956"]),
                "now": clean(r["gn_name"]),
                "rep": r["republic"].title(),
                "lon": round(east(r["lon"]), 4),
                "lat": round(r["lat"], 4),
                "pop": int(r["pop_1959"]),
                "listed": clean(r["listed"]),
                "has_dgz": clean(r["has_dgz"]),
                "sealed": bool(r["sealed"]),
                "gap": r["label_gap"] or None,
                "p": None
                if p is None
                else {t: [clean(round(float(p[f"{t}: {m}"]), 3)) for m in models] for t in TARGETS},
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
                    for _, e in own.iterrows()
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
    spatial = metrics[metrics["scheme"] == "spatial blocks"]
    random = metrics[metrics["scheme"] == "random"].set_index(["target", "model"])
    table = [
        {
            "target": m["target"],
            "model": m["model"],
            "pr_auc": round(m["pr_auc_mean"], 3),
            "pr_auc_sd": round(m["pr_auc_std"], 3),
            "roc_auc": round(m["roc_auc_mean"], 3),
            "p_at_k": round(m["precision_at_k_mean"], 3),
            "pr_auc_random": round(random.loc[(m["target"], m["model"]), "pr_auc_mean"], 3),
            "base": round(m["base_rate"], 3),
        }
        for _, m in spatial.iterrows()
    ]
    return {
        "models": models,
        "targets": TARGETS,
        "places": places,
        "sac": targets,
        "metrics": table,
        "land": outline(RAW / "naturalearth" / "ne_50m_land.geojson"),
        "lakes": [r for r in outline(RAW / "naturalearth" / "ne_50m_lakes.geojson") if len(r) > 12],
    }


def main() -> None:
    data = json.dumps(payload(), ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*DATA*/null", data)
    out = RUN / "map.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
