"""Acceptance checks of the open data issues, against the rebuilt tables.

    python -m nucprob.qa

Each row of runs/qa/issues.csv is one acceptance criterion of a GitHub issue, measured on
data/processed/ and the committed run outputs. tests/test_qa.py fails if a row does not pass, and
recomputes the table when the processed data are present. Issues #4, #5, #7 and #8 are also
covered by their own unit tests (test_model.py, test_sac1956_crossdoc.py, test_rank_floor.py,
test_transfer_paired.py).
"""

import pandas as pd

from nucprob.geo import haversine_km
from nucprob.paths import CURATED, PROCESSED, RUNS
from nucprob.transfer.features import MILITARY_GROUPS
from nucprob.transfer.regions import ITALY_NORTH_1961

OUT = RUNS / "qa"
# Issue #3's towns, with the point the issue gives or the SAC reference coordinates it prints.
TOWNS_3 = {
    ("East Germany", "Dessau"): (51.83, 12.25),
    ("Poland", "Sosnowiec"): (50.30, 19.17),
    ("China", "Anshan"): (41.12, 122.95),
    ("China", "Andong"): (40.13, 124.40),
    ("China", "Jinzhou"): (41.12, 121.10),
    ("China", "Suzhou"): (31.30, 120.62),
    ("China", "Datong"): (40.03, 113.25),
    ("China", "Huainan"): (32.63, 117.00),
    ("China", "Fuxin"): (42.02, 121.66),
    ("China", "Baotou"): (40.65, 109.84),
    ("China", "Liaoyang"): (41.27, 123.17),
}
CLOSED_6 = ("su-closed-ozersk", "su-closed-novouralsk", "su-closed-znamensk")
LAND_SEATS_11 = {"Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt", "Bregenz"}
KREIS_SEATS_10 = ("Wismar", "Weimar")


def check(issue: int, what: str, ok: bool, value: object) -> dict:
    return {"issue": issue, "criterion": what, "passes": bool(ok), "value": str(value)}


def issue_1() -> list[dict]:
    checks = pd.read_csv(CURATED / "sac1956" / "checks.csv", dtype=str, keep_default_na=False)
    text = checks.apply(lambda r: " ".join(r), axis=1)
    hits = int(text.str.contains("letter", case=False).sum())
    return [
        check(1, "checks.csv flags lines where a letter was struck for a digit", hits >= 4, hits)
    ]


def issue_3(places: pd.DataFrame) -> list[dict]:
    rows = []
    for (country, name), (lat, lon) in TOWNS_3.items():
        r = places[places["country_1956"].eq(country) & places["name_1956"].eq(name)]
        km = float(haversine_km(r["lat"].to_numpy(), r["lon"].to_numpy(), lat, lon).min())
        rows.append(
            check(3, f"{name} lies within 10 km of the real town", km <= 10, f"{km:.1f} km")
        )
    pc = pd.read_csv(PROCESSED / "places_1956_population_check.csv", keep_default_na=False)
    still = pc[pc["explanation"].eq("")]
    rows.append(
        check(3, "every population-check match is fixed or explained", still.empty, len(still))
    )
    return rows


def issue_6(places: pd.DataFrame, labels: pd.DataFrame) -> list[dict]:
    rows = []
    for pid in CLOSED_6:
        r = labels[labels["place_id"].eq(pid)].iloc[0]
        rows.append(
            check(6, f"{pid} is listed with an aim point", r["listed"] and r["has_dgz"], "")
        )
    verkh = places[places["name_ru"].eq("Верх-Нейвинский")].iloc[0]
    rows.append(
        check(
            6,
            "VERKHNE NEYVINSKIY no longer links to a row at Novouralsk's coordinates",
            verkh["geonameid"] == 1487504,
            int(verkh["geonameid"]),
        )
    )
    return rows


def issue_7(dataset: pd.DataFrame) -> list[dict]:
    means = dataset.groupby("country_1956")["pop_rank_pct"].mean()
    big = means[dataset.groupby("country_1956").size().ge(50)]
    spread = float(big.max() - big.min())
    return [
        check(
            7,
            "mean pop_rank_pct is about 0.5 in every large country",
            spread < 0.05,
            f"{spread:.3f}",
        )
    ]


def issue_9(features: pd.DataFrame) -> list[dict]:
    military = list(MILITARY_GROUPS)
    it = features[features["country"].eq("Italy")]
    outside = it[~it["admin1"].isin(ITALY_NORTH_1961)] if "admin1" in it else it.iloc[:0]
    no_table = features[features["region"].isin(["usa_1955", "canada_1956", "japan_1945"])]
    scores = pd.read_csv(RUNS / "m4-transfer-check" / "scores.csv")
    name = "LightGBM, common + military"
    unscored = scores[scores["region"].isin(["usa_1955", "canada_1956", "japan_1945"])][name]
    return [
        check(
            9,
            "no military distance for Italian towns outside the table's scope",
            len(outside) > 0 and outside[military].isna().all().all(),
            len(outside),
        ),
        check(
            9,
            "no military distance in the US, Canada or Japan",
            no_table[military].isna().all().all(),
            len(no_table),
        ),
        check(
            9,
            "no common + military score where no table covers the town",
            unscored.isna().all(),
            len(unscored),
        ),
    ]


def issue_10(dataset: pd.DataFrame) -> list[dict]:
    rows = []
    for name in KREIS_SEATS_10:
        v = dataset.loc[dataset["name_1956"].eq(name), "district_seat"]
        rows.append(check(10, f"{name} is a district seat", (v == 1).any(), v.tolist()))
    return rows


def issue_11(features: pd.DataFrame) -> list[dict]:
    au = features[features["country"].eq("Austria")]
    got = set(au.loc[au["regional_centre"].eq(1), "name"])
    missing = {s for s in LAND_SEATS_11 if not any(g.startswith(s) for g in got)}
    return [
        check(11, "the six Land capitals have regional_centre = 1", not missing, sorted(missing))
    ]


def table() -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    labels = pd.read_parquet(PROCESSED / "labels_sac1956.parquet")
    dataset = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    tp = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    tf = pd.read_parquet(PROCESSED / "features_transfer.parquet")
    keys = ["place_id", "region"]
    extra = [c for c in ("name", "admin1", "country") if c not in tf.columns]
    features = tf.merge(tp[[*keys, *extra]], on=keys, how="left")
    rows = [
        *issue_1(),
        *issue_3(places),
        *issue_6(places, labels),
        *issue_7(dataset),
        *issue_9(features),
        *issue_10(dataset),
        *issue_11(features),
    ]
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = table()
    t.to_csv(OUT / "issues.csv", index=False)
    print(t.to_string(index=False))
    print(f"{int(t['passes'].sum())} of {len(t)} pass")


if __name__ == "__main__":
    main()
