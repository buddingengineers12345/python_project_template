#!/usr/bin/env bash
# Claude PreCompact hook — * (all events)
# Snapshot git status, modified files, and current session context before
# context compaction so the state can be restored after /compact.
#
# Long template development sessions (editing copier.yml, Jinja files, tests,
# CI workflows) accumulate context that is valuable to preserve across compaction.
# The snapshot is written to ~/.claude/session-states/<project>_<timestamp>.txt.
#
# After compaction, run: cat ~/.claude/session-states/<latest-file>
# or use the session-start-bootstrap.sh output to recover key context.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:compact)
# Exits     : 0 always

set -uo pipefail

STATE_DIR="$HOME/.claude/session-states"
mkdir -p "$STATE_DIR"

PROJECT=$(basename "$PWD")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
STATE_FILE="$STATE_DIR/${PROJECT}_${TIMESTAMP}.txt"

{
    echo "=== Pre-compact state snapshot: $(date) ==="
    echo "Project : $PWD"
    echo "Timestamp: $TIMESTAMP"
    echo ""

    echo "--- Git branch ---"
    git branch --show-current 2>/dev/null || echo "(not a git repo or detached HEAD)"

    echo ""
    echo "--- Git status ---"
    git status --short 2>/dev/null || echo "(not a git repo)"

    echo ""
    echo "--- Staged files ---"
    git diff --cached --name-only 2>/dev/null || echo "(none)"

    echo ""
    echo "--- Modified (unstaged) ---"
    git diff --name-only 2>/dev/null || echo "(none)"

    echo ""
    echo "--- Recent commits (last 5) ---"
    git log --oneline -5 2>/dev/null || echo "(no commits)"

    echo ""
    echo "--- uv.lock present ---"
    [[ -f "uv.lock" ]] && echo "yes" || echo "NO — run just sync"

} > "$STATE_FILE" 2>/dev/null || true

echo "┌─ Pre-compact snapshot saved"
echo "│  File: $STATE_FILE"
echo "│"
echo "│  After /compact, review this file to restore key context."
echo "│  Command: cat $STATE_FILE"
echo "└─"

exit 0
