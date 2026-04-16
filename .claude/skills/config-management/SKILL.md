---
name: config-management
description: >-
  Guide for pyproject.toml, justfile, pre-commit, and CI pipeline configuration.
  Use this skill when modifying project configuration files, adding dependencies,
  configuring tools, or troubleshooting CI. Trigger on mentions of: pyproject.toml,
  justfile, pre-commit, CI configuration, GitHub Actions, tool configuration,
  dependency management, or any request to add/modify project config.
model: haiku
---

# Config Management Skill

Guidance for managing project-level configuration across the toolchain.

## Configuration files

| File | Purpose | When to modify |
|---|---|---|
| `pyproject.toml` | Package metadata, dependencies, tool configs (ruff, basedpyright, pytest, coverage) | Adding deps, changing tool settings |
| `justfile` | Task runner recipes (test, lint, fmt, ci, etc.) | Adding new workflows, modifying commands |
| `.pre-commit-config.yaml` | Git pre-commit hooks (ruff, basedpyright) | Adding/updating hook repos |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline | Modifying CI steps, adding jobs |
| `.copier-answers.yml` | Copier template answers — **never edit manually** | Only via `copier update` |
| `uv.lock` | Dependency lockfile — **never edit manually** | Only via `uv lock` or `just update` |

## pyproject.toml structure

Key sections and their tool owners:

| Section | Tool |
|---|---|
| `[project]` | Package metadata, version, dependencies |
| `[project.optional-dependencies]` | Extra dependency groups (dev, test, docs) |
| `[build-system]` | Build backend (hatchling) |
| `[tool.ruff]` | Ruff linter + formatter config |
| `[tool.ruff.lint]` | Rule selection, per-file-ignores |
| `[tool.basedpyright]` | Type checker mode, Python version |
| `[tool.pytest.ini_options]` | Pytest markers, flags, test paths |
| `[tool.coverage.*]` | Coverage thresholds, source paths |

## justfile quick reference

| Recipe | What it runs |
|---|---|
| `just test` | `pytest -q` |
| `just test-parallel` | `pytest -q -n auto` |
| `just coverage` | `pytest --cov=src --cov-report=term-missing` |
| `just lint` | `ruff check src/ tests/` |
| `just fmt` | `ruff format src/ tests/` |
| `just fix` | `ruff check --fix src/ tests/` |
| `just type` | `basedpyright` |
| `just docs-check` | `ruff check --select D src/` |
| `just ci` | Full pipeline: fix + fmt + lint + type + docs-check + test + precommit |
| `just review` | Pre-merge review: fix + lint + type + docs-check + test |

## Dependency management

```bash
# Add a runtime dependency
uv add <package>

# Add a dev dependency
uv add --optional dev <package>

# Sync from lockfile (no changes to lockfile)
just sync          # or: uv sync --frozen --extra dev --extra test --extra docs

# Update lockfile and resync
just update        # or: uv lock && uv sync --extra dev --extra test --extra docs
```

## Pre-commit configuration

Hooks run on `git commit`. Managed via `.pre-commit-config.yaml`:
- **ruff** — lint + format check on staged `.py` files
- **basedpyright** — type check on `src/`

Run all hooks manually: `just precommit`

## Rules for config changes

1. **Never weaken** ruff or basedpyright settings — the `pre-config-protection.sh` hook blocks this.
2. **Never edit** `uv.lock` directly — the `pre-protect-uv-lock.sh` hook blocks this.
3. **Never edit** `.copier-answers.yml` manually — use `copier update`.
4. Keep `justfile` recipes simple — one concern per recipe.
5. Pin all dependency versions in `pyproject.toml`.

## Quick reference: where to go deeper

| Topic                       | Reference file                                                   |
|-----------------------------|------------------------------------------------------------------|
| Complete tool configs       | [references/complete-configs.md](references/complete-configs.md) |
