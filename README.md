# Python Project Template

<!--
Badges: keep this row tight (5–8 max) and only include what is accurate for THIS repo.
-->

[![Lint](https://github.com/buddingengineers12345/python_project_template/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/buddingengineers12345/python_project_template/actions/workflows/lint.yml)
[![CI Tests](https://github.com/buddingengineers12345/python_project_template/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/buddingengineers12345/python_project_template/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-success.svg)](./LICENSE)
[![Copier](https://img.shields.io/badge/Template-Copier-blue.svg)](https://github.com/copier-org/copier)
[![uv](https://img.shields.io/badge/Dependency%20manager-uv-6f43ff.svg)](https://astral.sh/uv/)

✨ A **Copier template** for generating a modern Python project that is **uv-first**, **strict by default**, and easy to maintain.

> [!NOTE]
> This repository is the **template source** (a meta-project). To create a project, you **generate** into a new directory.

## Highlights ✨

- 🚀 **uv-first + lockfile-first**: reproducible installs with `uv.lock` and `uv sync --frozen`
- 🧹 **Quality gates**: ruff (format + lint), basedpyright (type checking), pytest
- 🛠️ **One-command workflows**: `just ci` mirrors what CI enforces
- 📚 **Optional docs**: MkDocs (toggle during generation)
- 📊 **Optional data stack**: NumPy and/or pandas (toggle during generation)
- 🔁 **Update-friendly**: conservative `copier update` behavior via `_skip_if_exists`

## Table of contents 🧭

- [Quickstart](#quickstart-)
- [Template options](#template-options-)
- [Updating a generated project](#updating-a-generated-project-)
- [Developing this template](#developing-this-template-)
- [FAQ](#faq-)

## Quickstart ⚡

Prerequisites:

- 🐍 Python 3.11+
- 🌱 Git
- 🧩 `copier`

Generate a project from this repo root:

```bash
copier copy . /path/to/new-project --trust --defaults
```

Then, inside the generated project, run:

```bash
just ci
```

### Useful Copier flags

- ✅ **`--defaults`**: accept defaults for all questions
- 🔒 **`--trust`**: allow post-generation tasks (bootstraps `uv`, installs deps, runs checks, installs hooks)
- 🤖 **`--data key=value`**: provide answers non-interactively (great for scripts)

## Template options 🧰

During `copier copy`, you’ll be prompted for:

- 🏷️ **Project identity**: `project_name`, `project_slug`, `package_name`, description, author, GitHub org/user
- 🐍 **Python baseline**: minimum version (3.11 / 3.12 / 3.13)
- ➕ **Add-ons**:
  - 📚 MkDocs (`include_docs`)
  - 📊 NumPy (`include_numpy`)
  - 🐼 pandas (`include_pandas_support`)

> [!TIP]
> For Codecov, prefer configuring the GitHub **repository secret** `CODECOV_TOKEN` rather than providing a token at generation time.

## Updating a generated project 🔁

Generated projects store answers in `.copier-answers.yml`. To update a project to the latest template:

```bash
copier update --trust --defaults
```

This template is intentionally conservative about overwriting user-edited files (see `copier.yml` → `_skip_if_exists`).

## Developing this template 🧪

Install dev dependencies for this template repo (uses the committed lockfile):

```bash
just sync
```

Run the full local CI mirror:

```bash
just ci
```

Other useful commands:

- 🧹 **`just fix`**: auto-fix lint issues
- ✨ **`just fmt`**: format
- 🔍 **`just lint`**: lint
- 🧠 **`just type`**: type check
- 🧪 **`just test`**: run template integration tests (renders the template and asserts output)

## FAQ ❓

### Why is this “uv-first”?

Both this template repo and generated projects expect a committed `uv.lock`. In CI and locally, `uv sync --frozen` keeps installs reproducible and fails fast on drift.

### How does Codecov work in generated projects?

If you enable coverage upload in your CI setup, configure a GitHub **repository secret** named `CODECOV_TOKEN`. You typically do not need to provide a token as a Copier answer.

## References 🔗

- Copier docs: `https://github.com/copier-org/copier`
