#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Pre-commit quality guard: scan staged Python files for secrets, debug markers,
# and ruff violations before git commit executes.
#
# Checks performed (in order):
#   1. Secrets/credentials — blocks if hardcoded passwords, API keys, or tokens
#      are detected in newly staged Python lines.
#   2. Debug markers — warns (non-blocking) if pdb.set_trace(), breakpoint(), or
#      similar debugger statements appear in staged changes.
#   3. Ruff lint — warns (non-blocking) if staged .py files have lint violations;
#      the pre-commit hook will enforce this at commit time regardless.
#
# This hook fires BEFORE git commit; the pre-commit hook enforces again at
# commit time. This layer provides early feedback on clearly dangerous content.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:bash:commit-quality)
# Exits     : 0 = allow (with warnings)  |  2 = block (secrets detected)

set -uo pipefail

INPUT=$(cat)

COMMAND=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("command", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

# Only fire for git commit commands
if ! echo "$COMMAND" | grep -qE '^\s*git\s+commit\b'; then
    echo "$INPUT"
    exit 0
fi

# Get staged Python files (ACMR = Added, Copied, Modified, Renamed)
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep '\.py$' || true)

if [[ -z "$STAGED_PY" ]]; then
    echo "$INPUT"
    exit 0
fi

echo "┌─ Pre-commit quality scan" >&2

BLOCKED=0
WARNED=0

# ── 1. Secrets detection ──────────────────────────────────────────────────────
# Scan only ADDED lines (+) for credential-like assignments.
SECRETS=$(git diff --cached -- '*.py' 2>/dev/null \
    | grep '^\+' \
    | grep -iE \
        '(password|api_key|api_secret|secret_key|auth_token|private_key|access_token)\s*=\s*["\x27][^\s"'\'']{6,}' \
    || true)

if [[ -n "$SECRETS" ]]; then
    echo "│" >&2
    echo "│  ✗ SECRETS: Potential credentials found in staged changes:" >&2
    echo "$SECRETS" | head -5 | while IFS= read -r line; do
        echo "│      $line" >&2
    done
    BLOCKED=1
fi

# ── 2. Debug marker detection ─────────────────────────────────────────────────
DEBUG=$(git diff --cached -- '*.py' 2>/dev/null \
    | grep '^\+' \
    | grep -E '(pdb\.set_trace\(\)|breakpoint\(\)|import\s+pdb\b)' \
    || true)

if [[ -n "$DEBUG" ]]; then
    echo "│" >&2
    echo "│  ⚠  DEBUG: Debugger statements found in staged changes:" >&2
    echo "$DEBUG" | head -3 | while IFS= read -r line; do
        echo "│      $line" >&2
    done
    WARNED=1
fi

# ── 3. Ruff lint on staged files ──────────────────────────────────────────────
# shellcheck disable=SC2086
RUFF_ISSUES=$(uv run ruff check $STAGED_PY --output-format concise 2>&1 \
    | grep -v '^\s*$' || true)

if [[ -n "$RUFF_ISSUES" ]]; then
    echo "│" >&2
    echo "│  ⚠  LINT: ruff found issues in staged files:" >&2
    echo "$RUFF_ISSUES" | head -10 | while IFS= read -r line; do
        echo "│      $line" >&2
    done
    WARNED=1
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo "│" >&2
if [[ $BLOCKED -eq 1 ]]; then
    echo "└─ ✗ Commit BLOCKED — remove secrets/credentials before committing" >&2
    exit 2
elif [[ $WARNED -eq 1 ]]; then
    echo "└─ ⚠  Warnings present — review above before committing" >&2
else
    echo "└─ ✓ Pre-commit scan passed" >&2
fi

echo "$INPUT"
