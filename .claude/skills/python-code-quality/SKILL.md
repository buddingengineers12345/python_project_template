---
name: python-code-quality
description: >-
  Use this skill whenever the task involves Python code style, formatting, linting, type
  checking, security scanning, or commit hygiene in this project. Triggers include:
  configuring or running ruff (lint or format), setting up or modifying pre-commit hooks,
  configuring or running basedpyright, running bandit or semgrep, fixing lint/type/security
  errors, writing or updating pyproject.toml quality sections, CI pipeline steps for code
  quality, or any question like "how do I enforce formatting", "why is ruff complaining",
  "pre-commit isn't running", "type error I don't understand", or "security finding I need
  to suppress". Also use proactively when writing new Python files that will need to pass
  CI checks.
---

# Python Code Quality Skill

This project enforces code quality through five tools:

| Tool | Role | Config location |
|---|---|---|
| **ruff** | Lint + format (replaces flake8 / isort / black) | `[tool.ruff]` in `pyproject.toml` |
| **pre-commit** | Git hook runner — gates every commit | `.pre-commit-config.yaml` |
| **basedpyright** | Static type checker (strict pyright fork) | `[tool.basedpyright]` in `pyproject.toml` |
| **bandit** | Security linter — fixed Python vulnerability patterns | `[tool.bandit]` in `pyproject.toml` |
| **semgrep** | Pattern-based scanner + custom rules | `.semgrep.yml` |

---

## Quick reference

### Run everything locally

```bash
pre-commit run --all-files          # run all hooks on every file (recommended)

# Or run each tool individually:
ruff format .                       # auto-format
ruff check --fix .                  # lint + auto-fix safe issues
basedpyright                        # type-check
bandit -c pyproject.toml -r src/    # security lint
semgrep --config .semgrep.yml src/  # pattern scan
```

### Common failures and fast fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `ruff` fails on unused import | `F401` rule | Remove import or `# noqa: F401` for intentional re-exports |
| `ruff format` changes file | File not formatted | Run `ruff format .` and re-stage |
| pre-commit hook not running | Hook not installed | Run `pre-commit install` |
| pre-commit passes locally, fails in CI | Staged-only vs all-files mismatch | Run `pre-commit run --all-files` before pushing |
| basedpyright `reportUnknownVariableType` | Missing annotation | Add type annotation; see `references/basedpyright.md` |
| basedpyright `reportMissingImports` | Package not in venv | Install package or add stub; see `references/basedpyright.md` |
| bandit `B[code]` finding | Security anti-pattern | Fix or add `# nosec B<code>` with explanation |
| semgrep finding | Code matches security pattern | Fix or add `# nosemgrep: <rule-id>` inline |

### CI ordering (fast-fail principle)

Run cheapest checks first so failures surface quickly without wasting time on later stages:

```
ruff format --check  →  ruff check  →  bandit  →  semgrep  →  basedpyright  →  pytest
```

| Stage | Why here |
|---|---|
| `ruff format --check` | Instant — no point type-checking badly formatted code |
| `ruff check` | Fast Rust linter — catches style and logic issues cheaply |
| `bandit` | Fast fixed-rule security scan — pure AST analysis |
| `semgrep` | Slower than bandit (fetches registry rules); runs after fast checks |
| `basedpyright` | Needs full import graph resolved — slower, but before tests |
| `pytest` | Most expensive — only run when everything above passes |

---

## When to load references

| If the task involves…                 | Load                              |
|----------------------------------------|-----------------------------------|
| Configuring or debugging ruff          | `references/ruff.md`              |
| Setting up or fixing pre-commit hooks  | `references/pre-commit.md`        |
| Type errors or basedpyright config     | `references/basedpyright.md`      |
| Security scan findings (bandit)        | `references/bandit.md`            |
| Custom semgrep rules                   | `references/semgrep.md`           |
| Complete config file examples          | `references/complete-configs.md`  |
| Running `just lint`/`just fix` (default) | No reference needed — use inline |

## Quick reference: where to go deeper

Read the relevant reference file for configuration details, error code explanations,
or CI integration specifics:

| Topic                           | Reference file                                                       |
|---------------------------------|----------------------------------------------------------------------|
| ruff (lint + format)            | [references/ruff.md](references/ruff.md)                             |
| pre-commit hooks                | [references/pre-commit.md](references/pre-commit.md)                 |
| basedpyright (type checking)    | [references/basedpyright.md](references/basedpyright.md)             |
| bandit (security linting)       | [references/bandit.md](references/bandit.md)                         |
| semgrep (pattern scanning)      | [references/semgrep.md](references/semgrep.md)                       |
| Complete config files            | [references/complete-configs.md](references/complete-configs.md)     |

---

## Efficiency: batch edits and parallel calls

- **Parallel calls:** Run independent checks (`ruff check`, `basedpyright`,
  `bandit`) in parallel as separate tool calls in a single message.
- **Batch edits:** When fixing multiple lint violations in the same file, combine
  all fixes into a single Edit tool call.
- **CI ordering:** Follow the fast-fail order (format → lint → bandit → semgrep →
  type → test) but run independent stages in parallel where possible.

## Adding a new tool

1. Create `references/<toolname>.md` using the template below.
2. Add a row to the tools table at the top of this file.
3. Add the tool's hook to `.pre-commit-config.yaml` (see `references/pre-commit.md`).
4. Add the tool's `pyproject.toml` section to `references/complete-configs.md`.
5. Insert the tool into the CI ordering table above with a rationale for placement.

### New tool reference template

```markdown
# <ToolName>

## What it does
## Installation
## pyproject.toml config (annotated)
## Common error codes and fixes
## Running <toolname>
## CI step
## Pre-commit hook entry
## Gotchas
```
