"""The rebuilt tables meet the issues' acceptance criteria: the committed record, and a recount
when the processed data are present."""

import pandas as pd
import pytest

from nucprob import qa
from nucprob.paths import PROCESSED


def test_committed_acceptance_table_passes():
    t = pd.read_csv(qa.OUT / "issues.csv")
    assert t["passes"].all(), t[~t["passes"]].to_string()
    assert {1, 3, 6, 7, 9, 10, 11} <= set(t["issue"])


@pytest.mark.skipif(
    not (PROCESSED / "features_transfer.parquet").exists(), reason="processed data not built"
)
def test_acceptance_table_recomputes():
    t = qa.table()
    assert t["passes"].all(), t[~t["passes"]].to_string()
