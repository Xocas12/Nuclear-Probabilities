# nuclear-probabilities. Requires uv and GNU make. PLAN section 8.
UV ?= uv
PY = $(UV) run python

.PHONY: us1985 setup data places labels features dataset train map check transfer evidence qa classifier probmap report viewer test test-full lint format clean

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

# The M2 check run (runs/m2-check/): every feature family, every bloc country with a universe. It is a
# historical record on the labels of its date, pinned in runs/milestone_hashes.json, and feeds no result;
# rerunning it overwrites that record, so these targets refuse unless RERUN_M2=1 is given.
train:
	@test "$(RERUN_M2)" = 1 || { echo "runs/m2-check is a pinned record; use RERUN_M2=1 to overwrite it"; exit 1; }
	$(PY) -m nucprob.model.check

map:
	@test "$(RERUN_M2)" = 1 || { echo "runs/m2-check is a pinned record; use RERUN_M2=1 to overwrite it"; exit 1; }
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
	$(PY) -m nucprob.sources.robots

# The pre-committed classifier (configs/protocol.yaml): global and per-state models, all holdouts.
classifier:
	$(PY) -m nucprob.classifier.table
	$(PY) -m nucprob.classifier.run
	$(PY) -m nucprob.classifier.sensitivity
	$(PY) -m nucprob.classifier.identification
	$(PY) -m nucprob.classifier.identification_fit
	$(PY) -m nucprob.classifier.divergence
	$(PY) -m nucprob.classifier.extended
	$(PY) -m nucprob.classifier.defence_targets
	$(PY) -m nucprob.classifier.link_audit

# P(area struck | stockpile scenario): configs/scenarios.yaml, the protocol's fourth amendment.
probmap:
	$(PY) -m nucprob.probmap.run

# REPORT.md, runs/classifier/TABLES.md and README's results, from the classifier's and the map's outputs:
# run after both, so that the map section describes this map run.
report:
	$(PY) -m nucprob.classifier.report

# The static viewer of the committed map: one self-contained page, runs/probmap/viewer/index.html.
viewer:
	$(PY) -m nucprob.probmap.viewer

# The check of FEMA's 1987 NAPB-90 risk bands on US counties (runs/m4-us-check/), a civil-defence reading outside
# the classifier: a check that the US features join, not a result.
# Its site table of 1985 is read back from git history (nucprob/sources/history.py), not from the tree.
# runs/m4-us-check/ is pinned, so the check writes runs/m4-us-check-rerun/ with a comparison against it.
us1985:
	$(PY) -m nucprob.sources.history
	$(PY) -m nucprob.us1985.places
	$(PY) -m nucprob.us1985.features
	$(PY) -m nucprob.us1985.dataset
	$(PY) -m nucprob.us1985.check --rerun

# A plain run skips the tests whose built tables (data/processed/, from data/raw/) are absent, and lists the skips.
test:
	$(UV) run pytest -q -rs

# The whole suite: builds the tables those tests read, then fails on any skip (tests/conftest.py). Needs data/raw/
# (`make data`) and the full git history.
test-full: places labels features dataset transfer evidence qa
	$(PY) -m nucprob.classifier.table
	NUCPROB_NO_SKIP=1 $(UV) run pytest -q -rs

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
