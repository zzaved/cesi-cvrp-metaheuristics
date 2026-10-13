# Common tasks. Run `make help` for the list.
PYTHON ?= python3
CONFIG ?= experiments/config.yaml

.PHONY: help install test lint format notebooks benchmark analyze docs docs-build clean

help:
	@echo "install    Install the package and dev tools in editable mode"
	@echo "test       Run the test suite (includes the end to end smoke test)"
	@echo "lint       Run ruff on src, tests and experiments"
	@echo "format     Auto-format with ruff"
	@echo "notebooks  Execute every notebook in place"
	@echo "benchmark  Run experiments/run_benchmark.py on $(CONFIG)"
	@echo "analyze    Build tables and figures from results/*.csv"
	@echo "docs       Start the documentation site locally"
	@echo "docs-build Build the documentation site"

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests experiments

format:
	$(PYTHON) -m ruff format src tests experiments
	$(PYTHON) -m ruff check --fix src tests experiments

notebooks:
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

benchmark:
	$(PYTHON) experiments/run_benchmark.py --config $(CONFIG)

analyze:
	$(PYTHON) experiments/analyze.py --results results

docs:
	cd docs && npm install && npm start

docs-build:
	cd docs && npm ci && npm run build

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
