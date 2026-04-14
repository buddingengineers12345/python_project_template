#!/usr/bin/env bash
set -uo pipefail

# PreToolUse hook for Bash: block git push to main/master branches.
# Feature branch pushes are allowed.

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null) || { echo "$INPUT"; exit 0; }

# Only check git push commands
case "$COMMAND" in
    *"git push"*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Check if pushing to main or master
if echo "$COMMAND" | grep -qE "git push\s+\S+\s+(main|master)(\s|$)"; then
    echo "┌─ Branch protection" >&2
    echo "│  ✗ BLOCKED: cannot push directly to main/master" >&2
    echo "│  Use a feature branch and create a pull request instead." >&2
    echo "└─ Example: git push origin feat/my-feature" >&2
    exit 2
fi

# Check if on main/master and pushing without specifying a branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    # If the push command doesn't specify a remote branch, it pushes current
    if echo "$COMMAND" | grep -qE "^git push\s*$|^git push\s+origin\s*$|^git push\s+-u\s+origin\s*$"; then
        echo "┌─ Branch protection" >&2
        echo "│  ✗ BLOCKED: currently on '$CURRENT_BRANCH' — cannot push directly" >&2
        echo "│  Create a feature branch first:" >&2
        echo "│    git checkout -b feat/my-feature" >&2
        echo "│    git push -u origin feat/my-feature" >&2
        echo "└─" >&2
        exit 2
    fi
fi

echo "$INPUT"
exit 0
