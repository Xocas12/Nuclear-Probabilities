"""The report's precision rule for differences: three decimals for an estimate and its bounds alike, a sign that
always gives the side of zero, and a fourth decimal only where an estimate would print equal to a bound it
differs from."""

import numpy as np

from nucprob.classifier.report import estimate_interval, point, signed


def test_a_difference_and_its_bounds_have_three_decimals():
    assert signed(0.0150) == "+0.015" and signed(-0.193) == "-0.193"
    assert point(0.0234, 0.0137, 0.0343) == "+0.023"
    assert estimate_interval(0.0091, 0.0036, 0.0145) == ("+0.009", "+0.004", "+0.015")


def test_a_value_near_zero_keeps_its_side_of_zero_in_its_sign():
    assert signed(0.0003) == "+0.000" and signed(-0.0001) == "-0.000"
    assert signed(-0.0) == "-0.000"  # a CSV bound stored as -0.0000: negative, rounded to zero
    for v in (-0.0004, -0.00001, 0.0002, 0.0049):
        assert signed(v).startswith("+" if v > 0 else "-")
        assert np.sign(float(signed(v)) or v) == np.sign(v)


def test_an_exact_zero_has_no_sign():
    assert signed(0.0) == "0.000" and point(0.0, -0.01, 0.01) == "0.000"


def test_an_estimate_never_prints_equal_to_a_bound_it_differs_from():
    est, lo, hi = estimate_interval(0.0101, 0.0098, 0.03)
    assert est not in (lo, hi) and (est, lo, hi) == ("+0.0101", "+0.0098", "+0.0300")
    assert estimate_interval(0.0201, 0.0249, 0.03) == ("+0.020", "+0.025", "+0.030")
