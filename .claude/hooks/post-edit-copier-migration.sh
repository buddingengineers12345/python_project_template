#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# Remind to update _migrations, _skip_if_exists, and tests after copier.yml edits.
#
# copier.yml is the heart of this template: it defines variables, computed
# values, lifecycle hooks, and skip rules. Edits to it often require
# accompanying changes in several other places that are easy to overlook:
#
#   _skip_if_exists   — new generated files may need protection on update
#   _migrations       — renamed/removed variables need migration blocks
#   tests/            — new variables need test coverage in test_template.py
#   CLAUDE.md         — copier variable conventions section may need updating
#
# This hook fires after any edit to copier.yml and surfaces the checklist.
# It is non-blocking (exit 0) and purely informational.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
) || exit 0

BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" != "copier.yml" ]]; then
    exit 0
fi

echo "┌─ copier.yml edited — migration checklist"
echo "│"
echo "│  If you added, removed, or renamed a template variable:"
echo "│"
echo "│    □  _skip_if_exists    — does the affected generated file need protection"
echo "│                            from being overwritten on copier update?"
echo "│"
echo "│    □  _migrations        — add a migration block if renaming or removing a"
echo "│                            variable so existing generated projects can upgrade"
echo "│"
echo "│    □  tests/integration/test_template.py  — add or update parametrized tests that cover"
echo "│                                 the new variable behaviour"
echo "│"
echo "│    □  CLAUDE.md          — update 'Copier variable conventions' section if"
echo "│                            the semantics or defaults changed meaningfully"
echo "│"
echo "│  Validate the template still renders correctly:"
echo "│    just test              — run full integration test suite"
echo "│    copier copy . /tmp/test-output --trust --defaults && rm -rf /tmp/test-output"
echo "└─"

exit 0
