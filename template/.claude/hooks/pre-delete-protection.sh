#!/usr/bin/env bash
set -uo pipefail

# PreToolUse hook for Bash: block rm/del of critical project files.

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null) || { echo "$INPUT"; exit 0; }

# Only check rm commands
case "$COMMAND" in
    *rm*) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Protected files — never delete these
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
    if echo "$COMMAND" | grep -q "$protected"; then
        echo "┌─ Delete protection" >&2
        echo "│  ✗ BLOCKED: cannot delete critical file: $protected" >&2
        echo "│  These files are essential to the project infrastructure." >&2
        echo "└─ If you must remove this file, do it manually outside Claude." >&2
        exit 2
    fi
done

# Block rm -rf on .claude/ directory
if echo "$COMMAND" | grep -qE "rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|)\.claude(/|$|\s)"; then
    echo "┌─ Delete protection" >&2
    echo "│  ✗ BLOCKED: cannot recursively delete .claude/ directory" >&2
    echo "│  This directory contains skills, hooks, and settings." >&2
    echo "└─ Delete specific files within .claude/ instead." >&2
    exit 2
fi

echo "$INPUT"
exit 0
