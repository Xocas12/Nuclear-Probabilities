"""The transfer check's military distances: missing where no table covers a town, and never
scored as if they were 0 km (issue #9)."""

import numpy as np
import pandas as pd
import pytest

from nucprob.paths import CURATED
from nucprob.transfer import check
from nucprob.transfer.features import COMMON, MILITARY_GROUPS, military
from nucprob.transfer.regions import REGIONS

MIL = list(MILITARY_GROUPS)
PLUS = "LightGBM, common + military"


def fixture(tmp_path):
    """A bloc where nearness to a naval base drives the label; a UK list with distances
    (some 0 km) and a US list with none."""
    rng = np.random.default_rng(0)
    n = 600
    bloc = pd.DataFrame(rng.normal(size=(n, len(COMMON))), columns=COMMON)
    for c in MIL:
        bloc[c] = rng.uniform(0, 3, n)
    bloc["listed"] = (bloc["log_km_to_naval_base"] < 0.8).astype(float)
    bloc["place_id"] = [f"bloc:{i}" for i in range(n)]
    bloc["country_1956"] = rng.choice(["USSR", "Poland", "GDR"], n)
    bloc["sealed"] = False
    bloc.to_parquet(tmp_path / "dataset_sac1956.parquet", index=False)

    towns = []
    for region, country, k in (("uk_1980", "UK", 40), ("usa_1955", "USA", 40)):
        t = pd.DataFrame(rng.normal(size=(k, len(COMMON))), columns=COMMON)
        for c in MIL:
            t[c] = rng.uniform(0, 3, k) if region == "uk_1980" else np.nan
        if region == "uk_1980":
            t.loc[:9, MIL] = 0.0
        t["place_id"] = [f"{region}:{country}:{i}" for i in range(k)]
        t["region"] = region
        t["country"] = country
        towns.append(t)
    feats = pd.concat(towns, ignore_index=True)
    feats.to_parquet(tmp_path / "features_transfer.parquet", index=False)

    plan = {"uk_1980": "cd_1980_square_leg", "usa_1955": "cd_1955_operation_alert"}
    labels = feats[["place_id", "region"]].assign(
        plan_id=feats["region"].map(plan),
        n_targets=0,
        listed=([1, 0, 0, 1] * (len(feats) // 4)),
    )
    labels.to_parquet(tmp_path / "labels_transfer.parquet", index=False)


@pytest.fixture
def run(tmp_path, monkeypatch):
    fixture(tmp_path)
    monkeypatch.setattr(check, "PROCESSED", tmp_path)
    monkeypatch.setattr(check, "OUT", tmp_path / "out")
    check.main()
    scores = pd.read_csv(tmp_path / "out" / "scores.csv")
    table = pd.read_csv(tmp_path / "out" / "metrics.csv")
    return scores, table


def test_9_nan_military_distance_is_not_scored_as_0_km(run):
    scores, table = run
    us = scores[scores["region"] == "usa_1955"]
    uk = scores[scores["region"] == "uk_1980"]
    # Before the fix every US town got the 0 km score: the bloc has no missing distance, so
    # LightGBM routes NaN down the 0 km branch.
    assert us[PLUS].isna().all()
    assert uk[PLUS].notna().all()
    # The models without military distances still score the US towns.
    assert us["LightGBM, common"].notna().all()
    row = table[(table["plan_id"] == "cd_1955_operation_alert") & (table["model"] == PLUS)]
    assert row[["pr_auc", "roc_auc"]].isna().all(axis=None)
    row = table[(table["plan_id"] == "cd_1980_square_leg") & (table["model"] == PLUS)]
    assert row[["pr_auc", "roc_auc"]].notna().all(axis=None)


def test_9_italian_towns_outside_the_table_scope_have_no_military_distances():
    p = pd.DataFrame(
        {
            "region": "wp_west_1965",
            "country": ["Italy", "Italy", "Italy", "Italy", "Austria"],
            "admin1": ["Taranto", "Roma", "Venezia", "Novara", "Wien"],
            "lat": [40.47, 41.89, 45.44, 45.45, 48.21],
            "lon": [17.24, 12.48, 12.33, 8.62, 16.37],
        }
    )
    d = military(p)
    assert d.loc[[0, 1]].isna().all(axis=None)  # Taranto and Rome: south of the Po
    assert d.loc[[2, 3, 4]].notna().all(axis=None)  # Venice, Novara, Vienna: covered


def test_9_italian_scope_is_the_documented_regions():
    """Lombardy, Veneto, Friuli-Venezia Giulia, Trentino-Alto Adige and Novara
    (weurope_military_sites_1965.md), as the 1961 provinces of the Italian town table."""
    towns = pd.read_csv(CURATED / "gazetteer" / "towns_it_1961.csv", keep_default_na=False)
    region = towns["notes"].str.extract(r"region ([^;]+)")[0]
    covered = {"Lombardia", "Veneto", "Friuli-Venezia Giulia", "Trentino-Alto Adige"}
    expected = set(towns.loc[region.isin(covered), "admin1"]) | {"Novara"}
    scope = REGIONS["wp_west_1965"].military_scope["Italy"]
    assert set(scope) == expected
    card = (CURATED / "features" / "weurope_military_sites_1965.md").read_text(encoding="utf-8")
    assert "north of the Po" in card
