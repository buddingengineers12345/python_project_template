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
    @uv run ruff format .

lint:
    @uv run ruff check .

# Lint only changed (unstaged+staged) Python files — fast feedback loop
lint-changed:
    @uv run ruff check $(git diff --name-only -- '*.py')

fix:
    @uv run ruff format .
    @uv run ruff check --fix .

# Format check (read-only) — matches GitHub Actions
fmt-check:
    @uv run ruff format --check .

# Check docstring coverage on all non-test Python files
docs-check:
    @echo "=== Docstring coverage check ==="
    @uv run ruff check --select D .
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
    @uv run basedpyright

# -------------------------------------------------------------------------
# Testing
#
# Default: Minimal logging (quiet mode, dots only, warnings/errors only)
# For verbose output with test names, use: just test-verbose
# For full debug output, use: just test-debug
# For failed tests only, use: just test-lf
# -------------------------------------------------------------------------

# Run tests with minimal output (default, fast, token-efficient)
test:
    @uv run pytest tests/

# Run only slow tests
test-slow:
    @uv run pytest tests/ -m slow

# Run tests in parallel with minimal output
test-parallel:
    @uv run pytest tests/ -n auto

# Run tests with verbose output (shows test names, INFO logs)
test-verbose:
    @uv run pytest tests/ -v

# Run tests with full debug output (shows all DEBUG logs)
test-debug:
    @uv run pytest tests/ -vv --show-debug

# Re-run only the tests that failed in the last run
test-lf:
    @uv run pytest tests/ --lf

# Stop on first test failure (fast feedback)
test-first-fail:
    @uv run pytest tests/ -x

# Run tests for changed (unstaged+staged) Python files only — fast incremental feedback
test-changed:
    @uv run pytest $(git diff --name-only -- '*.py' | sed 's/src/tests/g')

# Fast unit tests only — excludes slow and integration markers
test-fast:
    @uv run pytest tests/ -m "not slow and not integration"

# Integration tests only
test-integration:
    @uv run pytest tests/ -m integration

# Re-run last failed tests with maximum verbosity — fast debugging loop
test-failed-verbose:
    @uv run pytest --lf -vv

coverage:
    @uv run pytest --cov --cov-report=term-missing --cov-report=xml

# Test command matching GitHub CI (3.11 matrix leg in .github/workflows/tests.yml)
test-ci:
    @uv run pytest -q --cov --cov-report=xml --cov-report=term-missing

# Full tests.yml matrix (3.11 with coverage; 3.12/3.13 with pytest -q only).
# 3.11 uses the default project .venv (same as `test-ci`). 3.12/3.13 use
# UV_PROJECT_ENVIRONMENT so those syncs do not replace .venv.
test-ci-matrix:
    #!/usr/bin/env bash
    set -euo pipefail
    ROOT="$(git rev-parse --show-toplevel)"
    cd "$ROOT"
    uv python install 3.11 3.12 3.13
    echo "=== Python 3.11 + coverage (tests.yml matrix) ==="
    unset UV_PROJECT_ENVIRONMENT
    uv sync --frozen --extra dev --python 3.11
    uv run pytest -q --cov --cov-report=xml --cov-report=term-missing
    for py in 3.12 3.13; do
      echo "=== Python ${py} (tests.yml matrix) ==="
      suffix="${py//./}"
      export UV_PROJECT_ENVIRONMENT="${ROOT}/.venv-ci-${suffix}"
      uv sync --frozen --extra dev --python "${py}"
      uv run pytest -q
    done
    unset UV_PROJECT_ENVIRONMENT
    uv sync --frozen --extra dev --python 3.11
    echo "✓ Restored default .venv (Python 3.11)"

# -------------------------------------------------------------------------
# Pre-commit
# -------------------------------------------------------------------------

precommit-install:
    @uv run pre-commit install
    @uv run pre-commit install --hook-type pre-push
    @uv run pre-commit install --hook-type commit-msg
    @git config commit.template "$(git rev-parse --show-toplevel)/.gitmessage"

# Interactive conventional commit (Commitizen); alternative to `git commit`.
cz-commit:
    @uv run cz commit

precommit:
    @uv run pre-commit run --all-files --verbose

# Dependency audit matching .github/workflows/security.yml (pip-audit).
# Uses ``uv run --with pip-audit`` so the tool runs with the project Python (``uv tool run``/``uvx``
# can pick a different interpreter whose venv ``ensurepip`` fails on some hosts).
audit:
    @uv export --frozen --format requirements-txt --extra dev | uv run --with pip-audit pip-audit --requirement /dev/stdin

# -------------------------------------------------------------------------
# Dependency management
# -------------------------------------------------------------------------

sync: _set_env
    @uv sync --frozen --extra dev

update:
    @uv lock --upgrade
    @uv sync --frozen --extra dev

# Check for outdated dependencies
deps-outdated:
    @uv tree --outdated

# Verify lockfile is consistent with pyproject.toml
lock-check:
    @uv lock --check

# -------------------------------------------------------------------------
# Environment
# -------------------------------------------------------------------------

load-env:
    @if [ ! -f .env ]; then \
        cp env.example .env; \
        echo "✓ Created .env from env.example"; \
    else \
        echo ".env already exists"; \
    fi

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

