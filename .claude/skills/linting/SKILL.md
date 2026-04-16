---
name: linting
description: >-
  Ruff lint and format guidance: configuration, error codes, auto-fix workflows,
  CI ordering, and per-file-ignores. Use this skill when fixing lint violations,
  configuring ruff rules, or understanding lint error codes. Trigger on mentions
  of: ruff, lint, linting, format, formatter, auto-fix, lint errors, E/F/I/UP/B
  codes, isort, or any request to fix or configure Python linting.
model: haiku
---

# Linting Skill

Guidance for using **ruff** as the project's linter and formatter. Ruff replaces
black, isort, flake8, and pycodestyle in a single tool.

## Command dispatch

| Command | What it does |
|---|---|
| `just fix` | Auto-fix safe violations |
| `just fmt` | Format all files |
| `just lint` | Check for violations (read-only) |

## Workflow order

Always run in this order to avoid churn:

```bash
just fix    # auto-fix first
just fmt    # then format
just lint   # then verify clean
```

## Active rule sets

See `references/ruff.md` for the complete configuration and every rule set.

## Common fix patterns

| Code | Meaning | Fix |
|---|---|---|
| `E` | pycodestyle style error | Usually auto-fixable |
| `F` | pyflakes logic error | Review manually |
| `I` | isort import order | Auto-fixable |
| `UP` | pyupgrade modernisation | Auto-fixable |
| `B` | bugbear potential bugs | Review manually |
| `D` | pydocstyle docstring | Add/fix docstring |
| `T20` | print() in app code | Replace with structlog |
| `C90` | complexity > 10 | Extract functions |
| `PERF` | performance anti-pattern | Review suggestion |

## Per-file ignores

- `tests/**` — `ARG`, `T20` ignored (unused args OK, print OK)
- `scripts/**` — `T20` ignored (print OK in CLI scripts)
- Docstrings (`D` rules) are enforced in tests.

## Suppression rules

- Never add `# noqa` without a specific code: `# noqa: E501`
- Always include a comment explaining why: `# noqa: B008 — FastAPI Depends()`
- Prefer fixing over suppressing

## Quick reference: where to go deeper

| Topic                      | Reference file                                     |
|----------------------------|----------------------------------------------------|
| Full ruff configuration    | [references/ruff.md](references/ruff.md)           |
| Pre-commit integration     | [references/pre-commit.md](references/pre-commit.md) |
