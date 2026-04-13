# tests/ — Template Test Suite

This directory contains pytest tests for the **Copier template meta-repo**. Tests validate
that the template renders correctly, that generated files have the right content, and that
optional features are gated properly.

## Layout

| Path | Purpose |
|---|---|
| `constants.py` | Shared `REPO_ROOT`, `TEMPLATE_ROOT`, and `COPIER_YAML` for imports from nested packages |
| `conftest.py` | Top-level pytest fixtures shared across all test tiers |
| `unit/` | Fast isolated tests for automation scripts in `scripts/` |
| `unit/conftest.py` | Fixtures shared within the unit tier |
| `integration/` | Tests exercising Copier copy/update across the full template |
| `integration/conftest.py` | Fixtures shared within the integration tier |
| `e2e/` | End-to-end tests (placeholder for external-facing scenarios) |
| `e2e/conftest.py` | Fixtures shared within the e2e tier |

## How `integration/test_template.py` works

1. Each test function calls `copier copy` (via `run_copy` or `run_command`) with
   `--vcs-ref HEAD` so it uses the current uncommitted tree.
2. The template is rendered into a `tmp_path` (pytest's temporary directory fixture).
3. Tests assert on the rendered file tree, file contents, and parsed TOML/YAML.
4. Most tests pass `--skip-tasks` to avoid running `uv lock` / `pre-commit install`
   during the test suite (integration tasks are slow and not needed for content assertions).
5. An optional `RUN_TEMPLATE_INTEGRATION=1` environment variable enables smoke tests
   that actually run `uv lock` and other post-generation tasks.

## Key helpers in `integration/test_template.py`

| Helper | Purpose |
|---|---|
| `run_copy(...)` | Call Copier programmatically via the Python API |
| `run_command(cmd, cwd)` | Run a subprocess and capture stdout/stderr |
| `get_default_command_list(test_dir)` | Build the standard `copier copy --vcs-ref HEAD ...` CLI invocation |
| `load_copier_answers(project_dir)` | Parse `.copier-answers.yml` from a generated project |
| `git_commit_all(project_dir, message)` | Create an initial commit in the generated project (needed for `copier update` tests) |
| `require_mapping(obj, name)` | Type-safe cast helper for `yaml.safe_load` results |

## Test categories

### Defaults and computed variables
- Verify defaults are applied when `--defaults` is used.
- Verify computed variables (`current_year`, `github_actions_python_versions`) are not stored
  in `.copier-answers.yml`.

### Validators
- Package name with digits, hyphens, or spaces is rejected with the appropriate error message.

### _skip_if_exists
- Verify that files in `_skip_if_exists` (e.g. `pyproject.toml`, `README.md`, `CLAUDE.md`)
  are not overwritten on `copier update` when they already exist with custom content.

### Optional features
- `include_docs=true/false` — MkDocs files appear/absent; `docs-serve`/`docs-build` in justfile.
- `include_cli=true/false` — `cli.py` appears; Typer dep in `pyproject.toml`.
- `include_git_cliff=true/false` — `cliff.toml` appears; `just changelog` in justfile.
- `include_pandas_support=true/false` — pandas in `pyproject.toml` dependencies.
- `include_numpy=true/false` — NumPy in `pyproject.toml` dependencies.
- `include_release_workflow=true/false` — `release.yml` workflow present/absent.
- `include_pypi_publish=true/false` — PyPI OIDC publish step in `release.yml`.
- `include_security_scanning=true/false` — `security.yml` + `dependency-review.yml` present/absent.

### License
- Parametrized over all five license options: MIT, Apache-2.0, BSD-3-Clause, GPL-3.0, Proprietary.
- Asserts the correct license text appears in `LICENSE`.

### Tool configuration
- `pyproject.toml` contains correct ruff rules, basedpyright mode, pytest settings.
- Meta-repo and generated `pyproject.toml`: `per-file-ignores` for `tests/**` and `scripts/**` skip `T20`
  only; ruff `D` applies to modules, classes, and functions (see `test_generated_pyproject_ruff_includes_print_rules`).
- `.pre-commit-config.yaml` contains basedpyright, ruff, detect-secrets hooks.
- `renovate.json` is valid JSON.

### Root/template sync
- `check_root_template_sync.py` policies stay consistent with root and `template/` files
  (workflow pins, justfile parity, etc.); covered by `scripts/test_root_template_sync.py`.

### Package structure
- `src/<package_name>/__init__.py`, `core.py`, `common/` modules all exist.
- `tests/<package_name>/test_core.py`, `test_support.py` exist.
- `conftest.py` exists.

### Logging layout
- `logging_manager.py` is present under `common/`.

### GitHub Actions
- `ci.yml` references the correct Python version matrix for each `python_min_version` choice.
- Optional workflows appear only when the corresponding feature flag is set.
- `docs/github-repository-settings.md` is always rendered (even when `include_docs=false`);
  see `test_github_repository_settings_doc_in_generated_project`.

## Running tests

`pyproject.toml` sets `pythonpath = ["."]` under `[tool.pytest.ini_options]` so nested test
packages can import `tests.constants`.
```bash
just test               # run all tests (quiet)
just test-parallel      # run all tests in parallel with pytest-xdist
just coverage           # run with coverage report
RUN_TEMPLATE_INTEGRATION=1 just test   # include slow integration tests
```

## Adding a new test

When you add a new Copier variable or template file:

1. Add a test that renders the template with the new option enabled/disabled.
2. Assert the correct file exists (or does not exist).
3. Assert key content within the file (e.g. a dependency name, a recipe name).
4. If the variable is stored in `.copier-answers.yml`, assert it appears there.
5. If the variable is computed (`when: false`), assert it is **absent** from `.copier-answers.yml`.

## Skipped tests

Some tests are decorated with `@pytest.mark.skip` with explicit reasons:

- Tests that run the full generated project's CI (too slow for the template test suite).
- Tests that require `basedpyright` in the generated project's virtualenv.
- Tests that depend on network access for `uv lock`.

Use `RUN_TEMPLATE_INTEGRATION=1` to opt in to these when validating a release.
