# Git history size and maintenance

This document records how we keep the meta-repository’s object store lean, how to measure it, and when history rewrite is appropriate.

## Baseline metrics (recorded 2026-04-10)

Run these from the repository root after significant policy changes (freshness schedule, lockfile churn, large file adds).

```bash
git rev-list --count HEAD
git count-objects -vH
du -sh .git
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '/^blob/ {print $3, $4}' | sort -rn | head -20
```

Snapshot on 2026-04-10 (this clone):

- Commits: ~120
- `git count-objects` pack/loose: ~5.2 MiB counted objects; `.git` ~7.9 MiB on disk
- Largest historical blobs: repeated `uv.lock` revisions, `assets/file_freshness.json`, `tests/test_template.py`

Optional: install [git-sizer](https://github.com/github/git-sizer) for GitHub’s recommended complexity signals.

## CI checkout depth

| Workflow | `fetch-depth` | Rationale |
|----------|-----------------|-----------|
| [`file-freshness.yml`](../.github/workflows/file-freshness.yml) | `0` | `repo_file_freshness.py` walks Git history per file |
| [`sync-skip-if-exists.yml`](../.github/workflows/sync-skip-if-exists.yml) | `3000` | Matches `GIT_LOG_LIMIT` in `scripts/sync_skip_if_exists.py` (no need for full history beyond that window) |
| [`release.yml`](../.github/workflows/release.yml) | `1` | Release notes use `gh release create --generate-notes` (GitHub API); bump/tag steps need only the tip tree |
| [`tests.yml`](../.github/workflows/tests.yml), [`lint.yml`](../.github/workflows/lint.yml), [`security.yml`](../.github/workflows/security.yml), [`pre-commit-update.yml`](../.github/workflows/pre-commit-update.yml) | default (`1`) | No full-history Git commands |
| [`dependency-review.yml`](../.github/workflows/dependency-review.yml) | default | Keep aligned with [dependency-review-action](https://github.com/actions/dependency-review-action) guidance; set `fetch-depth: 0` only if the action fails to resolve the merge base |

## Freshness artifacts and `main`

The file freshness workflow commits generated reports and JSON under `docs/` and `assets/`. To limit commit noise on `main`, the schedule is **weekly** (see workflow). You can still run it manually via `workflow_dispatch` or locally with `just freshness`.

## Dependency updates

[`.github/dependabot.yml`](../.github/dependabot.yml) uses **weekly** schedules and **grouped** updates for both GitHub Actions and `uv`, which reduces the number of `uv.lock` blobs over time compared with many separate bumps.

`rebase-strategy: disabled` avoids constant PR rebases when the default branch moves (less churn; lockfile still updates on the Dependabot schedule).

## Pull requests and branches

- **GitHub merge and branch settings:** Use the single maintainer checklist [`github-repository-settings.md`](github-repository-settings.md) (squash merges, branch protection, required checks—not repeated here).
- **Prune stale local refs:** `git fetch --prune`
- **List merged local branches:** `git branch --merged main` (review then `git branch -d <branch>`)
- **Remote branches:** delete defunct branches on the host after merge (GitHub UI or `git push origin --delete <branch>`).

## Local housekeeping

Packing loose objects (does **not** remove old versions of tracked files):

```bash
git gc --prune=now
```

## When to rewrite history (rare)

Use **[git filter-repo](https://github.com/newren/git-filter-repo)** only if you must remove a path or large blob from **every** revision (for example, a committed secret or a multi-megabyte accidental add). This **rewrites SHAs**; all clones and forks must re-fetch or reset. It is **not** appropriate for routine maintenance of a public Copier template.

Do **not** use `git filter-branch` (deprecated). Replacing the entire history with a single squashed commit is almost never worth the coordination cost for this repository.

## What does not shrink history

- `.gitignore` and `git rm` only affect **future** commits.
- `git gc` compacts storage but keeps all reachable objects.
