import numpy as np
import pandas as pd

from nucprob.features.registry import FEATURES, by_family
from nucprob.model.check import ALL, MAIN, ablations


def test_ablations_cover_every_family_and_drop_anachronisms():
    models = ablations()
    families = set(by_family(ALL)) - {"population"}
    for fam in families:
        dropped = models[f"LightGBM, all but {fam}"][1]
        assert not set(dropped) & set(by_family(ALL)[fam])
        assert set(models[f"LightGBM, population + {fam}"][1]) >= set(by_family(ALL)["population"])
    clean = models["LightGBM, no anachronisms"][1]
    assert clean and not any(FEATURES[f].anachronism for f in clean)
    assert MAIN["population rule"][1] == ["log_pop"]


def test_population_baseline_has_a_country_term_and_every_family_is_scored_over_it():
    from nucprob.model.check import POP_COUNTRY, comparisons, controls, country_columns

    df = pd.DataFrame({"country_1956": ["USSR", "East Germany", "USSR", "China"]})
    df, country = country_columns(df)
    assert country == ["country_china", "country_east_germany", "country_ussr"]
    assert df["country_east_germany"].tolist() == [0.0, 1.0, 0.0, 0.0]
    models = controls(country)
    assert models["population rule + country"][1] == ["log_pop", *country]
    population = by_family(ALL)["population"]
    assert models[POP_COUNTRY][1] == population + country
    scored = {(m, b) for _, m, b in comparisons()}
    for fam in set(by_family(ALL)) - {"population"}:
        cols = models[f"LightGBM, population + country + {fam}"][1]
        assert set(cols) >= set(population) | set(country) | set(by_family(ALL)[fam])
        assert (f"LightGBM, population + country + {fam}", POP_COUNTRY) in scored
    assert ("population rule + country", "population rule") in scored


def test_geography_is_also_scored_over_a_location_only_control():
    from nucprob.model.check import POP_LOCATION, comparisons, controls

    models = controls([])
    population = by_family(ALL)["population"]
    assert models[POP_LOCATION][1] == [*population, "lat", "lon"]
    geo = models["LightGBM, population + location + geography"][1]
    assert geo == [*population, "lat", "lon", *by_family(ALL)["geography"]]
    assert ("LightGBM, population + location + geography", POP_LOCATION) in {
        (m, b) for _, m, b in comparisons()
    }


def test_within_country_pr_auc_scores_each_country_on_its_own():
    from nucprob.model.check import MIN_CLASS, within_country

    # Inside each country the score ranks perfectly, but country B's scores sit below
    # country A's, so pooled the ranking is poor; the third country is too small to score.
    n = MIN_CLASS
    y = np.r_[np.ones(n), np.zeros(n), np.ones(2 * n), np.zeros(n), [1, 0]]
    p = np.r_[np.full(n, 0.4), np.full(n, 0.3), np.full(2 * n, 0.2), np.full(n, 0.1), [0.5, 0.5]]
    c = np.array(["A"] * 2 * n + ["B"] * 3 * n + ["C"] * 2)
    score, scored = within_country(y, p, c)
    assert scored == 2
    assert score == 1.0
    none, scored = within_country(y[: n + 1], p[: n + 1], c[: n + 1])
    assert scored == 0 and np.isnan(none)


def synthetic_bloc(seed: int = 0) -> pd.DataFrame:
    """Three countries with the same sizes but very different listing rates at a given size."""
    rng = np.random.default_rng(seed)
    parts = []
    for name, (lat0, lon0), intercept in [
        ("USSR", (55.0, 40.0), -1.5),
        ("East Germany", (52.0, 12.0), 1.5),
        ("China", (35.0, 110.0), -3.0),
    ]:
        n = 400
        log_pop = rng.normal(4.5, 0.4, n)
        logit = intercept + 3.0 * (log_pop - 4.5)
        listed = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(float)
        parts.append(
            pd.DataFrame(
                {
                    "country_1956": name,
                    "lat": lat0 + rng.uniform(-6, 6, n),
                    "lon": lon0 + rng.uniform(-10, 10, n),
                    "log_pop": log_pop,
                    "listed": listed,
                    "has_dgz": listed * (rng.random(n) < 0.6),
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def test_check_reports_the_country_gain_pooled_and_within_country():
    from nucprob.model.check import RULE_COUNTRY, country_columns, evaluate
    from nucprob.model.zoo import logistic

    df, country = country_columns(synthetic_bloc())
    models = {
        "population rule": (logistic, ["log_pop"]),
        RULE_COUNTRY: (logistic, ["log_pop", *country]),
    }
    table, gains, _, _ = evaluate(df, models)
    spatial = table[table["scheme"] == "spatial blocks"]
    assert spatial["within_country_pr_auc"].notna().all()
    assert spatial["pooled_oof_pr_auc"].notna().all()
    assert table.loc[table["scheme"] == "random", "within_country_pr_auc"].isna().all()
    g = gains.set_index(["target", "comparison"]).loc[
        ("listed", "country term over the population rule")
    ]
    # Pooled, a country intercept looks like a large gain over the population rule; inside
    # each country it ranks towns exactly as the rule does, so it adds next to nothing.
    assert g["gain_mean"] > 0.05
    assert g["pooled_oof_gain"] > 0.05
    assert abs(g["within_country_gain"]) < 0.01


def test_map_reads_families_from_the_ablations_only():
    from nucprob.viz.map import ablated_families

    models = [
        "population rule",
        "population rule + country",
        "LightGBM, population family",
        "LightGBM, population family + country",
        "LightGBM, all but geography",
        "LightGBM, population + geography",
        "LightGBM, population + country + geography",
        "LightGBM, population + location",
        "LightGBM, population + location + geography",
        "LightGBM, all but transport",
    ]
    assert ablated_families(models) == ["geography", "transport"]
