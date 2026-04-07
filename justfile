# ==========================================================================
# Justfile for python_project_template (Copier template repo)
#
# Usage:
#   just             # list commands
#   just sync        # install dev deps for this template repo
#   just test        # run template tests (pytest)
#   just lint        # ruff lint this repo
#   just fmt         # ruff format this repo
# ==========================================================================

# Always show commands if no recipe is given
default:
    @just --list

# -------------------------------------------------------------------------
# Helpers (private)
# -------------------------------------------------------------------------

_set_env:
    @uv --version > /dev/null

# -------------------------------------------------------------------------
# Formatting & Linting
# -------------------------------------------------------------------------

fmt:
    @uv run --active ruff format .

lint:
    @uv run --active ruff check .

fix:
    @uv run --active ruff check --fix .

# Check docstring coverage on all non-test Python files
docs-check:
    @echo "=== Docstring coverage check ==="
    @uv run --active ruff check --select D .
    @echo "✓ Docstring check complete"

# Run all static analysis + docstring checks (pre-merge review)
review:
    @echo "=== Code Review ==="
    @just fix
    @just lint
    @just type
    @just docs-check
    @echo "=== Review passed ==="



# -------------------------------------------------------------------------
# Type checking
# -------------------------------------------------------------------------

type:
    @uv run --active basedpyright

# -------------------------------------------------------------------------
# Testing
# -------------------------------------------------------------------------

test:
    @uv run --active pytest

test-parallel:
    @uv run --active pytest -n auto

coverage:
    @uv run --active pytest --cov --cov-report=term-missing --cov-report=xml

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

sync: _set_env
    @uv sync --frozen --extra dev

update:
    @uv lock --upgrade
    @uv sync --frozen --extra dev

# -------------------------------------------------------------------------
# Docs (optional)
# -------------------------------------------------------------------------
# This repository is the Copier template source; there is no MkDocs site here.
# Generated projects (include_docs=true) define docs-serve / docs-build in their justfile.

docs-help:
    @echo "MkDocs recipes live in generated projects (see template/justfile.jinja)."

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
    @just sync
    @just precommit-install

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
    @just docs-check

ci:
    @just static_check
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
    @echo "Repo: python_project_template"
    @echo "Python: >= 3.11"
