#!/usr/bin/env bash
# Claude PostToolUse hook — Edit
# Post-edit fallback: warn if an existing .md file was edited outside docs/.
#
# This hook is the post-Edit secondary layer for Markdown placement.
# For Write (new file creation), pre-write-doc-file-warning.sh provides a
# pre-flight blocking check (exit 2) instead.
#
# If the edited file is a Markdown (.md) file that is NOT:
#   - README.md  (allowed anywhere)
#   - CLAUDE.md  (allowed anywhere)
#   - inside docs/ (allowed anywhere under any docs/ subtree)
#
# …this hook surfaces a violation message so Claude can self-correct.
# The hook always exits 0 so it never hard-blocks the tool response.
#
# Reference : Custom — project-specific hook, not derived from ECC.
#             Pre-Write blocking handled by pre-write-doc-file-warning.sh.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

# Read the tool-call JSON from stdin
INPUT=$(cat)

# Extract file_path from tool_input (works for both Edit and Write tools)
FILE_PATH=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
)

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

# Files under tasks_summary/ are allowed (SDLC workflow summaries)
if echo "$FILE_PATH" | grep -qE '(^|/)tasks_summary/'; then
    exit 0
fi

# ── Violation ──────────────────────────────────────────────────────────────
echo "┌─ Markdown placement violation: $FILE_PATH"
echo "│"
echo "│  RULE: Markdown files produced during agent workflows or analysis"
echo "│  MUST be written inside the docs/ or tasks_summary/ folder."
echo "│"
echo "│  Allowed exceptions:"
echo "│    • README.md        (anywhere)"
echo "│    • CLAUDE.md        (anywhere)"
echo "│    • docs/**          (any depth)"
echo "│    • tasks_summary/** (SDLC workflow summaries)"
echo "│"
echo "│  Action required: delete this file and recreate it under docs/ or tasks_summary/."
echo "└─"

exit 0
