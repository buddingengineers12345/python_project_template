---
name: maintain-hooks
description: >-
  Write, manage, and debug .claude/hooks — Claude Code's lifecycle automation system.
  Use this skill whenever the user mentions hooks, .claude/settings.json hook config,
  PreToolUse, PostToolUse, SessionStart, Stop, or any Claude Code hook event. Also
  trigger for: "automate Claude Code", "enforce rules in Claude Code", "run a script
  when Claude edits a file", "block dangerous commands", "notify me when Claude finishes",
  "hook into Claude Code", or any request to make Claude Code run custom scripts
  automatically. If the user is working inside a .claude/ directory or discussing
  Claude Code automation at all — use this skill.
---

# Claude Hooks Skill

Hooks let you attach shell commands, HTTP endpoints, LLM prompts, or subagents to
specific moments in Claude Code's lifecycle — turning guidelines into guaranteed,
deterministic enforcement.

## Quick mental model

```
Claude Code event fires
  → matcher filter (tool name / session type / etc.)
    → if condition (optional fine-grained filter)
      → hook handler runs (command / http / prompt / agent)
        → exit code + JSON output control what happens next
```

---

## 1. Where to put hooks

| File | Scope | Commit? |
|------|-------|---------|
| `~/.claude/settings.json` | All your projects | No — machine-local |
| `.claude/settings.json` | This project | Yes — share with team |
| `.claude/settings.local.json` | This project | No — gitignored |
| Plugin `hooks/hooks.json` | When plugin enabled | Yes — bundled |

**Best practice:** keep project-wide enforcement (linting, security gates) in
`.claude/settings.json`. Keep personal preferences (notifications, logging) in
`~/.claude/settings.json`. Never commit secrets — use `.claude/settings.local.json`
for hooks that reference API keys.

**Always reference scripts via `$CLAUDE_PROJECT_DIR`** to avoid path breakage when
Claude Code changes working directory:

```json
"command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/my-script.sh"
```

Store hook scripts in `.claude/hooks/` and make them executable (`chmod +x`).

---

## 2. Configuration schema

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-bash.sh",
            "timeout": 10,
            "statusMessage": "Validating command…"
          }
        ]
      }
    ]
  }
}
```

Three nesting levels:
1. **Hook event** — lifecycle point (`PreToolUse`, `Stop`, etc.)
2. **Matcher group** — regex/string filter for when it fires
3. **Hook handler** — the actual command/endpoint/prompt to run

### Matcher rules

| Matcher value | Behavior |
|---|---|
| `"*"`, `""`, or omitted | Match everything |
| Letters/digits/`_`/`|` only | Exact string or `\|`-separated list: `"Edit\|Write"` |
| Any other character | JavaScript regex: `"^Notebook"`, `"mcp__memory__.*"` |

MCP tools: `mcp__<server>__<tool>` — use `mcp__memory__.*` to match all tools
from a server (the `.*` suffix is required).

### Handler types

| `type` | How it works | Best for |
|--------|-------------|----------|
| `"command"` | Shell script, stdin=JSON, stdout+exit code=result | Most use cases |
| `"http"` | POST JSON to a URL, response body=result | Remote services, webhooks |
| `"prompt"` | Asks a Claude model, returns yes/no JSON | Semantic checks |
| `"agent"` | Spawns subagent with Read/Grep/Glob tools | Complex file analysis |

### Common handler fields

| Field | Default | Purpose |
|-------|---------|---------|
| `type` | — | Required: `command`, `http`, `prompt`, `agent` |
| `if` | — | Permission-rule syntax fine filter: `"Bash(git *)"`, `"Edit(*.ts)"` |
| `timeout` | 600/30/60s | Seconds before cancelling |
| `statusMessage` | — | Spinner text while hook runs |
| `async` | false | Run in background, don't block Claude |
| `asyncRewake` | false | Background, but wake Claude on exit 2 |

---

## 3. Exit codes and JSON output

### Exit codes (command hooks)

| Code | Meaning |
|------|---------|
| `0` | Success — Claude Code parses stdout for JSON |
| `2` | **Blocking error** — stderr fed back to Claude/user, blocks action |
| Other | Non-blocking error — shows first line of stderr, execution continues |

> **Critical:** Use `exit 2` to enforce policy. `exit 1` is non-blocking and
> will not stop the action, even though it's the conventional Unix failure code.

### JSON output (on exit 0)

Print a JSON object to stdout. Fields:

```json
{
  "continue": false,          // Stop Claude entirely (all events)
  "stopReason": "message",   // Shown to user when continue=false
  "suppressOutput": true,    // Hide stdout from debug log
  "systemMessage": "warn",   // Warning shown to user
  "decision": "block",        // Block action (PostToolUse, Stop, etc.)
  "reason": "why",            // Explanation when decision=block
  "hookSpecificOutput": { ... }  // Event-specific fields (see below)
}
```

**You must choose one approach per hook:** exit codes OR exit-0-plus-JSON.
JSON is only processed on exit 0.

---

## 4. Event decision control quick-reference

| Event | Can block? | How to block |
|-------|-----------|--------------|
| `PreToolUse` | ✅ | `hookSpecificOutput.permissionDecision: "deny"` |
| `PermissionRequest` | ✅ | `hookSpecificOutput.decision.behavior: "deny"` |
| `UserPromptSubmit` | ✅ | `decision: "block"` OR exit 2 |
| `Stop` / `SubagentStop` | ✅ | `decision: "block"` (with `reason`) |
| `TeammateIdle` | ✅ | exit 2 (teammate keeps working) |
| `TaskCreated` / `TaskCompleted` | ✅ | exit 2 |
| `ConfigChange` | ✅ | `decision: "block"` OR exit 2 |
| `PreCompact` | ✅ | exit 2 OR `decision: "block"` |
| `Elicitation` | ✅ | exit 2 (denies request) |
| `PostToolUse` | ⚠️ No | `decision: "block"` sends feedback to Claude |
| `SessionStart/End` | ❌ | Side effects only |
| `Notification` | ❌ | Side effects only |

### PreToolUse — richest control

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",      // allow / deny / ask / defer
    "permissionDecisionReason": "...", // shown to Claude on deny
    "updatedInput": { ... },           // modify tool args before execution
    "additionalContext": "..."         // inject context for Claude
  }
}
```

