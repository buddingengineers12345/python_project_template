# Template audit checklist (tracking)

All items from the original audit below are **done** in this repo (as of the commit that added this tracking header). The numbered sections are kept as the historical spec; trim or archive when you no longer need the detail.

| Ref   | Done | Implementation |
| ----- | ---- | ---------------- |
| 3.1   | Yes  | Explicit `_skip_if_exists` (no `*.md` glob); `scripts/sync_skip_if_exists.py` + `.github/workflows/sync-skip-if-exists.yml` |
| 3.2   | Yes  | `package_name` validator rejects leading digits |
| 3.3   | Yes  | `codecov_token` prompt removed; `docs/ci.md` + README “Continuous integration” |
| 3.5   | Yes  | `_tasks` bootstrap: `uv` on PATH, else `pip install uv`, else Astral install script |
| 3.7   | Yes  | Template `justfile.jinja`: `docs-serve`, `docs-build`, `docs-deploy` when `include_docs` |
| 3.8   | Yes  | `_set_env` is a dependency of `sync`, `test`, `test-parallel`, `coverage` (template + root `sync`) |
| 3.9   | Yes  | `install` uses `@just sync` / `@just precommit-install` |
| 3.12  | Yes  | `detect-secrets` + `.secrets.baseline` (repo + template) |
| 3.13  | Yes  | `.github/renovate.json` + template `renovate.json.jinja` with `pre-commit` enabled |
| 3.19  | Yes  | `[tool.basedpyright]` in root `pyproject.toml` and template `pyproject.toml.jinja` |
| 3.20  | Yes  | `[tool.coverage.*]` in both; template uses `source = ["src"]` and omits per policy |
| 4.1   | Yes  | `include_git_cliff`: `git-cliff` dependency group, `cliff.toml.jinja`, `just changelog` |
| 4.2   | Yes  | `.github/ISSUE_TEMPLATE/*`, `PULL_REQUEST_TEMPLATE.md` in template |
| 4.3   | Yes  | Root `CONTRIBUTING.md.jinja` |
| 4.4   | Yes  | `SECURITY.md.jinja` |
| 4.5   | Yes  | `release.yml` + `include_pypi_publish` (Trusted Publisher / `uv publish`) |
| 4.6   | Yes  | Renovate meta + generated `renovate.json` |
| 4.7   | Yes  | `include_cli` + Typer, `[project.scripts]`, `just run` |
| 4.8   | Yes  | `__version__` via `importlib.metadata.version("{{ package_name }}")` (matches `[project].name`) |
| 4.11  | Yes  | Expanded `tests/test_template.py` (combinations, validator, hooks, etc.); opt-in `RUN_TEMPLATE_INTEGRATION=1` runs `uv lock` + `uv sync --frozen` smoke |
| 4.13  | Yes  | `include_logging_setup` + `logging_config.py.jinja` |
| 4.14  | Yes  | Pinned docs extras incl. `mkdocs-gen-files`; Material theme in `mkdocs.yml.jinja` |

---

### 3.1 — `copier.yml`: `_skip_if_exists` wildcard is too broad

```yaml
_skip_if_exists:
  - "*.md"   # ← This skips ALL markdown files on updates
```

The wildcard `"*.md"` will prevent any generated markdown file (e.g., a `CHANGELOG.md` or `CONTRIBUTING.md` added to the template later) from ever being updated in existing projects. This makes template updates partially inert.

**Fix:** Be explicit. Replace `"*.md"` with only the files users are likely to edit:

```yaml
_skip_if_exists:
  - pyproject.toml
  - README.md
  - CONTRIBUTING.md
  - src/{{ package_name }}/__init__.py
  - mkdocs.yml
  - docs/
```

Write an agent that gets triggered automatically in the repo, that updates the _skip_if_exists section regularly based on the changes done to the repo. The agent should analyze the commit history and identify which files will be frequently modified by users. It should then update the `_skip_if_exists` section in the `copier.yml` file to include those files, ensuring that they are not overwritten during template updates. The agent should run on a regular schedule (e.g., weekly) to keep the `_skip_if_exists` section up to date with the latest changes in the repository.

---

### 3.2 — `copier.yml`: `package_name` validator allows digit-leading names

```yaml
validator: >-
  {% if not package_name.replace('_', '').isalnum() %}
  Package name must be a valid Python identifier ...
  {% endif %}
```

