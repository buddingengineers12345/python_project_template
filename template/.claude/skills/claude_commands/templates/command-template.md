# Command Template

Use this annotated template when writing a new `.claude/commands/*.md` file from scratch.
Delete the comment lines (`<!-- ... -->`) before saving your command.

---

```markdown
---
<!-- REQUIRED: Brief description of what this command does and when Claude should use it.
     Front-load the key action. This is the primary text Claude reads to decide
     whether to auto-invoke the skill. -->
description: [Action verb] [what it does]. Use when [trigger conditions].

<!-- OPTIONAL: Hint shown in autocomplete. Use <required> and [optional] conventions. -->
argument-hint: <required-arg> [optional-arg]

<!-- OPTIONAL: List tools this command needs, space-separated.
     ALWAYS scope Bash with a pattern: Bash(git *), Bash(npm run:*), etc.
     Only list what you need — extra permissions are a security risk. -->
allowed-tools: Read Grep

<!-- OPTIONAL: Set true for any command with side effects (deploy, push, mutate data).
     Prevents Claude from running it automatically. -->
disable-model-invocation: true

<!-- OPTIONAL: Pin to a model. Use claude-opus-4-6 for complex reasoning,
     claude-haiku-4-5-20251001 for fast/cheap operations. -->
# model: claude-sonnet-4-6

<!-- OPTIONAL: "fork" runs in subagent with copied context (good for long tasks).
     "agent" runs in fresh subagent (good for clean-slate tasks).
     Leave blank to run inline in current conversation. -->
# context: fork
---

<!-- ============================================================
     COMMAND BODY
     
     Start with the action immediately. Don't begin with "You are a..."
     or lengthy preamble. Claude reads the first line first.
     ============================================================ -->

[Primary action statement — what Claude should do]

<!-- OPTIONAL: Inject live shell context using !`command` syntax.
     Only works when allowed-tools includes the relevant Bash scope.
     Example:
     
## Current state
!`git status --short`
!`git diff --cached`
     
-->

<!-- ARGUMENTS:
     Use $ARGUMENTS for all args as one string.
     Use $1, $2, etc. for positional args.
     
     If using $ARGUMENTS:     /command-name my input here → $ARGUMENTS = "my input here"
     If using $1 / $2:        /command-name foo bar      → $1 = "foo", $2 = "bar"
-->

<!-- INSTRUCTIONS:
     List steps if the task is multi-stage.
     Explain the *why* behind important steps.
     Describe the expected output format.
     Mention what to do if something is ambiguous or fails.
-->

Steps:
1. [First action]
2. [Second action]
3. [What to report / output format]

<!-- QUALITY TIPS:
     - Be specific about output format if it matters
     - Mention what to skip or ignore
     - Add a "stop if" condition for side-effect commands
     - Don't over-specify — trust Claude's judgment for routine decisions
-->
```

---

## Template variants

### Minimal (no frontmatter needed)

```markdown
[Action]. $ARGUMENTS

1. [Step]
2. [Step]
3. Report: [format]
```

### With bash context injection

```markdown
---
allowed-tools: Bash(git log:*) Bash(git diff:*)
description: [description]
---

## Context
!`git log --oneline -10`
!`git diff HEAD~1`

[Instructions using the injected context above]
```

### Positional args

```markdown
---
argument-hint: <input-file> <output-format>
allowed-tools: Read Write
---

Convert @$1 to $2 format.

1. Read the source file
2. Transform to the target format
3. Write the result to $1.$2 (same name, new extension)
4. Confirm the output path
```

### Subagent + disable auto-invoke

```markdown
---
description: [Destructive or long-running operation]
disable-model-invocation: true
context: fork
allowed-tools: Bash(npm *) Bash(git *)
---

[Instructions for a long-running or side-effect operation]

Important: If any step fails, stop immediately and report what failed.
Do not attempt to continue past errors.
```

---

## Naming conventions

| Pattern | Example | Use for |
|---------|---------|---------|
| `verb-noun` | `gen-types`, `fix-lint` | Single-purpose actions |
| `noun` | `commit`, `review`, `deploy` | Well-known workflows |
| `namespace/verb` | `db/migrate`, `deploy/staging` | Grouped commands |
| `check-noun` | `check-deps`, `check-types` | Read-only audits |

Avoid:
- Names that shadow built-ins: `help`, `clear`, `compact`, `init`
- Generic names: `run`, `do`, `execute`, `task`
- Camel case: use `fix-lint` not `fixLint`
