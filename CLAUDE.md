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
| Coverage report | `just coverage` |
| Lint | `just lint` |
| Format | `just fmt` |
| Auto-fix lint issues | `just fix` |
| Type check | `just type` |
| Docstring check | `just docs-check` |
| Pre-merge review | `just review` |
| Full CI locally | `just ci` |
| Sync deps after lockfile change | `just sync` |
| Upgrade all deps | `just update` |
| Diagnose environment | `just doctor` |

**Always use `just` recipes.** Do not call `uv run ruff`, `pytest`, etc. directly —
the justfile handles the correct flags and order.

## Running the full CI pipeline

```bash
just ci
```

This runs in order: `fix` → `fmt` → `lint` → `type` → `docs-check` → `test` → `precommit`.
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
- Active ruff rules: `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `D`, `C90`, `PERF`.
  Rule `E501` (line too long) is ignored (handled by the formatter).
- Docstring convention: **Google style** (`pydocstyle` via ruff `D` rules).
  Test files and scripts are exempt from docstring requirements.
- McCabe complexity: max 10 per function (`C90`).
- Type annotations are required on all public functions and methods (basedpyright `standard` mode).
- BasedPyright is lenient with external packages (`reportMissingTypeStubs = false`).

## Standards enforcement

Standards are enforced at four layers — during development, at commit, in review, and in CI.

### Tooling layer (always active)

| What | Tool | When |
|---|---|---|
| Lint + style | ruff | `just lint` / pre-commit / CI |
| Docstrings | ruff `D` rules (Google) | `just docs-check` / CI |
| Complexity | ruff `C90` (max 10) | `just lint` |
| Performance | ruff `PERF` | `just lint` |
| Types | basedpyright `standard` | `just type` / pre-commit / CI |
| Test coverage | pytest-cov (reported) | `just coverage` |

### Claude layer (automatic feedback during development)

Two **PostToolUse hooks** fire automatically when Claude edits a file:

- **`post-edit-python.sh`** — after any `.py` edit: runs ruff + basedpyright and surfaces
  violations back to Claude so it can self-correct in the same turn.
- **`post-edit-jinja.sh`** — after any `.jinja` edit: validates Jinja2 syntax using the same
  extensions Copier uses, catching template errors before `copier copy` time.

### Claude commands (on-demand workflows)

| Slash command | Purpose |
|---|---|
| `/review` | Full pre-merge checklist: lint + types + docstrings + test coverage + symbol scan |
| `/coverage` | Run coverage, identify gaps, write missing tests |
| `/docs-check` | Audit and repair Google-style docstrings across all source files |
| `/standards` | Consolidated pass/fail report across all checks — the "ready to merge?" gate |
| `/update-claude-md` | Sync CLAUDE.md against pyproject.toml + justfile to prevent drift |

### Definition of done

A feature or fix is **done** when all of the following are true:

1. `just ci` passes with zero errors.
2. Every new public function/class/method has a Google-style docstring.
3. Every new function/method has complete type annotations (parameters + return type).
4. At least one test case covers each new public symbol.
5. `just coverage` does not show a new module below its previous coverage level.
6. No `TODO` or `FIXME` comments are left in modified files (unless tracked as issues).
7. CLAUDE.md is up to date (`/update-claude-md` shows no drift).

## Markdown file placement rule

Any Markdown (`.md`) file you create as part of a workflow, analysis, or investigation output
**must be written inside the `docs/` folder**.

**Allowed exceptions (may be placed anywhere):**
- `README.md`
- `CLAUDE.md`

Do **not** create free-standing `.md` files (e.g. `ANALYSIS.md`, `LOGGING_ANALYSIS.md`,
`NOTES.md`) at the repository root or inside `src/`, `tests/`, `scripts/`, or any directory
outside `docs/`. This rule is enforced by `.claude/hooks/post-edit-markdown.sh`, which fires
after every file write and surfaces a violation message if the rule is broken.

## Files you should never modify directly

- `uv.lock` — regenerated by `just update`. Never hand-edit.
- `.copier-answers.yml` (appears in generated projects, not this repo) — managed by Copier.

## Files that are safe to delete for a clean slate

```bash
just clean   # removes build/, dist/, .pytest_cache, .ruff_cache, __pycache__, *.pyc
```

## Recent improvements (April 2026)

### Standards enforcement (this PR)
- Added `D` (pydocstyle, Google convention), `C90` (McCabe complexity), `PERF` (perflint) to ruff rules
- Added `per-file-ignores` so test files and scripts are exempt from docstring requirements
- Added `[tool.ruff.lint.mccabe]` max-complexity = 10
- Enhanced basedpyright config: `standard` mode, lenient with external stubs
- Added `pytest-cov` + `coverage[toml]` to dev dependencies
- Added `just docs-check` and `just review` recipes; `just ci` now includes docs-check
- Added `.claude/hooks/post-edit-python.sh` and `post-edit-jinja.sh` (PostToolUse hooks)
- Added five new Claude commands: `/review`, `/coverage`, `/docs-check`, `/standards`, `/update-claude-md`
- Added Standards Enforcement section to CLAUDE.md (definition of done, tooling table, command table)
- Propagated all of the above into `template/` so generated projects inherit the same enforcement

### Package structure
- Renamed `_support` package to `common` for clearer semantics
- Refactored support utilities into dedicated modules: `file_manager`, `logging_manager`, `decorators`, `utils`
- Enhanced logging manager with level-aware log functions for all severity levels

### Testing enhancements
- Added comprehensive test coverage for `common` utilities (`test_support.py`)
- Improved test organization with new `tests/` directory structure in generated projects
- Added parametrized tests for license rendering and feature combinations

### CI/CD improvements
- Updated GitHub Actions workflow versions for better compatibility
- Added `--frozen` flag to `uv sync/update` recipes for reproducible builds
- Added pre-commit hook to reject Copier rejection files (`*.rej`)
- Enhanced test matrix to include Python 3.13 testing

### Documentation scaffolding
- Added `docs/` directory template with MkDocs structure
- Added `index.md.jinja` documentation template
- Added `.claude/` commands for template-specific automation

### Release automation
- Added `release.yml` GitHub Actions workflow for automated version bumping and releases
- Integrated `scripts/bump_version.py` for PEP 440 version management
- Template now supports manual release triggering with configurable bump strategy
