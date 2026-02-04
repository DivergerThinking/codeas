.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install run pre-commit style help
venv: ## Crea el virtualenv del proyecto
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtualenv..." && \
		python3 -m venv $(VENV) && \
		$(PIP) install --upgrade pip; \
	fi

install: venv ## Instala las dependencias del proyecto
	@echo "Installing dependencies..." && \
	$(PIP) install -e .

install-dev: venv ## Instala las dependencias de desarrollo (pre-commit, black, isort, ruff)
	@echo "Installing development tools..." && \
	$(PIP) install pre-commit black isort ruff

run: install ## Inicia la aplicación Codeas (instala dependencias primero)
	@echo "Starting Codeas..." && \
	$(PYTHON) -m streamlit run src/codeas/ui/🏠_Home.py

pre-commit: install-dev ## Instala y configura pre-commit hooks
	@echo "Configuring pre-commit hooks..." && \
	$(VENV)/bin/pre-commit install

style: install-dev ## Formatea el código con black, isort y ruff
	@echo "Running style tools..." && \
	echo "Run black" && \
	$(VENV)/bin/black . && \
	echo "Run isort" && \
	$(VENV)/bin/isort . && \
	echo "Run ruff" && \
	$(VENV)/bin/ruff check . --fix

help: ## Muestra esta ayuda
	@echo "Uso: make [target]\n"
	@echo "Targets disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'