`isalnum()` on a string like `"1bad"` returns `True` after replacing underscores, but `1bad` is not a valid Python identifier (starts with a digit). The validator will incorrectly accept it.

**Fix:**

```yaml
validator: >-
  {% if not package_name.replace('_', '').isalnum() or package_name[0].isdigit() %}
  Package name must be a valid Python identifier (cannot start with a digit)
  {% endif %}
```

---

### 3.3 — `copier.yml`: `codecov_token` prompt is confusing and leaks into answers file

The prompt asks for a `codecov_token` string but the README says to set it as a GitHub secret and leave the field empty. Having the question appear interactively trains users to paste tokens into the Copier prompt, which then get saved in `.copier-answers.yml` and potentially committed to the repo.

**Fix:** Remove this question from `copier.yml` entirely. Document the GitHub secret approach only in the README and a generated `docs/ci.md` page.

---

### 3.5 — `copier.yml`: uv bootstrap via pip is fragile on systems without pip

```yaml
- command: python -m ensurepip --upgrade
- command: python -m pip install --upgrade pip
- command: python -m pip install --upgrade uv
```

`python -m ensurepip` fails on distro-managed Pythons (Debian/Ubuntu) where `ensurepip` is disabled. A better bootstrap pattern is to check for uv first.

**Fix:**

```yaml
- command: >-
    command -v uv >/dev/null 2>&1 ||
    (python -m pip install --upgrade uv 2>/dev/null ||
     curl -LsSf https://astral.sh/uv/install.sh | sh)
```

---
### 3.7 — `justfile`: Docs section is completely empty

```just
# -------------------------------------------------------------------------
# Docs (optional)
# -------------------------------------------------------------------------
```

This is a dead section. When `include_docs=true`, users who run `just --list` see no docs-related commands and must figure out MkDocs usage independently.

**Fix:** Add recipes (guarded by a comment or optional flag):

```just
docs-serve:
  @uv run --active mkdocs serve

docs-build:
  @uv run --active mkdocs build

docs-deploy:
  @uv run --active mkdocs gh-deploy --force
```

These should exist in the generated project's justfile when `include_docs=true` (handled in the template with a Jinja condition).

---

### 3.8 — `justfile`: `_set_env` recipe is defined but never used

```just
_set_env:
  @uv --version > /dev/null
```

This private recipe is defined but not called from any other recipe, making it dead code. Either wire it as a dependency of `sync`, `test`, etc., or remove it.

---

### 3.9 — `justfile`: `install` recipe calls bare `just` commands without `@`

```just
install:
  @python -m pip install --upgrade pip
  @python -m pip install --upgrade uv
  just sync               # ← no @, will echo the command expansion
  just precommit-install  # ← no @
```

Missing `@` before `just sync` and `just precommit-install` means just will print the expanded recipe text to stdout, breaking the clean output convention used everywhere else in the file.

**Fix:**

```just
install:
  @python -m pip install --upgrade pip
  @python -m pip install --upgrade uv
  @just sync
  @just precommit-install
```

---

### 3.12 — `.pre-commit-config.yaml`: No secret scanning hook

There is no hook to detect accidentally committed secrets (API keys, tokens, passwords). This is a common and serious mistake.

**Fix:** Add `detect-secrets` or `gitleaks`:

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

---

### 3.13 — `.pre-commit-config.yaml`: `pre-commit-hooks` version is not Renovate-pinned or noted for review

The comment says "Pin external hooks; review revs regularly (Renovate can help)" but there is no Renovate config in the repo. The advice is given without a mechanism to act on it.

**Fix:** Add a `.github/renovate.json` (see Section 4.6).


---

### 3.19 — `pyproject.toml`: No `[tool.basedpyright]` configuration

Basedpyright runs with all defaults, including permissive settings. For a template that advertises "strict typing", this is inconsistent.

**Fix:**

```toml
[tool.basedpyright]
pythonVersion = "3.11"
typeCheckingMode = "standard"
reportMissingImports = true
reportMissingTypeStubs = false
```

---

### 3.20 — `pyproject.toml`: No `[tool.coverage]` configuration

The `just coverage` recipe uses `--cov` but there is no `[tool.coverage.run]` or `[tool.coverage.report]` section, meaning coverage reports will have inconsistent results depending on the working directory.

