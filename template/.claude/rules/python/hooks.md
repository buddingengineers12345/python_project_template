# Python Hooks

# applies-to: **/*.py, **/*.pyi

> This file extends [common/hooks.md](../common/hooks.md) with Python-specific content.

## PostToolUse hooks active for Python files

| Hook | Trigger | What it does |
|------|---------|--------------|
| `post-edit-python.sh` | Edit or Write on `*.py` | Runs `ruff check` + `basedpyright` on the saved file |

### What the hook checks

1. **ruff check** — all active rule sets including `D` (docstrings), `C90` (complexity),
   `PERF` (performance anti-patterns).
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

## `print()` warning

`print()` in `src/` is a ruff violation (`T201`). Use structlog:

```python
# Wrong
print(f"Processing order {order_id}")

# Correct
log = structlog.get_logger()
log.info("processing_order", order_id=order_id)
```

`print()` is permitted in `scripts/` and test files.

## Type-checking configuration

basedpyright settings in `pyproject.toml` under `[tool.basedpyright]`. Do not
weaken `typeCheckingMode` or add broad `# type: ignore` without a specific error
code and explanation.
