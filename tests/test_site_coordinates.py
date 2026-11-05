"""The rule for site coordinates (data/curated/features/README.md, "Site coordinates"): the committed site tables
feed dated features, and no output under runs/ names a site or gives its coordinates. Town tables of 1956 may
carry a town's coordinate that a site placed on that town shares."""

import csv
import gzip

from nucprob.paths import CURATED, ROOT

FEATURES = CURATED / "features"
# table -> the column naming a site
SITE_TABLES = {
    "military_sites_1956.csv": "site",
    "bloc_air_defence_1956.csv": "site",
    "weurope_military_sites_1965.csv": "site",
    "sac_bases_1956.csv": "base",
}
# Per-town prediction tables of the 1956 places: a site placed on a town's own coordinate shows up there as
# that town's coordinate, which a historical label may keep.
TOWN_TABLES_1956 = {"runs/m1-slice/oof_predictions.csv", "runs/m2-check/oof_predictions.csv"}
TEXT = {".csv", ".gz", ".json", ".md", ".html", ".txt", ".yaml"}


def _sites() -> tuple[dict[tuple[str, str], str], set[str]]:
    pairs, names = {}, set()
    for table, column in SITE_TABLES.items():
        with open(FEATURES / table, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pairs[(row["lat"], row["lon"])] = table
                names.add(row[column])
    return pairs, names


def _outputs():
    for path in sorted((ROOT / "runs").rglob("*")):
        if path.is_file() and path.suffix in TEXT:
            data = path.read_bytes()
            if path.suffix == ".gz":
                data = gzip.decompress(data)
            yield path.relative_to(ROOT).as_posix(), data.decode("utf-8", errors="replace")


def test_no_output_gives_a_site_coordinate_except_a_1956_town_it_sits_on():
    pairs, _ = _sites()
    found = []
    for name, text in _outputs():
        for (lat, lon), table in pairs.items():
            if f"{lat},{lon}" in text or f"{lat}, {lon}" in text:
                if (
                    table.endswith("_1956.csv")
                    and table != "sac_bases_1956.csv"
                    and name in TOWN_TABLES_1956
                ):
                    continue
                found.append((name, table, lat, lon))
    assert not found, found[:10]


def test_the_viewer_and_the_report_name_no_site():
    _, names = _sites()
    pages = [
        ROOT / "runs" / "probmap" / "viewer" / "index.html",
        ROOT / "README.md",
        ROOT / "REPORT.md",
    ]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        named = sorted(n for n in names if len(n) > 6 and n in text)
        assert not named, (page.name, named[:10])


def test_the_rule_is_written_once_and_the_1985_card_points_to_it():
    readme = (FEATURES / "README.md").read_text(encoding="utf-8")
    assert "## Site coordinates" in readme
    card = (FEATURES / "us_military_sites_1985.md").read_text(encoding="utf-8")
    assert '"Site coordinates"' in card
    assert "section E of the brief" not in card


def test_no_per_town_score_map_is_committed():
    """The per-town pages of nucprob.viz.map are finer than the 0.5-degree cells a committed map may use, so git
    ignores them; the only committed map is the probability map's viewer."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "runs"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    assert [p for p in tracked if p.endswith("map.html")] == []
