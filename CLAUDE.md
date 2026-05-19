# CLAUDE.md

**Shared knowledge lives in [AGENTS.md](./AGENTS.md) — read it first.**

This file holds only Claude-specific notes.

## Claude-specific notes

- Role: orchestration, planning, review, constrained implementation.
- Use subagents for parallel exploration; keep the main context lean.
- Deeper rules on demand: `.claude/rules/`, `.claude/references/` (load per the AGENTS.md table).
- Memory: AgentMemory only — see AGENTS.md. No MEMORY.md / CONFLICTS.md.