Precedence when multiple hooks conflict: `deny > defer > ask > allow`

---

## 5. All hook events

See `references/events.md` for the complete event reference with input schemas.
The most important events are:

**Security / enforcement:** `PreToolUse`, `UserPromptSubmit`, `PermissionRequest`
**Quality gates:** `PostToolUse`, `Stop`, `TeammateIdle`, `TaskCompleted`
**Automation / logging:** `SessionStart`, `SessionEnd`, `Notification`, `PostToolUse`
**Environment management:** `SessionStart`, `CwdChanged`, `FileChanged`
**Advanced:** `Elicitation`, `WorktreeCreate`, `PreCompact`, `SubagentStop`

---

## 6. Writing hook scripts

### Canonical shell script template

See `assets/templates/hook-template.sh` for a complete, copy-paste ready template.

Core pattern every command hook follows:

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Read the full JSON payload from stdin
INPUT=$(cat)

# 2. Extract what you need
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
CMD=$(echo "$INPUT"  | jq -r '.tool_input.command // empty')

# 3. Business logic
if [[ "$CMD" == *"rm -rf /"* ]]; then
  # exit 2 = blocking error; stderr goes to Claude
  echo "Blocked: cannot delete root filesystem" >&2
  exit 2
fi

# 4a. Allow with no output
exit 0

# 4b. OR: allow with JSON decision output
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "allow",
    additionalContext: "Command looks safe"
  }
}'
```

### Python script template

See `assets/templates/hook-template.py` for a Python template.

### Standard script header

Every hook script in this project uses the same header block so hooks are
self-describing and easy to audit. Follow this format:

```bash
#!/usr/bin/env bash
# Claude <EventName> hook — <Matcher>
# <One-line summary of what the hook does>
#
# <Optional multi-line description: behavior, scope, rationale,
# any conditions that trigger a block or warning.>
#
# Reference : <URL to source recipe>  OR  "Custom — project-specific hook"
# Exits     : <exit semantics, e.g. "0 = allow | 2 = block"
#                                or "0 always (PostToolUse cannot block)">

set -uo pipefail
```

Use `set -uo pipefail` (not `-euo`) for hooks that use `grep -q`, `case`, or
other pipelines that are expected to "fail" in the success path. `-e` would
otherwise abort the script on a no-match and skip the intended logic.

### Standard JSON extraction

Parse stdin once into a shell variable, then extract fields with a python
heredoc — never with `grep`/`sed` on JSON. Pass the JSON to python through an
**environment variable**, not via `<<<"$INPUT"`. Guard the extraction with
`|| { echo "$INPUT"; exit 0; }` so a malformed payload never accidentally
blocks the tool:

```bash
INPUT=$(cat)

