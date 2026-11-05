"""The report's precision rule: an estimate never prints with more decimals
than its interval supports, while a bound near zero keeps the decimals that show its side of zero."""

from nucprob.classifier.report import point, signed


def test_estimate_takes_the_coarser_bounds_decimals():
    assert point(-0.193, -0.41, 0.004) == "-0.19"
    assert point(-0.193, -0.41, 0.004) == "-0.19"
    assert point(0.021, 0.001, 0.04) == "+0.02"


def test_estimate_gets_more_decimals_only_when_both_bounds_need_them():
    assert point(-0.0003, -0.004, 0.003) == "-0.0003"
    assert signed(-0.004) == "-0.004" and signed(0.003) == "+0.003"


def test_exact_zero_and_missing_bounds():
    assert point(0.0, -0.01, 0.01) == "0.00"
    assert point(0.1234, float("nan"), 0.2) == "+0.12"


def test_an_estimate_near_zero_shows_its_sign_and_never_prints_as_minus_zero():
    """ "-0.00" was once printed."""
    assert point(-0.003, -0.11, 0.14) == "-0.003"
    for v in (-0.003, -0.0004, 0.0049, -0.00001):
        assert float(point(v, -0.2, 0.2)) != 0


def test_an_estimate_never_prints_equal_to_a_bound_it_differs_from():
    """Once "+0.01 [+0.004, +0.01]" for 0.0091 [0.0036, 0.0145]."""
    from nucprob.classifier.report import estimate_interval

    assert estimate_interval(0.0091, 0.0036, 0.0145) == ("+0.009", "+0.004", "+0.015")
    assert estimate_interval(0.021, 0.01, 0.03) == ("+0.02", "+0.01", "+0.03")
    est, lo, hi = estimate_interval(-0.0201, -0.0249, -0.0151)
    assert est not in (lo, hi)
