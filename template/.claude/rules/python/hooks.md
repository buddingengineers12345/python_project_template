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
2. **basedpyright** — type correctness in strict mode.

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

## Top-level module test reminder (PreToolUse)

| Hook | Trigger | What it does |
|------|---------|----------------|
| `pre-write-src-test-reminder.sh` | `Write` or `Edit` on `src/<pkg>/<module>.py` | Warns if `tests/<pkg>/test_<module>.py` is missing |

Only **top-level package modules** are checked (`src/<pkg>/<name>.py`, excluding
`__init__.py`). Nested packages (for example `src/<pkg>/common/foo.py`) are skipped,
since those modules are often covered by shared test modules such as `test_support.py`.

## Type-checking configuration

basedpyright settings in `pyproject.toml` under `[tool.basedpyright]`. Do not
weaken `typeCheckingMode` or add broad `# type: ignore` without a specific error
code and explanation.
