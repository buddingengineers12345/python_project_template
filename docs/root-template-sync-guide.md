# Keeping the Root and `template/` Trees in Sync

A deep-dive on why this repository has two near-identical copies of many files, where
the duplication actually lives, and a concrete, layered strategy for keeping the two
trees from drifting apart on GitHub.

---

## 1. Why the duplication exists in the first place

This repo is a **Copier template meta-project**. It has two roles that *look* alike
but serve very different purposes:

| Tree | Purpose | Who consumes it |
|---|---|---|
| **Root** (`./justfile`, `./pyproject.toml`, `./.claude/...`, `./.github/workflows/...`, `./scripts/...`) | The meta-repo's **own** project — it is "self-hosting." The root files are what lint, test, and release *this* repo. | Maintainers of the template itself. |
| **`template/`** (`template/justfile.jinja`, `template/pyproject.toml.jinja`, `template/.claude/...`, `template/.github/workflows/*.jinja`, `template/scripts/*.jinja`) | Jinja2 source files that Copier renders into a **new** Python project. | Downstream users who run `copier copy`. |

Many of those files are 90%+ identical because the meta-repo "eats its own dog food":
the tooling we want consumers to receive is the same tooling we use on ourselves. But
they can never be *exactly* identical because:

- Template files contain Jinja expressions (`{{ package_name }}`, `{% if include_docs %}`).
- Template files often have a `.jinja` suffix.
- Root files use concrete values (this repo's package name, license, Python version).
- Some hooks and workflows are meta-repo-only (e.g. `pre-write-jinja-syntax.sh`,
  `sync-skip-if-exists.yml`) and some are generated-project-only (e.g.
  `pre-bash-branch-protection.sh`, `post-write-test-structure.sh`).

The result is three logical classes of files, and the maintenance strategy has to
treat each class differently.

---

## 2. Inventory: what actually overlaps today

I walked the two trees and grouped every pair by relationship.

### 2.1 Exact-parity pairs (must be byte-identical modulo line endings)

These are shell hooks and other plain files copied verbatim into `template/`:

- `.claude/hooks/pre-bash-block-no-verify.sh` ↔ `template/.claude/hooks/pre-bash-block-no-verify.sh`
- `.claude/hooks/pre-bash-git-push-reminder.sh` ↔ `template/.claude/hooks/pre-bash-git-push-reminder.sh`
- `.claude/hooks/pre-bash-commit-quality.sh` ↔ same under `template/`
- `.claude/hooks/pre-bash-coverage-gate.sh` ↔ same
- `.claude/hooks/pre-config-protection.sh` ↔ same
- `.claude/hooks/pre-protect-uv-lock.sh` ↔ same
- `.claude/hooks/pre-write-src-require-test.sh` ↔ same
- `.claude/hooks/pre-write-src-test-reminder.sh` ↔ same
- `.claude/hooks/post-edit-python.sh` ↔ same
- `.claude/hooks/post-edit-markdown.sh` ↔ same
- `.claude/hooks/post-edit-refactor-test-guard.sh` ↔ same

These are the ones that bite hardest when they drift — fixing a bug in one and
forgetting the other is the single most common regression.

### 2.2 "Same content, different skin" pairs (Jinja-rendered)

Identical logic, but the template copy has variables, conditionals, or a `.jinja`
suffix:

- `justfile` ↔ `template/justfile.jinja` (291 vs 277 lines; differ mostly in Jinja
  conditionals for optional features).
- `pyproject.toml` ↔ `template/pyproject.toml.jinja` (154 vs 235 lines; template is
  larger because it carries feature-gated dependency blocks).
- `CLAUDE.md` ↔ `template/CLAUDE.md.jinja` (410 vs 330 lines).
- `README.md` ↔ `template/README.md.jinja`.
- `LICENSE` ↔ `template/LICENSE.jinja`.
- `env.example` ↔ `template/env.example.jinja`.
- `.github/workflows/lint.yml` ↔ `template/.github/workflows/lint.yml.jinja`.
- `.github/workflows/security.yml` ↔ `template/.github/workflows/security.yml.jinja`.
- `.github/workflows/pre-commit-update.yml` ↔ same.jinja.
- `.github/workflows/release.yml` ↔ same.jinja.
- `.github/workflows/dependency-review.yml` ↔ same.jinja.
- `.github/workflows/labeler.yml` ↔ same.jinja.
- `scripts/pr_commit_policy.py` ↔ `template/scripts/pr_commit_policy.py.jinja`.

These can't be byte-equal, but they must agree on *structural* invariants — the same
action pins, the same ruff rule codes, the same justfile recipe names, the same CI
job IDs.

### 2.3 Tree-exclusive files (intentionally only on one side)

Root-only (meta-repo infrastructure):

- `scripts/check_root_template_sync.py`, `repo_file_freshness.py`, `bump_version.py`,
  `sync_skip_if_exists.py`, `validate_dor.py`, `preflight.sh`.
- `.claude/hooks/pre-write-jinja-syntax.sh`, `post-edit-jinja.sh`,
  `post-edit-copier-migration.sh`, `post-edit-template-mirror.sh`,
  `pre-compact-save-state.sh`, `pre-suggest-compact.sh`, `pre-write-doc-file-warning.sh`,
  `stop-*`, `session-start-bootstrap.sh`, `post-bash-pr-created.sh`,
  `pre-protect-readonly-files.sh`.
- `.github/workflows/ci.yml` (meta-repo composite), `file-freshness.yml`,
  `stale.yml`, `sync-skip-if-exists.yml`, `tests.yml`, `pr-policy.yml`.
- `copier.yml`, `assets/`, `temp_*`.

Template-only (generated-project-specific):

- `template/.claude/hooks/pre-bash-branch-protection.sh`,
  `pre-delete-protection.sh`, `post-bash-test-coverage-reminder.sh`,
  `post-write-test-structure.sh`.
- `template/.claude/commands/`, `template/.claude/rules/`, `template/.claude/skills/`.
- `template/{{_copier_conf.answers_file}}.jinja`, `template/src/`, `template/tests/`,
  `template/docs/`, feature-gated files (`{% if include_docs %}mkdocs.yml{% endif %}.jinja`,
  `{% if include_git_cliff %}cliff.toml{% endif %}.jinja`), etc.
- `template/.github/workflows/ci.yml.jinja`, `docs.yml.jinja`.

These don't need to be kept in sync at all; the sync tooling must know to skip them.

---

## 3. The recommended layered strategy

No single mechanism covers all three classes cleanly, so the strategy is layered.
Each layer is cheap, and each one catches a different class of drift.

### Layer 1 — Declarative sync map (source of truth)

The file that enumerates "these pairs must agree" is
[`assets/root-template-sync-map.yaml`](../assets/root-template-sync-map.yaml). It's already
partially populated. It supports three kinds of check (implemented in
`scripts/check_root_template_sync.py`):

| Check type | What it enforces | Use for |
|---|---|---|
| `exact_file_pairs` | Byte-identical content (newline-normalized). | Class 2.1 hooks. |
| `workflow_action_versions` | Same `uses: owner/repo@version` pins. | Class 2.2 workflows. |
| `pyproject_sections` | Same keys and same `select = [...]` codes inside named TOML sections. | Class 2.2 `pyproject.toml`. |

**Action item:** grow the map to cover every pair listed in §2.1 and §2.2. Any file
that is *intentionally* divergent should be added to an `exclusions` block with a
comment explaining why — this turns tribal knowledge into a reviewable artifact.

### Layer 2 — Local verifier (`just sync-check`)

Already wired up (`justfile` target `sync-check` → `scripts/check_root_template_sync.py`).
It's fast (<1s), has zero dependencies, and returns a non-zero exit code on drift.
This is the canonical local command engineers run before pushing.

### Layer 3 — Pre-commit hook

Add `sync-check` to `.pre-commit-config.yaml` as a `local` hook that runs only when
files under `.claude/hooks/**`, `template/**`, `.github/workflows/**`, `justfile*`,
`pyproject.toml*`, `CLAUDE.md*`, or `README.md*` are staged:

```yaml
- repo: local
  hooks:
    - id: root-template-sync
      name: root/template sync policy
      entry: uv run scripts/check_root_template_sync.py
      language: system
      pass_filenames: false
      files: '^(\.claude/hooks/|template/|\.github/workflows/|justfile|pyproject\.toml|CLAUDE\.md|README\.md)'
```

This catches drift at commit time without slowing down unrelated commits.

### Layer 4 — CI required check on every PR

Add a job to `.github/workflows/lint.yml` (or a dedicated `sync.yml`) that runs
`just sync-check`. Mark it **required** in branch protection so a PR that drifts the
two trees cannot be merged — this is the only layer that enforces against contributors
who bypass pre-commit locally.

```yaml
sync-map:
  name: root/template sync
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v5
    - run: just sync-check
```

### Layer 5 — Scheduled drift audit (weekly)

Even with required checks, pairs can drift when only one side is edited in a way
that still parses. A weekly cron workflow runs `sync-check` against `main` and opens
an issue (via `peter-evans/create-issue-from-file`) if it fails. This catches
slow-burn regressions — e.g. someone added a new ruff rule to root `pyproject.toml`
six months ago and no one noticed it never landed in the template.

```yaml
on:
  schedule:
    - cron: '0 7 * * 1'    # Monday 07:00 UTC
  workflow_dispatch:
```

### Layer 6 — CODEOWNERS + PR template nudge

Create `.github/CODEOWNERS` entries that require a second reviewer on cross-tree
changes, and add a PR template checklist item:

> - [ ] If this PR edits `.claude/hooks/`, `.github/workflows/`, or a top-level
>   config file, the matching `template/` copy has been updated (or `sync-check`
>   confirms no mirror is expected).

This turns the invariant into a social contract on top of the mechanical check.

### Layer 7 — Single-source tactics (advanced, optional)

For the hardest-hit files — the §2.1 exact-parity hooks — you can eliminate
duplication entirely. Two low-risk options:

1. **Generate at render time.** Keep only `.claude/hooks/*.sh` in root. Add a
   `_tasks` step at the top of `copier.yml` that copies root hooks into the target
   project after rendering the rest of `template/`. Downside: people browsing the
   template on GitHub no longer see what consumers will receive; discoverability
   drops.
2. **Generate at commit time.** Keep only `.claude/hooks/*.sh` in root. A pre-commit
   hook mirrors the files into `template/.claude/hooks/` on every commit. The
   template tree is auto-regenerated and always in sync; reviewers still see both
   trees in diffs.

Option 2 gives you the best of both worlds: no manual duplication, no loss of GitHub
visibility. The added complexity is a single mirror script that sync-check can also
run in `--fix` mode.

For class 2.2 files (Jinja-rendered), single-sourcing is harder and usually not
worth it — the template copy diverges in small but meaningful ways. Stick with
invariant-level checks (workflow actions, pyproject sections, justfile recipe names)
rather than trying to single-source them.

### Layer 8 — Per-class helper scripts

Two small, high-leverage additions to `scripts/`:

- `scripts/diff_root_template.py`: print a side-by-side diff of every mapped pair,
  ignoring known Jinja tokens. Useful during a release to eyeball drift at a glance.
- `scripts/mirror_exact_pairs.py`: apply the §2.1 rule mechanically —
  `cp .claude/hooks/X template/.claude/hooks/X` for every pair in the map. Run by
  the Layer 7 option 2 pre-commit hook.

Both can live behind `just sync-fix` and `just sync-diff` recipes.

---

## 4. Putting it together: the "done" definition for sync

A change that touches any file in §2.1 or §2.2 is considered merge-ready only when:

1. The corresponding counterpart file has been updated in the same PR.
2. `just sync-check` exits 0 locally.
3. The `root/template sync` CI job is green.
4. The PR description's checklist item is ticked.
5. The sync map (`assets/root-template-sync-map.yaml`) has been updated if the PR
   added or removed a pair.

If you only remember one thing from this document: **add every new root/template
pair to the sync map in the same commit that introduces it.** The map is the
mechanism that turns "I should remember to mirror this" into "the CI will yell at
me if I forget." Everything else in this guide is scaffolding around that one habit.

---

## 5. Workflow recap

| When | Who | What |
|---|---|---|
| Authoring a hook or workflow | contributor | Edit both copies; run `just sync-check`. |
| Staging commits | pre-commit | Layer 3 runs `sync-check` if relevant paths are staged. |
| Opening a PR | GitHub Actions | Layer 4 runs `sync-check` as a required check. |
| Weekly | scheduled workflow | Layer 5 audits `main` and files an issue on drift. |
| On review | reviewer + CODEOWNERS | Layer 6 checklist confirms template counterpart is updated. |
| On release | maintainer | Run `just sync-diff` (Layer 8) to eyeball drift across every mapped pair. |

With those six checkpoints in place, a file can't cross the main-branch gate in only
one tree — and the two trees stop drifting for reasons other than deliberate,
reviewed divergence.
