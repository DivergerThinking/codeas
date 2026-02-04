.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv
venv: ## Create project virtualenv
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtualenv..." && \
		python3 -m venv $(VENV) && \
		$(PIP) install --upgrade pip; \
	fi

install: venv ## Install project dependencies
	@echo "Installing dependencies..." && \
	$(PIP) install -e .

install-dev: venv ## Installs development tools
	@echo "Installing development tools..." && \
	$(PIP) install pre-commit black isort ruff

run: install ## Start Codeas application (installs dependencies first)
	@echo "Starting Codeas..." && \
	$(PYTHON) -m streamlit run src/codeas/ui/🏠_Home.py

pre-commit: install-dev ## Installs and configures pre-commit hooks
	@echo "Installing pre-commit..." && \
	$(PIP) install pre-commit && \
	$(VENV)/bin/pre-commit install

style: venv ## Formats code with black, isort, and ruff
	@echo "Installing style tools..." && \
	$(PIP) install black isort ruff && \
	@echo "Run black" && \
	$(VENV)/bin/black . && \
	@echo "Run isort" && \
	$(VENV)/bin/isort . && \
	@echo "Run ruff" && \
	$(VENV)/bin/ruff check . --fix

help: ## Show this help
	@echo "Usage: make [target]\n"
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'