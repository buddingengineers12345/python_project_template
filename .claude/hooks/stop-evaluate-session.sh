#!/usr/bin/env bash
# Claude Stop hook — * (all events)
# Extract and log reusable patterns from the current session for continuous learning.
#
# After each response, scans the available transcript for indicators of:
#   - Repeated corrections (same tool called multiple times on the same file)
#   - Blocked operations (hooks that triggered exit 2)
#   - New just recipes or copier variable patterns introduced in this session
#
# Findings are appended to ~/.claude/patterns/<project>-patterns.jsonl.
# These observations accumulate over time and can be reviewed to identify
# recurring friction points worth addressing in CLAUDE.md or the hooks themselves.
#
# Runs async (non-blocking) so it does not delay Claude's response.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: stop:evaluate-session)
# Exits     : 0 always

set -uo pipefail

INPUT=$(cat)

echo "$INPUT" | python3 - <<'PYEOF'
import json, os, sys, datetime, re
from pathlib import Path
from collections import Counter

try:
    data = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

transcript_path = data.get("transcript_path", "")
if not transcript_path or not Path(transcript_path).exists():
    sys.exit(0)

patterns_dir = Path.home() / ".claude" / "patterns"
patterns_dir.mkdir(parents=True, exist_ok=True)

project = os.path.basename(os.getcwd())
patterns_file = patterns_dir / f"{project}-patterns.jsonl"

try:
    lines = Path(transcript_path).read_text(encoding="utf-8").strip().splitlines()
except Exception:
    sys.exit(0)

# Count tool calls per file to detect repeated corrections on the same file
file_edit_counts: Counter = Counter()
blocked_tools: list[str] = []
new_patterns: list[str] = []

for line in lines:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        continue

    # Count edits per file path
    if entry.get("type") == "tool_use" and entry.get("name") in ("Edit", "Write", "MultiEdit"):
        fp = entry.get("input", {}).get("file_path", "")
        if fp:
            file_edit_counts[fp] += 1

    # Look for block signals in tool results
    if entry.get("type") == "tool_result":
        content = str(entry.get("content", ""))
        if "BLOCKED" in content:
            blocked_tools.append(content[:120])

# Identify files edited 4+ times (potential repeated-correction pattern)
hot_files = [f for f, c in file_edit_counts.items() if c >= 4]

observation = {
    "timestamp": datetime.datetime.now().isoformat(),
    "session_id": data.get("session_id", "unknown"),
    "project": project,
    "hot_files": hot_files,
    "block_events": len(blocked_tools),
    "total_edits": sum(file_edit_counts.values()),
}

if hot_files or blocked_tools:
    with patterns_file.open("a") as f:
        f.write(json.dumps(observation) + "\n")
PYEOF

exit 0
