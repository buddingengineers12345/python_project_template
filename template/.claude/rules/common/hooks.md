# Hooks (Common)

This file provides cross-language guidance for Claude Code hooks (PreToolUse/PostToolUse/Stop).
Language-specific hook documentation should live in `../python/hooks.md`, `../bash/...`, etc.

When documenting a new hook:
- List the script in the relevant `hooks/README.md` table.
- Document the lifecycle event, matcher, and whether it blocks (exit code 2) or warns.
- Keep PreToolUse hooks fast (they run on every matching tool call).
