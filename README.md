# Python Starter Template

This repository is a **Copier template** for generating a modern, batteries-included Python project that is:

- **uv-first**: reproducible installs with a committed `uv.lock`
- **fast to iterate**: one `just ci` command mirrors your local/CI checks
- **strict by default**: ruff for lint/format and basedpyright for type checking
- **optionally data- and docs-ready**: toggle NumPy/pandas and MkDocs during generation

This repo is the **template source** (a meta-project), not the generated project itself.

## What you get

- **Dependency workflow**: `uv` + lockfile-first installs (`uv sync --frozen`)
- **Quality gates**: ruff (format + lint), basedpyright (strict typing), pytest
- **Automation**: pre-commit hooks and a `justfile` with common commands
- **CI-ready defaults**: GitHub Actions workflow and coverage upload wiring (optional)
- **Update-friendly**: conservative `copier update` behavior via `_skip_if_exists`

## Quickstart: generate a new project

Prerequisites:

- Python 3.11+
- Git
- `copier` (installed however you prefer)

Generate a project from this repo root:

```bash
copier copy . /path/to/new-project --trust --defaults
```

Common flags:

- **`--defaults`**: accept defaults for all questions
- **`--trust`**: allow running post-generation tasks (install, format, type-check, hooks)
- **`--data key=value`**: answer questions non-interactively (useful in scripts/CI)

After generation, the new project will include a `justfile`. Typical first run:

```bash
just ci
```

## Template options (prompts)

During `copier copy`, you’ll be asked for:

- **Project identity**: `project_name`, `project_slug`, `package_name`, description, author, GitHub org/user
- **Python baseline**: minimum version (3.11 / 3.12 / 3.13)
- **Add-ons**:
  - **Docs**: MkDocs setup (`include_docs`)
  - **Data stack**: NumPy (`include_numpy`) and pandas (`include_pandas_support`)
- **Codecov**: leave the `codecov_token` prompt empty; prefer the GitHub secret described below

## Updating a generated project

Generated projects store answers in `.copier-answers.yml`. To update a project to the latest template:

```bash
copier update --trust --defaults
```

This template is intentionally conservative about overwriting user-edited files (see `copier.yml`’s `_skip_if_exists`).

## Developing this template

Install dev dependencies for the template repo (uses the committed lockfile):

```bash
just sync
```

Run the full local CI mirror:

```bash
just ci
```

Other useful commands:

- **`just fmt`**: format
- **`just lint`**: lint
- **`just type`**: type check
- **`just test`**: run template integration tests (renders the template and asserts output)

## FAQ

### Why is this “uv-first”?

Both this template repo and generated projects expect a committed `uv.lock`. In CI and locally, `uv sync --frozen` keeps installs reproducible and fails fast on drift.

### How does Codecov work in generated projects?

If you enable coverage upload in your CI setup, configure a **repository secret** named `CODECOV_TOKEN` in GitHub. You typically do not need to provide a token as a Copier answer.

## References

- Copier docs: `https://github.com/copier-org/copier`
