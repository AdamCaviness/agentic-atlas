# Agentic Workflow Atlas
# Run `make` or `make help` to list targets.

.DEFAULT_GOAL := help

VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF   := $(VENV)/bin/ruff
ATLAS  := $(VENV)/bin/atlas

# Overridable on the command line, e.g. make profile TARGET=/path JUDGE=manual
RUBRIC  ?= rubric/v1.0.0.yaml
TARGET  ?=
JUDGE   ?= none
ANSWERS ?=
FORMAT  ?= text

.PHONY: help setup install test check lint fmt format validate profile self-profile clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# Rebuild the environment whenever pyproject.toml changes.
$(VENV): pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -e ".[dev]"
	@touch $(VENV)
	@echo "environment ready. try: make test"

setup: $(VENV) ## Create the venv and install the package (editable) with dev deps

install: setup ## Alias for setup

test: setup ## Run the test suite
	$(PYTEST) -q

lint: setup ## Lint with ruff
	$(RUFF) check .

fmt: setup ## Format the code with ruff
	$(RUFF) format .

format: fmt ## Alias for fmt

check: lint test ## Lint then test (the CI gate)

validate: setup ## Validate the rubric against the schema (RUBRIC=...)
	$(ATLAS) validate $(RUBRIC)

profile: setup ## Profile a target: make profile TARGET=/path [JUDGE=manual ANSWERS=a.yaml FORMAT=md]
	@test -n "$(TARGET)" || { \
		echo "usage: make profile TARGET=/path/to/workflow [JUDGE=none|manual ANSWERS=file FORMAT=text|md|json]"; \
		exit 2; }
	$(ATLAS) profile "$(TARGET)" --rubric "$(RUBRIC)" --judge "$(JUDGE)" \
		$(if $(ANSWERS),--answers "$(ANSWERS)",) --format "$(FORMAT)"

self-profile: setup ## Profile agentic-toolkit as a quick smoke test (measured-only)
	$(ATLAS) profile ~/_opensource/agentic-toolkit --rubric $(RUBRIC) --judge none --format text

clean: ## Remove the venv, caches, and build artifacts
	rm -rf $(VENV) .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
