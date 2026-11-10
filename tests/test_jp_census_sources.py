"""Every e-Stat volume that a row of towns_jp_1940.csv cites is registered in data/sources.yaml,
under a path named for that volume (review 23, finding 1: three of four volumes were unregistered and
the one entry gave the URL of one volume and the path of another)."""

import re

import pandas as pd
import yaml

from nucprob.paths import REGISTRIES, ROOT

TABLE = ROOT / "data" / "curated" / "gazetteer" / "towns_jp_1940.csv"


def test_every_cited_census_volume_is_registered_with_a_hash():
    cited = set(pd.read_csv(TABLE)["source_page"].str.extract(r"statInfId (\d+)")[0])
    assert cited and None not in cited
    sources = [
        s
        for path in REGISTRIES
        for s in yaml.safe_load(path.read_text(encoding="utf-8"))["sources"]
    ]
    for vol in cited:
        hits = [s for s in sources if s["path"] == f"japan/s15_{vol[-7:]}.pdf"]
        assert len(hits) == 1, vol
        src = hits[0]
        assert re.search(rf"statInfId={vol}\b", src["url"]), (vol, src["url"])
        assert re.fullmatch(r"[0-9a-f]{64}", src["sha256"]) and src["retrieved"], vol
