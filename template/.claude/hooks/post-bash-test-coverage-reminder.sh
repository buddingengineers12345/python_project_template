#!/usr/bin/env bash
set -uo pipefail

# PostToolUse hook for Bash: after pytest/just test runs, parse coverage output
# and surface modules below 85%.

INPUT=$(cat)

# Only trigger on pytest or just test commands
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_result', {}).get('stdout', '') if 'tool_result' in data else '')
" 2>/dev/null) || { echo "$INPUT"; exit 0; }

TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null) || { echo "$INPUT"; exit 0; }

# Check if the command was a test/coverage command
case "$TOOL_INPUT" in
    *pytest*|*"just test"*|*"just coverage"*|*"just ci"*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Look for coverage output in the result
if echo "$COMMAND" | grep -q "TOTAL"; then
    # Parse modules below 85%
    LOW_COVERAGE=$(echo "$COMMAND" | python3 -c "
import sys

lines = sys.stdin.read().strip().split('\n')
low = []
for line in lines:
    parts = line.split()
    if len(parts) >= 4 and parts[0].startswith('src/'):
        try:
            pct = int(parts[-1].rstrip('%'))
            if pct < 85:
                low.append(f'{parts[0]}: {pct}%')
        except (ValueError, IndexError):
            pass
if low:
    print('\n'.join(low))
" 2>/dev/null)

    if [[ -n "$LOW_COVERAGE" ]]; then
        echo "┌─ Coverage reminder"
        echo "│  Modules below 85% threshold:"
        echo "$LOW_COVERAGE" | while IFS= read -r line; do
            echo "│  ⚠  $line"
        done
        echo "└─ Consider writing tests to close gaps before committing"
    fi
fi

echo "$INPUT"
exit 0