FIELD=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("<field>", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }
```

> **Why not `python3 - <<'PYEOF' ... PYEOF <<<"$INPUT"`?** Both the heredoc
> (which carries the python script) and the herestring (`<<<`) target stdin.
> Bash applies the second redirection last, so `sys.stdin.read()` returns an
> empty string and `json.loads("")` raises `JSONDecodeError`. The `||` fallback
> then silently swallows the error and the hook does nothing. Use the env-var
> pattern above instead — it is unambiguous and works on every shell.

### Standard output conventions

Use box-drawing characters for all user-visible output so hook messages are
visually consistent:

```
┌─ <Hook name>: <context>
│
│  <content lines>
│
└─ ✓ OK   or   ✗ <problem>   or   (bare close for block messages)
```

- **PreToolUse blocks** print the box to **stderr** and `exit 2`.
- **PreToolUse pass-through** ends with `echo "$INPUT"` on stdout.
- **PostToolUse / SessionStart / Stop** print to **stdout** and `exit 0`.

### Key rules for scripts

1. **Parse stdin fully before writing to stdout** — Claude Code reads the entire
   stdout after the script exits, not line-by-line.
2. **Redirect non-JSON output to stderr** — any non-JSON text on stdout when you
   intend to return JSON will break parsing.
3. **Keep SessionStart and SessionEnd hooks fast** — they run on every session;
   SessionEnd has a 1.5s default timeout.
4. **Check `stop_hook_active`** in Stop hooks to prevent infinite loops.
5. **Use `jq` for JSON parsing** in shell scripts — never use `grep/awk` on JSON.
6. **Test locally with echo pipe**: `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh`

---

## 7. Common patterns

Copy-paste recipes for the most frequent use cases — auto-format after writes,
block dangerous shell commands, desktop notifications on completion, test
quality gates, direnv reload, audit logging, and session-start context
injection — live in [references/patterns.md](references/patterns.md). Adapt
the matcher and command to your project.

---

## 8. Debugging hooks

1. **Run `/hooks`** in Claude Code — read-only browser for all configured hooks,
   shows source file, type, matcher, and full command/URL.

2. **Test the script directly:**
   ```bash
   echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls"}}' \
     | bash .claude/hooks/my-hook.sh
   echo "Exit: $?"
   ```

3. **Start Claude Code with `--debug`** — all hook stdout/stderr appears in the
   debug log even when not shown in the transcript.

4. **Common problems:**
   - Hook not firing → wrong event name casing (it's `PreToolUse` not `preToolUse`)
   - JSON not parsed → something printed to stdout before your JSON object
   - Path not found → use `$CLAUDE_PROJECT_DIR` prefix; check the script is executable
   - exit 1 doesn't block → use `exit 2` for blocking errors
   - Infinite Stop loop → check `stop_hook_active` field before blocking

5. **Temporarily disable all hooks:**
   ```json
   { "disableAllHooks": true }
   ```

---

## 9. Security considerations

Hooks execute arbitrary shell commands. Before writing or accepting hook config:

- **Never put secrets in the command string** — use env vars referenced via
  `allowedEnvVars` in HTTP hooks, or load from a secrets file in scripts.
- **Validate all JSON inputs** — don't blindly eval anything from `tool_input`.
- **Avoid writing hooks that read from user-controlled input into shell** without
  sanitization — command injection is real.
- **Review third-party hook configurations** before enabling them.
- **Commit `.claude/settings.json` to source control** so team changes are visible.
- **Use `.claude/settings.local.json` for personal overrides** — it's gitignored.

---

## Quick reference: where to go deeper

| Topic                                           | Reference file                                                                     |
|-------------------------------------------------|------------------------------------------------------------------------------------|
| Full event input schemas for all 26 events      | [references/events.md](references/events.md)                                       |
| Copy-paste recipes for common hook use cases    | [references/patterns.md](references/patterns.md)                                   |
| Production-ready bash hook template             | [assets/templates/hook-template.sh](assets/templates/hook-template.sh)             |
| Python hook template with full JSON handling    | [assets/templates/hook-template.py](assets/templates/hook-template.py)             |
| Annotated settings.json starter                 | [assets/templates/settings-example.json](assets/templates/settings-example.json)   |
