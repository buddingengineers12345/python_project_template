#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# Remind to mirror template/.claude/ changes to the root .claude/ (and vice versa).
#
# This repository has two parallel .claude/ hierarchies:
#
#   .claude/              — used while developing THIS template (the meta-project)
#   template/.claude/     — rendered into generated projects via Copier
#
# Changes to one side frequently need to be reflected in the other:
#   • A new hook added to template/.claude/hooks/ may also make sense for the
#     template repo itself (root .claude/hooks/).
#   • A root .claude/commands/ update (e.g. /review, /standards) may need to
#     be propagated to template/.claude/commands/ so generated projects inherit it.
#   • Permission changes in template/.claude/settings.json should be reviewed
#     against the root .claude/settings.json for parity.
#
# This hook fires after any edit inside template/.claude/ and surfaces a
# targeted reminder based on which subdirectory was changed.
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
<<<"$INPUT") || exit 0

# Only fire for template/.claude/ edits
if ! echo "$FILE_PATH" | grep -qE '(^|/)template/\.claude/'; then
    exit 0
fi

echo "┌─ template/.claude/ edited — mirror reminder"
echo "│"
echo "│  Changed: $FILE_PATH"
echo "│"
echo "│  template/.claude/ changes affect GENERATED projects."
echo "│  Check whether the same change belongs in the root .claude/ too:"

if echo "$FILE_PATH" | grep -q '/hooks/'; then
    HOOK_NAME=$(basename "$FILE_PATH")
    echo "│"
    echo "│    Root counterpart to review: .claude/hooks/$HOOK_NAME"
    echo "│    — If this hook applies during template development, add it here too."
fi

if echo "$FILE_PATH" | grep -q '/commands/'; then
    CMD_NAME=$(basename "$FILE_PATH")
    echo "│"
    echo "│    Root counterpart to review: .claude/commands/$CMD_NAME"
    echo "│    — If this command is useful when developing the template, add it too."
fi

if echo "$FILE_PATH" | grep -q 'settings.json'; then
    echo "│"
    echo "│    Root counterpart to review: .claude/settings.json"
    echo "│    — Check permissions (allow/deny) and hook list parity."
fi

echo "│"
echo "│  Conversely: root .claude/ improvements should usually be propagated"
echo "│  to template/.claude/ so generated projects benefit as well."
echo "└─"

exit 0