# Validate the built distribution (catches README/metadata issues before PyPI upload)
check-dist:
    @uv run python -m twine check dist/*

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

# One-command developer onboarding: sync deps, register hooks, run diagnostics
bootstrap:
    @just sync
    @just precommit-install
    @just doctor

# -------------------------------------------------------------------------
# Cleaning
# -------------------------------------------------------------------------

clean:
    @test -f pyproject.toml || (echo "ERROR: Not in project root!" && exit 1)
    @rm -rf build dist *.egg-info
    @rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
    @find . -type d -name "__pycache__" -exec rm -rf {} +
    @find . -type f -name "*.pyc" -delete

# -------------------------------------------------------------------------
# CI (local mirror of GitHub Actions)
# -------------------------------------------------------------------------

# Read-only mirror of GitHub Actions: lint.yml + tests.yml matrix + pip-audit (CodeQL/dep-review are GHA-only).
check:
    @uv sync --frozen --extra dev
    @just fmt-check
    @uv run ruff check .
    @uv run basedpyright
    @just sync-check
    @just docs-check
    @just test-ci
    @uv run pre-commit run --all-files --verbose
    # @just audit

ci:
    @just fix
    @just check

# -------------------------------------------------------------------------
# Doctor / Diagnostics
# -------------------------------------------------------------------------

doctor:
    @echo "=== Environment ==="
    @python --version
    @uv --version
    @echo ""
    @echo "=== Python Tools ==="
    @uv run ruff --version
    @uv run basedpyright --version || echo "basedpyright not installed"
    @uv run pytest --version
    @uv run cz version || echo "commitizen installed"
    @echo ""
    @echo "=== System Tools ==="
    @git-cliff --version || echo "⚠️  git-cliff not found (required for 'just release')"
    @echo ""
    @echo "=== Project ==="
    @echo "Repo: python_project_template"
    @echo "Python: >= 3.11"

# -------------------------------------------------------------------------
# Repo automation
# -------------------------------------------------------------------------

# Generate repo freshness dashboard + JSON artifacts
freshness:
    @uv run python scripts/repo_file_freshness.py

# Validate root/template sync map and parity checks
sync-check:
    @uv run python scripts/check_root_template_sync.py

# Print a conventional PR title + PR body (template + git log) for pr-policy compliance
pr-draft:
    @uv run python scripts/pr_commit_policy.py draft

# -------------------------------------------------------------------------
# SDLC: Task management
# -------------------------------------------------------------------------

# Validate a task YAML against Definition of Ready
dor-check TASK_ID:
    python3 .claude/skills/sdlc-workflow/scripts/validate_dor.py tasks/{{TASK_ID}}.yaml

# List all tasks and their statuses
tasks:
    @echo "Task ID       Status        Title"
    @echo "----------    ----------    -----"
    @python3 -c "import yaml; from pathlib import Path; [print(f\"{d['task_id']:<14}{d['status']:<14}{d['title']}\") for p in sorted(Path('tasks').glob('TASK_*.yaml')) if (d := yaml.safe_load(p.read_text()))]"

# Run pre-flight checks before starting SDLC pipeline
preflight TASK_ID:
    bash .claude/skills/sdlc-workflow/scripts/preflight.sh {{TASK_ID}}

# -------------------------------------------------------------------------
# Release & Versioning
# -------------------------------------------------------------------------

# Orchestrates the complete release workflow:
# 1. Validates repository is clean (no uncommitted changes)
# 2. Runs full CI to ensure all tests pass
# 3. Uses Commitizen to bump version (reads/writes [project].version)
# 4. Uses git-cliff to generate CHANGELOG.md from commits
# 5. Creates annotated git tag (v<version>)
# 6. Pushes tag and commits to main
#
# Workflow: conventional commits → commitizen validation → git-cliff changelog → semantic versioning
#
# Requirements:
#   - Clean git state (no uncommitted changes)
#   - All CI checks passing (just ci)
#   - git-cliff installed (brew install git-cliff on macOS)
#   - Push permissions to main branch
#
# Usage:
#   just release patch       # v0.0.8 → v0.0.9 (bug fixes)
#   just release minor       # v0.0.8 → v0.1.0 (new features)
#   just release major       # v0.0.8 → v1.0.0 (breaking changes)
release BUMP_TYPE="patch":
    @echo "=== Release Workflow ==="
    @echo "Release type: {{BUMP_TYPE}}"
    @echo ""

    @echo "1️⃣  Checking git state..."
    @if [ -n "$(git status --porcelain)" ]; then \
        echo "❌ Error: Uncommitted changes detected. Commit or stash before release."; \
        git status --short; \
        exit 1; \
    fi
    @echo "✓ Git state clean"
    @echo ""

    @echo "2️⃣  Checking git-cliff installation..."
    @if ! command -v git-cliff &> /dev/null; then \
        echo "❌ Error: git-cliff not found."; \
        echo "Install with: brew install git-cliff (macOS) or visit https://github.com/orhun/git-cliff"; \
        exit 1; \
    fi
    @echo "✓ git-cliff found"
    @echo ""

    @echo "3️⃣  Running CI checks..."
    @just ci
    @echo "✓ CI passed"
    @echo ""

    @echo "4️⃣  Bumping version with Commitizen..."
    @uv run cz bump --increment {{BUMP_TYPE}} --changelog
    @echo "✓ Version bumped, changelog generated"
    @echo ""

    @echo "5️⃣  Generating release notes with git-cliff..."
    @git-cliff --output CHANGELOG.md
    @git add CHANGELOG.md
    @git commit --amend --no-edit
    @echo "✓ CHANGELOG.md updated"
    @echo ""

    @echo "6️⃣  Pushing release to main..."
    @git push origin main --tags
    @echo "✓ Release pushed"
    @echo ""

    @echo "✅ Release complete!"
    @git describe --tags --abbrev=0
