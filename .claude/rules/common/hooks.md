# Hooks (Common)

This document defines shared conventions for Claude Code hooks across languages.
Language-specific hook requirements live in their respective rule files (e.g. `python/hooks.md`).

## General rules

- Hooks must be fast and side-effect free unless explicitly intended.
- **PreToolUse** hooks may block actions (exit code `2`) and should avoid long-running commands.
- **PostToolUse** hooks must not block (exit code is ignored); use them for reminders and checks.
- Prefer printing concise, actionable guidance on stderr for warnings and blocks.

