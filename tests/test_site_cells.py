"""The nineteenth amendment: every site that may be in use today (no recorded end year; every SAC base) is held at
the centre of its 0.5-degree cell, with no coordinate text left in its row."""

import csv
import re
import subprocess
import sys

from nucprob.paths import CURATED, ROOT

FEATURES = CURATED / "features"
TABLES = {
    "military_sites_1956.csv": "until_year",
    "bloc_air_defence_1956.csv": "until_year",
    "weurope_military_sites_1965.csv": "until_year",
    "sac_bases_1956.csv": None,
}
COORD_TEXT = re.compile(
    r"[Cc]oord\s*\||lat\s*=|\d{1,3}°\s?\d{1,2}['′]|\d{1,3}\.\d{3,}\s*[,/ ]\s*\d{1,3}\.\d{3,}"
)


def _on_centre(x: str) -> bool:
    return abs((float(x) * 2) % 1 - 0.5) < 1e-9


def test_possibly_present_sites_sit_on_cell_centres_with_no_coordinate_text():
    seen = 0
    for table, end in TABLES.items():
        with open(FEATURES / table, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if end is not None and row[end].strip():
                    continue
                seen += 1
                assert _on_centre(row["lat"]) and _on_centre(row["lon"]), (
                    table,
                    row["lat"],
                    row["lon"],
                )
                cells = [v for k, v in row.items() if k not in ("lat", "lon") and v]
                assert not any(COORD_TEXT.search(v) for v in cells), (table, row)
    assert seen > 250


def test_the_coarsening_script_finds_nothing_left_to_do():
    r = subprocess.run(
        [sys.executable, "-I", "scripts/coarsen_site_coordinates.py", "--check"],
        cwd=ROOT,
        capture_output=True,
    )
    assert r.returncode == 0, r.stdout.decode()


def test_the_czechoslovak_rows_cited_only_to_a_refusing_host_are_gone():
    text = (FEATURES / "military_sites_1956.csv").read_text(encoding="utf-8")
    assert "armedconflicts.com" not in text
    pages = (FEATURES / "cited_pages.csv").read_text(encoding="utf-8")
    assert "armedconflicts.com" not in pages
