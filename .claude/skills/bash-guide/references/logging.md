# Logging library reference

## Philosophy

All scripts implement the **dual-context logging pattern**:

| Context | Format | Audience | Destination |
|---|---|---|---|
| `human` | Colorized, timestamped, plain English | Developers/operators | STDERR |
| `llm` | Structured `KEY=VALUE`, no ANSI | LLM agents, CI parsers | STDERR |

**Data output always goes to STDOUT. Log output always goes to STDERR.**

---

## Full Logging Library (embed or source)

```bash
#!/bin/bash
# lib/logging.sh — portable structured logging for human and LLM contexts
# Source this file; do not execute directly.

# ─── Config (read from environment, with defaults) ────────────────────────────
readonly _LOG_EXECUTION_CONTEXT="${EXECUTION_CONTEXT:-human}"
readonly _LOG_HUMAN_LEVEL="${HUMAN_LOG_LEVEL:-info}"
readonly _LOG_LLM_LEVEL="${LLM_LOG_LEVEL:-info}"

# Prevent double-sourcing
[[ -n "${_LOGGING_LOADED:-}" ]] && return 0
readonly _LOGGING_LOADED=1

# ─── Level → numeric mapping ──────────────────────────────────────────────────
_log_level_value() {
  case "${1,,}" in   # lowercase comparison
    debug) printf '%d' 0 ;;
    info)  printf '%d' 1 ;;
    warn)  printf '%d' 2 ;;
    error) printf '%d' 3 ;;
    *)     printf '%d' 1 ;;
  esac
}

# ─── ANSI colors (human mode only) ───────────────────────────────────────────
_LOG_COLOR_DEBUG='\033[0;36m'   # cyan
_LOG_COLOR_INFO='\033[0;32m'    # green
_LOG_COLOR_WARN='\033[0;33m'    # yellow
_LOG_COLOR_ERROR='\033[0;31m'   # red
_LOG_COLOR_RESET='\033[0m'

# ─── Core log function ────────────────────────────────────────────────────────
#######################################
# Emit a log message at the given level.
# Globals:
#   _LOG_EXECUTION_CONTEXT
#   _LOG_HUMAN_LEVEL
#   _LOG_LLM_LEVEL
#   SCRIPT_NAME (optional, falls back to basename $0)
# Arguments:
#   $1 - Log level: debug|info|warn|error
#   $@ - Message
# Outputs:
#   Writes to STDERR only. No STDOUT.
#######################################
log() {
  local level="${1,,}"; shift
  local message="$*"
  local script_name="${SCRIPT_NAME:-$(basename "$0")}"
  local timestamp
  timestamp="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

  # Determine active threshold
  local active_threshold
  if [[ "${_LOG_EXECUTION_CONTEXT}" == "llm" ]]; then
    active_threshold="${_LOG_LLM_LEVEL}"
  else
    active_threshold="${_LOG_HUMAN_LEVEL}"
  fi

  # Filter below threshold
  local msg_val active_val
  msg_val="$(_log_level_value "${level}")"
  active_val="$(_log_level_value "${active_threshold}")"
  (( msg_val < active_val )) && return 0

  if [[ "${_LOG_EXECUTION_CONTEXT}" == "llm" ]]; then
    # ── LLM mode: structured, parseable, no color ──────────────────────────
    # Format: [ISO8601] LEVEL=X SCRIPT=Y MSG="Z"
    # LLM agents can extract fields with: grep -oP 'LEVEL=\K\S+'
    printf '[%s] LEVEL=%s SCRIPT=%s MSG="%s"\n' \
      "${timestamp}" \
      "${level^^}" \
      "${script_name}" \
      "${message}" \
      >&2
  else
    # ── Human mode: colorized, labeled ─────────────────────────────────────
    local color_var="_LOG_COLOR_${level^^}"
    local color="${!color_var:-}"
    printf "${color}[%s] [%-5s] %s${_LOG_COLOR_RESET}\n" \
      "${timestamp}" \
      "${level^^}" \
      "${message}" \
      >&2
  fi
}

# ─── Convenience wrappers ─────────────────────────────────────────────────────
log_debug() { log "debug" "$@"; }
log_info()  { log "info"  "$@"; }
log_warn()  { log "warn"  "$@"; }
log_error() { log "error" "$@"; }

# ─── Structured exit (always use for final exit) ──────────────────────────────
#######################################
# Log an error and exit with a code.
# Arguments:
#   $1 - Exit code (integer)
#   $@ - Error message
#######################################
die() {
  local code="$1"; shift
  local message="$*"
  local script_name="${SCRIPT_NAME:-$(basename "$0")}"

  log_error "${message}"

  # In LLM mode, emit a final structured exit line so agents can detect it
  if [[ "${_LOG_EXECUTION_CONTEXT}" == "llm" ]]; then
    printf 'EXIT_CODE=%d SCRIPT=%s REASON="%s"\n' \
      "${code}" "${script_name}" "${message}" >&2
  fi
  exit "${code}"
}
```

