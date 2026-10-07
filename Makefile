# nuclear-probabilities. Requires uv and GNU make. PLAN section 8.
UV ?= uv
PY = $(UV) run python

.PHONY: setup data places labels features dataset train map slice test lint format clean

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

train:
	$(PY) -m nucprob.model.slice

map:
	$(PY) -m nucprob.viz.slice_map

# Milestone M1, end to end on real data (PLAN section 9).
slice: places labels features dataset train map

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
