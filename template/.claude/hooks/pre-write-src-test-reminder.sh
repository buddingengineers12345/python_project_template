#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit
# Remind to add a pytest module when touching a top-level package source file.
#
# Scope: only paths matching src/<package>/<module>.py (exactly one directory between
# src/ and the file), excluding __init__.py. Nested layouts such as
# src/<pkg>/common/foo.py are skipped — they are often covered by shared tests
# (e.g. test_support.py).
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/README.md
#             (recipe: Require test files alongside new source files — pytest layout)
# Exits     : 0 always (non-blocking; warnings on stderr only)

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(printf '%s' "$INPUT" | python3 -c '
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
') || {
    echo "$INPUT"
    exit 0
}

[[ "$FILE_PATH" == *.py ]] || {
    echo "$INPUT"
    exit 0
}

# Normalise for matching (JSON paths may use backslashes on Windows clients).
FP="${FILE_PATH//\\//}"
FP="${FP#./}"

if [[ ! "$FP" =~ ^(.*/)?src/([^/]+)/([^/]+)\.py$ ]]; then
    echo "$INPUT"
    exit 0
fi

PKG="${BASH_REMATCH[2]}"
MOD="${BASH_REMATCH[3]}"

if [[ "$MOD" == "__init__" ]]; then
    echo "$INPUT"
    exit 0
fi

EXPECTED_TEST="tests/${PKG}/test_${MOD}.py"

if [[ -f "$EXPECTED_TEST" ]]; then
    echo "$INPUT"
    exit 0
fi

echo "┌─ Test module reminder" >&2
echo "│" >&2
echo "│  Source : $FP" >&2
echo "│  No file: $EXPECTED_TEST" >&2
echo "│" >&2
echo "│  Add tests under tests/<package>/ (pytest: test_<module>.py) or extend an" >&2
echo "│  existing test module that imports this code." >&2
echo "│  Nested src paths (e.g. src/<pkg>/common/…) are not checked." >&2
echo "└─" >&2

echo "$INPUT"
exit 0
