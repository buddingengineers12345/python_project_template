# .github/ — GitHub Actions Workflows (Meta-Repo)

This directory contains GitHub Actions workflows and community health files for
**this Copier template repository** (the meta-repo). These workflows test and maintain
the template itself, not the projects generated from it.

> [!NOTE]
> Generated projects get their own separate set of workflows from `template/.github/workflows/`.
> The meta-repo workflows here are not rendered into generated projects.

## Workflows

| File | Trigger | Purpose |
|---|---|---|
| `tests.yml` | push/PR to main, manual | Full pytest suite across Python 3.11–3.13 matrix; uploads coverage |
| `lint.yml` | push/PR to main | Ruff lint + format check + basedpyright type check |
| `security.yml` | push/PR to main, weekly schedule | pip-audit dependency vulnerability scan |
| `dependency-review.yml` | PR | Review dependency changes for security issues |
| `release.yml` | tag push (`v*`), manual (`workflow_dispatch`) | Bump version, create tag, publish GitHub Release |
| `pre-commit-update.yml` | weekly schedule, manual | Auto-update pre-commit hook versions via PR |
| `file-freshness.yml` | push to main, weekly schedule, manual | Run `scripts/repo_file_freshness.py` and commit artifacts |
| `sync-skip-if-exists.yml` | push to main, manual | Sync `_skip_if_exists` list in `copier.yml` via `scripts/sync_skip_if_exists.py` |
| `stale.yml` | daily schedule | Mark and close stale issues/PRs |
| `labeler.yml` | PR | Auto-label PRs based on changed file paths |

## Workflow design principles

All workflows follow these conventions:

- **Least-privilege permissions** — each workflow requests only the minimum `GITHUB_TOKEN`
  scopes it needs (typically `contents: read`; `contents: write` only for release/update workflows).
- **Concurrency cancellation** — `cancel-in-progress: true` prevents redundant runs on the
  same branch/PR.
- **`uv` for Python** — all Python steps use `uv` for fast, reproducible installs
  (`uv sync --frozen --extra dev`).
- **No pinned Python interpreter conflicts** — workflows use `uv`'s managed Python, not
  the GitHub-hosted runner's system Python.

## Release workflow (`release.yml`)

The release workflow can be triggered two ways:

1. **Manually** via `workflow_dispatch` — choose a bump type (`patch`/`minor`/`major`) or
   supply an explicit `X.Y.Z` version. The workflow calls `scripts/bump_version.py`, commits
   the version change, creates a tag, and publishes a GitHub Release.

2. **On tag push** (`v*`) — skips the bump step and publishes a release for the existing tag.
   Use this when you create a tag manually (e.g. via the `/release` Claude command).

The `/release` and `/validate-release` Claude slash commands orchestrate this flow locally
before pushing a tag.

## Template workflows vs meta-repo workflows

| Meta-repo (here) | Generated projects (`template/.github/workflows/`) |
|---|---|
| `tests.yml` — tests the template rendering | `ci.yml` — tests the generated project's code |
| `lint.yml` — lints meta-repo Python/tests | `lint.yml` — lints generated project code |
| `security.yml` — audits meta-repo deps | `security.yml` — audits generated project deps (conditional) |
| `release.yml` — releases the template | `release.yml` — releases the generated project (conditional) |
| `file-freshness.yml` — tracks template file age | _(no equivalent)_ |
| `sync-skip-if-exists.yml` — syncs copier.yml | _(no equivalent)_ |

## Other files

| Path | Purpose |
|---|---|
| `dependabot.yml` | Dependabot config for GitHub Actions version updates |
| `renovate.json` | Renovate bot config for dependency updates |
| `labeler.yml` | Label mapping for `labeler.yml` workflow |
| `ISSUE_TEMPLATE/` | Bug report and feature request templates |
| `PULL_REQUEST_TEMPLATE.md` | Default PR description template |

## Modifying workflows

- Run `just ci` before pushing — CI must pass locally before merging.
- After changing a workflow, check that the `sync-skip-if-exists.yml` does not need to be
  updated (it reads `copier.yml` `_skip_if_exists`).
- When bumping GitHub Actions versions (e.g. `actions/checkout@v4`), also update the
  corresponding actions in `template/.github/workflows/` so generated projects stay current.
