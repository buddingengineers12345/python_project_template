#!/usr/bin/env bash
# Claude Stop hook — * (all events)
# Persist a lightweight session state record after each Claude response.
#
# The Stop event fires after each response and includes a transcript_path when
# available. This hook writes a compact JSON state file that session-start-bootstrap.sh
# can surface on the next session start, providing continuity across restarts.
#
# State stored: timestamp, session_id, project CWD, git branch, transcript_path.
#
# Runs async (non-blocking) so it does not delay Claude's response.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: stop:session-end)
# Exits     : 0 always

set -uo pipefail

INPUT=$(cat)

STATE_DIR="$HOME/.claude/session-states"
mkdir -p "$STATE_DIR"

PROJECT=$(basename "$PWD")
STATE_FILE="$STATE_DIR/${PROJECT}_latest.json"

echo "$INPUT" | python3 - <<'PYEOF'
import json, os, sys, datetime, subprocess
from pathlib import Path

try:
    data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

state = {
    "timestamp": datetime.datetime.now().isoformat(),
    "project": os.path.basename(os.getcwd()),
    "cwd": os.getcwd(),
    "session_id": data.get("session_id", "unknown"),
    "transcript_path": data.get("transcript_path", ""),
    "git_branch": None,
}

try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()
    state["git_branch"] = branch
except Exception:
    pass

state_dir = Path.home() / ".claude" / "session-states"
state_dir.mkdir(parents=True, exist_ok=True)
state_file = state_dir / f"{state['project']}_latest.json"

with state_file.open("w") as f:
    json.dump(state, f, indent=2)
PYEOF

exit 0
