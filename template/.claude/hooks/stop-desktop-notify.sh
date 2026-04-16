#!/usr/bin/env bash
# Claude Stop hook — * (all events)
# Send a macOS desktop notification when Claude finishes a response.
#
# On macOS, uses osascript to fire a system notification with:
#   - Title:   "Claude Code — <project name>"
#   - Message: first 80 chars of the last assistant text message (if transcript
#              is available), otherwise a generic "Task complete" message.
#
# This is especially useful when waiting on long just ci / copier copy runs
# that execute uv sync, ruff, basedpyright, and the test suite as _tasks.
#
# Runs async (non-blocking) so it does not delay Claude's response.
# Silently skips on non-macOS systems.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: stop:desktop-notify)
# Exits     : 0 always

set -uo pipefail

# Only run on macOS
if ! command -v osascript >/dev/null 2>&1; then
    exit 0
fi

INPUT=$(cat)

PROJECT=$(basename "$PWD")
MESSAGE="Task complete in $PROJECT"

# Try to extract the last assistant message from the transcript for a richer notification
TRANSCRIPT_PATH=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

try:
    data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
    print(data.get("transcript_path", ""))
except Exception:
    print("")
PYEOF
) || true

if [[ -n "$TRANSCRIPT_PATH" ]] && [[ -f "$TRANSCRIPT_PATH" ]]; then
    LAST_MSG=$(python3 - "$TRANSCRIPT_PATH" <<'PYEOF'
import json, os
from pathlib import Path

transcript_file = sys.argv[1]
try:
    lines = Path(transcript_file).read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("role") == "assistant":
                content = entry.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block["text"].strip()[:80].replace('"', "'")
                            print(text)
                            break
                elif isinstance(content, str):
                    print(content.strip()[:80].replace('"', "'"))
                break
        except (json.JSONDecodeError, KeyError):
            continue
except Exception:
    pass
PYEOF
2>/dev/null || true)
    if [[ -n "$LAST_MSG" ]]; then
        MESSAGE="$LAST_MSG"
    fi
fi

osascript \
    -e "display notification \"$MESSAGE\" with title \"Claude Code — $PROJECT\"" \
    2>/dev/null || true

exit 0
