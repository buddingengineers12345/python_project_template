---
name: type-checking
description: >-
  BasedPyright type checking: configuration, common errors, fix strategies, and
  standard mode settings. Use this skill when debugging type errors, configuring
  basedpyright, or understanding type annotations. Trigger on mentions of:
  type checking, type annotation, basedpyright, typing errors, mypy, type error,
  Protocol, Union, Generic, or any request to fix type issues in Python.
model: haiku
---

# Type checking Skill

Guidance for **basedpyright** in `standard` mode for strict type checking across
the project.

## Command dispatch

| Command | What it does |
|---|---|
| `just type` | Run basedpyright type check |
| `just type --outputjson` | Machine-readable type errors |

## Configuration

See `pyproject.toml` under `[tool.basedpyright]`:
- Mode: `standard` (strict)
- Python version: 3.11
- venv: `.venv`

Never change mode to `off`, `basic`, or `strict` without discussion.

## Common errors and fixes

See `references/basedpyright.md` for:
- All error codes and what they mean
- Step-by-step fix strategies
- Type annotation patterns for common scenarios

## Type annotation rules

1. **All public functions** must have complete type annotations (parameters + return).
2. **Private functions** (_prefixed) are less strict but encouraged.
3. Use modern syntax: `X | Y` instead of `Optional[X]` / `Union[X, Y]`
4. Use `never` for impossible paths, `NoReturn` for non-returning functions.
5. Use `Protocol` for structural typing instead of ABC when possible.

## Suppression

- Avoid `# type: ignore` without specific error codes.
- When suppressing, use: `# type: ignore[error-code]` with an explanation.

## Quick reference: where to go deeper

| Topic                    | Reference file                                           |
|--------------------------|----------------------------------------------------------|
| Error codes and fixes    | [references/basedpyright.md](references/basedpyright.md) |
