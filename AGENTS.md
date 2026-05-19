# AGENTS.md — Python Project Template

> Canonical, model-agnostic agent guide. CLAUDE.md / GEMINI.md / CURSOR.md are thin wrappers that
> point here. Edit shared knowledge in THIS file only.

## What this repo is

This repository is a **Copier template repository** (a meta-project). Running Copier against
this repo **generates** a new Python project by rendering the `template/` directory into a
destination folder.

> [!WARNING]
> Copier can run **template tasks** during `copier copy`/`copier update`. Only use the
> `--trust` flag with templates you trust.

## Behavioral guidelines

Bias toward caution over speed; use judgment on trivial tasks.

- **Think before coding** — state assumptions; surface multiple interpretations instead of silently picking one; ask when unclear.
- **Simplicity first** — minimum code that solves the problem; nothing speculative.
- **Surgical changes** — touch only what the task requires; match existing style; don't refactor what isn't broken.
- **Goal-driven execution** — define a verifiable success check before starting; loop until it passes.

## Context loading (progressive disclosure)

1. Read this file first.
2. Load a deeper reference ONLY when the task touches its area:

| When the task involves… | Read |
|---|---|
| Directory structure, project layout | `scripts/CLAUDE.md`, `tests/CLAUDE.md`, `.github/CLAUDE.md`, `template/CLAUDE.md` |
| Development setup, just recipes, CI | `.claude/references/dev-setup.md`, `.claude/references/justfile-recipes.md`, `.claude/references/ci-pipeline.md` |
| Generating or updating projects | `.claude/references/copier-template.md` |
| Testing strategy and patterns | `tests/CLAUDE.md` + `.claude/references/testing.md` |
| Copier variables and Jinja2 | `.claude/references/copier-variables.md` |
| Code style and standards | `.claude/references/code-style.md` |
| Standards enforcement (hooks, commands, definition of done) | `.claude/references/standards-enforcement.md` |
| Markdown file placement | `.claude/references/markdown-placement.md` |
| File management (what not to edit) | `.claude/references/files-management.md` |
| Recent improvements | `.claude/references/recent-improvements.md` |
| AI rules, hooks, and skills | `.claude/rules/README.md`, `.claude/hooks/README.md` |
| Scripts | `scripts/CLAUDE.md` |
| GitHub workflows | `.github/CLAUDE.md` |
| Template structure | `template/CLAUDE.md` |

3. Do not bulk-load all references — avoid context flooding.

## Memory — AgentMemory only

This repo uses AgentMemory (MCP server `localhost:3111`, project-scoped TEAM_ID `python_project_template`).

- Session start: call `memory_recall` with the task/goal.
- During work: call `memory_save` for durable decisions, bug root causes, conventions, gotchas (types: pattern | architecture | bug | workflow | preference).
- Session end: call `memory_save` with lessons learned.
- Do NOT create, read, or append to `MEMORY.md`, `CONFLICTS.md`, `NOTES.md`, or any markdown "memory" / "conflict log" file. Cross-session memory and conflict tracking live in AgentMemory exclusively.

## Repo-specific guidance

Detailed how-tos live in `.claude/references/` (load per the table above). Rules and enforcement hooks are under `.claude/rules/` and `.claude/hooks/` — referenced in `.claude/rules/README.md` and `.claude/hooks/README.md`.
