#########################################################################
# ENVIRONMENT SETUP
#########################################################################

# Consistent shell behavior
SHELL := $(shell which bash)

# Enable parallel execution
MAKEFLAGS += --jobs
.NOTPARALLEL: install install-all update update-all  # These targets shouldn't run in parallel

# Variables
VENV := .venv
VENV_BIN := $(VENV)/bin
ACTIVATE_COMMAND := source $(VENV_BIN)/activate
ROOT_DIR := $(shell git rev-parse --show-toplevel)
SLUG := emsipi
MINIMUM_PYTHON_VERSION := 3.12
LATEST_STABLE_PYTHON_VERSION := $(shell uv python list | grep -E 'cpython-3\.[0-9]+\.[0-9]+[-|\+]' | head -n1 | cut -d'-' -f2 | cut -d'.' -f2)

# Python package includes Playwright
INCLUDES_PLAYWRIGHT := False

# Define common tool paths
UV := uv
NPX := npx --yes

# Define directory patterns for cleaning
CLEANUP_PATTERNS := __pycache__/ *.pyc *.pyo *.pyd .coverage htmlcov/ .pytest_cache/

# Define patterns to exclude from spell checking
SPELLCHECK_EXCLUDE_PATTERNS := site/ scratch/

# Define patterns to exclude from "fast" testing
# Needs to be written in a way that pytest understands
# (e.g. "not test_browser and not test_doc")
PYTEST_EXCLUDE_PATTERNS := "not integration"

# Markdownlint exclude patterns
# These are shell patterns, not markdownlint ones anymore
MDLINT_EXCLUDE_DIRS := ".venv" "scratch" "runs" "node_modules"

# Build the list of Markdown files, excluding symlinks and excluded dirs
MD_FILES := $(shell find . \
	-type d \( $(foreach dir,$(MDLINT_EXCLUDE_DIRS),-name $(dir) -o) -false \) -prune \
	-o -name '*.md' ! -type l -print)

# Checkable files
CHECKABLE_FILES := src/$(SLUG)/ $(shell find tests/ -name '*.py' -not -path 'tests/tmp/*' -not -path 'tests/fixtures/*') docs/

# Default target
.DEFAULT_GOAL := help
.PHONY: help
help: ## Display this help message
	@printf "Usage: make [target]\n\nTargets:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

#########################################################################
# TOOL VALIDATORS
#########################################################################

.PHONY: check-npx check-uv check-venv
check-npx: ## Check that npx is installed. If not, we tell the user to install it.
	@command -v npx >/dev/null 2>&1 || echo "We couldn't find npx. Please install it."

check-uv: ## Check that uv is installed. If not, we tell the user to install it.
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

check-venv: check-uv ## Ensure virtual environment exists and is up to date
	@if [ ! -d "$(VENV)" ]; then \
        echo "Creating virtual environment..."; \
        $(UV) venv; \
	fi

#########################################################################
# INSTALLATION
#########################################################################

.PHONY: install install-all update update-all
install: check-venv ## Install basic dependencies
	@echo "Installing dependencies..."
	@echo "If you want to install development dependencies, use `make install-dev`"
	@$(UV) sync
	@make maybe-playwright-install
	@echo "Installation complete. Run 'source $(VENV_BIN)/activate' to activate the environment"

install-all: check-venv ## Install all (including development) dependencies
	@echo "Installing all dependencies..."
	@$(UV) sync --all-groups
	@make maybe-playwright-install
	@$(UV) run pre-commit install -t pre-push
	@$(UV) run pre-commit install --install-hooks
	@echo "Installation complete. Run 'source $(VENV_BIN)/activate' to activate the environment"

update: check-venv ## Update dependencies
	@$(UV) sync -U
	@make maybe-playwright-install
	@echo "Update complete."

update-all: check-venv ## Update all (including development) dependencies
	@$(UV) sync -U --all-groups
	@make maybe-playwright-install
	@$(UV) run pre-commit install --install-hooks
	@echo "Update complete."

#########################################################################
# CLEANUP
#########################################################################

.PHONY: clean
clean: ## Remove generated files
	@echo "Cleaning project..."
	@for pattern in $(CLEANUP_PATTERNS); do \
		find . -name "$$pattern" -type d -exec rm -rf {} + 2>/dev/null || true & \
		find . -name "$$pattern" -type f -delete 2>/dev/null || true & \
	done
	wait

#########################################################################
# BASIC CODE QUALITY CHECKS
#########################################################################

.PHONY: ruff-check ruff-format mypy-check check
ruff-check: ## Run ruff checks
	@$(UV) run ruff check $(CHECKABLE_FILES)

ruff-format: ## Run ruff formatter
	@$(UV) run ruff format $(CHECKABLE_FILES)

mypy-check: ## Run mypy checks
	@$(UV) run mypy --check-untyped-defs --strict $(CHECKABLE_FILES) --ignore-missing-imports

check: ruff-check ruff-format mypy-check ## Run basic code quality checks in parallel

#########################################################################
# STRICT CHECKS
#########################################################################

.PHONY: check-strict-file-prep
.PHONY: check-strict-file-ruff check-strict-file-pyright check-strict-file-mypy
.PHONY: check-strict-file check-strict-all
check-strict-file-prep: ## Prepare config for strict file check
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter is required (e.g., make check-strict-file FILE=path/to/file)"; \
		exit 1; \
	fi
	@mkdir -p scratch
	@cp pyproject.toml scratch/pyproject.toml
	@cat ruff-strict.toml >> scratch/pyproject.toml

