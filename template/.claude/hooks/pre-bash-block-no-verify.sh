#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Block any git command that uses --no-verify, protecting pre-commit quality gates.
#
# --no-verify skips pre-commit, commit-msg, and pre-push hooks. This project
# enforces quality via those hooks (ruff, basedpyright, secret scanning). The
# flag is also explicitly listed in the deny block of settings.json; this hook
# fires first and surfaces a clear reason rather than a silent permission deny.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:bash:block-no-verify)
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

COMMAND=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("command", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

if echo "$COMMAND" | grep -qE -- '--no-verify'; then
    echo "┌─ BLOCKED: --no-verify detected" >&2
    echo "│" >&2
    echo "│  --no-verify skips pre-commit, commit-msg, and pre-push hooks." >&2
    echo "│  Those hooks enforce ruff, basedpyright, and secret-detection guards." >&2
    echo "│  Bypassing them is explicitly prohibited in .claude/settings.json." >&2
    echo "│" >&2
    echo "│  Correct approach: fix the code so it passes quality gates, then" >&2
    echo "│  commit normally without --no-verify." >&2
    echo "│" >&2
    echo "│    just fix   — auto-fix ruff issues" >&2
    echo "│    just lint  — see remaining violations" >&2
    echo "│    just type  — type-check with basedpyright" >&2
    echo "└─" >&2
    exit 2
fi

echo "$INPUT"