---

## Log Level Decision Guide

| Use level | When |
|---|---|
| `debug` | Step-by-step internals, variable values, loop iterations. Not shown in default runs. |
| `info` | Normal progress milestones: "Started", "Processing X", "Done". |
| `warn` | Something unexpected but recoverable: missing optional file, using default value. |
| `error` | Fatal condition. Always followed by `die` or `exit`. |

---

## LLM Log Parsing Patterns

An LLM agent (or script) reading output in `llm` mode can extract fields:

```bash
# Extract all warnings from a script run
script_output=$(EXECUTION_CONTEXT=llm ./deploy.sh 2>&1 1>/dev/null)
echo "${script_output}" | grep 'LEVEL=WARN'

# Extract exit code from final line
exit_line=$(echo "${script_output}" | grep '^EXIT_CODE=')
exit_code=$(echo "${exit_line}" | grep -oP 'EXIT_CODE=\K[0-9]+')

# Parse as key=value pairs (awk)
echo "${script_output}" | awk -F'[ =]' '/LEVEL=ERROR/ { print $0 }'
```

---

## Reducing Log Noise in LLM Mode

When `EXECUTION_CONTEXT=llm` and `LLM_LOG_LEVEL=info` (the defaults), scripts should:

1. **Suppress all debug output** (default threshold is `info`)
2. **Emit only meaningful milestones** at `info`
3. **Never emit progress bars, spinners, or interactive prompts**
4. **Suppress command output** with `>/dev/null` for noisy utilities:
   ```bash
   apt-get install -y curl >/dev/null 2>&1 \
     || die 3 "Failed to install curl"
   ```
5. **One log event per logical operation**, not per loop iteration (unless debug)

---

## Minimal Inline Version (for short scripts)

For scripts under ~80 lines where sourcing a library is overkill:

```bash
# Compact inline logging
_LL="${LLM_LOG_LEVEL:-info}"; _HL="${HUMAN_LOG_LEVEL:-info}"
log() {
  local lvl="$1"; shift
  local ts; ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  local thr; [[ "${EXECUTION_CONTEXT:-human}" == "llm" ]] && thr="${_LL}" || thr="${_HL}"
  local lv; case "${lvl}" in debug)lv=0;;info)lv=1;;warn)lv=2;;*)lv=3;;esac
  local tv; case "${thr}" in debug)tv=0;;info)tv=1;;warn)tv=2;;*)tv=3;;esac
  (( lv < tv )) && return 0
  if [[ "${EXECUTION_CONTEXT:-human}" == "llm" ]]; then
    printf '[%s] LEVEL=%s MSG="%s"\n' "${ts}" "${lvl^^}" "$*" >&2
  else
    printf '[%s] [%-5s] %s\n' "${ts}" "${lvl^^}" "$*" >&2
  fi
}
log_debug() { log debug "$@"; }
log_info()  { log info  "$@"; }
log_warn()  { log warn  "$@"; }
log_error() { log error "$@"; }
die()       { log_error "$@"; exit 1; }
```
