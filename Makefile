.PHONY: install install-dev lint format test validate e2e help

PYTHON ?= python

help:
	@echo "Targets: install install-dev lint format test validate e2e"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	$(PYTHON) -m ruff check scripts tests config/scrapers
	$(PYTHON) -m ruff format --check scripts tests config/scrapers
	$(PYTHON) -m compileall -q scripts config/scrapers

format:
	$(PYTHON) -m ruff check --fix scripts tests config/scrapers
	$(PYTHON) -m ruff format scripts tests config/scrapers

test:
	$(PYTHON) -m pytest -q

validate:
	$(PYTHON) scripts/validate_data.py

e2e:
	$(PYTHON) -m pytest tests/test_refresh_catalog.py -q
