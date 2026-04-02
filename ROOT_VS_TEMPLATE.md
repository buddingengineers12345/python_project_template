# Root vs `template/`: structure and duplication

This repository is a **Copier template**: the **root** is the maintainer-facing repo (tests, lockfile, workflows that validate the template). The **`template/`** tree is what Copier renders into **new Python projects**. Many paths are **conceptual pairs** (same role, different filename: plain file at root vs `*.jinja` under `template/`).

The lists below use **git-tracked paths** only (see `git ls-files`).

---

## Similarities

### Shared purpose and “paired” artifacts

These pairs express the **same kind of configuration**, usually with Jinja variables and conditionals only in `template/`:

| Root | Template counterpart | Notes |
|------|----------------------|--------|
| `justfile` | `template/justfile.jinja` | Same overall recipe layout (fmt, lint, type, test, pre-commit, ci, clean, etc.); targets differ (`.` + template tests vs `src`/`tests/`). |
| `pyproject.toml` | `template/pyproject.toml.jinja` | Same Ruff line length (100) and overlapping rule philosophy; root is minimal **dev-only** metadata, template is a full **installable package** (Hatch, extras, optional docs/pandas/numpy). |
| `CLAUDE.md` | `template/CLAUDE.md.jinja` | Both are AI/editor onboarding; root describes **this repo**, template describes **generated projects**. |
| `README.md` | `template/README.md.jinja` | Root explains the template; template becomes the new project’s README. |
| `LICENSE` | `template/LICENSE.jinja` | Same legal role; template selects license via Copier. |
| `.gitignore` | `template/.gitignore.jinja` | Intended to stay in sync; see **Dissimilarities** (small drift today). |
| `.pre-commit-config.yaml` | `template/.pre-commit-config.yaml.jinja` | Nearly identical; minor whitespace/comment spacing differences only. |
| `.vscode/extensions.json` | `template/.vscode/extensions.json.jinja` | Maintained by copy script (see below). |
| `.vscode/launch.json` | `template/.vscode/launch.json.jinja` | Same. |
| `.vscode/settings.json` | `template/.vscode/settings.json.jinja` | Same. |
| `.github/workflows/lint.yml` | `template/.github/workflows/lint.yml.jinja` | Same **name** and coarse shape (uv, ruff format check, ruff lint); **behavior diverges** (versions, extra steps). |

### Deliberate sync mechanism

`scripts/update_files.sh` **copies** root files into template counterparts for:

- `.vscode/*.json` → `template/.vscode/*.jinja`
- `.gitignore` → `template/.gitignore.jinja`
- `.pre-commit-config.yaml` → `template/.pre-commit-config.yaml.jinja`

So those paths are **designed to be duplicates** after running the script; anything **not** in that script is at higher risk of **manual drift** (justfile, workflows, pyproject, CLAUDE, README).

### Overlapping CI philosophy

- Root **`lint.yml`** runs format check, Ruff, BasedPyright, and full **pre-commit** on all files.
- Template **`ci.yml.jinja`** splits **lint**, **typecheck**, and **matrix test** (plus optional **docs** workflow, Codecov). Generated projects get a **richer** default pipeline than the standalone root **`tests.yml`** alone.

---

## Dissimilarities

### Only at repository root (not under `template/`)

These exist to **build and maintain the template**, not to be copied wholesale into every generated project:

| Path | Role |
|------|------|
| `copier.yml` | Prompts, computed values, `_tasks`, `_exclude`, `_skip_if_exists`. |
| `tests/test_template.py` | Pytest suite that renders the template and asserts output. |
| `uv.lock` | Lockfile for **this** repo’s dev dependencies (Copier, pytest, etc.). |
| `scripts/update_files.sh` | Copies selected root files into `template/*.jinja`. |
| `.github/workflows/tests.yml` | CI for the **template repo** (pytest on push/PR); Python 3.11/3.12 matrix. |
| `.github/dependabot.yml` | Dependency updates for **this** GitHub repo. |
| `.claude/commands/*.md`, `.claude/settings.json` | Claude Code / editor automation for **maintainers** of the template repo. |

### Only under `template/` (not at root)

These are **generated-project** assets (or Copier plumbing):

| Path | Role |
|------|------|
| `template/{{_copier_conf.answers_file}}.jinja` | Copier answers file stub. |
| `template/mkdocs.yml.jinja`, `template/docs/index.md.jinja` | Optional docs site for **generated** projects (`include_docs`). |
| `template/.github/workflows/ci.yml.jinja` | Monolithic CI for generated repos (lint + type + tests + gate job). |
| `template/.github/workflows/docs.yml.jinja` | Docs build workflow (gated on `include_docs`). |
| `template/.github/renovate.json.jinja` | Renovate config for **generated** repos (contrast with root Dependabot). |
| `template/.github/CODEOWNERS.jinja`, `CODE_OF_CONDUCT.md.jinja`, `CONTRIBUTING.md.jinja`, `ISSUE_TEMPLATE/*`, `PULL_REQUEST_TEMPLATE.md.jinja` | Community / governance files for **new** repositories. |
| `template/src/{{ package_name }}/**` | Application/library skeleton. |
| `template/tests/**` | Generated test layout and import smoke test. |

