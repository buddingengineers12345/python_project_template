# Python Hooks

# applies-to: **/*.py, **/*.pyi

> This file extends [common/hooks.md](../common/hooks.md) with Python-specific content.

## PostToolUse hooks active for Python files

These hooks fire automatically in a Claude Code session after any `.py` file is
edited or created. They provide immediate feedback so violations are fixed in the
same turn, not at CI time.

| Hook script | Trigger | What it does |
|-------------|---------|--------------|
| `post-edit-python.sh` | Edit or Write on `*.py` | Runs `ruff check` + `basedpyright` on the saved file; prints violations to stdout |

### What the hook checks

1. **ruff check** — all active rule sets: `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`,
   `D` (docstrings), `C90` (complexity), `PERF` (performance anti-patterns).
2. **basedpyright** — type correctness in `standard` mode.

If either tool reports violations, the hook prints a structured block:

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

Fix all reported violations before moving on to the next file.

## Pre-commit hooks active for Python files

The following hooks run on every `git commit` via pre-commit:

| Hook | What it does |
|------|-------------|
| `ruff` | Lint + format check on staged `.py` files |
| `basedpyright` | Type check on the entire `src/` tree |
| `pre-bash-commit-quality.sh` | Scan staged `.py` files for hardcoded secrets and debug statements |

The `pre-bash-block-no-verify.sh` hook blocks `git commit --no-verify`, ensuring
pre-commit hooks cannot be skipped.

## Warning: `print()` in application code

Using `print()` in `src/` is a violation (ruff `T201`). Use `structlog` instead:

```python
# Wrong
print(f"Processing order {order_id}")

# Correct
log = structlog.get_logger()
log.info("processing_order", order_id=order_id)
```

`print()` is allowed in `scripts/` and in test files.

## Type-checking configuration

basedpyright settings live in `pyproject.toml` under `[tool.basedpyright]`:

```toml
[tool.basedpyright]
pythonVersion = "3.11"
typeCheckingMode = "standard"
reportMissingTypeStubs = false
```

Do not weaken `typeCheckingMode` or add broad `# type: ignore` comments without
a specific error code and a comment explaining why it is necessary.
