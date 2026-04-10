# Claude Code Hooks — Developer Guide

This directory contains shell hooks that integrate with Claude Code's lifecycle
events. Hooks let you enforce project standards deterministically — blocking
dangerous operations, running linters after edits, or persisting session state —
without relying on Claude's non-deterministic instruction-following.

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
- `hooks[].command` — the shell command to run (relative to the project root)
- `description` — shown in the UI; be specific about what the hook does

## Lifecycle events

| Event | When it fires | Can block? | Input |
|---|---|---|---|
| `SessionStart` | Once when a session begins | No | Session metadata |
| `PreToolUse` | Before every tool call | **Yes** (exit 2) | Tool call JSON |
| `PostToolUse` | After every tool call | No | Tool call + output JSON |
| `PreCompact` | Before `/compact` context compaction | No | Compact metadata |
| `Stop` | After every Claude response | No | Session + transcript path |

## Matchers

Matchers are matched against the tool name. Combine with `|` for multiple:

| Matcher | Triggers on |
|---|---|
| `*` | Every tool call |
| `Bash` | Shell command execution |
| `Edit` | Single-file edits |
| `Write` | New file creation (Write tool) |
| `MultiEdit` | Multi-location edits in one call |
| `Edit\|Write` | Either edit or new-file creation |
| `Write\|Edit\|MultiEdit` | Any file modification |

## Exit codes

Exit codes are meaningful **only for PreToolUse** hooks. For all other events
the exit code is ignored; always exit `0` to avoid confusing output.

| Exit code | PreToolUse meaning | Other events |
|---|---|---|
| `0` | Allow the tool call to proceed | No effect |
| `2` | **Block** the tool call; stderr is shown to Claude | Treated as success |
| Other non-zero | Treated as `0` (allow); stderr surfaced as warning | Treated as success |

> **Rule**: Only PreToolUse hooks should ever exit `2`. All PostToolUse, Stop,
> PreCompact, and SessionStart hooks must exit `0`.

## JSON input format

Every hook receives a JSON object on **stdin**. Read it with `INPUT=$(cat)`.

### PreToolUse / PostToolUse — tool call fields

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

For the `Bash` tool, `tool_input` contains `"command"` instead of `"file_path"`.

For `PostToolUse`, the JSON also includes the tool's output:

```json
{
  "tool_output": {
    "output": "command stdout",
    "error": "command stderr",
    "exit_code": 0
  }
}
```

### Stop / SessionStart fields

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/session.jsonl"
}
```

### Parsing with Python (preferred pattern)

```bash
INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")
```

Always guard against parse failure with `|| { echo "$INPUT"; exit 0; }` for
PreToolUse hooks (so a malformed payload never accidentally blocks the tool).

## Output conventions

All hooks in this project use box-drawing characters for visual structure:

```
┌─ Hook name: context
│
│  Informational content here
│  More content
│
└─ Summary line (e.g. ✓ All checks passed  or  ✗ Fix before committing)
```

**stdout vs stderr:**
- `PostToolUse` / `SessionStart` / `Stop` — print to **stdout**; Claude reads it
- `PreToolUse` blocking messages — print to **stderr**; shown on block
- `PreToolUse` pass-through — echo `$INPUT` back to stdout (required for the
  tool call to proceed with the original payload intact)

## File naming convention

```
{event-prefix}-{matcher}-{purpose}.sh
```

| Prefix | Lifecycle event |
|---|---|
| `pre-bash-` | PreToolUse on Bash |
| `pre-write-` | PreToolUse on Write |
| `pre-config-` | PreToolUse on Edit/Write/MultiEdit |
| `pre-protect-` | PreToolUse guard for a specific file/resource |
| `pre-suggest-` | PreToolUse advisory (never blocks) |
| `pre-compact-` | PreCompact |
| `post-edit-` | PostToolUse on Edit or Write |
| `post-bash-` | PostToolUse on Bash |
| `session-` | SessionStart |
| `stop-` | Stop |

## Shell script template

### PreToolUse — blocking hook

```bash
#!/usr/bin/env bash
# Claude PreToolUse hook — <Matcher>
# One-line description of what this hook does.
#
# Reference : <URL or "Custom">
# Exits     : 0 = allow  |  2 = block

set -uo pipefail   # note: NOT -e (we handle exit manually)

INPUT=$(cat)

