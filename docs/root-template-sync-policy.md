# Root-Template Sync Policy

## Why this policy exists

This repository contains two different products:

- `root/` is the maintainer/meta-repo used to develop and release the Copier template.
- `template/` is the rendered-project blueprint consumed by end users.

Some files should evolve together across both trees, while others must stay intentionally
different. This document defines those boundaries and the automation that enforces them.

## Decision rules

Use these rules in order:

1. If a file controls template-maintainer workflows, keep it root-only.
2. If a file controls generated-project behavior, keep it template-only.
3. If a file encodes shared standards (lint/type/test/hook conventions), sync it explicitly.
4. Never blind-copy whole files across trees when Jinja conditionals or audience differ.

## Sync classifications

- `must_sync`: Content (or normalized content) is expected to match.
- `sync_structure_only`: Selected sections/keys must match; full content may differ.
- `intentionally_divergent`: Not enforced by parity checks; divergence is expected.

## Counterpart inventory

| Root | Template | Classification | Default direction |
|---|---|---|---|
| `justfile` | `template/justfile.jinja` | sync_structure_only | root -> template |
| `pyproject.toml` | `template/pyproject.toml.jinja` | sync_structure_only | root -> template |
| `.pre-commit-config.yaml` | `template/.pre-commit-config.yaml.jinja` | sync_structure_only | root -> template |
| `.claude/hooks/*.sh` (allowlist) | `template/.claude/hooks/*.sh` | must_sync | bidirectional review |
| `.claude/skills/tdd-test-planner/SKILL.md` | `template/.claude/skills/tdd-test-planner/SKILL.md` | must_sync | bidirectional review |
| `.claude/skills/tdd-workflow/SKILL.md` | `template/.claude/skills/tdd-workflow/SKILL.md` | must_sync | bidirectional review |
| `.claude/skills/test-quality-reviewer/SKILL.md` | `template/.claude/skills/test-quality-reviewer/SKILL.md` | must_sync | bidirectional review |
| `.github/workflows/lint.yml` | `template/.github/workflows/lint.yml.jinja` | sync_structure_only | bidirectional versions |
| `.github/workflows/security.yml` | `template/.github/workflows/security.yml.jinja` | sync_structure_only | bidirectional versions |
| `.github/workflows/pre-commit-update.yml` | `template/.github/workflows/pre-commit-update.yml.jinja` | sync_structure_only | bidirectional versions |
| `.github/workflows/release.yml` | `template/.github/workflows/release.yml.jinja` | sync_structure_only | bidirectional versions |
| `.github/workflows/dependency-review.yml` | `template/.github/workflows/dependency-review.yml.jinja` | sync_structure_only | bidirectional versions |
| `.github/workflows/labeler.yml` | `template/.github/workflows/labeler.yml.jinja` | sync_structure_only | bidirectional versions |

## Intentionally divergent areas

These areas are out of scope for strict parity:

- `copier.yml` and Copier task orchestration.
- Root-only workflows (`tests.yml`, `file-freshness.yml`, `sync-skip-if-exists.yml`, etc.).
- Root `tests/` versus `template/tests/`.
- Root `scripts/` versus generated-package source in `template/src/{{ package_name }}/`.
- Root `.claude` hooks related to Jinja/Copier/session lifecycle (`session-start`, `stop-*`,
  `pre-write-jinja-syntax`, `post-edit-template-mirror`, etc.).

## Automated enforcement

The checker (`scripts/check_root_template_sync.py`) enforces:

1. Action-version parity in mapped workflow pairs.
2. Exact parity for allowlisted shared hooks.
3. Section parity for selected `pyproject` tool blocks.
4. Exact parity for allowlisted shared skill files.

The machine-readable map in `assets/root-template-sync-map.yaml` is the source of truth for
what gets checked.

## Update workflow

When editing shared standards:

1. Update the root file first (unless the change starts in template context).
2. Port the equivalent change to the mapped template counterpart.
3. Run `just sync-check` locally.
4. Run `just check` before merge.

## Non-goals

- Auto-rewriting counterpart files.
- Full-file mirror of root and template trees.
- Enforcing parity for intentionally divergent files.
