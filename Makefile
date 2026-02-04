.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv
venv: ## Crea el virtualenv del proyecto
	@echo "Creating virtualenv..." && \
	python3 -m venv $(VENV) && \
	$(PIP) install --upgrade pip

install: venv ## Instala las dependencias del proyecto
	@echo "Installing dependencies..." && \
	$(PIP) install -e .

run: install ## Inicia la aplicación Codeas (instala dependencias primero)
	@echo "Starting Codeas..." && \
	$(PYTHON) -m streamlit run src/codeas/ui/🏠_Home.py

pre-commit: venv ## Instala y configura pre-commit hooks
	@echo "Installing pre-commit..." && \
	$(PIP) install pre-commit && \
	$(VENV)/bin/pre-commit install

style: venv ## Formatea el código con black, isort y ruff
	@echo "Run black" && \
	$(VENV)/bin/black . && \
	echo "Run isort" && \
	$(VENV)/bin/isort . && \
	echo "Run ruff" && \
	$(VENV)/bin/ruff check . --fix

help: ## Muestra esta ayuda
	@echo "Uso: make [target]\n"
	@echo "Targets disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'