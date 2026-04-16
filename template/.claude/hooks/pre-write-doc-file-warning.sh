#!/usr/bin/env bash
# Claude PreToolUse hook — Write
# Block creation of .md files outside the docs/ directory (pre-flight check).
#
# This is the pre-Write counterpart to the post-Edit markdown placement check.
# Firing BEFORE the file is written (exit 2 = block) is strictly better UX than
# the post-write approach: the wrong file is never created and Claude is steered
# to the correct location immediately.
#
# Allowed locations (pass freely):
#   •  README.md       — allowed anywhere
#   •  CLAUDE.md       — allowed anywhere
#   •  docs/**/         — any depth under any docs/ directory
#   •  .claude/**/      — skills, rules, commands, hooks docs
#
# All other .md files → BLOCKED. Recreate them under docs/.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:write:doc-file-warning — adapted to block instead of warn)
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Only process .md files
if [[ "$FILE_PATH" != *.md ]] || [[ -z "$FILE_PATH" ]]; then
    echo "$INPUT"
    exit 0
fi

BASENAME=$(basename "$FILE_PATH")

# README.md and CLAUDE.md are always allowed
if [[ "$BASENAME" == "README.md" ]] || [[ "$BASENAME" == "CLAUDE.md" ]]; then
    echo "$INPUT"
    exit 0
fi

# Files under any docs/ directory are allowed
if echo "$FILE_PATH" | grep -qE '(^|/)docs/'; then
    echo "$INPUT"
    exit 0
fi

# Files under tasks_summary/ are allowed (SDLC workflow summaries)
if echo "$FILE_PATH" | grep -qE '(^|/)tasks_summary/'; then
    echo "$INPUT"
    exit 0
fi

# ── Violation — block the write ───────────────────────────────────────────────
echo "┌─ BLOCKED: Markdown placement violation" >&2
echo "│" >&2
echo "│  Attempted path: $FILE_PATH" >&2
echo "│" >&2
echo "│  RULE: Markdown files produced during workflows or analysis must" >&2
echo "│  be written inside the docs/ or tasks_summary/ folder." >&2
echo "│" >&2
echo "│  Allowed exceptions:" >&2
echo "│    • README.md        — anywhere" >&2
echo "│    • CLAUDE.md        — anywhere" >&2
echo "│    • docs/**          — any depth" >&2
echo "│    • tasks_summary/** — SDLC workflow summaries" >&2
echo "│" >&2
echo "│  Action: recreate the file under docs/ or tasks_summary/" >&2
echo "└─" >&2
exit 2
