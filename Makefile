.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv
venv: ## Create project virtualenv
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtualenv..."; \
		python3 -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
	else \
		echo "Virtual environment already exists at $(VENV)"; \
	fi

.PHONY: install
install: venv ## Install project dependencies
	@echo "Installing dependencies..."
	$(PIP) install -e .

.PHONY: install-dev
install-dev: install ## Install development dependencies
	@echo "Installing development dependencies..."
	$(PIP) install black isort ruff pytest pytest-cov

.PHONY: run
run: install ## Start Codeas application
	@echo "Starting Codeas..."
	$(PYTHON) -m streamlit run src/codeas/ui/🏠_Home.py

.PHONY: style
style: venv ## Format code with black, isort, and ruff
	@echo "Running code formatting..."
	@$(PIP) install black isort ruff > /dev/null 2>&1
	@echo "Running black..."
	@$(PYTHON) -m black .
	@echo "Running isort..."
	@$(PYTHON) -m isort .
	@echo "Running ruff..."
	@$(PYTHON) -m ruff check . --fix
	@echo "Code formatting complete!"

.PHONY: lint
lint: venv ## Run linting checks (black, isort, ruff)
	@echo "Running code quality checks..."
	@$(PYTHON) -m black --check .
	@$(PYTHON) -m isort --check-only .
	@$(PYTHON) -m ruff check .
	@echo "Linting complete!"

.PHONY: test
test: install-dev ## Run tests with pytest
	@echo "Running tests..."
	@$(PYTHON) -m pytest -v --cov=src/codeas

.PHONY: clean
clean: ## Clean up temporary files and caches
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	@echo "Cleanup complete!"

.PHONY: clean-venv
clean-venv: ## Remove virtual environment
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "Virtual environment removed!"

.PHONY: reset
reset: clean clean-venv ## Reset project (clean + remove venv)
	@echo "Project reset complete!"

.PHONY: help
help: ## Show this help message
	@echo "Codeas - CODEbase ASsistant"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install        Install dependencies and set up development environment"
	@echo "  make run           Start the Codeas application"
	@echo "  make style         Format all code"
	@echo "  make lint          Run code quality checks"
	@echo "  make test          Run test suite"
	@echo "  make clean         Clean up temporary files"
	@echo "  make reset         Full reset (remove venv and clean)"
