# Ruff

Ruff is a fast Python linter and formatter written in Rust. It replaces flake8, isort,
and black in a single tool.

---

## What it does

- **`ruff check`** — lints: enforces rules (unused imports, style, complexity, bugs, etc.)
- **`ruff format`** — formats: opinionated code formatter (Black-compatible output)

Both read from `[tool.ruff]` in `pyproject.toml`.

---

## Installation

```bash
pip install ruff          # or: uv add --dev ruff
```

Verify:
```bash
ruff --version
```

---

## pyproject.toml config (annotated)

```toml
[tool.ruff]
# Target Python version — affects which syntax is valid and which rules apply.
# Keep in sync with the minimum Python version the project supports.
target-version = "py311"

# Directories ruff will scan. Excludes generated, vendored, or build dirs.
src = ["src"]
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.lint]
# Rule sets to enable. Add a prefix letter to enable the entire ruleset.
# E/W = pycodestyle errors/warnings
# F   = pyflakes (undefined names, unused imports)
# I   = isort (import order) — replaces standalone isort
# UP  = pyupgrade (modernise syntax for target Python version)
# B   = flake8-bugbear (likely bugs and design issues)
# SIM = flake8-simplify (suggest simpler expressions)
# S   = flake8-bandit (security — lightweight overlap with bandit)
select = ["E", "W", "F", "I", "UP", "B", "SIM"]

# Rules to ignore project-wide.
# E501 = line too long — controlled by the formatter, not the linter.
ignore = ["E501"]

# Allow autofix for all enabled rules when running `ruff check --fix`.
fixable = ["ALL"]
unfixable = []

# Per-file rule overrides. Use sparingly — prefer fixing the root cause.
[tool.ruff.lint.per-file-ignores]
# Test files: assert is valid (pytest), magic values are fine, fixtures look unused.
# S101 requires the S ruleset to be in `select` above — add "S" if you want it.
"tests/**/*.py" = ["PLR2004", "F401"]
# __init__.py: re-exports don't need to be explicitly used.
"**/__init__.py" = ["F401"]

[tool.ruff.format]
# Double quotes matches Black's default.
quote-style = "double"
# Spaces, not tabs.
indent-style = "space"
# Preserve magic trailing commas (they affect how multi-line structures are formatted).
skip-magic-trailing-comma = false
# Normalise line endings to LF on all platforms.
line-ending = "lf"
# Line length for the formatter. Default is 88 (same as Black).
# If you change this, also set line-length under [tool.ruff.lint] for E501.
line-length = 88
```

---

## Common rule codes and fixes

| Code | Meaning | Fix |
|---|---|---|
| `F401` | Unused import | Remove import; `# noqa: F401` only for intentional re-exports |
| `F811` | Redefinition of unused name | Remove or rename the duplicate |
| `F841` | Local variable assigned but never used | Remove assignment or rename to `_` |
| `E711` | `== None` instead of `is None` | Use `is None` / `is not None` |
| `E712` | `== True` instead of `is True` | Use `is True` or just the boolean directly |
| `I001` | Import block unsorted | Run `ruff check --fix` to auto-sort |
| `UP006` | Use `list` instead of `List` (3.9+) | Update type annotation |
| `UP007` | Use `X \| Y` instead of `Optional[X]` (3.10+) | Update union syntax |
| `B006` | Mutable default argument | Use `None` default + guard in body |
| `B007` | Loop variable unused | Rename to `_` |
| `B008` | Function call as default argument | Move call inside the function body |
| `SIM108` | Ternary can replace if/else | Simplify to `x = a if cond else b` |
| `SIM117` | Nested `with` can be merged | Use `with a(), b():` |

### Looking up an unfamiliar rule

```bash
ruff rule F401          # prints full explanation of the rule
ruff rule --all         # lists every available rule with description
```

### Suppressing a rule inline

```python
import os  # noqa: F401       ← suppress one specific rule (preferred)
import os  # noqa              ← suppress all rules on this line (avoid)
```

Prefer adding an entry to `per-file-ignores` in `pyproject.toml` over scattering
`# noqa` across files — it keeps suppression decisions visible and reviewable.

---

## Running ruff

```bash
# Check (no changes, exits non-zero on violations):
ruff check .

# Check and auto-fix safe issues:
ruff check --fix .

# Show a summary of which rules fired most (useful for tuning config):
ruff check --statistics .

# Format (rewrites files in place):
ruff format .

# Format check — CI mode: no changes, exits non-zero if formatting needed:
ruff format --check .

# Show exactly what the formatter would change without writing:
ruff format --diff .

# Check a single file:
ruff check src/mymodule.py
```

---

## CI step (GitHub Actions)

```yaml
- name: Install ruff
  run: pip install ruff

- name: Ruff — format check
  run: ruff format --check .

- name: Ruff — lint
  run: ruff check .
```

Always run `ruff format --check` before `ruff check` — formatting failures surface
first without wasting time on lint output.

With `cache: 'pip'` on `actions/setup-python`, repeated installs are fast.

---

## Pre-commit hook entry

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.9.0          # pin to a specific release; update with: pre-commit autoupdate
  hooks:
    - id: ruff
      args: ["--fix"]  # auto-fix on commit so the developer sees clean diffs
    - id: ruff-format  # auto-format on commit
```

---

## Gotchas

- **`ruff format` and `ruff check` are separate concerns.** A file can pass linting but
  still need formatting, and vice versa. Always run both.
- **`--fix` in local dev, `--check` in CI.** Using `--fix` in CI silently rewrites files;
  the pipeline appears to pass but the rewrite never gets committed. Use check mode in CI.
- **`target-version` drives UP rules.** `UP006` (drop `List`/`Dict`) only fires at
  `py39+`. Keep `target-version` in sync with your actual minimum Python.
- **isort is built in via the `I` ruleset.** Do not also run standalone isort — they will
  conflict on import ordering decisions.
- **`S` ruleset (flake8-bandit) overlaps with bandit.** If you add `"S"` to `select`,
  expect duplicate findings. Either add it and accept overlap, or omit it and rely on
  bandit for security rules. If you add `"S"`, also update `per-file-ignores` for tests
  to include `"S101"` (assert statements).
- **Line length must be set consistently.** If you change `line-length` from 88, set it
  in *both* `[tool.ruff.format]` and `[tool.ruff.lint]` (for `E501` if you enable it).
