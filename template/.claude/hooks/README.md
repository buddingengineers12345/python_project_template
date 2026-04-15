# Claude Code Hooks — Developer Guide

This directory contains shell hooks for Claude Code lifecycle events in projects
generated from the `python_starter_template` Copier template. The hooks enforce
project standards deterministically: blocking dangerous operations, running
linters after edits, and providing contextual reminders.

## How hooks are registered

Hooks are declared in `.claude/settings.json` under the `"hooks"` key:

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "bash .claude/hooks/post-edit-python.sh"
        }
      ],
      "description": "Run ruff + basedpyright after every .py edit"
    }
  ]
}
```

Each entry requires:
- `matcher` — which tool(s) trigger this hook (see Matchers below)
- `hooks[].type` — always `"command"` for shell hooks
- `hooks[].command` — the shell command (relative to the project root)
- `description` — shown in the Claude Code UI

## Lifecycle events

| Event | When it fires | Can block? | Typical use |
|---|---|---|---|
| `SessionStart` | Once at session start | No | Project orientation, show status |
| `PreToolUse` | Before every tool call | **Yes** (exit 2) | Guard dangerous operations |
| `PostToolUse` | After every tool call | No | Lint, type-check, reminders |
| `PreCompact` | Before `/compact` | No | Snapshot state for recovery |
| `Stop` | After every Claude response | No | Notifications, persistence |

## Matchers

| Matcher | Triggers on |
|---|---|
| `*` | Every tool call |
| `Bash` | Shell command execution |
| `Edit` | Single-file edits |
| `Write` | New file creation |
| `MultiEdit` | Multi-location edits |
| `Edit\|Write` | Any file write |
| `Write\|Edit\|MultiEdit` | Any file modification |

## Exit codes

Exit codes are meaningful **only in PreToolUse** hooks.

| Exit code | PreToolUse | Other events |
|---|---|---|
| `0` | Allow tool call | No effect |
| `2` | **Block** tool call (stderr shown to Claude) | Treated as success |

All PostToolUse, Stop, PreCompact, and SessionStart hooks must exit `0`.

## JSON input format

Every hook receives JSON on **stdin**. Read it with `INPUT=$(cat)`.

### Tool call fields (PreToolUse / PostToolUse)

```json
{
  "session_id": "abc123",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/abs/path/to/file.py",
    "old_string": "...",
    "new_string": "..."
  }
}
```

For `Bash`, `tool_input` has `"command"` instead of `"file_path"`.

For `PostToolUse`, additionally:

```json
{
  "tool_output": {
    "output": "stdout",
    "error": "stderr",
    "exit_code": 0
  }
}
```

### Stop / SessionStart

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/session.jsonl"
}
```

### Standard JSON parsing pattern

```bash
INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")
```

For PreToolUse, always guard the parse: `|| { echo "$INPUT"; exit 0; }` so a
malformed payload never accidentally blocks the tool.

## Output conventions

Use box-drawing characters for consistent visual structure:

```
┌─ Hook name: context
│
│  Content lines
│
└─ ✓ OK  or  ✗ Problem found
```

- **PostToolUse / SessionStart / Stop**: print to **stdout**
- **PreToolUse blocking messages**: print to **stderr**
- **PreToolUse pass-through**: echo `$INPUT` back to stdout so the tool proceeds

## Shell script templates

### PreToolUse — blocking hook

```bash
#!/usr/bin/env bash
# Claude PreToolUse hook — <Matcher>
# <One-line description>
#
# Reference : <URL or "Custom">
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

VALUE=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("command", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

if echo "$VALUE" | grep -qE '<pattern>'; then
    echo "┌─ BLOCKED: <reason>" >&2
    echo "│" >&2
    echo "│  Why this is blocked and how to fix it." >&2
    echo "└─" >&2
    exit 2
fi

echo "$INPUT"
```

### PostToolUse — non-blocking feedback hook

```bash
#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# <One-line description>
#
# Reference : <URL or "Custom">
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")

if [[ "$FILE_PATH" != *.ext ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

echo "┌─ Check: $FILE_PATH"
# ... run checks ...
echo "└─ ✓ Done"

exit 0
```

## Hooks in this generated project

| Script | Event | Matcher | Purpose |
|---|---|---|---|
| `post-edit-python.sh` | PostToolUse | Edit\|Write | ruff + basedpyright after `.py` edits |
| `post-edit-markdown.sh` | PostToolUse | Edit | Warn if `.md` edited outside `docs/` |
| `post-edit-refactor-test-guard.sh` | PostToolUse | Edit\|Write | Remind to run tests after several `src/` edits |
| `post-bash-test-coverage-reminder.sh` | PostToolUse | Bash | Surface modules below 85% after test runs |
| `post-write-test-structure.sh` | PostToolUse | Write | Check test file structure and markers |
| `pre-bash-block-no-verify.sh` | PreToolUse | Bash | Block `git --no-verify` |
| `pre-bash-git-push-reminder.sh` | PreToolUse | Bash | Warn to review before push |
| `pre-bash-commit-quality.sh` | PreToolUse | Bash | Secret/debug scan before commit |
| `pre-bash-coverage-gate.sh` | PreToolUse | Bash | Warn before `git commit` if coverage below threshold |
| `pre-bash-branch-protection.sh` | PreToolUse | Bash | Block `git push` to main/master |
| `pre-delete-protection.sh` | PreToolUse | Bash | Block `rm` of critical files |
| `pre-config-protection.sh` | PreToolUse | Write\|Edit\|MultiEdit | Block weakening ruff/basedpyright config |
| `pre-protect-uv-lock.sh` | PreToolUse | Write\|Edit | Block direct edits to `uv.lock` |
| `pre-write-src-require-test.sh` | PreToolUse | Write\|Edit | Block if test file missing in `tests/unit/`, `tests/integration/`, or `tests/e2e/` for `src/<pkg>/<module>.py` (strict TDD) |
| `pre-write-src-test-reminder.sh` | (optional) | Write\|Edit | Non-blocking alternative to `pre-write-src-require-test.sh` — **do not register both** |

## Adding a new hook

1. **Write the script** using a template above. Keep it fast — hooks run on
   every matching tool call, so avoid slow operations in PreToolUse hooks.

2. **Register it** in `.claude/settings.json`:
   ```json
   {
     "matcher": "Edit|Write",
     "hooks": [{"type": "command", "command": "bash .claude/hooks/my-hook.sh"}],
     "description": "What this hook does"
   }
   ```

3. **Test manually** before relying on it:
   ```bash
   echo '{"tool_input":{"file_path":"/tmp/test.py"}}' \
     | bash .claude/hooks/my-hook.sh
   ```
