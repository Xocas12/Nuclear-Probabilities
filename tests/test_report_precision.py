"""The report's precision rule (review of bde7e54, finding 6): an estimate never prints with more decimals
than its interval supports, while a bound near zero keeps the decimals that show its side of zero."""

from nucprob.classifier.report import point, signed


def test_estimate_takes_the_coarser_bounds_decimals():
    assert point(-0.003, -0.11, 0.14) == "-0.00"
    assert point(-0.193, -0.41, 0.004) == "-0.19"
    assert point(0.021, 0.001, 0.04) == "+0.02"


def test_estimate_gets_more_decimals_only_when_both_bounds_need_them():
    assert point(-0.0003, -0.004, 0.003) == "-0.000"
    assert signed(-0.004) == "-0.004" and signed(0.003) == "+0.003"


def test_exact_zero_and_missing_bounds():
    assert point(0.0, -0.01, 0.01) == "0.00"
    assert point(0.1234, float("nan"), 0.2) == "+0.12"
