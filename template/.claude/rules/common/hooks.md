# Hooks

- Hooks must be fast and side-effect free unless explicitly intended.
- PreToolUse hooks may block (exit code `2`); echo `$INPUT` back to stdout to allow.
- PostToolUse and Stop hooks must exit `0`; use them for reminders only, not blocking.
- Document new hooks in `hooks/README.md` with lifecycle event, matcher, and blocking behaviour.
