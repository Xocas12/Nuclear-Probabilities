"""The leakage guard (PLAN section 3.2, rules for features): nothing derived from a target list
may become a feature."""

import fnmatch
import re
from pathlib import Path

import yaml

from nucprob.features.registry import FEATURES
from nucprob.paths import CURATED, ROOT, SOURCES
from nucprob.sources import history
from nucprob.us1985.features import FEATURES as US_FEATURES

FEATURE_CODE = [
    *sorted((ROOT / "nucprob" / "features").glob("*.py")),
    ROOT / "nucprob" / "us1985" / "features.py",
    ROOT / "nucprob" / "us1985" / "places.py",
    ROOT / "nucprob" / "transfer" / "features.py",
    ROOT / "nucprob" / "transfer" / "places.py",
    ROOT / "nucprob" / "classifier" / "features.py",
    ROOT / "nucprob" / "classifier" / "state_features.py",
    *[ROOT / "nucprob" / "sources" / f"{m}.py" for m in ("terrain", "cshapes", "naturalearth")],
]
# What the label code reads or writes: the SAC transcription, its links and labels, and the label
# folder and any list in it by its file name.
LABEL_MARKERS = re.compile(
    r"sac1956|nucprob\.labels|labels_|dgz|complexes\.csv|installations|napb|cd_19|band_rank"
    r"|curated[/\"' ]+labels|(?:wp|us|nato|cd|fr|rec)_\d{4}_\w+"
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
            if ref.startswith("history:"):
                # A table read back from git history (nucprob.sources.history): it must be pinned
                # there, and it is held to the same rule as a curated table.
                path = Path(ref.removeprefix("history:"))
                assert path.as_posix() in {p.path for p in history.PINNED}, f"{name}: {path}"
                assert not LABEL_FOLDERS & set(path.parts), f"{name} reads a label transcription"
                continue
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


def test_a_feature_module_naming_a_warsaw_pact_list_fails_the_guard():
    """The markers catch a label file of any list, not only SAC's."""
    assert LABEL_MARKERS.search('_LEAK = "data/curated/labels/wp_1967_lato67.csv"')
    assert LABEL_MARKERS.search('Path("nato_1965_hu_wargame_mirror.csv")')
    assert not LABEL_MARKERS.search("log_km_to_sam = distance to a Nike site")


def test_the_feature_card_names_the_inputs_later_than_their_document():
    """REPORT ("Inputs later than the document") and the gazetteer card name population figures that
    postdate the document they serve. The classifier's feature card must not claim the contrary."""
    card = (ROOT / "data" / "FEATURES_CLASSIFIER.md").read_text()
    gazetteer = (CURATED / "gazetteer" / "README.md").read_text()
    assert "census at or before the document" not in card
    assert "No site table runs past its own date" not in card
    for later in ("1959 census", "1960", "1961", "Kurchatov", "1990"):
        assert later in card, later
    assert "Kurchatov has only a 1990 figure" in gazetteer
    assert "censuses of 1941, 1949, 1960" in gazetteer
