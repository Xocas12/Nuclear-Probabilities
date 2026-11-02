"""Repository paths. Everything is resolved from the repository root, so modules can be run
from any working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"  # downloads, git-ignored (make data)
PROCESSED = DATA / "processed"  # places, labels, features, datasets; git-ignored, rebuilt
CURATED = DATA / "curated"  # small hand-built or transcribed tables, committed
SOURCES = DATA / "sources.yaml"
SOURCES_AMENDMENT_5 = DATA / "sources_amendment_5.yaml"  # feeds only that amendment's readings
REGISTRIES = (SOURCES, SOURCES_AMENDMENT_5)
OBTAINED = DATA / "sources_obtained.yaml"  # where held bytes came from, if not the publisher's url
RUNS = ROOT / "runs"
