---
paths:
  - "**/*.sh"
  - "**/*.bash"
---

# Bash Coding Style

- Start with `#!/usr/bin/env bash` and `set -euo pipefail` (omit `-e` for PreToolUse hooks).
- Always quote variable expansions: `"$var"`. Use `[[ ]]`, not `[ ]`.
- PreToolUse hooks: echo `$INPUT` and exit 0 to allow; exit 2 to block.
- Print to stdout for PostToolUse/Stop output; print to stderr for PreToolUse blocking messages.
- Hooks run on macOS and Linux — avoid GNU-specific flags.