### Same “slot,” different content (noteworthy drift)

1. **GitHub Actions action versions**  
   Root workflows tend to use **newer** pins (e.g. `actions/checkout@v6`, `astral-sh/setup-uv@v7`). Template workflows often use **older** pins (`checkout@v4`, `setup-uv@v5`). Same idea, different freshness.

2. **`lint.yml` vs `lint.yml.jinja`**  
   Root runs **BasedPyright** and **pre-commit** in the lint job. Template `lint.yml.jinja` stops after **Ruff** (type-checking lives in **`ci.yml.jinja`** as a separate job). So “Lint” is not the same step boundary across root vs generated projects.

3. **Test orchestration**  
   Root has a dedicated **`tests.yml`** (pytest, two Python versions). Template embeds tests in **`ci.yml.jinja`** with a **dynamic matrix** from `github_actions_python_versions` in `copier.yml` and adds **coverage** + optional **Codecov**.

4. **`justfile` vs `justfile.jinja`**  
   - Root `sync`/`update` use `--frozen --extra dev`; template uses extras for **test** and optional **docs**, and template `sync`/`update` omit `--frozen` in the recipes (relying on lockfile from post-gen tasks).  
   - Template duplicates a section header around the `ci` recipe (“CI (local mirror…)”) compared to root’s cleaner `static_check` + `ci` split.  
   - Root `test` targets the repo root; template scopes Ruff/pytest to **`src`** and **`tests/`**.

5. **`.gitignore` vs `.gitignore.jinja`**  
   Root includes **`.claude/todos/`** (Claude Code local state). Template copy has an stray line **`1`** under “Specific files to ignore” and **omits** `.claude/todos/`. So the copy script has not produced a byte-identical pair.

6. **`pyproject.toml` vs `pyproject.toml.jinja`**  
   Root has **no** `[build-system]` / Hatch / package layout; template is a full package with **optional** `docs` extra, **test** extra with coverage tools, and stricter Ruff configuration (extra rules, `src` layout). They should **not** be merged blindly.

---

## Pairs worth aligning (recommended)

These reduce maintainer confusion and avoid “fixed in root, forgot template” (or the reverse):

| Pair | Why align |
|------|-----------|
| `.github/workflows/lint.yml` ↔ `template/.github/workflows/lint.yml.jinja` | Same **action major versions** and a documented split: either template lint also runs pre-commit, or document that **CI** is the single source of truth for typecheck/pre-commit in generated repos. |
| `.gitignore` ↔ `template/.gitignore.jinja` | Remove the erroneous **`1`** in the template; decide whether generated projects should ignore **`.claude/todos/`** like the template repo, then re-run `scripts/update_files.sh`. |
| `justfile` ↔ `template/justfile.jinja` | Fix duplicate heading in template; consider whether `sync`/`update` in generated projects should use **`--frozen`** consistently with root and with `copier.yml` post-gen `uv sync --frozen`. |
| Any workflow using `uv` / `actions/checkout` | Periodically bump template pins to match root **or** automate with Renovate/Dependabot notes so both stay in policy. |

Optional: extend **`scripts/update_files.sh`** (or `just` recipes) to copy or validate more pairs—only where the **content** should truly stay identical (not `pyproject` or `CLAUDE`).

---

## Pairs that should stay different (by design)

| Root-only or template-only | Reason |
|----------------------------|--------|
| `copier.yml`, `tests/test_template.py`, `uv.lock` | Template **repository** infrastructure; never part of a generated library. |
| `template/{{_copier_conf.answers_file}}.jinja` | Copier-specific. |
| `pyproject.toml` vs `template/pyproject.toml.jinja` | Different products: **meta-repo** vs **shippable package** with extras and metadata. |
| `CLAUDE.md` vs `template/CLAUDE.md.jinja` | Different audiences and content. |
| `README.md` vs `template/README.md.jinja` | Template marketing vs end-user project readme. |
| `.github/dependabot.yml` vs `template/.github/renovate.json.jinja` | Two valid strategies; merging would lose intentional choice for generated repos. |
| `template/.github/workflows/ci.yml.jinja`, `docs.yml.jinja`, community templates | Apply to **consumer** repositories, not to this Copier source repo. |
| `template/src/**`, `template/tests/**` | Only meaningful after rendering with a concrete `package_name`. |
| `.claude/**` at root | Maintainer tooling; optional to expose in every generated project. |

---

## Quick reference: tracked file counts

- **Root (excluding `template/`):** 22 tracked paths (including `template/` subtree counted separately below).
- **`template/` subtree:** 33 tracked `*.jinja` (and templated paths under `src/` / `tests/`).

For an authoritative list, run:

```bash
git ls-files | grep -v '^template/' | sort
git ls-files template/ | sort
```

---

*Generated as a structural comparison of the repository layout and representative file contents; re-run the copy script and diff after changes to root files that participate in `scripts/update_files.sh`.*
