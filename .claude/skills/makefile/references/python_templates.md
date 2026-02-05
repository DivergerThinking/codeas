# Python Makefile Templates

This file contains professional Makefile templates for Python projects.

## Basic Python Project Template

```makefile
# Project configuration
PROJECT_NAME := my_project
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP_VENV := $(VENV_BIN)/pip

# Source directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs

# Phony targets
.PHONY: all clean install test lint format help venv

# Default target
all: install lint test

# Help target
help:
	@echo "Available targets:"
	@echo "  make install   - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linters"
	@echo "  make format    - Format code"
	@echo "  make clean     - Remove generated files"
	@echo "  make venv      - Create virtual environment"

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip setuptools wheel

# Install dependencies
install: venv
	$(PIP_VENV) install -r requirements.txt
	$(PIP_VENV) install -r requirements-dev.txt

# Run tests
test:
	$(PYTHON_VENV) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR)

# Run linters
lint:
	$(PYTHON_VENV) -m flake8 $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_VENV) -m pylint $(SRC_DIR)
	$(PYTHON_VENV) -m mypy $(SRC_DIR)

# Format code
format:
	$(PYTHON_VENV) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_VENV) -m isort $(SRC_DIR) $(TEST_DIR)

# Clean generated files
clean:
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
```

## Advanced Python Project Template (with Docker and CI)

```makefile
# Project configuration
PROJECT_NAME := my_advanced_project
PYTHON := python3
VENV := venv
DOCKER_IMAGE := $(PROJECT_NAME):latest

# Directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist

# Python executables
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP_VENV := $(VENV_BIN)/pip

# Test coverage threshold
COVERAGE_THRESHOLD := 80

.PHONY: all clean install test lint format docs build docker-build docker-run help

all: install lint test

help:
	@echo "Development targets:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run all linters"
	@echo "  make format        - Format code (black, isort)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo ""
	@echo "Build targets:"
	@echo "  make build         - Build package"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs          - Generate documentation"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove generated files"
	@echo "  make clean-all     - Remove all generated files including venv"

# Virtual environment
$(VENV_BIN)/activate: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip setuptools wheel
	$(PIP_VENV) install -r requirements.txt
	$(PIP_VENV) install -r requirements-dev.txt
	touch $(VENV_BIN)/activate

venv: $(VENV_BIN)/activate

# Install dependencies
install: venv
	@echo "✓ Dependencies installed"

# Run tests with coverage
test: venv
	$(PYTHON_VENV) -m pytest $(TEST_DIR) \
		-v \
		--cov=$(SRC_DIR) \
		--cov-report=html \
		--cov-report=term \
		--cov-fail-under=$(COVERAGE_THRESHOLD)

# Quick test (no coverage)
test-quick: venv
	$(PYTHON_VENV) -m pytest $(TEST_DIR) -v

# Run linters
lint: venv
	@echo "Running flake8..."
	$(PYTHON_VENV) -m flake8 $(SRC_DIR) $(TEST_DIR)
	@echo "Running pylint..."
	$(PYTHON_VENV) -m pylint $(SRC_DIR)
	@echo "✓ All linters passed"

# Type checking
type-check: venv
	$(PYTHON_VENV) -m mypy $(SRC_DIR) --strict

# Format code
format: venv
	$(PYTHON_VENV) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_VENV) -m isort $(SRC_DIR) $(TEST_DIR)
	@echo "✓ Code formatted"

# Check formatting without modifying
format-check: venv
	$(PYTHON_VENV) -m black --check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_VENV) -m isort --check-only $(SRC_DIR) $(TEST_DIR)

# Generate documentation
docs: venv
	cd $(DOCS_DIR) && $(PYTHON_VENV) -m sphinx-build -b html . _build/html

# Build package
build: venv
	$(PYTHON_VENV) -m build

# Docker targets
docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run:
	docker run -it --rm $(DOCKER_IMAGE)

# Clean generated files
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

clean-all: clean
	rm -rf $(VENV)

# CI/CD targets
ci: install lint type-check test
	@echo "✓ CI pipeline passed"
```

## Flask/FastAPI Web Application Template

```makefile
# Project configuration
PROJECT_NAME := my_web_app
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP_VENV := $(VENV_BIN)/pip

# Application settings
APP_MODULE := app.main:app
HOST := 0.0.0.0
PORT := 8000

.PHONY: all install dev run test lint format migrate help

all: install lint test

help:
	@echo "Development:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make run        - Run production server"
	@echo "  make shell      - Open interactive shell"
	@echo ""
	@echo "Database:"
	@echo "  make migrate    - Run database migrations"
	@echo "  make db-upgrade - Upgrade database"
	@echo "  make db-reset   - Reset database"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"

# Virtual environment and dependencies
$(VENV_BIN)/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip
	touch $(VENV_BIN)/activate

install: $(VENV_BIN)/activate
	$(PIP_VENV) install -r requirements.txt
	$(PIP_VENV) install -r requirements-dev.txt

# Development server
dev: install
	$(PYTHON_VENV) -m uvicorn $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

# Production server
run: install
	$(PYTHON_VENV) -m uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT)

# Interactive shell
shell: install
	$(PYTHON_VENV) -i -c "from app import *"

# Database migrations
migrate: install
	$(PYTHON_VENV) -m alembic revision --autogenerate

db-upgrade: install
	$(PYTHON_VENV) -m alembic upgrade head

db-reset: install
	$(PYTHON_VENV) -m alembic downgrade base
	$(PYTHON_VENV) -m alembic upgrade head

# Testing
test: install
	$(PYTHON_VENV) -m pytest tests/ -v --cov=app

# Code quality
lint: install
	$(PYTHON_VENV) -m flake8 app tests
	$(PYTHON_VENV) -m pylint app

format: install
	$(PYTHON_VENV) -m black app tests
	$(PYTHON_VENV) -m isort app tests

# Clean
clean:
	rm -rf $(VENV) .pytest_cache .coverage htmlcov .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

## Data Science / ML Project Template

```makefile
PROJECT_NAME := ml_project
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
JUPYTER := $(VENV_BIN)/jupyter

# Directories
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
MODELS_DIR := models
REPORTS_DIR := reports

.PHONY: all install notebook train evaluate report clean

all: install

help:
	@echo "Data Science targets:"
	@echo "  make notebook    - Start Jupyter notebook"
	@echo "  make train       - Train models"
	@echo "  make evaluate    - Evaluate models"
	@echo "  make report      - Generate report"
	@echo "  make clean-data  - Clean data directory"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

notebook: install
	$(JUPYTER) notebook --notebook-dir=$(NOTEBOOKS_DIR)

train: install
	$(PYTHON_VENV) scripts/train.py --data $(DATA_DIR) --output $(MODELS_DIR)

evaluate: install
	$(PYTHON_VENV) scripts/evaluate.py --models $(MODELS_DIR) --data $(DATA_DIR)

report: install
	$(PYTHON_VENV) scripts/generate_report.py --output $(REPORTS_DIR)

clean-data:
	rm -rf $(DATA_DIR)/processed/*
	rm -rf $(DATA_DIR)/interim/*

clean: clean-data
	rm -rf $(VENV) .pytest_cache .ipynb_checkpoints
	find . -type d -name "__pycache__" -exec rm -rf {} +
```
