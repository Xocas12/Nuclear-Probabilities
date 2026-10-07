from pathlib import Path

from nucprob.sources import demoscope, popstat

FIXTURES = Path(__file__).parent / "fixtures"


def test_popstat_number():
    assert popstat.number("34,327") == 34327
    assert popstat.number("157,0") == 157000
    assert popstat.number("9,") == 9000
    assert popstat.number("1 034,0") == 1034000
    assert popstat.number("…") is None
    assert popstat.number("") is None


def test_popstat_parse():
    df = popstat.parse(FIXTURES / "popstat_sample.htm", "russia")
    assert list(df["name_ru"]) == ["Пермь", "Полазна"]
    assert set(df["region"]) == {"Пермский край"}
    perm = df.iloc[0]
    assert perm["is_city"] and not df.iloc[1]["is_city"]
    assert perm["pop_1939-01-17"] == 306000
    assert perm["pop_1959-01-15"] == 628600
    assert perm["notes"] == "до 1940 Пермь, 1940-1957 Молотов"
    assert "pop_2010'" not in df.columns  # estimates are skipped, censuses kept
    assert (
        df.iloc[1]["pop_1926-12-17"] is None
        or df.iloc[1]["pop_1926-12-17"] != df.iloc[1]["pop_1926-12-17"]
    )


def test_demoscope_parse():
    df = demoscope.parse(FIXTURES / "demoscope_sample.html")
    assert list(df["name_ru"]) == ["Ташкент", "Бухара", "Галаасия"]
    assert list(df["pop_1959"]) == [911930, 69254, 5001]
    assert df.iloc[1]["oblast"] == "Бухарская областъ"  # the source's typo is kept
    assert df.iloc[2]["status"] == "пгт" and df.iloc[2]["district_centre"]
    assert set(df["republic"]) == {"Узбекская ССР"}
