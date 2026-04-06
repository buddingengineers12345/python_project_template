# Bash Security

# applies-to: **/*.sh

> This file extends [common/security.md](../common/security.md) with Bash-specific content.

## Never use `eval`

`eval` executes arbitrary strings as code. Any user-controlled input passed to `eval`
is a code injection vulnerability:

```bash
# Wrong — if $user_input = "rm -rf /", this destroys the filesystem
eval "process_$user_input"

# Correct — use a case statement or associative array
case "$action" in
    start) start_service ;;
    stop)  stop_service ;;
    *)     echo "Unknown action: $action" >&2; exit 1 ;;
esac
```

## Never use `shell=True` equivalent

Constructing commands via string interpolation and passing to a shell interpreter
enables injection:

```bash
# Wrong — $filename could contain shell metacharacters
system("process $filename")

# Correct — pass as separate argument
process_file "$filename"
```

When calling external programs, pass arguments as separate words, never concatenated
into a single string.

## Validate and sanitise all inputs

Scripts that accept arguments or read from environment variables must validate them
before use:

```bash
file_path="${1:?Usage: script.sh <file-path>}"   # fail with message if empty

# Reject paths containing traversal sequences
if [[ "$file_path" == *..* ]]; then
    echo "Error: path traversal not allowed" >&2
    exit 1
fi
```

## Secrets in environment variables

- Do not echo or log environment variables that may contain secrets.
- Do not write secrets to temporary files unless the file is created with `mktemp`
  and cleaned up in an `EXIT` trap.
- Check that required environment variables exist before using them:

```bash
: "${API_KEY:?API_KEY environment variable is required}"
```

## Temporary file handling

Use `mktemp` for temporary files and clean up with a trap:

```bash
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Use $TMPFILE safely
some_command > "$TMPFILE"
process_output "$TMPFILE"
```

Never use predictable filenames like `/tmp/output.txt` — they are vulnerable to
symlink attacks.

## Subprocess calls in hook scripts

Hook scripts in `.claude/hooks/` execute in the context of the developer's machine.
They should:
- Only call trusted binaries (`uv`, `git`, `python3`, `ruff`, `basedpyright`).
- Never download or execute code from the network.
- Avoid `curl | bash` patterns.
- Not modify files outside the project directory.

The `pre-bash-block-no-verify.sh` hook blocks `git commit --no-verify` to ensure
pre-commit security gates cannot be bypassed.
