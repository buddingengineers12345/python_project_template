#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit
# TDD enforcement: block writing to src/<pkg>/<module>.py if the corresponding
# test file does not exist in tests/unit/, tests/integration/, or tests/e2e/.
#
# This is the strict version of pre-write-src-test-reminder.sh. That hook warns;
# this one blocks. Use this hook when the project follows strict TDD discipline.
#
# Scope: paths matching src/<package>/<module>.py (top-level modules) and
# src/<package>/common/<module>.py (common subpackage), excluding __init__.py.
#
# Test file search order:
#   1. tests/unit/test_<module>.py (or tests/unit/common/test_<module>.py)
#   2. tests/integration/test_<module>.py
#   3. tests/e2e/test_<module>.py
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 = allow  |  2 = block (test file missing)

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

# Normalise for matching.
FP="${FILE_PATH//\\//}"
FP="${FP#./}"

# Match top-level package modules: src/<pkg>/<module>.py
# or common subpackage modules: src/<pkg>/common/<module>.py
IS_COMMON=false
if [[ "$FP" =~ ^(.*/)?src/([^/]+)/common/([^/]+)\.py$ ]]; then
    PKG="${BASH_REMATCH[2]}"
    MOD="${BASH_REMATCH[3]}"
    IS_COMMON=true
elif [[ "$FP" =~ ^(.*/)?src/([^/]+)/([^/]+)\.py$ ]]; then
    PKG="${BASH_REMATCH[2]}"
    MOD="${BASH_REMATCH[3]}"
else
    echo "$INPUT"
    exit 0
fi

# Skip __init__.py — these rarely need a dedicated test file.
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

# If a test file exists in any type subdirectory, allow the write.
for path in "${SEARCH_PATHS[@]}"; do
    if [[ -f "$path" ]]; then
        echo "$INPUT"
        exit 0
    fi
done

# Block: test file does not exist.
echo "┌─ TDD enforcement: test-first required" >&2
echo "│" >&2
echo "│  Source file : $FP" >&2
echo "│  Expected    : $EXPECTED_TEST" >&2
echo "│" >&2
echo "│  Write the test file first, then come back to implement." >&2
echo "│  This hook enforces RED → GREEN discipline: no implementation" >&2
echo "│  code before a failing test exists." >&2
echo "│" >&2
echo "│  To create the test file:" >&2
if [[ "$IS_COMMON" == true ]]; then
    echo "│    mkdir -p tests/unit/common && touch $EXPECTED_TEST" >&2
else
    echo "│    mkdir -p tests/unit && touch $EXPECTED_TEST" >&2
fi
echo "└─ ✗ Blocked — write test first" >&2

exit 2
