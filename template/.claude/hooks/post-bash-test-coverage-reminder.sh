#!/usr/bin/env bash
# Claude PostToolUse hook — Bash
# After pytest / just test runs, parse coverage output and surface modules
# below the 85% project threshold.
#
# Only fires on commands that look like test or coverage runs (pytest, just
# test, just coverage, just ci). Reads the tool's stdout from tool_response and
# greps the coverage table; any src/ module under 85% is listed as a reminder
# so the developer can add tests before committing.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -uo pipefail

INPUT=$(cat)

# Extract the bash command that was executed
TOOL_INPUT=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("command", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Only trigger on pytest / just test / just coverage / just ci commands
case "$TOOL_INPUT" in
    *pytest*|*"just test"*|*"just coverage"*|*"just ci"*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Extract the tool's stdout from tool_response
TOOL_OUTPUT=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
resp = data.get("tool_response") or data.get("tool_result") or {}
print(resp.get("stdout", "") or resp.get("output", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Look for coverage output in the tool response
if echo "$TOOL_OUTPUT" | grep -q "TOTAL"; then
    LOW_COVERAGE=$(CLAUDE_HOOK_INPUT="$TOOL_OUTPUT" python3 - <<'PYEOF'
import os
lines = os.environ["CLAUDE_HOOK_INPUT"].strip().split("\n")
low = []
for line in lines:
    parts = line.split()
    if len(parts) >= 4 and parts[0].startswith("src/"):
        try:
            pct = int(parts[-1].rstrip("%"))
            if pct < 85:
                low.append(f"{parts[0]}: {pct}%")
        except (ValueError, IndexError):
            pass
if low:
    print("\n".join(low))
PYEOF
)

    if [[ -n "$LOW_COVERAGE" ]]; then
        echo "┌─ Coverage reminder"
        echo "│"
        echo "│  Modules below 85% threshold:"
        echo "$LOW_COVERAGE" | while IFS= read -r line; do
            echo "│  ⚠  $line"
        done
        echo "│"
        echo "└─ Consider writing tests to close gaps before committing"
    fi
fi

echo "$INPUT"
exit 0
