# Common hook patterns

Copy-paste hook recipes for the most frequent use cases. Drop these into
`.claude/settings.json` (or `~/.claude/settings.json`) and adapt the matcher,
command, and script paths to your project.

## Auto-format after writes

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "npx prettier --write \"$CLAUDE_TOOL_INPUT_FILE_PATH\"",
        "async": true
      }]
    }]
  }
}
```

## Block dangerous shell commands

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "if": "Bash(rm *)",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
      }]
    }]
  }
}
```

## Desktop notification on completion (macOS)

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "osascript -e 'display notification \"Claude finished\" with title \"Claude Code\"'",
        "async": true
      }]
    }]
  }
}
```

## Run tests before Stop (quality gate)

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-gate.sh"
      }]
    }]
  }
}
```

## Reload direnv on directory change

```json
{
  "hooks": {
    "FileChanged": [{
      "matcher": ".envrc",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'direnv export bash >> \"$CLAUDE_ENV_FILE\"'"
      }]
    }],
    "CwdChanged": [{
      "hooks": [{
        "type": "command",
        "command": "bash -c 'direnv export bash >> \"$CLAUDE_ENV_FILE\" 2>/dev/null || true'"
      }]
    }]
  }
}
```

## Log all tool calls (audit trail)

```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "bash -c 'cat >> ~/.claude/audit.jsonl'",
        "async": true
      }]
    }]
  }
}
```

## Inject context at session start

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/inject-context.sh"
      }]
    }]
  }
}
```
