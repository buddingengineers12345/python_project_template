#!/usr/bin/env bash
# Claude SessionStart hook — * (all events)
# Display project status and surface any previous session snapshot on startup.
#
# Fires once when a new Claude Code session begins. Outputs:
#   - Project directory and detected toolchain versions
#   - Current git branch and lock-file health
#   - Path to the most recent pre-compact snapshot (if any) for context recovery
#   - Quick reference of the most common just recipes
#
# This gives Claude immediate orientation without requiring a manual "what's
# the project state?" follow-up question.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: session:start)
# Exits     : 0 always

set -uo pipefail

PROJECT=$(basename "$PWD")
STATE_DIR="$HOME/.claude/session-states"

echo "┌─ Session start: $PROJECT"
echo "│"
echo "│  Directory : $PWD"

# Toolchain versions (best-effort; versions may vary)
UV_VER=$(uv --version 2>/dev/null | head -1 || echo "uv not found")
echo "│  uv        : $UV_VER"

PYTHON_VER=$(uv run python --version 2>/dev/null || python3 --version 2>/dev/null || echo "python not found")
echo "│  python    : $PYTHON_VER"

echo "│"

# Git context
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached HEAD")
    DIRTY=$(git status --short 2>/dev/null | grep -c '.' || echo "0")
    echo "│  Branch    : $BRANCH"
    if [[ "$DIRTY" -gt 0 ]]; then
        echo "│  Status    : $DIRTY modified/staged file(s)"
    else
        echo "│  Status    : clean"
    fi
else
    echo "│  Git       : not a git repository"
fi

echo "│"

# Lock-file health
if [[ -f "uv.lock" ]]; then
    echo "│  uv.lock   : present ✓"
else
    echo "│  uv.lock   : MISSING — run: just sync"
fi

# Previous snapshot
LATEST_STATE=$(ls -t "$STATE_DIR/${PROJECT}_"*.txt 2>/dev/null | head -1 || true)
if [[ -n "$LATEST_STATE" ]]; then
    SNAP_TIME=$(basename "$LATEST_STATE" | grep -oE '[0-9]{8}_[0-9]{6}' | \
        sed 's/\([0-9]\{8\}\)_\([0-9]\{6\}\)/\1 \2/' || true)
    echo "│"
    echo "│  Pre-compact snapshot available ($SNAP_TIME):"
    echo "│    cat $LATEST_STATE"
fi

echo "│"
echo "│  Common commands:"
echo "│    just ci         — full pipeline (fix+fmt+lint+type+test)"
echo "│    just test       — run test suite"
echo "│    just review     — pre-merge checks"
echo "│    /generate       — render the template to /tmp/test-output"
echo "└─"

exit 0
