#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Warn before git push to encourage running quality checks first.
#
# git push is already denied in .claude/settings.json; this hook fires first and
# gives a clear, actionable reminder rather than a silent permission failure.
# It exits 0 so it does not itself block (the deny rule handles that).
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:bash:git-push-reminder)
# Exits     : 0 = allow (warn only — settings.json deny handles the actual block)

set -uo pipefail

INPUT=$(cat)

COMMAND=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("command", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

if echo "$COMMAND" | grep -qE '^\s*git\s+push\b'; then
    echo "┌─ Reminder: git push must be done manually" >&2
    echo "│" >&2
    echo "│  Pushing is blocked in .claude/settings.json. Before pushing manually:" >&2
    echo "│" >&2
    echo "│    just review        — lint + types + docstrings" >&2
    echo "│    just test          — full test suite" >&2
    echo "│    git diff origin/main  — review the diff" >&2
    echo "│" >&2
    echo "│  When ready: run git push in your terminal (not via Claude)." >&2
    echo "└─" >&2
fi

echo "$INPUT"
