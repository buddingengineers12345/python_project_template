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

set -o pipefail

# Fail open: if this hook crashes for any reason other than a deliberate block
# (exit code 2), allow the tool to proceed.
INPUT=""
hook_fail_open_exit() {
  local rc=$?
  if [[ $rc -ne 0 && $rc -ne 2 ]]; then
    [[ -n "${INPUT}" ]] && echo "${INPUT}"
    trap - EXIT
    exit 0
  fi
}
trap hook_fail_open_exit EXIT

INPUT=$(cat)

COMMAND=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("command", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

ROUTE=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os, shlex, sys

def allow():
    print("ALLOW")

try:
    payload = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
except Exception:
    allow()
    sys.exit(0)

cmd = payload.get("tool_input", {}).get("command", "") or ""
try:
    tokens = shlex.split(cmd)
except ValueError:
    # Malformed quoting in the command: fail open.
    allow()
    sys.exit(0)

if not tokens or tokens[0] != "git":
    allow()
    sys.exit(0)

# Identify subcommand (first non-option token after known git globals).
i = 1
subcmd = None
while i < len(tokens):
    t = tokens[i]
    if t in ("-c", "-C", "--git-dir", "--work-tree", "--namespace"):
        i += 2
        continue
    if t.startswith("-"):
        i += 1
        continue
    subcmd = t
    i += 1
    break

if subcmd != "commit":
    allow()
    sys.exit(0)

# Scan commit args and only treat --no-verify as an option when it's not a value
# consumed by other option arguments (avoids false positives like: git commit -m --no-verify).
no_verify = False
while i < len(tokens):
    t = tokens[i]
    if t == "--":
        break

    if t in ("-m", "-F", "--message"):
        i += 2
        continue

    if t == "--no-verify":
        no_verify = True
        break

    i += 1

print("BLOCK" if no_verify else "ALLOW")
PYEOF
) || { echo "$INPUT"; exit 0; }

if [[ "$ROUTE" == "BLOCK" ]]; then
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
