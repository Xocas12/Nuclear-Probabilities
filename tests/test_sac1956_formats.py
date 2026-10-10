"""Line formats of the SAC 1956 transcription (scripts/sac1956_compare.py, sac1956_excerpts.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import sac1956_compare as cmp
import sac1956_excerpts as ex


def kind(page: str, text: str) -> tuple[str, dict]:
    typ, fields, _ = cmp.classify(page, cmp.norm(text), cmp.light(text))
    return typ, fields


def test_part2_aim_point_with_ba_mark():
    typ, f = kind("R009", "4045- 4351E R X")
    assert typ == "dgz" and f["label"] == "R" and f["ba"] == "X"
    typ, f = kind("C002", "5340-5339E B")
    assert typ == "dgz" and f["ba"] is None


def test_stray_marks_by_the_category_code():
    for text in ("245. 0103-0295", "336- 0168-0266", "-208 0323-0183"):
        typ, _ = kind("R011", text)
        assert typ == "installation", text
    assert kind("R011", "245. 0103-0295")[1]["cat"] == "245"


def test_msite_with_a_comma():
    typ, f = kind("R022", "NIZHNEYE SHAKHLOVO,M-58 5501-03715 QB")
    assert typ == "msite" and f["mnum"] == "58"


def test_cross_reference_rows():
    m = ex.XREF.match("5112 MONINO AF SEE 5570 NOGINSK")
    assert (m["ref"], m["name"], m["af"], m["see_ref"], m["see_name"]) == (
        "5112",
        "MONINO",
        "AF",
        "5570",
        "NOGINSK",
    )
    m = ex.XREF.match("5075 MOINESTI RUM SEE 1945 DARMANESTI RUM")
    assert m["name"] == "MOINESTI RUM" and m["af"] is None and m["see_name"] == "DARMANESTI RUM"
    m = ex.XREF.match("BELBEK AF")
    assert m["ref"] is None and m["name"] == "BELBEK" and m["af"] == "AF"


def test_wilson_interval_for_zero_errors():
    sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
    import sac1956_audit as au

    lo, hi = au.wilson(0, 743)
    assert lo < 1e-12 and 0.005 < hi < 0.0052