COMMAND=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("command", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

if echo "$COMMAND" | grep -qE '<pattern>'; then
    echo "┌─ BLOCKED: <reason>" >&2
    echo "│" >&2
    echo "│  Explanation of why this is blocked." >&2
    echo "│  Recovery steps." >&2
    echo "└─" >&2
    exit 2
fi

echo "$INPUT"   # pass through: required for the tool call to proceed
```

### PostToolUse — non-blocking feedback hook

```bash
#!/usr/bin/env bash
# Claude PostToolUse hook — Edit|Write
# One-line description of what this hook does.
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

# Guard: skip if not the file type this hook cares about
if [[ "$FILE_PATH" != *.ext ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

echo "┌─ Check: $FILE_PATH"
# ... do work ...
echo "└─ ✓ Done"

exit 0
```

### Stop — async side-effect hook

```bash
#!/usr/bin/env bash
# Claude Stop hook — * (all events)
# One-line description.
#
# Reference : <URL or "Custom">
# Exits     : 0 always

set -uo pipefail

INPUT=$(cat)

echo "$INPUT" | python3 - <<'PYEOF'
import json, os, sys, datetime
from pathlib import Path

try:
    data = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

# ... do async work (write files, send notifications) ...
PYEOF

exit 0
```

## Hooks in this project

| Script | Event | Matcher | Purpose |
|---|---|---|---|
| `session-start-bootstrap.sh` | SessionStart | * | Display project status and previous snapshot |
| `pre-bash-block-no-verify.sh` | PreToolUse | Bash | Block `git --no-verify` |
| `pre-bash-git-push-reminder.sh` | PreToolUse | Bash | Warn to run `just review` before push |
| `pre-bash-commit-quality.sh` | PreToolUse | Bash | Secret/debug scan before `git commit` |
| `pre-bash-coverage-gate.sh` | PreToolUse | Bash | Warn before `git commit` if coverage below threshold |
| `pre-config-protection.sh` | PreToolUse | Write\|Edit\|MultiEdit | Block weakening ruff/pyright config edits |
| `pre-protect-uv-lock.sh` | PreToolUse | Write\|Edit | Block direct edits to `uv.lock` |
| `pre-write-src-require-test.sh` | PreToolUse | Write\|Edit | Block if `tests/<pkg>/test_<module>.py` missing for top-level `src/<pkg>/<module>.py` (strict TDD) |
| `pre-write-src-test-reminder.sh` | (optional) | Write\|Edit | Non-blocking alternative to `pre-write-src-require-test.sh` — **do not register both** |
| `pre-write-doc-file-warning.sh` | PreToolUse | Write | Block `.md` files outside `docs/` |
| `pre-write-jinja-syntax.sh` | PreToolUse | Write | Validate Jinja2 syntax before writing |
| `pre-suggest-compact.sh` | PreToolUse | Edit\|Write | Suggest `/compact` every 50 operations |
| `pre-compact-save-state.sh` | PreCompact | * | Snapshot git state before compaction |
| `post-edit-python.sh` | PostToolUse | Edit\|Write | ruff + basedpyright after `.py` edits |
| `post-edit-jinja.sh` | PostToolUse | Edit\|Write | Jinja2 syntax check after `.jinja` edits |
| `post-edit-markdown.sh` | PostToolUse | Edit | Warn if existing `.md` edited outside `docs/` |
| `post-edit-copier-migration.sh` | PostToolUse | Edit\|Write | Migration checklist after `copier.yml` edits |
| `post-edit-template-mirror.sh` | PostToolUse | Edit\|Write | Remind to mirror `template/.claude/` ↔ root |
| `post-bash-pr-created.sh` | PostToolUse | Bash | Log PR URL and suggest review commands |
| `post-edit-refactor-test-guard.sh` | PostToolUse | Edit\|Write | Remind to run tests after several `src/` or `scripts/` edits |
| `stop-session-end.sh` | Stop | * | Persist session state JSON |
| `stop-evaluate-session.sh` | Stop | * | Extract reusable patterns from transcript |
| `stop-cost-tracker.sh` | Stop | * | Track and accumulate session costs |
| `stop-desktop-notify.sh` | Stop | * | macOS desktop notification on completion |

## Adding a new hook

1. **Write the script** using the appropriate template above.
   - Place it in this directory.
   - Make it executable (it is invoked via `bash .claude/hooks/name.sh` so the
     x bit is optional but conventional: `chmod +x`).

2. **Register it** in `.claude/settings.json` under the correct lifecycle event.
   - Add a `description` field — this is shown in the UI and helps during review.

3. **Test it** by running the script manually with a representative JSON payload:
   ```bash
   echo '{"tool_input":{"file_path":"/tmp/test.py"}}' \
     | bash .claude/hooks/post-edit-python.sh
   ```

4. **Mirror if needed** — if the hook is also useful for generated projects,
   add it to `template/.claude/hooks/` and register it in
   `template/.claude/settings.json`.

## Dual-hierarchy reminder

This repository has two parallel `.claude/` trees:

```
.claude/hooks/            ← used while DEVELOPING this Copier template
template/.claude/hooks/   ← rendered into GENERATED projects
```

When you add or modify a hook:
- Changes to `template/.claude/hooks/` affect every project generated from
  this template going forward.
- Changes to the root `.claude/hooks/` affect only this meta-repo.
- Many hooks belong in **both** (e.g. ruff post-edit, no-verify blocker).

The `post-edit-template-mirror.sh` hook will remind you when you edit files
under `template/.claude/` to check whether parity with the root hooks is needed.
