"""The report's precision rule for differences: two decimals for an estimate and its bounds alike (a bound moves by
about 0.005 between bootstrap seeds), and a sign that always gives the side of zero. An estimate within 0.005 of a
bound may print equal to it."""

import numpy as np

from nucprob.classifier.report import estimate_interval, point, signed


def test_a_difference_and_its_bounds_have_two_decimals():
    assert signed(0.0150) == "+0.01" and signed(-0.193) == "-0.19"
    assert point(0.0234) == "+0.02"
    assert estimate_interval(0.0391, 0.0136, 0.0645) == ("+0.04", "+0.01", "+0.06")


def test_a_value_near_zero_keeps_its_side_of_zero_in_its_sign():
    assert signed(0.003) == "+0.00" and signed(-0.0001) == "-0.00"
    assert signed(-0.0) == "-0.00"  # a CSV bound stored as -0.0000: negative, rounded to zero
    for v in (-0.0049, -0.00001, 0.0002, 0.0049):
        assert signed(v).startswith("+" if v > 0 else "-")
        assert np.sign(float(signed(v)) or v) == np.sign(v)


def test_an_exact_zero_has_no_sign():
    assert signed(0.0) == "0.00" and point(0.0) == "0.00"


def test_an_estimate_and_its_bounds_keep_two_decimals_even_where_they_print_alike():
    # No extra decimal where an estimate and a bound round alike: a bound moves by about 0.005 between seeds, so
    # a third decimal would show noise. The verdict is read from the unrounded bounds.
    assert estimate_interval(0.0121, 0.0098, 0.03) == ("+0.01", "+0.01", "+0.03")
    assert estimate_interval(0.0101, 0.0098, 0.03) == ("+0.01", "+0.01", "+0.03")
    assert estimate_interval(0.0, 0.0, 0.01) == ("0.00", "0.00", "+0.01")
    for v, lo, hi in [(0.0101, 0.0098, 0.03), (0.02, 0.0151, 0.0249), (-0.004, -0.0044, 0.001)]:
        assert all(len(x.split(".")[1]) == 2 for x in estimate_interval(v, lo, hi))