check-strict-file-ruff: check-strict-file-prep ## Run ruff on single file
	@$(UV) run ruff check --preview $(FILE) --config scratch/pyproject.toml

check-strict-file-pyright: check-strict-file-prep ## Run pyright on single file
	@$(UV) tool run basedpyright $(FILE)

check-strict-file-mypy: check-strict-file-prep ## Run mypy on single file
	@$(UV) run mypy --strict $(FILE)

check-strict-file: check-strict-file-prep ## Run strict checks on a single file in parallel
	@$(MAKE) -k -j3 check-strict-file-ruff check-strict-file-pyright check-strict-file-mypy
	@rm scratch/pyproject.toml

check-strict-all: ## Run strict checks on all files
	@$(MAKE) check-strict-file-prep FILE="$(CHECKABLE_FILES)"
	@$(MAKE) -j3 -k check-strict-file-ruff FILE="$(CHECKABLE_FILES)" check-strict-file-mypy check-strict-file-pyright FILE="$(CHECKABLE_FILES)"
	@rm scratch/pyproject.toml

###############################################################################
# TESTING
###############################################################################

.PHONY: check-dotenv test test-all test-verbose test-all-versions
check-dotenv: ## Check that the .env file exists
	@if [ ! -f ".env" ]; then \
		echo "Please create a .env file with the necessary environment variables."; exit 1; fi

test: ## Run basic tests
	@$(UV) run pytest -k $(PYTEST_EXCLUDE_PATTERNS)

test-verbose: ## Run verbose tests
	@$(UV) run pytest --log-cli-level=2 -k $(PYTEST_EXCLUDE_PATTERNS) -s -vv

test-all: check-dotenv ## Run all tests with coverage
	@$(UV) run --all-groups coverage run -m pytest --log-cli-level=2
	@$(UV) run --all-groups coverage combine
	@$(UV) run --all-groups coverage html --show-contexts

test-all-versions: check-venv ## Run tests with coverage for all supported Python versions
	@echo "Running tests across Python versions..."
	@MIN_VERSION=$$(echo $(MINIMUM_PYTHON_VERSION) | cut -d'.' -f2); \
	CURRENT_VERSION=$(LATEST_STABLE_PYTHON_VERSION); \
	echo "Testing Python versions from 3.$$MIN_VERSION to 3.$$CURRENT_VERSION"; \
	for version in $$(seq $$MIN_VERSION $$CURRENT_VERSION); do \
		echo "Testing Python 3.$$version..."; \
		$(UV) run --all-groups --python 3.$$version coverage run -p -m pytest --log-cli-level=2 || exit 1; \
	done
	@echo "Combining coverage reports..."
	@$(UV) run coverage combine
	@$(UV) run coverage html --show-contexts
	@echo "Coverage report generated in htmlcov/index.html"

#########################################################################
# SPELL CHECKS
#########################################################################

.PHONY: spell-check-py spell-check-md spell-check
spell-check-py: check-npx ## Run spell check on Python files
	$(NPX) cspell lint "**/*.py" \
		--exclude "$(SPELLCHECK_EXCLUDE_PATTERNS)"

spell-check-md: check-npx ## Run spell check on Markdown files
	$(NPX) cspell lint "**/*.md" \
		--exclude "$(SPELLCHECK_EXCLUDE_PATTERNS)"

spell-check: spell-check-py spell-check-md ## Run all spell checks in parallel

#########################################################################
# MARKDOWN CHECKS
#########################################################################

.PHONY: prettier-md markdownlint-md md-check
prettier-md: check-npx ## Format markdown files
	@$(NPX) prettier --write --prose-wrap always --print-width 80 \
		$(MD_FILES)

markdownlint-md: check-npx ## Lint markdown files
	@$(NPX) markdownlint-cli2 $(MD_FILES)

md-check: prettier-md markdownlint-md ## Check markdown files in parallel

#########################################################################
# DOCUMENTATION
#########################################################################

.PHONY: doc doc-serve
doc: check-npx ## Build documentation
	make md-check & \
	make spell-check & \
	wait && \
	$(UV) run mkdocs build

doc-serve: ## Serve documentation locally
	@$(UV) run mkdocs serve

#########################################################################
# ALL TASKS
#########################################################################

.PHONY: all
all: install-all check check-strict-all test-all doc update-all ## Run all main tasks

#########################################################################
# PLAYWRIGHT
#########################################################################

.PHONY: playwright-deps-ubuntu playwright-install maybe-playwright-install
playwright-deps-ubuntu: ## Install Playwright Ubuntu dependencies
	@echo "Installing Playwright Ubuntu dependencies..."
	@sudo apt-get update
	@sudo apt-get install -y \
        libwoff1 \
        libopus0 \
        libwebpdemux2 \
        libharfbuzz-icu0 \
        libenchant-2-2 \
        libhyphen0 \
        libflite1 \
        libegl1 \
        libglx0 \
        libgudev-1.0-0 \
        libevdev2 \
        libgles2 \
        libx264-dev

playwright-install: check-venv ## Install Playwright and its dependencies
	$(UV) add playwright && \
	$(UV) run playwright install --with-deps || \
		(echo "Playwright installation failed. Automated dependencies only available for Ubuntu." && exit 1)

maybe-playwright-install: ## Install Playwright if needed
	@if [ "$(INCLUDES_PLAYWRIGHT)" = "True" ]; then \
		make playwright-install; \
	fi
