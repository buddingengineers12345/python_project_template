#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# Refactor safety net: after editing a src/**/*.py or scripts/**/*.py file, remind the developer to
# re-run tests if they haven't done so recently.
#
# This hook tracks the last test run via a timestamp file (.last-test-run). If
# more than 3 source edits have occurred since the last test run, it surfaces a
# reminder. This prevents silent regressions during the REFACTOR stage of TDD.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(printf '%s' "$INPUT" | python3 -c '
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("file_path", ""))
') || {
    echo "$INPUT"
    exit 0
}

# Only care about Python source files (not tests).
if [[ "$FILE_PATH" != *.py ]] || [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Normalise path.
FP="${FILE_PATH//\\//}"
FP="${FP#./}"

# Only fire for src/ or scripts/ files.
if [[ ! "$FP" =~ ^(.*/)?(src|scripts)/ ]]; then
    exit 0
fi

# Track edit count since last test run.
COUNTER_FILE=".claude/.refactor-edit-count"
mkdir -p .claude

if [[ -f "$COUNTER_FILE" ]]; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
    COUNT=$((COUNT + 1))
else
    COUNT=1
fi

echo "$COUNT" > "$COUNTER_FILE"

# Remind after every 3 edits.
if [[ $((COUNT % 3)) -eq 0 ]]; then
    echo "┌─ Refactor test guard"
    echo "│"
    echo "│  ${COUNT} source edits since last test run."
    echo "│  Run \`just test\` to catch regressions early."
    echo "│  In TDD: tests must stay green throughout REFACTOR."
    echo "└─ ⚠  Consider running tests"
fi

exit 0
