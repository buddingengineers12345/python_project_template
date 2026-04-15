#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Block git push to main/master branches; feature branch pushes are allowed.
#
# Two guards are applied:
#   1. Explicit targets — `git push <remote> main|master` is blocked.
#   2. Implicit current-branch pushes — if HEAD is main/master and the command
#      is a bare `git push`, `git push origin`, or `git push -u origin`, the
#      push is blocked so the protected branch is never advanced directly.
#
# Developers should create a feature branch and open a pull request instead.
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

# Only check git push commands
case "$COMMAND" in
    *"git push"*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Explicit push to main/master
if echo "$COMMAND" | grep -qE "git push\s+\S+\s+(main|master)(\s|$)"; then
    echo "┌─ BLOCKED: direct push to main/master" >&2
    echo "│" >&2
    echo "│  Pushing directly to a protected branch is not allowed." >&2
    echo "│  Use a feature branch and open a pull request instead." >&2
    echo "│" >&2
    echo "│    git checkout -b feat/my-feature" >&2
    echo "│    git push -u origin feat/my-feature" >&2
    echo "└─" >&2
    exit 2
fi

# Implicit push from main/master
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    if echo "$COMMAND" | grep -qE "^git push\s*$|^git push\s+origin\s*$|^git push\s+-u\s+origin\s*$"; then
        echo "┌─ BLOCKED: HEAD is on protected branch '$CURRENT_BRANCH'" >&2
        echo "│" >&2
        echo "│  A bare 'git push' would advance the protected branch directly." >&2
        echo "│  Create a feature branch first:" >&2
        echo "│" >&2
        echo "│    git checkout -b feat/my-feature" >&2
        echo "│    git push -u origin feat/my-feature" >&2
        echo "└─" >&2
        exit 2
    fi
fi

echo "$INPUT"
