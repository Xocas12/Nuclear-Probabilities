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
