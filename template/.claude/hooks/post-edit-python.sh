#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# Run ruff check and basedpyright on every edited Python file for immediate feedback.
#
# If the edited file is a Python (.py) file, this hook:
#   1. Runs ruff check (lint + docstring rules) on that file
#   2. Runs basedpyright (type checking) on that file
#
# Output is surfaced back to Claude so it can self-correct in the same turn.
# The hook always exits 0 so it never blocks the tool response.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")

if [[ "$FILE_PATH" != *.py ]] || [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

echo "┌─ Standards check: $FILE_PATH"

FAILED=0

echo "│"
echo "│  ruff check"
if ! uv run --active ruff check "$FILE_PATH" --output-format concise 2>&1; then
    FAILED=1
fi

echo "│"
echo "│  basedpyright"
if ! uv run --active basedpyright "$FILE_PATH" 2>&1; then
    FAILED=1
fi

echo "│"
if [[ $FAILED -eq 0 ]]; then
    echo "└─ ✓ All checks passed"
else
    echo "└─ ✗ Violations found — fix before committing"
fi

exit 0
