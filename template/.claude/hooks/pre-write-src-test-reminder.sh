#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit
# Remind to add a pytest module when touching a package source file.
#
# Scope: paths matching src/<package>/<module>.py (top-level modules) and
# src/<package>/common/<module>.py (common subpackage), excluding __init__.py.
#
# Test files are searched in tests/unit/, tests/integration/, and tests/e2e/.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/README.md
#             (recipe: Require test files alongside new source files — pytest layout)
# Exits     : 0 always (non-blocking; warnings on stderr only)

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(printf '%s' "$INPUT" | python3 -c '
import json, sys

data = json.load(sys.stdin)
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

# Match top-level package modules or common subpackage modules.
IS_COMMON=false
if [[ "$FP" =~ ^(.*/)?src/([^/]+)/common/([^/]+)\.py$ ]]; then
    MOD="${BASH_REMATCH[3]}"
    IS_COMMON=true
elif [[ "$FP" =~ ^(.*/)?src/([^/]+)/([^/]+)\.py$ ]]; then
    MOD="${BASH_REMATCH[3]}"
else
    echo "$INPUT"
    exit 0
fi

if [[ "$MOD" == "__init__" ]]; then
    echo "$INPUT"
    exit 0
fi

# Search for the test file in type subdirectories.
if [[ "$IS_COMMON" == true ]]; then
    SEARCH_PATHS=(
        "tests/unit/common/test_${MOD}.py"
        "tests/integration/common/test_${MOD}.py"
        "tests/e2e/common/test_${MOD}.py"
    )
    EXPECTED_TEST="tests/unit/common/test_${MOD}.py"
else
    SEARCH_PATHS=(
        "tests/unit/test_${MOD}.py"
        "tests/integration/test_${MOD}.py"
        "tests/e2e/test_${MOD}.py"
    )
    EXPECTED_TEST="tests/unit/test_${MOD}.py"
fi

for path in "${SEARCH_PATHS[@]}"; do
    if [[ -f "$path" ]]; then
        echo "$INPUT"
        exit 0
    fi
done

echo "┌─ Test module reminder" >&2
echo "│" >&2
echo "│  Source : $FP" >&2
echo "│  No file: $EXPECTED_TEST" >&2
echo "│" >&2
echo "│  Add tests under tests/unit/ (or tests/integration/, tests/e2e/) using" >&2
echo "│  the naming convention test_<module>.py." >&2
echo "└─" >&2

echo "$INPUT"
exit 0
