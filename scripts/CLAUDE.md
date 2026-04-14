# scripts/ — Automation Scripts

This directory contains Python and shell scripts for CI automation and local maintenance
tasks. Scripts are invoked via `just` recipes or GitHub Actions workflows.

> [!NOTE]
> Scripts follow the same **Google-style docstrings** as the rest of the repo (ruff `D`). Only **`T20`**
> (`print`) is ignored under `scripts/**` so CLI output stays simple.

## Scripts

### `repo_file_freshness.py`

Generates a Git-history-based file freshness dashboard for the repository.

**Invocation:** `just freshness` → `uv run python scripts/repo_file_freshness.py`

**What it does:**
- Queries `git ls-files` for all tracked files.
- For each file, runs `git log -1` to get the last commit date and hash.
- Classifies files as **green** (recently updated), **yellow** (aging), **red** (stale),
  or **blue** (ignored via `assets/freshness_ignore.json`).
- Writes three output artifacts:
  - `docs/repo_file_status_report.md` — human-readable dashboard table
  - `assets/file_freshness.json` — per-file details (date, hash, status, commit count)
  - `assets/freshness_summary.json` — aggregate counts + optional badge metadata

**CLI flags:**

| Flag | Default | Purpose |
|---|---|---|
| `--repo-root PATH` | `.` | Repository root to scan |
| `--metric commits\|days` | `commits` | Classification metric |
| `--ignore-config PATH` | `assets/freshness_ignore.json` | Glob patterns to mark blue |

**Thresholds (commits metric):**
- green: ≥ 3 commits
- yellow: 1–2 commits
- red: 0 commits (file has never been updated after initial add)

**Tested by:** `tests/scripts/test_repo_file_freshness.py`

---

### `bump_version.py`

Bumps the PEP 440 version string in `pyproject.toml`.

**Invocation:** `python scripts/bump_version.py --bump patch`

**What it does:**
- Reads the `version = "X.Y.Z"` line from `[project]` in `pyproject.toml`.
- Increments the requested component (patch / minor / major).
- Writes the updated version back to the file in-place.

**CLI flags:**

| Flag | Purpose |
|---|---|
| `--bump patch\|minor\|major` | Increment the specified version component |
| `--new-version X.Y.Z` | Set an explicit version (overrides `--bump`) |
| `--pyproject PATH` | Path to `pyproject.toml` (default: `pyproject.toml`) |

**Used by:** `.github/workflows/release.yml` and the `/release` Claude slash command.

**Output:** Prints the new version string to stdout (e.g. `0.0.6`), which callers capture
via `$(python scripts/bump_version.py --bump patch)`.

**Generated projects:** Copier renders `src/<package>/common/bump_version.py` from
`template/.../bump_version.py.jinja`. That module uses Google-style docstrings like the rest of
`src/`; the generated `pyproject.toml` does not exempt it from ruff `D`. The version line is emitted
via `logging_manager.write_machine_stdout_line` (T20 still enforces no `print()` in that file).

---

### `pr_commit_policy.py`

Validates pull request titles and bodies (against `.github/PULL_REQUEST_TEMPLATE.md`) and
conventional commit subjects over a `git rev-list` range.

**Invocation:**

- CI / check: `python3 scripts/pr_commit_policy.py pr` with `PR_TITLE` and `PR_BODY` set, or
  `python3 scripts/pr_commit_policy.py commits` with `PR_BASE_SHA` and `PR_HEAD_SHA` (or
  `--base` / `--head`).
- Local automation: `just pr-draft` → `pr_commit_policy.py draft` prints a Conventional
  Commits title (from `type/slug-branch` or the latest valid commit subject) and a PR body
  from `.github/PULL_REQUEST_TEMPLATE.md` with *Changes introduced* bullets from
  `git log <base>..HEAD` (default base: `origin/main` or `main`).

**Used by:** `.github/workflows/pr-policy.yml` (and the generated-project copy from `template/`).

**Tested by:** `tests/scripts/test_pr_commit_policy.py`

---

### `check_root_template_sync.py`

Validates that root and `template/` stay aligned on configured paths (for example GitHub
Actions pins, shared recipes, and other policy maps).

**Invocation:** `just sync-check` → `uv run python scripts/check_root_template_sync.py`

**What it does:**
- Loads JSON policy maps under the repo (workflow action versions, justfile parity rules, etc.).
- Compares root files to their `template/` counterparts and fails with a diff on drift.

**Used by:** `.github/workflows/lint.yml` (meta-repo CI) and `just check` / `just sync-check`.

**Tested by:** `tests/scripts/test_root_template_sync.py`

---

### `sync_skip_if_exists.py`

Synchronises the `_skip_if_exists` list in `copier.yml` with the actual template file paths
and their commit frequency.

**Invocation:** Called by `.github/workflows/sync-skip-if-exists.yml` on push to `main`.

**What it does:**
- Scans `template/` for all tracked paths.
- For each path, checks the Git commit frequency to determine if it is user-customisable
  (high churn = likely user-edited → should be in `_skip_if_exists`).
- Produces a suggested diff to `copier.yml`'s `_skip_if_exists` list.

---

## Adding a new script

1. Place the script in this directory.
2. Add a `just` recipe if the script is run regularly (see `justfile`).
3. If it produces output files, write them to `docs/` (Markdown) or `assets/` (JSON/data).
4. Add a GitHub Actions workflow under `.github/workflows/` if it should run in CI.
5. Update this file with a description of the new script.
