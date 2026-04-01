# ==========================================================================
# Justfile for google_adk_guide
#
# Usage:
#   just            # list commands
#   just ci         # run full CI locally
#   just test       # run tests
# ==========================================================================

# Always show commands if no recipe is given
default:
    @just --list

# -------------------------------------------------------------------------
# Helpers (private)
# -------------------------------------------------------------------------

_set_env:
    @echo "Using Python >= 3.11"
    @uv --version > /dev/null

# -------------------------------------------------------------------------
# Formatting & Linting
# -------------------------------------------------------------------------

fmt:
    @uv run --active ruff format src tests

lint:
    @uv run --active ruff check src tests

fix:
    @uv run --active ruff check --fix src tests



# -------------------------------------------------------------------------
# Type checking
# -------------------------------------------------------------------------

type:
    @uv run --active basedpyright

# -------------------------------------------------------------------------
# Testing
# -------------------------------------------------------------------------

test:
    @uv run --active pytest tests/ -v

test-parallel:
    @uv run --active pytest tests/ -v -n auto

coverage:
    @uv run --active pytest tests/ \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml

# -------------------------------------------------------------------------
# Pre-commit
# -------------------------------------------------------------------------

precommit-install:
    @uv run --active pre-commit install
    @uv run --active pre-commit install --hook-type pre-push

precommit:
    @uv run --active pre-commit run --all-files --verbose

# -------------------------------------------------------------------------
# Dependency management
# -------------------------------------------------------------------------

sync:
    @uv sync --extra dev --extra test

update:
    @uv lock --upgrade
    @uv sync --extra dev --extra test

# -------------------------------------------------------------------------
# Docs (optional)
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# Build & Publish
# -------------------------------------------------------------------------

build:
    @uv build

publish:
    @uv publish

# -------------------------------------------------------------------------
# Install all package dependencies
# -------------------------------------------------------------------------

install:
    @python -m pip install --upgrade pip
    @python -m pip install --upgrade uv
    just sync
    just precommit-install

# -------------------------------------------------------------------------
# Cleaning
# -------------------------------------------------------------------------

clean:
    @rm -rf build/ dist/ *.egg-info
    @rm -rf .pytest_cache .ruff_cache .coverage htmlcov
    @find . -type d -name "__pycache__" -exec rm -rf {} +
    @find . -type f -name "*.pyc" -delete

# -------------------------------------------------------------------------
# CI (local mirror of GitHub Actions)
# -------------------------------------------------------------------------

static_check:
    @just fix
    @just fmt
    @just lint
    @just type

# -------------------------------------------------------------------------
# CI (local mirror of GitHub Actions)
# -------------------------------------------------------------------------

ci:
    @just fix
    @just fmt
    @just lint
    @just type
    @just test
    @just precommit

# -------------------------------------------------------------------------
# Doctor / Diagnostics
# -------------------------------------------------------------------------

doctor:
    @echo "=== Environment ==="
    @python --version
    @uv --version
    @echo ""
    @echo "=== Tools ==="
    @uv run --active ruff --version
    @uv run --active basedpyright --version || echo "basedpyright not installed"
    @uv run --active pytest --version
    @echo ""
    @echo "=== Project ==="
    @echo "Package: google_adk_guide"
    @echo "Python: >= 3.11"
