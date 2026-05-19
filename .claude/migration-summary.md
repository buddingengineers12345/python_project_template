# Migration Summary — 4-File Agent Guide Model

**Date:** 2026-05-19  
**Status:** Completed (root only; template/ deferred)

## What was done

Established the canonical 4-file model at the repository root:

1. **AGENTS.md** (new, canonical) — all shared knowledge, behavioral guidelines, context loading table, memory protocol
2. **CLAUDE.md** (replaced) — thin wrapper (~15 lines), Claude-specific notes only
3. **GEMINI.md** (new) — thin wrapper (~10 lines), Gemini-specific notes only
4. **CURSOR.md** (new) — thin wrapper (~10 lines), Cursor-specific notes only

## Long content moved to `.claude/references/`

All substantive content extracted from the 439-line root `CLAUDE.md` into separate reference files (verbatim):

- `.claude/references/directory-structure.md` — directory layout
- `.claude/references/dev-setup.md` — Python 3.11+, uv, just prerequisites
- `.claude/references/justfile-recipes.md` — complete just recipe table (all 50+ recipes)
- `.claude/references/ci-pipeline.md` — `just ci`, pipeline description, merge gate
- `.claude/references/copier-template.md` — copy vs update, conflict handling, migrations, release workflow
- `.claude/references/testing.md` — pytest + copier integration test approach
- `.claude/references/copier-variables.md` — Copier variable conventions, Jinja2 extensions
- `.claude/references/code-style.md` — ruff rules, docstrings, complexity, type annotations
- `.claude/references/ai-rules.md` — `.claude/rules/` structure, skills vs rules philosophy
- `.claude/references/standards-enforcement.md` — tooling layer (ruff, basedpyright, pytest-cov), Claude hooks table, slash commands table, definition of done
- `.claude/references/markdown-placement.md` — `docs/` placement rule + exceptions
- `.claude/references/files-management.md` — do-not-edit list (uv.lock, .copier-answers.yml), clean artifacts
- `.claude/references/recent-improvements.md` — April 2026 changes (standards, package structure, testing, CI/CD, docs, release automation, Claude docs)

## Nested CLAUDE.md files (unchanged)

- `scripts/CLAUDE.md` (139 lines) — documents each script, CLI flags, CI integration
- `tests/CLAUDE.md` (136 lines) — test patterns, helpers, categories, how to add tests
- `.github/CLAUDE.md` (89 lines) — meta-repo workflows and design principles
- `template/CLAUDE.md` (156 lines) — Jinja2 source layout, Copier variables, dual `.claude/` hierarchy (this is source material for generated projects, NOT edited)

These files are referenced from AGENTS.md via progressive disclosure and are NOT modified this pass.

## No MEMORY.md / CONFLICTS.md refs found

Grep of all `.md` files shows zero references to `MEMORY.md` or `CONFLICTS.md`. Project is clean per governance rules.

## TEAM_ID / AgentMemory slug

Read from `.agentmemory-project`: **`python_project_template`**

## template/ subdir — needs separate pass

### Finding: `copier.yml` structure

- `_subdirectory: template` — Copier renders this subtree into generated projects
- `_skip_if_exists:` — preserves user-edited files on update (includes `CLAUDE.md`)
- `_exclude:` — files not copied (`.git`, `.venv`, `__pycache__`, `*.pyc`)
- `.jinja` suffix — files with this are rendered as Jinja2; others copied verbatim
- `template/CLAUDE.md` — plain file (NOT Jinja2), explains Jinja2 source layout to humans

### Finding: `template/CLAUDE.md` is NOT a template

This file is verbatim source material (no Jinja2 syntax), read by humans during generated-project development. It is NOT `.jinja` suffixed, so Copier copies it verbatim to generated projects as `CLAUDE.md`.

### Recommended approach for template/ (future pass)

The 4-file model should be applied **inside `template/`** so **generated projects inherit it**. Approach:

1. Create `template/.claude/references/` (mirrors root `.claude/references/`)
2. Extract long sections from `template/CLAUDE.md` into reference files (same topics as root, but generated-project context)
3. Replace `template/CLAUDE.md` with thin wrapper (like root CLAUDE.md, but Jinja2-aware for generated project context)
4. Create `template/AGENTS.md` — canonical guide for generated projects (mirrors root AGENTS.md)
5. Copier will render these into generated projects, establishing the 4-file model automatically

**Why deferred:** `template/` is a Copier template (Jinja2 source). Changes here affect all **future-generated projects**. This is higher risk and benefits from human review of the Jinja2 layer. The root refactor is complete and validates the 4-file model; the template pass applies it to future artifacts.

## Validation checklist

- [x] All relative links in 4 root files resolve (`.AGENTS.md`, `.claude/references/*`)
- [x] Each wrapper ≤ ~15–20 lines
- [x] AGENTS.md preserves all substantive content by reference
- [x] No MEMORY.md / CONFLICTS.md refs in instruction files outside this summary
- [x] TEAM_ID verified: `python_project_template`
- [x] Nested `scripts/`, `tests/`, `.github/` CLAUDE.md files untouched
- [x] `template/CLAUDE.md` untouched (defer to next pass)
- [x] Progressive disclosure table in AGENTS.md points to all deeper docs
- [x] AgentMemory protocol documented inline (no external memory files)

## Files created

- `AGENTS.md` (66 lines) — canonical guide
- `CLAUDE.md` (rewrote; now 11 lines) — Claude wrapper
- `GEMINI.md` (11 lines) — Gemini wrapper
- `CURSOR.md` (11 lines) — Cursor wrapper
- `.claude/migration-summary.md` (this file)
- `.claude/references/directory-structure.md`
- `.claude/references/dev-setup.md`
- `.claude/references/justfile-recipes.md`
- `.claude/references/ci-pipeline.md`
- `.claude/references/copier-template.md`
- `.claude/references/testing.md`
- `.claude/references/copier-variables.md`
- `.claude/references/code-style.md`
- `.claude/references/ai-rules.md`
- `.claude/references/standards-enforcement.md`
- `.claude/references/markdown-placement.md`
- `.claude/references/files-management.md`
- `.claude/references/recent-improvements.md`

Total: 4 root `.md` + 1 migration summary + 13 reference files = 18 new/modified files.
