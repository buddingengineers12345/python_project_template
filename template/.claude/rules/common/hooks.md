# Hooks (Common)

This file provides cross-language guidance for Claude Code hooks (PreToolUse/PostToolUse/Stop).
Language-specific hook documentation should live in `../python/hooks.md`, `../bash/...`, etc.

## General rules

- Hooks must be fast and side-effect free unless explicitly intended.
- **PreToolUse** hooks may block actions (exit code `2`) and should avoid long-running commands.
- **PostToolUse** hooks must not block (exit code is ignored); use them for reminders and checks.
- Prefer printing concise, actionable guidance on stderr for warnings and blocks.

When documenting a new hook:
- List the script in the relevant `hooks/README.md` table.
- Document the lifecycle event, matcher, and whether it blocks (exit code 2) or warns.
- Keep PreToolUse hooks fast (they run on every matching tool call).
