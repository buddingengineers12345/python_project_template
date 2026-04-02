# python_project_template — Claude Project Knowledge

## What this repo is

This repository is a **Copier template repository** (a meta-project). Running Copier against
this repo **generates** a new Python project by rendering the `template/` directory into a
destination folder.

> [!WARNING]
> Copier can run **template tasks** during `copier copy`/`copier update`. Only use the
> `--trust` flag with templates you trust.

## Directory structure

```
.
├── template/          # Jinja2 source files that Copier renders (includes `.claude/` for generated projects)
├── tests/             # pytest tests that render the template and assert output
├── scripts/           # Helper shell scripts for CI or local tasks
├── .github/           # GitHub Actions workflows
├── copier.yml         # Template prompts, computed vars, and post-gen tasks
├── justfile           # Task runner (use `just` not raw commands)
├── pyproject.toml     # Dev deps for THIS repo (not for generated projects)
├── .pre-commit-config.yaml
└── uv.lock            # Committed lockfile — never delete
```

## How to set up the development environment

```bash
uv sync --frozen --extra dev   # install all dev deps from the lockfile
just precommit-install         # register git hooks
```

Prerequisites: Python 3.11+, `uv`, `just`, `git`.

## Common development commands

| Task | Command |
|---|---|
| Run all tests | `just test` |
| Run tests in parallel | `just test-parallel` |
| Lint | `just lint` |
| Format | `just fmt` |
| Auto-fix lint issues | `just fix` |
| Type check | `just type` |
| Full CI locally | `just ci` |
| Sync deps after lockfile change | `just sync` |
| Upgrade all deps | `just update` |

**Always use `just` recipes.** Do not call `uv run ruff`, `pytest`, etc. directly —
the justfile handles the correct flags and order.

## Running the full CI pipeline

```bash
just ci
```

This runs in order: `fix` → `fmt` → `lint` → `type` → `test` → `precommit`.
All steps must pass before a PR is mergeable.

## Generating a test project from the template

To manually generate a project and inspect the output:

```bash
copier copy . /tmp/test-output --trust --defaults
```

To pass specific answers non-interactively:

```bash
copier copy . /tmp/test-output --trust \
  --data project_name="My Library" \
  --data include_docs=false \
  --data include_pandas_support=false
```

Clean up afterward: `rm -rf /tmp/test-output`

When iterating on an **uncommitted** local template, use **`copier copy --vcs-ref HEAD . DESTINATION`**
so Copier uses the current tree (otherwise it may select the latest PEP 440 tag and skip dirty files).

## Copy vs update (important)

- **Generate** a new project: `copier copy TEMPLATE DESTINATION`.
- **Update** an existing generated project to the latest template version: `copier update`.
- **`copier recopy`**: reapplies the template and keeps answers; does **not** use the smart merge
  algorithm. Prefer `copier update` for normal sync.

For updates, Copier works best when:

1. The template includes a valid `.copier-answers.yml`.
2. The template is versioned with git tags (PEP 440 versions).
3. The destination folder is versioned with git.

Useful flags: **`copier update --defaults`**, **`--data` / `--data-file`** for selective answer changes,
**`--vcs-ref=:current:`** to re-record answers without changing template version, **`copier check-update`**
(JSON via **`--output-format json`**, **`--quiet`** exit code `2` when an update exists).

### Never edit `.copier-answers.yml` by hand

Do not manually change the answers file (`.copier-answers.yml`, controlled by `_answers_file` in
`copier.yml`). The update algorithm relies on it and manual edits can lead to unpredictable diffs.

### Handle update conflicts

Default **`--conflict inline`** produces merge-style markers in files; **`--conflict rej`** writes
`*.rej` sidecars. Generated projects ship pre-commit hooks for both patterns (`check-merge-conflict`
and a fail-on-`*.rej` hook). Review conflicts before committing.

### Template `_tasks` on copy vs update

Post-generation **`_tasks`** in `copier.yml` run after both **`copier copy`** and **`copier update`**
(intentionally, so `uv.lock` and the dev environment stay aligned). Use **`copier update --skip-tasks`**
when you need to skip them.

### Maintainer: releases and `_migrations`

Tag releases with **PEP 440**-compatible versions so consumers’ `copier update` picks the right template
revision. Introduce **`_migrations`** in `copier.yml` when you need scripted steps across template
versions (e.g. renaming generated paths). Prefer SSH or credential-free Git URLs so `_src_path` in
answers files stays clean. Shallow template clones in CI can increase Git work for Copier; use full
clones if you hit resource issues.

## How tests work

Tests live in `tests/`. They use pytest to call `copier copy` programmatically,
render the template into a temporary directory, then assert that expected files
exist and contain expected content. When adding a new Copier variable or template
file, add a corresponding test.

## Copier variable conventions (copier.yml)

- Questions are defined under top-level keys in `copier.yml`.
- Computed values (not shown to users) use **`when: false`** with a **`default`** so they are not
  prompted or stored in the answers file.
- Use **`secret: true`** (with a **`default`**) for sensitive answers so they are not written to
  `.copier-answers.yml`.
- Post-generation `_tasks` run shell commands after rendering. Keep them idempotent.
- `_skip_if_exists` prevents overwriting user edits when running `copier update`.

## Jinja2 template conventions (template/)

- Template files use `{{ variable_name }}` for substitution.
- Conditional blocks use `{% if condition %}...{% endif %}`.
- File names can themselves be templated: e.g., `src/{{ package_name }}/__init__.py.jinja`.
- The `jinja2_time.TimeExtension` is available for `{% now %}` expressions.
- The `jinja2.ext.do` and `jinja2.ext.loopcontrols` extensions are also enabled.

## Code style

- Line length: 100 characters (set in pyproject.toml under `[tool.ruff]`).
- Target Python version: 3.11.
- Active ruff rules: E, F, I, UP, B, SIM, C4, RUF. Rule E501 (line too long) is ignored.
- Type annotations are required (basedpyright in strict mode via pre-commit).

## Files you should never modify directly

- `uv.lock` — regenerated by `just update`. Never hand-edit.
- `.copier-answers.yml` (appears in generated projects, not this repo) — managed by Copier.

## Files that are safe to delete for a clean slate

```bash
just clean   # removes build/, dist/, .pytest_cache, .ruff_cache, __pycache__, *.pyc
```
