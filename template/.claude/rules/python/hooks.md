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

`print()` is permitted in `scripts/` and `tests/**` only. Package code under `src/<pkg>/` must use
the public APIs in `common.logging_manager` (`configure_logging`, `get_logger`, context and `log_*`
helpers, `write_machine_stdout_line` for raw stdout only) plus `structlog.get_logger()` for events —
never `logging.getLogger()`, `logging.basicConfig()`, or `structlog.configure()` outside
`logging_manager`. Prefer other `common/*` modules over duplicating utilities in `core`, `cli`, etc.;
see `CLAUDE.md`.

## TDD enforcement hooks (PreToolUse)

Register **at most one** of the source/test hooks below for `Write|Edit`. They use
the same scope; running both would warn and then block on the same condition.

| Hook | Trigger | What it does |
|------|---------|----------------|
| `pre-write-src-require-test.sh` | `Write` or `Edit` on `src/<pkg>/<module>.py` | **Blocks** write if a matching test file does not exist in `tests/unit/`, `tests/integration/`, or `tests/e2e/` (strict TDD). **Registered by default** in `.claude/settings.json`. |
| `pre-write-src-test-reminder.sh` | Same | Warns only (non-blocking). Swap into `settings.json` **instead of** `pre-write-src-require-test.sh` if you want reminders without blocking. |
| `pre-bash-coverage-gate.sh` | `Bash` on `git commit` | Warns if test coverage is below 85% threshold |

Both source/test hooks check top-level package modules (`src/<pkg>/<name>.py`,
excluding `__init__.py`) and common subpackage modules (`src/<pkg>/common/<name>.py`).
Test files are searched in `tests/unit/`, `tests/integration/`, and `tests/e2e/`
subdirectories (e.g. `tests/unit/test_<module>.py` or `tests/unit/common/test_<module>.py`).

### How to swap to the warn-only reminder

The default strict hook (`pre-write-src-require-test.sh`) blocks any write to
`src/<pkg>/<module>.py` when the matching test file is missing. If you prefer a non-blocking
reminder, swap the registration in `.claude/settings.json`:

1. Locate the `PreToolUse` entry whose `command` is
   `bash .claude/hooks/pre-write-src-require-test.sh`.
2. Replace `pre-write-src-require-test.sh` with `pre-write-src-test-reminder.sh` in that
   entry.
3. Register only one at a time. Registering both produces duplicate output on every write.

## Refactor test guard (PostToolUse)

| Hook | Trigger | What it does |
|------|---------|----------------|
| `post-edit-refactor-test-guard.sh` | `Edit` or `Write` on `src/**/*.py` | Reminds to run tests after every 3 source edits |

Tracks edit count since last test run. Helps maintain GREEN during the REFACTOR phase.

## Type-checking configuration

basedpyright settings in `pyproject.toml` under `[tool.basedpyright]`. Do not
weaken `typeCheckingMode` or add broad `# type: ignore` without a specific error
code and explanation.
