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

> [!WARNING]
> Generate from **trusted templates**: when a template uses Copier `tasks`, they run with the
> same access level as your user.

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
- 📌 **`--data-file path.yml`**: provide answers from a YAML file
- 🔖 **`--vcs-ref ref`**: generate from a specific git ref (tag/branch/commit) of the template

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

Generated projects store answers in `.copier-answers.yml`.

For the update to work best, ensure:

1. The template includes a valid `.copier-answers.yml`
2. The template is versioned with git tags
3. The destination folder is versioned with git

Then, from inside the generated project folder (make sure `git status` is clean), run:

```bash
copier update --trust
```

If Copier cannot apply some changes automatically, it may produce `*.rej` files containing unresolved diffs.
Review and resolve those before committing.

Important:

- Never manually edit `.copier-answers.yml` — it can break Copier’s update algorithm.
- This template is intentionally conservative about overwriting user-edited files (see `copier.yml` → `_skip_if_exists`).

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

## Releasing this template 🏷️

This repo uses a manually-triggered GitHub Actions workflow to bump the template repo version, tag it, and create a GitHub Release.

To cut a release:

1. Go to GitHub Actions → workflow `Release`
2. Click “Run workflow”
3. Choose either:
   - `bump`: `patch` / `minor` / `major`, or
   - `version`: an explicit `X.Y.Z` (overrides `bump`)

The workflow will:

- Update `[project].version` in `pyproject.toml`
- Commit the change
- Create and push a tag `vX.Y.Z`
- Create a GitHub Release with auto-generated release notes

## FAQ ❓

### Can Copier be applied over a preexisting project?

Yes. Copier understands this use case (it powers features like updating).

### Should I edit `.copier-answers.yml` manually?

No. Updates rely on that file; editing it manually can lead to unpredictable diffs.

### Why is this “uv-first”?

Both this template repo and generated projects expect a committed `uv.lock`. In CI and locally, `uv sync --frozen` keeps installs reproducible and fails fast on drift.

### How does Codecov work in generated projects?

If you enable coverage upload in your CI setup, configure a GitHub **repository secret** named `CODECOV_TOKEN`. You typically do not need to provide a token as a Copier answer.

## References 🔗

- Copier docs: `https://github.com/copier-org/copier`
- Copier docs (official): generating, updating, configuring, FAQ
- `https://copier.readthedocs.io/en/stable/creating/`
- `https://copier.readthedocs.io/en/v6.0.0/updating/`
- `https://copier.readthedocs.io/en/stable/configuring/`
- `https://copier.readthedocs.io/en/stable/faq/`
