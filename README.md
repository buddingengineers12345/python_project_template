# Copier uv-first Python template

This repository is a **Copier** template that generates a modern Python project using **uv** for dependency management, **ruff** for formatting/linting, and **basedpyright** for type checking.

Reference: [copier-org/copier README](https://github.com/copier-org/copier?tab=readme-ov-file)

## Prerequisites

- Python 3.11+
- Git
- `uv`
- `copier`

## Getting started (developing this template)

Sync dev dependencies:

```bash
uv sync --extra dev
```

Run template tests:

```bash
uv run pytest
```

## Generating a project from this template

From this repo root:

```bash
copier copy . /path/to/new-project --trust --defaults
```

Common flags:

- `--defaults`: accept defaults for all questions
- `--trust`: allow running template tasks (post-generation commands)
- `--data key=value`: provide answers non-interactively

## Updating a generated project

If you generated a project from this template, Copier stores answers in `.copier-answers.yml` in the generated project.

To update:

```bash
copier update --trust --defaults
```

## FAQ

### Why does CI use `uv sync --frozen`?

Generated projects are expected to have a committed `uv.lock`. This makes CI deterministic.

