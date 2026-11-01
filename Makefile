# nuclear-probabilities. Requires uv and GNU make. PLAN section 8.
UV ?= uv
PY = $(UV) run python

.PHONY: setup data places labels features dataset train map check transfer evidence qa classifier probmap viewer test lint format clean

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

# The smaller lists: transfer universes, features, links and the check (runs/m4-transfer-check/).
transfer:
	$(PY) -m nucprob.transfer.places
	$(PY) -m nucprob.transfer.features
	$(PY) -m nucprob.transfer.labels
	$(PY) -m nucprob.transfer.check

# Evidence by attacker and the state-model gate (runs/evidence/), and the issues' acceptance
# checks against the rebuilt tables (runs/qa/).
evidence:
	$(PY) -m nucprob.plans

qa:
	$(PY) -m nucprob.qa

# The pre-committed classifier (configs/protocol.yaml): global and per-state models, all holdouts.
classifier:
	$(PY) -m nucprob.classifier.table
	$(PY) -m nucprob.classifier.run
	$(PY) -m nucprob.classifier.sensitivity
	$(PY) -m nucprob.classifier.report

# P(area struck | stockpile scenario): configs/scenarios.yaml, the protocol's fourth amendment.
probmap:
	$(PY) -m nucprob.probmap.run

# The static viewer of the committed map: one self-contained page, runs/probmap/viewer/index.html.
viewer:
	$(PY) -m nucprob.probmap.viewer

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
