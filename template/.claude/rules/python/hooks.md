# Python Hooks

# applies-to: **/*.py, **/*.pyi

> This file extends [common/hooks.md](../common/hooks.md) with Python-specific content.

## PostToolUse hooks active for Python files

| Hook | Trigger | What it does |
|------|---------|--------------|
| `post-edit-python.sh` | Edit or Write on `*.py` | Runs `ruff check` + `basedpyright` on the saved file |

### What the hook checks

1. **ruff check** — all active rule sets including `D` (docstrings), `C90` (complexity),
   `PERF` (performance anti-patterns), `T20` / `T201` (no `print()` in app code).
2. **basedpyright** — type correctness in `standard` mode (`pyproject.toml` `[tool.basedpyright]`).

Example output:

```
┌─ Standards check: src/mypackage/core.py
│
│  ruff check
│  src/mypackage/core.py:42:5: D401 First line should be in imperative mood
│
│  basedpyright
│  src/mypackage/core.py:17:12: error: Type "str | None" cannot be assigned to "str"
│
└─ ✗ Violations found — fix before committing
```

Fix all violations before moving to the next file.

## Pre-commit hooks for Python

| Hook | What it does |
|------|-------------|
| `ruff` | Lint + format check on staged `.py` files |
| `basedpyright` | Type check on the entire `src/` tree |
| `pre-bash-commit-quality.sh` | Scan staged files for secrets and debug statements |

The `pre-bash-block-no-verify.sh` hook prevents `git commit --no-verify`.

## `print()` enforcement

Ruff includes **`T20`** (flake8-print) in `[tool.ruff.lint] select`. `print()` in
application code is reported as **`T201`**. Use structlog:

```python
# Wrong
print(f"Processing order {order_id}")

# Correct
log = structlog.get_logger()
log.info("processing_order", order_id=order_id)
```

`print()` is permitted in `scripts/`, `tests/**`, and `src/**/bump_version.py` (per-file
ignores in `pyproject.toml`).

## TDD enforcement hooks (PreToolUse)

Register **at most one** of the source/test hooks below for `Write|Edit`. They use
the same scope; running both would warn and then block on the same condition.

| Hook | Trigger | What it does |
|------|---------|----------------|
| `pre-write-src-require-test.sh` | `Write` or `Edit` on `src/<pkg>/<module>.py` | **Blocks** write if `tests/<pkg>/test_<module>.py` does not exist (strict TDD). **Registered by default** in `.claude/settings.json`. |
| `pre-write-src-test-reminder.sh` | Same | Warns only (non-blocking). Swap into `settings.json` **instead of** `pre-write-src-require-test.sh` if you want reminders without blocking. |
| `pre-bash-coverage-gate.sh` | `Bash` on `git commit` | Warns if test coverage is below 85% threshold |

Both source/test hooks only check top-level package modules (`src/<pkg>/<name>.py`,
excluding `__init__.py`). Nested packages are skipped.

## Refactor test guard (PostToolUse)

| Hook | Trigger | What it does |
|------|---------|----------------|
| `post-edit-refactor-test-guard.sh` | `Edit` or `Write` on `src/**/*.py` | Reminds to run tests after every 3 source edits |

Tracks edit count since last test run. Helps maintain GREEN during the REFACTOR phase.

## Type-checking configuration

basedpyright settings in `pyproject.toml` under `[tool.basedpyright]`. Do not
weaken `typeCheckingMode` or add broad `# type: ignore` without a specific error
code and explanation.
