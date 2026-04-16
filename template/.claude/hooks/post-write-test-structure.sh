#!/usr/bin/env bash
# Claude PostToolUse hook — Write
# After creating test_*.py files, check for proper test structure:
# test_ functions, no unittest.TestCase, and module-level pytest markers.
#
# Only inspects files under tests/ or matching test_*.py. Surfaces warnings to
# Claude so it can self-correct in the same turn, but never blocks (PostToolUse
# cannot block). The three checks enforce:
#   1. At least one test_ function is defined in the file.
#   2. No unittest.TestCase classes (pytest function-based tests are preferred).
#   3. A pytestmark = pytest.mark.<marker> or @pytest.mark.<marker> is present.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Only check test files that actually exist
case "$FILE_PATH" in
    */test_*.py|*tests/*.py) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

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

# Check for pytest markers
if ! grep -q "pytestmark\|@pytest.mark\." "$FILE_PATH"; then
    WARNINGS="${WARNINGS}\n│  ⚠  No pytest markers — set pytestmark = pytest.mark.<marker> at module level"
fi

if [[ -n "$WARNINGS" ]]; then
    echo "┌─ Test structure check: $(basename "$FILE_PATH")"
    echo -e "$WARNINGS"
    echo "│"
    echo "└─ Fix these issues to maintain test quality standards"
fi

echo "$INPUT"
exit 0
