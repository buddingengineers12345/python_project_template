#!/usr/bin/env bash
set -uo pipefail

# PostToolUse hook for Write: after creating test_*.py files, check for proper
# test structure: test_ functions, no unittest.TestCase, proper marker usage.

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null) || { echo "$INPUT"; exit 0; }

# Only check test files
case "$FILE_PATH" in
    */test_*.py|*tests/*.py) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Verify the file exists
[[ -f "$FILE_PATH" ]] || { echo "$INPUT"; exit 0; }

WARNINGS=""

# Check for test_ functions
if ! grep -q "^def test_\|^    def test_\|^async def test_" "$FILE_PATH"; then
    WARNINGS="${WARNINGS}\n│  ⚠  No test_ functions found — file may not contain any tests"
fi

# Check for unittest.TestCase (discouraged)
if grep -q "unittest.TestCase\|class.*TestCase" "$FILE_PATH"; then
    WARNINGS="${WARNINGS}\n│  ⚠  unittest.TestCase detected — prefer pytest function-based tests"
fi

# Check for pytest markers (pytestmark at module level or @pytest.mark on functions)
if ! grep -q "pytestmark\|@pytest.mark\." "$FILE_PATH"; then
    WARNINGS="${WARNINGS}\n│  ⚠  No pytest markers found — every test file must set pytestmark = pytest.mark.<marker> at module level"
fi

if [[ -n "$WARNINGS" ]]; then
    echo "┌─ Test structure check: $(basename "$FILE_PATH")"
    echo -e "$WARNINGS"
    echo "└─ Fix these issues to maintain test quality standards"
fi

echo "$INPUT"
exit 0
