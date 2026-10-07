"""Repository paths. Everything is resolved from the repository root, so modules can be run
from any working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"  # downloads, git-ignored (make data)
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"  # places, labels, features, datasets; git-ignored, rebuilt
CURATED = DATA / "curated"  # small hand-built or transcribed tables, committed
SOURCES = DATA / "sources.yaml"
RUNS = ROOT / "runs"
