# Copilot Instructions

**Shared knowledge lives in [../AGENTS.md](../AGENTS.md) — read it first.**
This file holds only Copilot-specific notes.

## Copilot-specific notes

- Cross-session memory: AgentMemory via MCP (`localhost:3111`, project-scoped TEAM_ID `python_project_template`).
- **Session start:** call `memory_recall` with the task/goal.
- **During work:** call `memory_save` for durable decisions, bug root causes, conventions, gotchas.
- **Session end (mandatory):** before finishing, call `memory_save` with the lessons learned — every session, no exceptions.
- Do NOT create, read, or append to `MEMORY.md`, `CONFLICTS.md`, `NOTES.md`, or any markdown memory file.
