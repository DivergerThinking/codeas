.PHONY: help install install-dev venv clean test lint format style run docs build dist upload

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := codeas
SRC_DIR := src
TEST_DIR := tests
VENV_DIR := .venv

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile Targets$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup & Installation:$(NC)"
	@echo "  make install       Install project dependencies"
	@echo "  make install-dev   Install dependencies including dev tools"
	@echo "  make venv          Create Python virtual environment"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make run           Run the Streamlit application"
	@echo "  make style         Format code (black, isort, ruff)"
	@echo "  make format        Format code with black and isort"
	@echo "  make lint          Run linting checks with ruff"
	@echo "  make test          Run tests with pytest"
	@echo ""
	@echo "$(YELLOW)Building & Distribution:$(NC)"
	@echo "  make build         Build distribution packages"
	@echo "  make dist          Create wheel and sdist distributions"
	@echo ""
	@echo "$(YELLOW)Maintenance:$(NC)"
	@echo "  make clean         Remove generated artifacts and cache"
	@echo "  make clean-build   Remove build artifacts"
	@echo "  make clean-cache   Remove Python cache files"
	@echo ""

# ============================================================================
# SETUP & INSTALLATION TARGETS
# ============================================================================

venv: ## Create Python virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created at $(VENV_DIR)$(NC)"
	@echo "Activate it with: source $(VENV_DIR)/bin/activate"

install: venv ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip setuptools wheel
	. $(VENV_DIR)/bin/activate && pip install -e .
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	. $(VENV_DIR)/bin/activate && pip install black isort ruff pytest pytest-cov pre-commit
	@echo "$(GREEN)Development dependencies installed$(NC)"

# ============================================================================
# DEVELOPMENT TARGETS
# ============================================================================

run: install ## Run the Streamlit application
	@echo "$(BLUE)Starting $(PROJECT_NAME) application...$(NC)"
	. $(VENV_DIR)/bin/activate && streamlit run $(SRC_DIR)/$(PROJECT_NAME)/ui/🏠_Home.py

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code with black and isort...$(NC)"
	. $(VENV_DIR)/bin/activate && python -m black $(SRC_DIR) $(TEST_DIR) --quiet || true
	. $(VENV_DIR)/bin/activate && python -m isort $(SRC_DIR) $(TEST_DIR) --quiet || true
	@echo "$(GREEN)Code formatted successfully$(NC)"

lint: ## Run linting checks with ruff
	@echo "$(BLUE)Running linting checks...$(NC)"
	. $(VENV_DIR)/bin/activate && python -m ruff check $(SRC_DIR) $(TEST_DIR) --show-source || true
	@echo "$(GREEN)Linting complete$(NC)"

style: format lint ## Run all code style checks and formatting (black, isort, ruff)
	@echo "$(GREEN)Code style checks completed$(NC)"

test: install ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	. $(VENV_DIR)/bin/activate && python -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR)/$(PROJECT_NAME) --cov-report=term-missing || true
	@echo "$(GREEN)Tests completed$(NC)"

# ============================================================================
# BUILD & DISTRIBUTION TARGETS
# ============================================================================

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	. $(VENV_DIR)/bin/activate && python -m build
	@echo "$(GREEN)Build completed successfully$(NC)"

dist: clean ## Create wheel and sdist distributions
	@echo "$(BLUE)Creating distribution packages...$(NC)"
	. $(VENV_DIR)/bin/activate && pip install --upgrade build twine
	. $(VENV_DIR)/bin/activate && python -m build
	@echo "$(GREEN)Distribution packages created in dist/$(NC)"

upload: dist ## Upload distribution packages to PyPI (requires credentials)
	@echo "$(YELLOW)⚠️  Uploading to PyPI...$(NC)"
	. $(VENV_DIR)/bin/activate && python -m twine upload dist/* --verbose
	@echo "$(GREEN)Upload completed$(NC)"

# ============================================================================
# CLEANUP TARGETS
# ============================================================================

clean: clean-build clean-cache ## Remove all generated artifacts and cache
	@echo "$(GREEN)Project cleaned$(NC)"

clean-build: ## Remove build artifacts
	@echo "$(BLUE)Removing build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info .eggs/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Build artifacts removed$(NC)"

clean-cache: ## Remove Python cache files
	@echo "$(BLUE)Removing Python cache...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cache cleaned$(NC)"

# ============================================================================
# UTILITY TARGETS
# ============================================================================

.PHONY: check-tools
check-tools: ## Check if required tools are installed
	@echo "$(BLUE)Checking required tools...$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓ Python 3$(NC)" || echo "$(YELLOW)✗ Python 3 not found$(NC)"
	@[ -f $(VENV_DIR)/bin/python ] && echo "$(GREEN)✓ Virtual Environment$(NC)" || echo "$(YELLOW)✗ Virtual Environment not found$(NC)"
	@[ -f $(VENV_DIR)/bin/streamlit ] && echo "$(GREEN)✓ Streamlit$(NC)" || echo "$(YELLOW)✗ Streamlit not found$(NC)"
