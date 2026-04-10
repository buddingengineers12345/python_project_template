#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit
# TDD enforcement: block writing to src/<pkg>/<module>.py if the corresponding
# test file tests/<pkg>/test_<module>.py does not exist yet.
#
# This is the strict version of pre-write-src-test-reminder.sh. That hook warns;
# this one blocks. Use this hook when the project follows strict TDD discipline.
#
# Scope: only paths matching src/<package>/<module>.py (exactly one directory
# between src/ and the file), excluding __init__.py. Nested layouts such as
# src/<pkg>/common/foo.py are skipped.
#
# Exits: 0 = allow  |  2 = block (test file missing)

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

# Normalise for matching.
FP="${FILE_PATH//\\//}"
FP="${FP#./}"

# Only match top-level package modules: src/<pkg>/<module>.py
if [[ ! "$FP" =~ ^(.*/)?src/([^/]+)/([^/]+)\.py$ ]]; then
    echo "$INPUT"
    exit 0
fi

PKG="${BASH_REMATCH[2]}"
MOD="${BASH_REMATCH[3]}"

# Skip __init__.py — these rarely need a dedicated test file.
if [[ "$MOD" == "__init__" ]]; then
    echo "$INPUT"
    exit 0
fi

EXPECTED_TEST="tests/${PKG}/test_${MOD}.py"

# If the test file already exists, allow the write.
if [[ -f "$EXPECTED_TEST" ]]; then
    echo "$INPUT"
    exit 0
fi

# Also check if the test file exists at the flat layout: tests/test_<module>.py
EXPECTED_TEST_FLAT="tests/test_${MOD}.py"
if [[ -f "$EXPECTED_TEST_FLAT" ]]; then
    echo "$INPUT"
    exit 0
fi

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
echo "│    mkdir -p tests/${PKG} && touch $EXPECTED_TEST" >&2
echo "└─ ✗ Blocked — write test first" >&2

exit 2
