SHELL := /bin/bash
PYTHON := .venv/bin/python
PIP_STAMP := .venv/.pip-upgraded
DEV_STAMP := .venv/.dev-deps-installed

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make install              Setup venv + dev deps + hunspell"
	@echo "  make install-dev          Install dev deps (pytest, coverage) into venv"
	@echo "  make dict-de              Download German dictionary to ~/Library/Spelling"
	@echo "  make run LETTERS=... MANDATORY=...   Run solver"
	@echo "  make test                 Run unit tests"
	@echo "  make coverage             Run tests + coverage"
	@echo "  make clean                Remove venv + caches"

.PHONY: venv
venv:
	@test -d .venv || python3 -m venv .venv
	@if [ ! -f "$(PIP_STAMP)" ]; then \
		$(PYTHON) -m ensurepip --upgrade >/dev/null 2>&1 || true; \
		$(PYTHON) -m pip install --upgrade pip >/dev/null; \
		touch "$(PIP_STAMP)"; \
	fi

.PHONY: install
install: venv
	@command -v brew >/dev/null || (echo "Homebrew required. Install from brew.sh"; exit 1)
	@brew list hunspell >/dev/null 2>&1 || brew install hunspell
	@if [ ! -f "$(DEV_STAMP)" ] || [ requirements-dev.txt -nt "$(DEV_STAMP)" ]; then \
		$(PYTHON) -m pip install -r requirements-dev.txt >/dev/null; \
		touch "$(DEV_STAMP)"; \
	fi
.PHONY: install-dev
install-dev: venv
	@if [ ! -f "$(DEV_STAMP)" ] || [ requirements-dev.txt -nt "$(DEV_STAMP)" ]; then \
		$(PYTHON) -m pip install -r requirements-dev.txt; \
		touch "$(DEV_STAMP)"; \
	fi

.PHONY: dict-de
dict-de:
	@command -v curl >/dev/null || (echo "curl missing"; exit 1)
	@mkdir -p ~/Library/Spelling
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/de/de_DE_frami.dic" \
	  -o ~/Library/Spelling/de_DE_frami.dic
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/de/de_DE_frami.aff" \
	  -o ~/Library/Spelling/de_DE_frami.aff
	@echo "Installed: ~/Library/Spelling/de_DE_frami.dic/.aff"

.PHONY: dict-fr
dict-fr:
	@command -v curl >/dev/null || (echo "curl missing"; exit 1)
	@mkdir -p ~/Library/Spelling
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/fr/fr_FR.dic" \
	  -o ~/Library/Spelling/fr_FR.dic
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/fr/fr_FR.aff" \
	  -o ~/Library/Spelling/fr_FR.aff
	@echo "Installed: ~/Library/Spelling/fr_FR.dic/.aff"

.PHONY: dict-en
dict-en:
	@command -v curl >/dev/null || (echo "curl missing"; exit 1)
	@mkdir -p ~/Library/Spelling
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/en/en_US.dic" \
	  -o ~/Library/Spelling/en_US.dic
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/en/en_US.aff" \
	  -o ~/Library/Spelling/en_US.aff
	@echo "Installed: ~/Library/Spelling/en_US.dic/.aff"

.PHONY: dict-es
dict-es:
	@command -v curl >/dev/null || (echo "curl missing"; exit 1)
	@mkdir -p ~/Library/Spelling
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/es/es_ES.dic" \
	  -o ~/Library/Spelling/es_ES.dic
	@curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/es/es_ES.aff" \
	  -o ~/Library/Spelling/es_ES.aff
	@echo "Installed: ~/Library/Spelling/es_ES.dic/.aff"

.PHONY: run
run: install
	@if [ -z "$(LETTERS)" ] || [ -z "$(MANDATORY)" ]; then \
		echo "Usage: make run LETTERS=aelnrst MANDATORY=e"; \
		exit 1; \
	fi
	@$(PYTHON) main.py "$(LETTERS)" "$(MANDATORY)"

.PHONY: test
test: install-dev
	@$(PYTHON) -m pytest

.PHONY: coverage
coverage: install-dev
	@$(PYTHON) -m pytest --cov=solver --cov-report=term-missing

.PHONY: clean
clean:
	@rm -rf .venv
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} \;
	@rm -rf .pytest_cache .coverage htmlcov