**Fix:**

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
show_missing = true
skip_covered = false
```


---
### 4.1 — No CHANGELOG infrastructure

There is no changelog tooling. Projects generated from this template have no guidance on versioning or release notes.

**Recommendation:** Add `git-cliff` as an optional dev dependency with a `cliff.toml` configuration committed to the template. Add a `just changelog` recipe.

---

### 4.2 — No GitHub issue & PR templates

Generated projects have no `.github/ISSUE_TEMPLATE/` or `.github/pull_request_template.md`. This causes inconsistent bug reports and PRs.

**Recommendation:** Add to the template's `.github/` output:
- `ISSUE_TEMPLATE/bug_report.md`
- `ISSUE_TEMPLATE/feature_request.md`
- `pull_request_template.md`

---

### 4.3 — No `CONTRIBUTING.md` in generated projects

`CONTRIBUTING.md` is in `_skip_if_exists` but it's not clear if it's actually generated. Contributing guidelines are essential for open source projects.

**Recommendation:** Add a `CONTRIBUTING.md.jinja` template that covers: development setup, running tests, submitting PRs, and coding standards.

---

### 4.4 — No `SECURITY.md` in generated projects

There is no security disclosure policy template.

**Recommendation:** Add a minimal `SECURITY.md.jinja` with a supported versions table and a contact/reporting mechanism.

---

### 4.5 — No PyPI publish workflow in GitHub Actions

The `just publish` recipe calls `uv publish`, but there is no corresponding GitHub Actions workflow to automate releases. Users must trigger PyPI publishing manually.

**Recommendation:** Add a `release.yml` GitHub Actions workflow (triggered on tag push or GitHub Release creation) that builds and publishes to PyPI using OIDC trusted publishing (no long-lived API token needed).

---

### 4.6 — No Renovate / Dependabot configuration

Pre-commit hook revisions and GitHub Actions workflow versions will go stale with no automated update mechanism.

**Recommendation:** Add `.github/renovate.json` (preferred) or `.github/dependabot.yml`:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:base"],
  "pre-commit": { "enabled": true }
}
```

---

### 4.7 — No CLI scaffold option

The template has no option to generate a CLI entry point. Many Python libraries benefit from a command-line interface.

**Recommendation:** Add a `include_cli` boolean prompt. When `true`, generate:
- A `cli.py` stub using `typer` or `click`
- A `[project.scripts]` entry in `pyproject.toml.jinja`
- A `just run` recipe

---

### 4.8 — No `__version__` in generated `__init__.py`

Python packages should expose a version string. Without it, `importlib.metadata.version()` is the only way to get the version at runtime, and it requires the package to be installed.

**Recommendation:** In the generated `src/{{ package_name }}/__init__.py`:

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("{{ project_slug }}")
except PackageNotFoundError:
    __version__ = "unknown"
```

---

### 4.11 — Template tests are likely minimal

The `tests/` directory exists but only 3 commits total in the repo suggests tests may be placeholder only. A Copier template without comprehensive render tests is unreliable — a broken template will generate broken projects silently.

**Recommendation:** Add tests that:
- Render the template with all boolean combinations (`include_docs=true/false`, `include_numpy=true/false`, etc.)
- Assert generated files exist and have expected content
- Run `uv sync` on the generated output (smoke test)
- Test the `package_name` validator rejects invalid identifiers

---


### 4.13 — No logging setup scaffold

Projects commonly need a logging configuration. The generated code has no standard logging setup.

**Recommendation:** Add a `src/{{ package_name }}/logging.py` stub with a `configure_logging()` function and standard `structlog` or stdlib `logging` setup, guarded by an `include_logging_setup` prompt.

---

### 4.14 — MkDocs version and plugins not specified

When `include_docs=true`, the generated project gets MkDocs, but there is no specification of which MkDocs plugins are included. The `material` theme, `mkdocstrings`, and `mkdocs-gen-files` are standard companions.

**Recommendation:** In the template's `pyproject.toml.jinja`, the `docs` optional dependency group should pin:

```toml
docs = [
  "mkdocs>=1.6",
  "mkdocs-material>=9.0",
  "mkdocstrings[python]>=0.25",
]
```

And the generated `mkdocs.yml` should use Material theme by default.
