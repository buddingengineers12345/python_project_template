#!/usr/bin/env bash
# Claude Stop hook — * (all events)
# Log a lightweight cost/token metrics entry per session turn.
#
# Appends a JSONL entry to ~/.claude/cost-log/<YYYY-MM>.jsonl after each
# Claude response. Each entry captures: timestamp, session_id, project, and
# any usage fields the Stop event exposes (token counts, etc.).
#
# Useful for tracking session activity over time without requiring external
# monitoring infrastructure. The log is append-only and never grows unbounded
# unless you have very high session frequency (one line per Stop event).
#
# Runs async (non-blocking) so it does not delay Claude's response.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: stop:cost-tracker)
# Exits     : 0 always

set -uo pipefail

INPUT=$(cat)

echo "$INPUT" | python3 - <<'PYEOF'
import json, os, sys, datetime
from pathlib import Path

try:
    data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

log_dir = Path.home() / ".claude" / "cost-log"
log_dir.mkdir(parents=True, exist_ok=True)

now = datetime.datetime.now()
log_file = log_dir / f"{now.strftime('%Y-%m')}.jsonl"

entry = {
    "timestamp": now.isoformat(),
    "session_id": data.get("session_id", "unknown"),
    "project": os.path.basename(os.getcwd()),
    "cwd": os.getcwd(),
    # Capture any usage/cost fields the Stop event may expose
    "usage": data.get("usage", {}),
    "cost": data.get("cost_usd", None),
}

with log_file.open("a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

exit 0
