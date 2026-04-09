# Complete configurations

Ready-to-use configuration files for all tools in this project. Copy these into
your project and adjust versions, paths, and rule selections as needed.

---

## pyproject.toml — all tool sections

```toml
# ── Ruff ────────────────────────────────────────────────────────────────────
[tool.ruff]
target-version = "py311"
src = ["src"]
exclude = [".git", ".venv", "__pycache__", "build", "dist"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]
fixable = ["ALL"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["PLR2004", "F401"]
"**/__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "lf"
line-length = 88

# ── basedpyright ─────────────────────────────────────────────────────────────
[tool.basedpyright]
pythonVersion = "3.11"
include = ["src"]
exclude = ["**/__pycache__", ".venv", "build", "dist"]
venvPath = "."
venv = ".venv"
typeCheckingMode = "standard"

# ── Bandit ───────────────────────────────────────────────────────────────────
[tool.bandit]
targets = ["src"]
skips = []                                  # add rule IDs here only with a comment explaining why
exclude_dirs = [".venv", "build", "dist", "tests"]
# Note: severity/confidence thresholds are CLI flags (-ll -ii), not pyproject keys.
```

---

## .pre-commit-config.yaml — all hooks

```yaml
minimum_pre_commit_version: "3.0.0"

default_language_version:
  python: python3.11

repos:
  # ── Ruff: lint + format ──────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format

  # ── Bandit: security lint ─────────────────────────────────────────────────
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml", "-ll", "-ii"]
        files: ^src/

  # ── Semgrep: pattern-based security scan ─────────────────────────────────
  - repo: https://github.com/semgrep/semgrep
    rev: v1.60.0
    hooks:
      - id: semgrep
        args: ["--config", "p/python", "--config", ".semgrep.yml", "--severity", "ERROR"]
        files: ^src/

  # ── basedpyright: type checking ──────────────────────────────────────────
  # Requires basedpyright to be installed in the active venv.
  - repo: local
    hooks:
      - id: basedpyright
        name: basedpyright
        entry: basedpyright
        language: system
        types: [python]
        pass_filenames: false

  # ── General hygiene ──────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
```

---

## .semgrep.yml — local custom rules

```yaml
# .semgrep.yml
# Local project-specific rules. Registry packs (p/python etc.) are passed
# as --config flags on the CLI, not listed here.
#
# Usage:
#   semgrep --config p/python --config p/owasp-top-ten --config .semgrep.yml src/

rules:
  - id: no-eval
    pattern: eval(...)
    message: >
      eval() executes arbitrary code. Use ast.literal_eval() for safe data
      parsing, or refactor to avoid dynamic evaluation entirely.
    languages: [python]
    severity: ERROR

  - id: no-hardcoded-secrets-in-jwt
    patterns:
      - pattern: jwt.encode(..., "$SECRET", ...)
      - pattern-not: jwt.encode(..., os.environ.get(...), ...)
    message: Hardcoded JWT secret. Load from environment variable or secrets manager.
    languages: [python]
    severity: ERROR
```

---

## GitHub Actions workflow — full CI pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  # ── Fast checks: format + lint + security ───────────────────────────────
  quality:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install quality tools
        run: pip install ruff bandit semgrep

      - name: Ruff — format check
        run: ruff format --check .

      - name: Ruff — lint
        run: ruff check .

      - name: Bandit — security lint
        run: bandit -c pyproject.toml -r src/ -ll -ii

      - name: Cache semgrep rules
        uses: actions/cache@v4
        with:
          path: ~/.semgrep/cache
          key: semgrep-${{ hashFiles('.semgrep.yml') }}

      - name: Semgrep — pattern scan
        run: |
          semgrep --config p/python \
                  --config p/owasp-top-ten \
                  --config .semgrep.yml \
                  --severity ERROR \
                  src/

  # ── Type checking ────────────────────────────────────────────────────────
  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    needs: quality          # only run if quality checks pass

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt   # must include basedpyright

      - name: basedpyright — type check
        run: basedpyright

  # ── Tests ────────────────────────────────────────────────────────────────
  test:
    name: Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [quality, typecheck]   # only run if both upstream jobs pass

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run pytest with coverage
        run: pytest --maxfail=1 --disable-warnings --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
```

---

## Version update checklist

When updating tool versions, change them in all three places:

| Tool | pyproject.toml | .pre-commit-config.yaml | requirements.txt / pyproject deps |
|---|---|---|---|
| ruff | `target-version` (Python, not ruff) | `rev: v0.9.0` | `ruff>=0.9.0` |
| bandit | — | `rev: 1.8.3` | `bandit>=1.8.3` |
| semgrep | — | `rev: v1.60.0` | `semgrep>=1.60.0` |
| basedpyright | `pythonVersion` (Python, not tool) | (local hook — no rev) | `basedpyright>=1.x` |
| pre-commit-hooks | — | `rev: v5.0.0` | — |
