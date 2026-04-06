# Bash Security

# applies-to: **/*.sh

> This file extends [common/security.md](../common/security.md) with Bash-specific content.

## Never use `eval`

`eval` executes arbitrary strings as code. Any user-controlled input is a code
injection vector. Use `case` statements instead:

```bash
case "$action" in
    start) start_service ;;
    stop)  stop_service ;;
    *)     echo "Unknown action: $action" >&2; exit 1 ;;
esac
```

## Validate all inputs

```bash
file_path="${1:?Usage: script.sh <file-path>}"

if [[ "$file_path" == *..* ]]; then
    echo "Error: path traversal not allowed" >&2
    exit 1
fi
```

## Secrets in environment

- Do not echo or log environment variables that may contain secrets.
- Validate required variables exist before use:
  ```bash
  : "${API_KEY:?API_KEY environment variable is required}"
  ```

## Temporary files

```bash
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT
```

Never use predictable names like `/tmp/output.txt`.

## Subprocess calls

Pass arguments as separate words; never concatenate into a shell string:

```bash
# Correct
git status --porcelain

# Wrong — injection risk
sh -c "git $user_command"
```

Avoid `curl | bash` patterns.
