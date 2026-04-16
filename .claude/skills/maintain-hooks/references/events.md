# Hook events

Complete input schemas and decision control for all Claude Code hook events.

## Table of Contents

| Category | Events |
|----------|--------|
| Session lifecycle | [SessionStart](#sessionstart), [SessionEnd](#sessionend) |
| Prompt handling | [UserPromptSubmit](#userpromptsubmit) |
| Tool lifecycle | [PreToolUse](#pretooluse), [PermissionRequest](#permissionrequest), [PermissionDenied](#permissiondenied), [PostToolUse](#posttooluse), [PostToolUseFailure](#posttoolusefailure) |
| Agent lifecycle | [SubagentStart](#subagentstart), [SubagentStop](#subagentstop) |
| Stop events | [Stop](#stop), [StopFailure](#stopfailure) |
| Team events | [TeammateIdle](#teammateidle), [TaskCreated](#taskcreated), [TaskCompleted](#taskcompleted) |
| Compaction | [PreCompact](#precompact), [PostCompact](#postcompact) |
| Config & files | [InstructionsLoaded](#instructionsloaded), [ConfigChange](#configchange), [CwdChanged](#cwdchanged), [FileChanged](#filechanged) |
| Worktrees | [WorktreeCreate](#worktreecreate), [WorktreeRemove](#worktreeremove) |
| Notifications | [Notification](#notification) |
| MCP Elicitation | [Elicitation](#elicitation), [ElicitationResult](#elicitationresult) |

---

## Common input fields (all events)

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../transcript.jsonl",
  "cwd": "/Users/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

`permission_mode` values: `default`, `plan`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`

When running inside a subagent:
- `agent_id` — unique subagent identifier
- `agent_type` — agent name (e.g., `"Explore"`, `"security-reviewer"`)

---

## SessionStart

**When:** Session begins or resumes. Only `type: "command"` hooks supported.

**Matcher values:** `startup` | `resume` | `clear` | `compact`

**Input:**
```json
{
  "source": "startup",
  "model": "claude-sonnet-4-6"
}
```

**Output:**
- stdout text → added to Claude's context
- `hookSpecificOutput.additionalContext` → string added to context
- `CLAUDE_ENV_FILE` — append `export VAR=value` lines to persist env vars to Bash

**Cannot block.** Use for context injection and environment setup.

**Pattern — inject git context:**
```bash
#!/usr/bin/env bash
INPUT=$(cat)
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
RECENT=$(git log --oneline -5 2>/dev/null || echo "no git history")
echo "Current branch: $BRANCH"
echo "Recent commits:"
echo "$RECENT"
```

---

## SessionEnd

**When:** Session terminates. Default timeout: 1.5s (configurable via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`).

**Matcher values:** `clear` | `resume` | `logout` | `prompt_input_exit` | `bypass_permissions_disabled` | `other`

**Input:**
```json
{
  "reason": "other"
}
```

**Cannot block.** Use for cleanup, logging, archiving transcripts.

---

## UserPromptSubmit

**When:** User submits a prompt, before Claude processes it.

**No matcher support** — fires on every prompt.

**Input:**
```json
{
  "prompt": "Write a function to calculate factorial"
}
```

**Output:**
- Plain stdout (non-JSON) → added as context visible to Claude
- `hookSpecificOutput.additionalContext` → added more discretely
- `hookSpecificOutput.sessionTitle` → renames the session
- `decision: "block"` + `reason` → rejects the prompt

**Block a prompt:**
```bash
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt')
if echo "$PROMPT" | grep -qi "drop table\|delete from"; then
  jq -n '{"decision":"block","reason":"SQL destructive operations require human review"}'
  exit 0
fi
exit 0
```

---

## PreToolUse

**When:** After Claude creates tool parameters, before the tool executes. Can block.

**Matcher values:** `Bash` | `Edit` | `MultiEdit` | `Write` | `Read` | `Glob` | `Grep` | `Agent` | `WebFetch` | `WebSearch` | `AskUserQuestion` | `ExitPlanMode` | MCP tools (`mcp__<server>__<tool>`)

**Input:**
```json
{
  "tool_name": "Bash",
  "tool_use_id": "toolu_01ABC...",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite",
    "timeout": 120000,
    "run_in_background": false
  }
}
```

**tool_input by tool:**

| Tool | Key fields |
|------|-----------|
| `Bash` | `command`, `description`, `timeout`, `run_in_background` |
| `Write` | `file_path`, `content` |
| `Edit` | `file_path`, `old_string`, `new_string`, `replace_all` |
| `Read` | `file_path`, `offset`, `limit` |
| `Glob` | `pattern`, `path` |
| `Grep` | `pattern`, `path`, `glob`, `output_mode`, `-i`, `multiline` |
| `WebFetch` | `url`, `prompt` |
| `WebSearch` | `query`, `allowed_domains`, `blocked_domains` |
| `Agent` | `prompt`, `description`, `subagent_type`, `model` |

**Output (hookSpecificOutput):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Reason shown to user (allow/ask) or Claude (deny)",
    "updatedInput": { "command": "modified command" },
    "additionalContext": "Extra context for Claude before tool runs"
  }
}
```

`permissionDecision` values:
- `"allow"` — skip permission prompt, proceed
- `"deny"` — block the tool call (reason shown to Claude)
- `"ask"` — show permission dialog to user (reason shown to user)
- `"defer"` — pause for external input (non-interactive `-p` mode only)

**Precedence:** `deny > defer > ask > allow`

**Pattern — block specific file paths:**
```bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE" == *".env"* || "$FILE" == *"secrets"* ]]; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"Access to secret files is blocked"}}'
  exit 0
fi
exit 0
```

**Pattern — auto-approve safe git commands:**
```bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if [[ "$CMD" =~ ^git\ (status|log|diff|show|branch|fetch) ]]; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"allow",permissionDecisionReason:"Read-only git command"}}'
  exit 0
fi
exit 0
```

---

## PermissionRequest

**When:** A permission dialog is about to be shown to the user.

**Matcher values:** Same as PreToolUse tool names.

**Input:**
```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf node_modules" },
  "permission_suggestions": [
    {
      "type": "addRules",
      "rules": [{"toolName": "Bash", "ruleContent": "rm -rf node_modules"}],
      "behavior": "allow",
      "destination": "localSettings"
    }
  ]
}
```

**Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "modified" },
      "updatedPermissions": [ ... ]
    }
  }
}
```

`updatedPermissions` entry types: `addRules`, `replaceRules`, `removeRules`, `setMode`, `addDirectories`, `removeDirectories`
`destination` values: `session`, `localSettings`, `projectSettings`, `userSettings`

---

## PermissionDenied

**When:** Auto mode classifier denies a tool call. Only fires in auto mode.

**Input:**
```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /tmp/build" },
  "tool_use_id": "toolu_01...",
  "reason": "Auto mode denied: command targets a path outside the project"
}
```

**Output:** Return `{"hookSpecificOutput":{"hookEventName":"PermissionDenied","retry":true}}` to let Claude retry.

---

## PostToolUse

**When:** Tool completes successfully. Cannot undo — can only give Claude feedback.

**Matcher values:** Same as PreToolUse tool names.

**Input:**
```json
{
  "tool_name": "Write",
  "tool_use_id": "toolu_01...",
  "tool_input": { "file_path": "/path/file.txt", "content": "..." },
  "tool_response": { "filePath": "/path/file.txt", "success": true }
}
```

**Output:**
```json
{
  "decision": "block",
  "reason": "Tests failed after this file was written",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "...",
    "updatedMCPToolOutput": { ... }
  }
}
```

`updatedMCPToolOutput` — replaces MCP tool response (MCP tools only).

**Pattern — run linter after file write:**
```bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
EXT="${FILE##*.}"
if [[ "$EXT" == "py" ]]; then
  if ! python -m ruff check "$FILE" 2>&1; then
    jq -n --arg f "$FILE" '{"decision":"block","reason":"Ruff linting failed on \($f). Fix lint errors before proceeding."}'
    exit 0
  fi
fi
exit 0
```

---

## PostToolUseFailure

**When:** Tool execution throws an error or returns failure.

**Input:**
```json
{
  "tool_name": "Bash",
  "tool_use_id": "toolu_01...",
  "tool_input": { "command": "npm test" },
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

**Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "Hint: check package.json for correct test script name"
  }
}
```

Cannot block (tool already failed). Use to inject diagnostic context for Claude.

---

## SubagentStart

**When:** A subagent is spawned via the Agent tool.

**Matcher values:** `Bash` | `Explore` | `Plan` | custom agent names

**Input:**
```json
{
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

**Output:** `hookSpecificOutput.additionalContext` — injected into subagent's context.

---

## SubagentStop

**When:** A subagent finishes responding.

**Matcher values:** Same as SubagentStart.

**Input:**
```json
{
  "stop_hook_active": false,
  "agent_id": "agent-abc123",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../subagents/agent-abc123.jsonl",
  "last_assistant_message": "Analysis complete. Found 3 issues..."
}
```

Uses the same decision control as [Stop](#stop).

---

## Stop

**When:** Main Claude Code agent finishes responding. Does not fire on user interrupt.

**No matcher support.**

**Input:**
```json
{
  "stop_hook_active": true,
  "last_assistant_message": "I've completed the refactoring..."
}
```

⚠️ **Always check `stop_hook_active`** to avoid infinite loops when blocking.

**Output:**
```json
{
  "decision": "block",
  "reason": "Tests are still failing. Run npm test and fix any errors."
}
```

**Pattern — quality gate (safe):**
```bash
INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')
# Only gate on first Stop, not recursive ones
if [[ "$ACTIVE" == "true" ]]; then
  exit 0
fi
if ! npm test --silent 2>/dev/null; then
  jq -n '{"decision":"block","reason":"Test suite is failing. Fix all tests before finishing."}'
  exit 0
fi
exit 0
```

---

## StopFailure

**When:** Turn ends due to API error (rate limit, auth, billing, etc.).

**Matcher values:** `rate_limit` | `authentication_failed` | `billing_error` | `invalid_request` | `server_error` | `max_output_tokens` | `unknown`

**Input:**
```json
{
  "error": "rate_limit",
  "error_details": "429 Too Many Requests",
  "last_assistant_message": "API Error: Rate limit reached"
}
```

**Cannot block.** Use for alerting and logging only.

---

## TeammateIdle

**When:** An agent team teammate is about to stop working.

**No matcher support.**

**Input:**
```json
{
  "teammate_name": "researcher",
  "team_name": "my-project"
}
```

**Control:**
- `exit 2` + stderr → teammate keeps working with your feedback
- `{"continue": false, "stopReason": "..."}` → stops teammate entirely

---

## TaskCreated

**When:** A task is being created via `TaskCreate`.

**No matcher support.**

**Input:**
```json
{
  "task_id": "task-001",
  "task_subject": "Implement user authentication",
  "task_description": "Add login and signup endpoints",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```

**Control:** exit 2 blocks creation; `{"continue":false}` stops teammate.

---

## TaskCompleted

**When:** A task is being marked complete via `TaskUpdate`.

**No matcher support.** Same input shape as TaskCreated. Same control options.

---

## PreCompact

**When:** Before context compaction.

**Matcher values:** `manual` | `auto`

**Input:**
```json
{
  "trigger": "manual",
  "custom_instructions": ""
}
```

**Can block:** exit 2 or `{"decision":"block"}`.

---

## PostCompact

**When:** After compaction completes.

**Matcher values:** `manual` | `auto`

**Input:**
```json
{
  "trigger": "auto",
  "compact_summary": "Summary of compacted conversation..."
}
```

**Cannot block.** Use for logging or archiving summaries.

---

## InstructionsLoaded

**When:** A `CLAUDE.md` or `.claude/rules/*.md` file is loaded into context.

**Matcher values:** `session_start` | `nested_traversal` | `path_glob_match` | `include` | `compact`

**Input:**
```json
{
  "file_path": "/Users/my-project/CLAUDE.md",
  "memory_type": "Project",
  "load_reason": "session_start",
  "globs": ["src/**"],
  "trigger_file_path": "/Users/my-project/src/index.ts"
}
```

**No decision control.** Observability / audit only.

---

## ConfigChange

**When:** A settings file changes during a session.

**Matcher values:** `user_settings` | `project_settings` | `local_settings` | `policy_settings` | `skills`

**Input:**
```json
{
  "source": "project_settings",
  "file_path": "/Users/my-project/.claude/settings.json"
}
```

**Can block** (except `policy_settings`): `{"decision":"block","reason":"..."}` or exit 2.

---

## CwdChanged

**When:** Working directory changes (e.g., Claude runs `cd`).

**No matcher support.**

**Input:**
```json
{
  "old_cwd": "/Users/my-project",
  "new_cwd": "/Users/my-project/src"
}
```

**Has access to `CLAUDE_ENV_FILE`.** Return `watchPaths` array to update FileChanged watch list.

---

## FileChanged

**When:** A watched file changes on disk.

**Matcher / watch list:** `|`-separated literal filenames: `".envrc|.env"`. The same value both defines which files to watch AND filters hooks when they fire.

**Input:**
```json
{
  "file_path": "/Users/my-project/.envrc",
  "event": "change"
}
```

`event` values: `change` | `add` | `unlink`

**Has access to `CLAUDE_ENV_FILE`.** Return `watchPaths` to update dynamic watch list.

---

## WorktreeCreate

**When:** Creating a worktree via `--worktree` or `isolation: "worktree"`. Replaces default git behavior.

**Input:**
```json
{
  "name": "feature-auth"
}
```

**Output:** Hook MUST print the absolute path to the new worktree directory on stdout.
HTTP hooks: `hookSpecificOutput.worktreePath`.

---

## WorktreeRemove

**When:** Removing a worktree at session exit or when a subagent finishes.

**Input:**
```json
{
  "worktree_path": "/Users/.../my-project/.claude/worktrees/feature-auth"
}
```

**No decision control.** Use for cleanup.

---

## Notification

**When:** Claude Code sends a notification.

**Matcher values:** `permission_prompt` | `idle_prompt` | `auth_success` | `elicitation_dialog`

**Input:**
```json
{
  "message": "Claude needs your permission to use Bash",
  "title": "Permission needed",
  "notification_type": "permission_prompt"
}
```

**Cannot block.** Return `additionalContext` in `hookSpecificOutput` to inject context.

---

## Elicitation

**When:** An MCP server requests user input during a tool call.

**Matcher values:** MCP server names.

**Input (form mode):**
```json
{
  "mcp_server_name": "my-mcp-server",
  "message": "Please provide your credentials",
  "mode": "form",
  "requested_schema": {
    "type": "object",
    "properties": {
      "username": { "type": "string", "title": "Username" }
    }
  }
}
```

**Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept",
    "content": { "username": "alice" }
  }
}
```

`action` values: `accept` | `decline` | `cancel`. Exit 2 denies.

---

## ElicitationResult

**When:** After user responds to MCP elicitation, before response is sent to server.

**Matcher values:** MCP server names.

**Can block** (exit 2 → response becomes decline).

**Output:** Same schema as Elicitation output — can override user's response.
