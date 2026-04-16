# Frontmatter fields

Complete reference for all YAML frontmatter fields in `.claude/commands/*.md` and `.claude/skills/*/SKILL.md` files.

---

## `name`

**Type**: string
**Default**: directory name (for skills) or filename without `.md` (for commands)
**Constraints**: lowercase letters, numbers, hyphens only; max 64 characters

Overrides the display name and the `/slash-command` trigger. Usually you want the filename to be the name, so this field is rarely needed.

```yaml
name: deploy-prod
```

---

## `description`

**Type**: string
**Default**: first paragraph of markdown body
**Recommended**: always include

The primary text Claude reads to decide whether to auto-invoke this skill. Also shown in `/help` listings and autocomplete.

- Front-load the key use case — descriptions are truncated at ~1,536 chars in the skill listing
- Be specific about *when* to use it, not just *what* it does
- For `disable-model-invocation: true` commands, you can be terser since Claude never auto-triggers it

```yaml
description: Generate a conventional commit message from staged changes. Use when committing code or when the user asks to "commit", "save changes", or "create a commit".
```

---

## `when_to_use`

**Type**: string (supports multi-line with `|`)
**Default**: none

Additional context for auto-invocation. Extends `description` without cluttering it. Useful for listing synonyms, edge cases, and trigger phrases.

```yaml
when_to_use: |
  Also trigger when user says: "ship it", "push this", "make a commit",
  "save my work", "check in these changes".
  Do NOT trigger for git operations that aren't commits (pull, push, branch).
```

---

## `argument-hint`

**Type**: string
**Default**: none

Hint shown in the autocomplete dropdown describing expected arguments. Purely cosmetic — does not validate or parse arguments.

```yaml
argument-hint: <filepath> [--strict]
```

Common conventions:
- `<required>` — required positional argument
- `[optional]` — optional argument
- `...` — variadic (multiple values)
- `<key>=<value>` — key-value pair

---

## `allowed-tools`

**Type**: space-separated string
**Default**: none (uses session permissions)

Pre-approves specific tools so Claude can use them without per-call confirmation when this command is active. This does NOT grant tools not already available in the session — it only pre-approves prompts for tools that are available.

### Tool identifiers

```yaml
# File tools
allowed-tools: Read Write Edit

# Search tools
allowed-tools: Grep Glob

# Combined
allowed-tools: Read Grep Glob

# Bash — ALWAYS scope with a pattern
allowed-tools: Bash(git *)          # All git subcommands
allowed-tools: Bash(npm run:*)      # Only npm run scripts
allowed-tools: Bash(pytest *)       # Only pytest
allowed-tools: Bash(git log:*) Bash(git diff:*)  # Multiple bash patterns
```

### Bash scoping patterns

`Bash(command *)` — all arguments to `command`
`Bash(command subcommand:*)` — only `command subcommand` and its args
`Bash(command subcommand flag)` — exact command only

**Best practice**: never use bare `Bash` without a scope pattern for production commands. It grants unrestricted shell access.

---

## `disable-model-invocation`

**Type**: boolean
**Default**: `false`

When `true`, prevents Claude from auto-triggering this command based on context. The user must invoke it explicitly with `/command-name`.

Use for any command with side effects:

```yaml
disable-model-invocation: true
```

Good candidates:
- Deployment commands (`/deploy`, `/release`)
- Database mutations (`/db:migrate`, `/db:seed`)
- Git push/publish commands
- Any command that sends external requests
- Destructive operations (`/db:reset`, `/clean`)

---

## `model`

**Type**: string
**Default**: session default (usually Sonnet)

Pins this command to a specific Claude model. Useful when a command requires Opus for complex reasoning, or Haiku for fast/cheap operations.

```yaml
model: claude-opus-4-6      # Best reasoning, slower, pricier
model: claude-sonnet-4-6    # Balanced (session default)
model: claude-haiku-4-5-20251001  # Fast, cheap, good for simple tasks
```

---

## `context`

**Type**: string
**Default**: inline (runs in current conversation)

Controls where the skill executes.

| Value | Behavior |
|-------|----------|
| (none / inline) | Runs in the current conversation context |
| `fork` | Runs in a new subagent with a copy of current context; results summarized back |
| `agent` | Runs in a fresh subagent with no inherited context |

```yaml
context: fork   # Good for long-running analysis you want isolated
context: agent  # Good for clean-slate tasks (security scan, full review)
```

`fork` is the right choice for most complex commands — the subagent can do deep work without polluting your conversation context.

---

## Complete example: production-ready command

```yaml
---
name: pr-review
description: >
  Comprehensive pull request review covering correctness, security, and
  performance. Use when reviewing a PR, before merging, or when asked to
  "review these changes" or "check this PR".
argument-hint: [branch-or-diff-ref]
allowed-tools: Read Grep Glob Bash(git log:*) Bash(git diff:*)
disable-model-invocation: false
model: claude-opus-4-6
context: fork
when_to_use: |
  Trigger for: "review this PR", "check my changes", "look at this diff",
  "is this ready to merge", "code review".
  Do not trigger for: simple file edits, asking about code without a review intent.
---

## Changed files
!`git diff --name-only $ARGUMENTS..HEAD 2>/dev/null || git diff --cached --name-only`

## Diff
!`git diff $ARGUMENTS..HEAD 2>/dev/null || git diff --cached`

Review the diff above. Prioritize:
1. **Correctness** — logic errors, off-by-ones, missing edge cases
2. **Security** — injection risks, exposed secrets, auth bypasses
3. **Error handling** — unhandled exceptions, missing null checks
4. **Performance** — N+1 queries, unnecessary re-renders, blocking calls

Skip style comments — linting handles those. Be specific and actionable.
Group findings by file, severity first.
```

---

## Minimal viable command (no frontmatter)

When you just want a reusable prompt with no configuration, you can omit frontmatter entirely:

```markdown
Analyze this codebase and explain its architecture:
1. Identify the main layers (API, business logic, data access)
2. List the key entry points
3. Draw an ASCII diagram of how components relate
4. Highlight any unusual patterns or technical debt
```

Save as `.claude/commands/architecture.md` → `/architecture`
