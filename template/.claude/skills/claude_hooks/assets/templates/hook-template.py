#!/usr/bin/env python3
"""
Claude Code Hook Script Template (Python)
==========================================
Usage: Copy to .claude/hooks/<your-hook-name>.py
Make executable: chmod +x .claude/hooks/<your-hook-name>.py

Reference in settings.json:
  "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<your-hook-name>.py"

For UV single-file scripts with inline dependencies:
  "command": "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<your-hook-name>.py"

If using UV, add a dependencies block at the top:
  # /// script
  # dependencies = ["requests>=2.28"]
  # ///
"""

import json
import sys
import os
import subprocess
from pathlib import Path


# =============================================================================
# OUTPUT HELPERS
# =============================================================================

def allow(additional_context: str = None) -> None:
    """Allow the action, optionally injecting context."""
    if additional_context:
        _exit_json({
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": additional_context,
            }
        })
    sys.exit(0)


def deny(reason: str) -> None:
    """Block the tool call (PreToolUse). Reason shown to Claude."""
    _exit_json({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def ask_user(reason: str) -> None:
    """Ask user to confirm (PreToolUse). Reason shown to user."""
    _exit_json({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    })


def block(reason: str) -> None:
    """Block action with feedback (PostToolUse, Stop, etc.)."""
    _exit_json({"decision": "block", "reason": reason})


def blocking_error(message: str) -> None:
    """Exit with code 2: blocking error, message sent to Claude."""
    print(message, file=sys.stderr)
    sys.exit(2)


def _exit_json(data: dict) -> None:
    """Print JSON to stdout and exit 0."""
    print(json.dumps(data))
    sys.exit(0)


def log(message: str) -> None:
    """Write to a log file (NOT stderr, which goes to Claude)."""
    log_path = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.home())) / ".claude" / "hooks.log"
    try:
        with open(log_path, "a") as f:
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass  # Never let logging break the hook


# =============================================================================
# READ INPUT
# =============================================================================

try:
    raw = sys.stdin.read()
    payload = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"Failed to parse hook input JSON: {e}", file=sys.stderr)
    sys.exit(1)

# Common fields
event_name   = payload.get("hook_event_name", "")
session_id   = payload.get("session_id", "")
cwd          = payload.get("cwd", "")
perm_mode    = payload.get("permission_mode", "")

# Tool fields (present in PreToolUse, PostToolUse, etc.)
tool_name    = payload.get("tool_name", "")
tool_input   = payload.get("tool_input", {})
tool_response= payload.get("tool_response", {})

# Common sub-fields
command      = tool_input.get("command", "")
file_path    = tool_input.get("file_path", "")


# =============================================================================
# PRETOOLUSE — validate before tool runs
# =============================================================================

if event_name == "PreToolUse":

    if tool_name == "Bash":
        # Block dangerous deletion patterns
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf ~",
            "rm -rf $HOME",
            "> /dev/sda",
            "mkfs.",
        ]
        for pattern in dangerous_patterns:
            if pattern in command:
                blocking_error(f"BLOCKED: Dangerous command pattern detected: {pattern!r}")

        # Block cloud metadata endpoint access
        if "169.254.169.254" in command or "metadata.google.internal" in command:
            deny("Access to cloud metadata endpoints is blocked")

        # Log the command
        log(f"Bash command: {command[:120]}")

    if tool_name in ("Write", "Edit", "MultiEdit"):
        # Protect sensitive files
        sensitive_names = {".env", ".env.local", ".env.production", "credentials.json"}
        sensitive_paths = {"secrets/", "private/", ".ssh/"}

        basename = Path(file_path).name
        if basename in sensitive_names:
            ask_user(f"Writing to sensitive file: {basename}")

        if any(p in file_path for p in sensitive_paths):
            ask_user(f"Writing inside a sensitive directory: {file_path}")

    # Default: allow
    allow()


# =============================================================================
# POSTTOOLUSE — react after tool ran
# =============================================================================

elif event_name == "PostToolUse":

    if tool_name in ("Write", "Edit") and file_path.endswith(".py"):
        # Run ruff linter if available
        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--quiet"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                issues = result.stdout[:500] or result.stderr[:500]
                block(f"Ruff lint errors in {file_path}:\n{issues}\nFix before proceeding.")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # ruff not installed or timed out — don't block

    allow()


# =============================================================================
# STOP — quality gate before Claude finishes
# =============================================================================

elif event_name == "Stop":
    stop_active = payload.get("stop_hook_active", False)

    # CRITICAL: prevent infinite stop loops
    if stop_active:
        sys.exit(0)

    # Example: check for TODO/FIXME comments left behind
    # Uncomment to enable:
    # result = subprocess.run(
    #     ["grep", "-r", "--include=*.py", "-l", "TODO\|FIXME", cwd],
    #     capture_output=True, text=True
    # )
    # if result.stdout.strip():
    #     files = result.stdout.strip()
    #     block(f"TODO/FIXME comments remain in:\n{files}\nResolve before finishing.")

    sys.exit(0)


# =============================================================================
# USERPROMPTSUBMIT — augment or validate prompt
# =============================================================================

elif event_name == "UserPromptSubmit":
    prompt = payload.get("prompt", "")

    # Example: add git branch context
    try:
        branch = subprocess.check_output(
            ["git", "-C", cwd, "branch", "--show-current"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        context = f"Current git branch: {branch}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        context = None

    if context:
        _exit_json({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        })

    sys.exit(0)


# =============================================================================
# SESSIONSTART — inject environment and context
# =============================================================================

elif event_name == "SessionStart":
    env_file = os.environ.get("CLAUDE_ENV_FILE")

    if env_file:
        # Persist env vars for all subsequent Bash commands
        with open(env_file, "a") as f:
            f.write('export PATH="./node_modules/.bin:$PATH"\n')

    # Inject project summary as context (plain stdout)
    readme = Path(cwd) / "README.md"
    if readme.exists():
        content = readme.read_text()[:1000]
        print(f"Project README (truncated):\n{content}")

    sys.exit(0)


# =============================================================================
# SESSIONEND — cleanup
# =============================================================================

elif event_name == "SessionEnd":
    reason = payload.get("reason", "other")
    log(f"Session ended: reason={reason} session_id={session_id}")
    sys.exit(0)


# =============================================================================
# FALLBACK — unknown or unhandled event
# =============================================================================

else:
    # Silently allow anything we don't handle
    sys.exit(0)
