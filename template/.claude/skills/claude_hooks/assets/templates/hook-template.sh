#!/usr/bin/env bash
# =============================================================================
# Claude Code Hook Script Template
# =============================================================================
# Usage: Copy and adapt this file to .claude/hooks/<your-hook-name>.sh
# Make executable: chmod +x .claude/hooks/<your-hook-name>.sh
#
# Reference in settings.json:
#   "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<your-hook-name>.sh"
#
# Supported hook events this template handles:
#   PreToolUse, PostToolUse, Stop, UserPromptSubmit, SessionStart, SessionEnd
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 1. READ FULL JSON INPUT FROM STDIN
# Always read the complete payload before doing anything else.
# -----------------------------------------------------------------------------
INPUT=$(cat)

# -----------------------------------------------------------------------------
# 2. EXTRACT COMMON FIELDS
# -----------------------------------------------------------------------------
EVENT=$(echo "$INPUT"      | jq -r '.hook_event_name // empty')
SESSION=$(echo "$INPUT"    | jq -r '.session_id // empty')
CWD=$(echo "$INPUT"        | jq -r '.cwd // empty')
PERM_MODE=$(echo "$INPUT"  | jq -r '.permission_mode // empty')

# Tool-specific fields (PreToolUse / PostToolUse)
TOOL_NAME=$(echo "$INPUT"  | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT"    | jq -r '.tool_input.command // empty')
FILE_PATH=$(echo "$INPUT"  | jq -r '.tool_input.file_path // empty')

# Stop-specific fields
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
LAST_MSG=$(echo "$INPUT"    | jq -r '.last_assistant_message // empty')

# -----------------------------------------------------------------------------
# 3. OPTIONAL: LOG FOR DEBUGGING
# Comment out or redirect to file in production.
# Note: stderr is shown to user/Claude on exit 2; write logs to a file instead.
# -----------------------------------------------------------------------------
LOG_FILE="${CLAUDE_PROJECT_DIR:-$HOME}/.claude/hooks.log"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] EVENT=$EVENT TOOL=$TOOL_NAME CMD=${COMMAND:0:80}" \
  >> "$LOG_FILE" 2>/dev/null || true

# -----------------------------------------------------------------------------
# 4. BUSINESS LOGIC — adapt to your use case
# -----------------------------------------------------------------------------

# --- PreToolUse: validate before tool runs ---
if [[ "$EVENT" == "PreToolUse" ]]; then

  # Example: block rm -rf on root or home directory
  if [[ "$TOOL_NAME" == "Bash" ]]; then
    if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+(/|~|/home|/Users)\b'; then
      # exit 2 = blocking error; stderr goes to Claude as error message
      echo "BLOCKED: Recursive delete on root/home directory is not allowed." >&2
      exit 2
    fi

    # Example: block network requests to internal metadata servers
    if echo "$COMMAND" | grep -qE '169\.254\.169\.254|metadata\.google\.internal'; then
      echo "BLOCKED: Access to cloud metadata endpoints is not permitted." >&2
      exit 2
    fi
  fi

  # Example: protect sensitive files from being written
  if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]]; then
    BASENAME=$(basename "$FILE_PATH")
    if [[ "$BASENAME" == ".env" || "$BASENAME" == "*.pem" || "$FILE_PATH" == *"secrets"* ]]; then
      # Use JSON output for richer control
      jq -n '{
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "ask",
          permissionDecisionReason: "Writing to a sensitive file — please confirm"
        }
      }'
      exit 0
    fi
  fi

  # Default: allow the tool call (exit 0 with no JSON = allow)
  exit 0
fi

# --- PostToolUse: react after tool completed ---
if [[ "$EVENT" == "PostToolUse" ]]; then
  TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // {}')

  # Example: run linter after Python file is written
  if [[ "$TOOL_NAME" == "Write" && "$FILE_PATH" == *.py ]]; then
    if command -v ruff &>/dev/null; then
      if ! ruff check "$FILE_PATH" --quiet 2>/dev/null; then
        ISSUES=$(ruff check "$FILE_PATH" 2>&1 | head -20)
        jq -n --arg issues "$ISSUES" '{
          decision: "block",
          reason: ("Ruff found lint issues:\n" + $issues + "\nFix before proceeding.")
        }'
        exit 0
      fi
    fi
  fi

  exit 0
fi

# --- Stop: quality gate before Claude finishes ---
if [[ "$EVENT" == "Stop" ]]; then

  # CRITICAL: check stop_hook_active to prevent infinite loops
  if [[ "$STOP_ACTIVE" == "true" ]]; then
    # Already in a stop-hook cycle — do not block again
    exit 0
  fi

  # Example: run tests and block completion if they fail
  # Uncomment and adapt:
  # if ! npm test --silent 2>/dev/null; then
  #   jq -n '{"decision":"block","reason":"Test suite is failing. Fix all failing tests before finishing."}'
  #   exit 0
  # fi

  exit 0
fi

# --- UserPromptSubmit: validate or augment prompt ---
if [[ "$EVENT" == "UserPromptSubmit" ]]; then
  PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

  # Example: add context about current git branch to every prompt
  BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
  jq -n --arg branch "$BRANCH" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: ("Current git branch: " + $branch)
    }
  }'
  exit 0
fi

# --- SessionStart: inject environment / context ---
if [[ "$EVENT" == "SessionStart" ]]; then

  # Persist environment variables for all subsequent Bash commands
  if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then
    # Example: add project-local node_modules to PATH
    echo 'export PATH="./node_modules/.bin:$PATH"' >> "$CLAUDE_ENV_FILE"
  fi

  # Inject project context into Claude's context window
  if [[ -f "$CWD/README.md" ]]; then
    echo "Project README summary:"
    head -30 "$CWD/README.md" 2>/dev/null || true
  fi

  exit 0
fi

# --- SessionEnd: cleanup ---
if [[ "$EVENT" == "SessionEnd" ]]; then
  REASON=$(echo "$INPUT" | jq -r '.reason // "other"')
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Session ended: $REASON (id=$SESSION)" \
    >> "$LOG_FILE" 2>/dev/null || true
  exit 0
fi

# Fallback: if none of the events matched, just exit 0
exit 0
