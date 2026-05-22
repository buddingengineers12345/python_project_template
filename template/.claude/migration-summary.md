# template/.claude — 4-file model (generated projects)

**Date:** 2026-05-21

## Added for Copier output

- `template/AGENTS.md.jinja`, `GEMINI.md.jinja`, `CURSOR.md.jinja` — thin wrappers for generated repos
- `template/CLAUDE.md.jinja` — replaced long monolith with thin wrapper + quick command table
- `template/.claude/references/` — mirrors meta-repo reference docs (13 files)
- `template/.claude/settings.json.jinja` — hooks + `AGENTMEMORY_TEAM_ID: {{ project_slug }}`
- `copier.yml` `_skip_if_exists`: `AGENTS.md`, `GEMINI.md`, `CURSOR.md`

## Unchanged

- `template/CLAUDE.md` — human-readable Copier source layout doc (not copied to generated projects)
- `template/.claude/hooks/`, `commands/`, `rules/`, `skills/` — existing generated-project tooling
