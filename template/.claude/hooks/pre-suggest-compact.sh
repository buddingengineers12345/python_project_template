#!/usr/bin/env bash
# Claude PreToolUse hook — Edit|Write
# Suggest /compact at regular intervals to prevent context degradation.
#
# Long Copier template development sessions involve many file reads (Jinja files,
# pyproject, copier.yml, tests) and successive edits. Context window saturation
# increases hallucination and missed instruction risk. This hook counts Edit/Write
# tool calls and surfaces a compact suggestion every THRESHOLD operations.
#
# The counter is stored in a temp file scoped to the current working directory
# so multiple concurrent Claude sessions in different projects don't interfere.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:edit-write:suggest-compact)
# Exits     : 0 = allow (warn only — never blocks)

set -uo pipefail

INPUT=$(cat)

# Project-scoped counter file (hash of CWD path for uniqueness)
CWD_HASH=$(echo "$PWD" | cksum | cut -d' ' -f1)
COUNTER_FILE="/tmp/.claude-compact-count-${CWD_HASH}"

THRESHOLD=50

# Read and increment counter
COUNT=0
if [[ -f "$COUNTER_FILE" ]]; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
fi
# Strip any non-numeric characters that might have crept in
COUNT=$(echo "$COUNT" | tr -dc '0-9' || echo "0")
COUNT=${COUNT:-0}
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Suggest compact at each threshold crossing
if (( COUNT % THRESHOLD == 0 )); then
    echo "┌─ Compact suggestion (tool call #${COUNT})" >&2
    echo "│" >&2
    echo "│  This session has reached ${COUNT} edit/write operations." >&2
    echo "│  Long sessions increase context saturation and may cause Claude" >&2
    echo "│  to miss earlier instructions or introduce drift." >&2
    echo "│" >&2
    echo "│  Consider running /compact to compress the context before" >&2
    echo "│  continuing with large changes (e.g. new template variable," >&2
    echo "│  refactoring copier.yml, updating multiple Jinja files)." >&2
    echo "└─" >&2
fi

echo "$INPUT"
