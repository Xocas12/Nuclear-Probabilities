"""The leakage guard (PLAN section 3.2, rules for features): nothing derived from a target list
may become a feature."""

import fnmatch
import re
from pathlib import Path

import yaml

from nucprob.features.registry import FEATURES
from nucprob.paths import CURATED, ROOT, SOURCES
from nucprob.us1985.features import FEATURES as US_FEATURES

FEATURE_CODE = [
    *sorted((ROOT / "nucprob" / "features").glob("*.py")),
    ROOT / "nucprob" / "us1985" / "features.py",
    ROOT / "nucprob" / "us1985" / "places.py",
    *[ROOT / "nucprob" / "sources" / f"{m}.py" for m in ("terrain", "cshapes", "naturalearth")],
]
# What the label code reads or writes: the SAC transcription, its links and labels.
LABEL_MARKERS = re.compile(
    r"sac1956|nucprob\.labels|labels_|dgz|complexes\.csv|installations|napb|cd_19|band_rank"
)
# Curated folders that hold label transcriptions.
LABEL_FOLDERS = {"sac1956", "napb90", "labels"}


def manifest() -> dict[str, dict]:
    return {s["id"]: s for s in yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]}


def test_every_source_has_a_role():
    roles = {s.get("role") for s in manifest().values()}
    assert roles <= {"labels", "universe", "features", "map"}
    assert None not in roles


def test_no_feature_reads_a_label_source():
    sources = manifest()
    for name, feature in [*FEATURES.items(), *US_FEATURES.items()]:
        assert feature.sources, f"{name} names no source"
        for ref in feature.sources:
            if ref.startswith("curated:"):
                path = CURATED / ref.removeprefix("curated:")
                assert path.exists(), f"{name}: {path} missing"
                assert not LABEL_FOLDERS & set(path.parts), f"{name} reads a label transcription"
                continue
            matched = fnmatch.filter(sources, ref)
            assert matched, f"{name}: source {ref} is not in data/sources.yaml"
            for sid in matched:
                assert sources[sid]["role"] != "labels", f"{name} uses label source {sid}"


def test_feature_code_does_not_touch_labels():
    for path in FEATURE_CODE:
        text = Path(path).read_text(encoding="utf-8")
        hits = LABEL_MARKERS.findall(text)
        assert not hits, f"{path.name} mentions {sorted(set(hits))}"
