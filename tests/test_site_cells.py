"""The nineteenth and twentieth amendments: every row of every site table is held at the centre of its 0.5-degree
cell, whatever its end year, with no coordinate text left in its row; the specification the 1965 table is built
from and the bloc table's hand rows hold no finer point either."""

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
    seen = ended = 0
    for table, end in TABLES.items():
        with open(FEATURES / table, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                seen += 1
                ended += bool(end is not None and row[end].strip())
                assert _on_centre(row["lat"]) and _on_centre(row["lon"]), (
                    table,
                    row["lat"],
                    row["lon"],
                )
                cells = [v for k, v in row.items() if k not in ("lat", "lon") and v]
                assert not any(COORD_TEXT.search(v) for v in cells), (table, row)
    assert seen > 750 and ended > 400


def test_the_row_specifications_hold_no_point_finer_than_a_cell():
    finer = re.compile(r"\d{1,3}\.\d{3,}|\d{1,3}°\s?\d{1,2}['′]|\b\d{1,3} \d{1,2} \d{1,2}[NS]\b")
    for path in (
        ROOT / "scripts" / "weurope_military_1965_spec.py",
        ROOT / "scripts" / "bloc_air_defence_1956" / "hand.py",
    ):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            assert not finer.search(line), (path.name, i, line.strip()[:80])


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


def test_no_hand_checked_link_sits_at_an_air_base_or_airport():
    """A label link is placed at what its document prints (a town, or an offset from one), not at the point of a
    facility the document does not locate that finely (twentieth amendment)."""
    with open(
        CURATED / "gazetteer" / "transfer_target_links.csv", encoding="utf-8", newline=""
    ) as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    for row in rows:
        assert not re.search(r"air ?base|airport|airfield", row["located_as"], re.I), row


def test_the_1985_specification_gives_only_cell_centres():
    """Review 23, finding 2: the one coordinate typed into the 1985 specification (Savannah River Plant) was
    finer than a cell."""
    spec = (ROOT / "scripts" / "us_military_1985_spec.py").read_text(encoding="utf-8")
    pairs = re.findall(r"\(\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\s*\)", spec)
    assert pairs
    for lat, lon in pairs:
        assert _on_centre(lat) and _on_centre(lon), (lat, lon)
