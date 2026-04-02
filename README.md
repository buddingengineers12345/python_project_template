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
- 🧪 **`--vcs-ref HEAD`**: when developing a **local** template clone, use the current working tree (including uncommitted changes). By default Copier may pick the latest PEP 440 **tag** instead of your dirty tree.
- ⏭️ **`--skip-tasks`**: render files without running `_tasks` (faster checks; tasks still run on `copier update` unless you pass `--skip-tasks` there too)

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

Use **`copier update --defaults`** to reuse all previous answers without re-prompting. To change one answer only:  
`copier update --defaults --data key=value`, or put overrides in a YAML file and use **`--data-file`**. To refresh answers against the template **without** bumping template version: **`copier update --vcs-ref=:current:`**.

**`copier recopy`** reapplies the template while keeping stored answers; it does **not** use Copier’s smart merge used by **`copier update`**. Prefer `copier update` for day-to-day sync; use `recopy` when recovering from a broken update or when you explicitly want a full re-application (then reconcile with Git).

**`copier check-update`** reports whether a newer template version exists (`--output-format json`, **`--quiet`** exits `2` when an update is available — useful in automation).

If Copier cannot apply some changes automatically, it either writes **inline conflict markers** (default, **`--conflict inline`**) or separate **`*.rej`** files (**`--conflict rej`**). Review and resolve before committing. Generated projects include pre-commit hooks: **`check-merge-conflict`** (inline) and a hook that rejects **`*.rej`** files if you use rejection-file mode.

Important:

- Never manually edit `.copier-answers.yml` — it can break Copier’s update algorithm.
- This template is intentionally conservative about overwriting user-edited files (see `copier.yml` → `_skip_if_exists`).
- Prefer **SSH** or a clean Git remote URL for the template so credentials do not end up inside `.copier-answers.yml`.

## Developing this template 🧪

### Maintainer notes (releases and migrations)

- **Version tags**: Consumers get the best `copier update` experience when this template uses **PEP 440**-compatible Git tags (Copier compares tags to choose versions).
- **`_migrations`**: When a template change is breaking (e.g. renaming paths or reshaping answers), consider adding **`_migrations`** in `copier.yml` with a **`version`** threshold so update-time scripts run in the right order. See Copier’s configuring and updating docs.
- **Shallow clones** of the template repo can make Copier’s Git usage heavier; prefer full clones in CI if you see resource issues.

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
