#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Block `rm` (and recursive deletes) of files critical to the project
# infrastructure, and block `rm -rf` of the .claude/ directory.
#
# Protected files include pyproject.toml, justfile, CLAUDE.md,
# .pre-commit-config.yaml, .copier-answers.yml, uv.lock, and
# .claude/settings.json. These files are essential for builds, quality gates,
# and Claude Code configuration; deleting them through Claude is never the
# right move. If a real removal is needed, the user should do it manually.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

COMMAND=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("command", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Only check rm commands
case "$COMMAND" in
    *rm*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Protected files — never delete these via Claude
PROTECTED_FILES=(
    "pyproject.toml"
    "justfile"
    "CLAUDE.md"
    ".pre-commit-config.yaml"
    ".copier-answers.yml"
    "uv.lock"
    ".claude/settings.json"
)

for protected in "${PROTECTED_FILES[@]}"; do
    if echo "$COMMAND" | grep -q -- "$protected"; then
        echo "┌─ BLOCKED: delete protection" >&2
        echo "│" >&2
        echo "│  Cannot delete critical file: $protected" >&2
        echo "│  These files are essential to the project infrastructure." >&2
        echo "│" >&2
        echo "└─ If you must remove this file, do it manually outside Claude." >&2
        exit 2
    fi
done

# Block rm -rf on the .claude/ directory itself
if echo "$COMMAND" | grep -qE "rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|)\.claude(/|$|\s)"; then
    echo "┌─ BLOCKED: delete protection" >&2
    echo "│" >&2
    echo "│  Cannot recursively delete the .claude/ directory." >&2
    echo "│  It contains skills, hooks, and settings that drive Claude Code." >&2
    echo "│" >&2
    echo "└─ Delete specific files within .claude/ instead, one at a time." >&2
    exit 2
fi

echo "$INPUT"
