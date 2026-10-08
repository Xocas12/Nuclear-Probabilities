# nuclear-probabilities. Requires uv and GNU make. PLAN section 8.
UV ?= uv
PY = $(UV) run python

.PHONY: setup data places labels features dataset train map check test lint format clean

setup:
	$(UV) sync --all-extras
	-$(UV) run pre-commit install

# Downloads into data/raw/ (git-ignored); every source is listed in data/sources.yaml.
data:
	$(PY) -m nucprob.sources.fetch

# The place universe (PLAN section 3.1): settlements, census populations, coordinates.
places:
	$(PY) -m nucprob.places

# Targets and labels from the transcribed SAC 1956 list (PLAN section 4.2).
labels:
	$(PY) -m nucprob.labels.sac1956

features:
	$(PY) -m nucprob.features

dataset:
	$(PY) -m nucprob.dataset

# The M2 check run (runs/m2-check/): every feature family, every bloc country with a universe.
train:
	$(PY) -m nucprob.model.check

map:
	$(PY) -m nucprob.viz.map --run m2-check

# Milestone M2, end to end (PLAN section 9). The M1 slice is kept in runs/m1-slice/ as run.
check: places labels features dataset train map

test:
	$(UV) run pytest -q

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
