#!/usr/bin/env bash
# Claude PostToolUse hook — runs after any Edit or Write tool call.
#
# If the written file is a Markdown (.md) file that is NOT:
#   - README.md  (allowed anywhere)
#   - CLAUDE.md  (allowed anywhere)
#   - inside docs/ (allowed anywhere under any docs/ subtree)
#
# …this hook surfaces a violation message so Claude can self-correct
# by moving the file to docs/ before finalising the turn.
#
# The hook always exits 0 so it never hard-blocks the tool response.

set -euo pipefail

# Read the tool-call JSON from stdin
INPUT=$(cat)

# Extract file_path from tool_input (works for both Edit and Write tools)
FILE_PATH=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")

# Only process .md files that exist
if [[ "$FILE_PATH" != *.md ]] || [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

BASENAME=$(basename "$FILE_PATH")

# README.md and CLAUDE.md are always allowed
if [[ "$BASENAME" == "README.md" ]] || [[ "$BASENAME" == "CLAUDE.md" ]]; then
    exit 0
fi

# Files under any docs/ directory are allowed
if echo "$FILE_PATH" | grep -qE '(^|/)docs/'; then
    exit 0
fi

# ── Violation ──────────────────────────────────────────────────────────────
echo "┌─ Markdown placement violation: $FILE_PATH"
echo "│"
echo "│  RULE: Markdown files produced during agent workflows or analysis"
echo "│  MUST be written inside the docs/ folder."
echo "│"
echo "│  Allowed exceptions:"
echo "│    • README.md  (anywhere)"
echo "│    • CLAUDE.md  (anywhere)"
echo "│"
echo "│  Action required: delete this file and recreate it under docs/."
echo "└─"

exit 0
