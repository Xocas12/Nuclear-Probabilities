import pandas as pd
import pytest

from nucprob.gazetteer.lookup import fold, loose
from nucprob.places_bloc import interpolate
from nucprob.sources.ddr import _clusters
from nucprob.sources.gus import VOIVODESHIP, figure


def test_gus_figures_survive_ocr_slips():
    assert figure(["1", "022,9"]) == 1022.9
    assert figure(["49", "3"]) == 49.3  # the comma lost
    assert figure(["120,C"]) == 120.0
    assert figure(["184.6"]) == 184.6
    assert figure(["X"]) is None


def test_gus_voivodeship_rows():
    assert VOIVODESHIP.match("Warszawskie") and VOIVODESHIP.match("Poznańskie (dok.)")
    assert VOIVODESHIP.match("Stalinogrodzkie")
    assert not VOIVODESHIP.match("Warszawa") and not VOIVODESHIP.match("Gorzów Wielkopolski")


def test_clusters_group_nearby_values():
    assert _clusters([10.0, 30.0, 11.5, 29.0], 2.0) == [[0, 2], [3, 1]]


def test_interpolation_to_the_study_date():
    # Growing from 100 to 200 over 1955-12-31 .. 1956-12-31: mid-June is about 1.45x.
    v = interpolate([100.0], [200.0], "1955-12-31", "1956-12-31").iloc[0]
    assert v == pytest.approx(100 * 2 ** (166 / 366), rel=0.01)
    # a missing first figure falls back on the second
    assert interpolate([None], [12100.0], "1950-12-03", "1956-12-31").iloc[0] == 12100.0


def test_folding_latin_letters():
    assert fold("Łódź") == "Lodz" and fold("Nyíregyháza") == "Nyiregyhaza"
    assert loose("Łódź") == loose("Lodz")
    assert loose("Großräschen") == loose("Grossraschen")


def test_east_german_parser_on_the_yearbook():
    from nucprob.sources import ddr

    if not ddr.page_path("0041").exists():
        pytest.skip("yearbook pages not downloaded")
    df = ddr.parse()
    assert len(df) == 214 and (df["name"] != "").all() and (df["bezirk"] != "").all()
    row = df.set_index("name").loc["Annaberg-Buchholz"]
    assert row["parts"] == 2 and row["pop_1939"] == 19278 + 8954
    assert pd.isna(df.set_index("name").at["Stalinstadt", "pop_1950"])
