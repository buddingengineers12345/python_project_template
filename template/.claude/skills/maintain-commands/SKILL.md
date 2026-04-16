---
name: maintain-commands
description: >-
  Write, create, edit, manage, and organize .claude/commands and .claude/skills files
  for Claude Code. Use whenever the user wants to create a new slash command, write a
  custom command, add a command to their project, manage their command library, scaffold
  a .claude/commands directory, understand command syntax, build a skill file, or set up
  personal or project-scoped commands. Also trigger when the user says things like "add
  a /command", "make a slash command", "create a custom command", "set up commands for
  my project", or "help me write a SKILL.md".
---

# Claude Commands Skill

This skill helps you write, manage, and organize custom slash commands for Claude Code. It covers both the legacy `.claude/commands/` format and the modern `.claude/skills/` system — both produce `/command-name` shortcuts.

## Quick orientation

| Format | Path | Slash command | Extras |
|--------|------|---------------|--------|
| Legacy command | `.claude/commands/deploy.md` | `/deploy` | Simple, works everywhere |
| Modern skill | `.claude/skills/deploy/SKILL.md` | `/deploy` | Supports supporting files, auto-invocation |
| Personal command | `~/.claude/commands/deploy.md` | `/deploy` | Available across all projects |
| Personal skill | `~/.claude/skills/deploy/SKILL.md` | `/deploy` | Available across all projects |

**Rule of thumb**: Use `.claude/commands/` for quick, simple prompts. Graduate to `.claude/skills/` when you need supporting files (scripts, templates, examples) or want Claude to auto-invoke it from natural language.

If both a command and skill share a name, the skill takes precedence.

---

## Standard command format (required baseline)

Every command file in `.claude/commands/` must follow this minimum structure. Use this
as the target when auditing or standardizing an existing command library.

```markdown
---
description: <Verb-first summary of what the command does>. Use when <trigger conditions>.
argument-hint: <required> [optional]         # include only if command accepts args
allowed-tools: <tightly scoped tools>         # always scope Bash(...) patterns
disable-model-invocation: true                # include only for side-effect commands
context: fork                                 # include only for long/isolated work
---

<Action verb leads the first line — no preamble, no "You are a..." framing>

## <Optional section headings>

<Body: steps, context injection via !`...`, arguments via $ARGUMENTS / $1 / $2>
```

### Required fields

- **`description`** — one sentence, starts with a verb, includes a "Use when ..." clause
  so Claude knows when to auto-invoke. Keep under ~200 characters.

### Conditionally required fields

- **`argument-hint`** — include whenever the command consumes `$ARGUMENTS`, `$1`, `$2`, etc.
- **`allowed-tools`** — include when the command calls Bash, Read/Write/Edit, or search
  tools. Always scope `Bash(...)` as narrowly as possible.
- **`disable-model-invocation: true`** — include for any command with side effects
  (writes files, runs git mutations, deploys, sends data, mutates the project).
- **`context: fork`** — include for long-running or autonomous workflows that benefit
  from an isolated subagent (e.g., `/ci-fix`, `/review`, `/validate-release`).

### Body conventions

1. First line is an imperative action statement ("Run X", "Fix Y", "Audit Z").
2. Use `## Step 1 — ...` or `## Steps` headings for multi-stage work.
3. Fenced code blocks (```bash ... ```) for every shell command so intent is explicit.
4. Include an `## Output format` or `## Report format` section when the command
   produces a structured deliverable.
5. Include a `## Rules`, `## Tips`, or `## Rollback` section when the command has
   strict guardrails or recovery steps.

### Auditing an existing library against this standard

Use this checklist when running a standardization pass over `.claude/commands/`:

- [ ] Every file starts with a YAML frontmatter block between `---` markers
- [ ] Every file has a `description` with a "Use when ..." clause
- [ ] Every file with arguments declares `argument-hint`
- [ ] Every file using tools declares a scoped `allowed-tools`
- [ ] Every side-effect command sets `disable-model-invocation: true`
- [ ] Every command body starts with an action verb (no "You are a..." preamble)
- [ ] Filenames are kebab-case, verb-first where possible
- [ ] No two commands share a name with a skill of the same name

---

## Anatomy of a command file

Every command is a Markdown file. The filename (without `.md`) becomes the slash command name.

```
.claude/commands/
├── commit.md          → /commit
├── review.md          → /review
├── fix-issue.md       → /fix-issue
└── git/
    ├── push.md        → /git:push
    └── sync.md        → /git:sync
```

Subdirectories create namespaced commands using `:` as the separator. Use namespaces to group related commands and avoid collisions.

---

## Frontmatter fields

All frontmatter is optional, but `description` is strongly recommended. Place frontmatter between `---` markers at the top of the file.

```markdown
---
name: my-command           # Override display name (default: filename)
description: One-line summary of what this command does and when to use it
argument-hint: [file] [flags]  # Shown in autocomplete as usage hint
allowed-tools: Read Grep Bash(git *)  # Pre-approve tools (space-separated)
disable-model-invocation: true  # Prevent Claude from auto-triggering this
model: claude-opus-4-6     # Pin to a specific model
context: fork              # Run in subagent: "fork" | "agent" | inline (default)
when_to_use: |             # Extended trigger context for auto-invocation
  Use when the user mentions deployments, releases, or shipping code.
---
```

See `references/frontmatter-reference.md` for the full field reference with all options and caveats.

---

## Argument handling

### All arguments as one string: `$ARGUMENTS`

```markdown
---
argument-hint: <branch-name>
---
Create a new feature branch named `$ARGUMENTS` from main:
1. git checkout main && git pull
2. git checkout -b feature/$ARGUMENTS
3. Confirm the branch was created
```

Invoked as: `/branch my-feature` → `$ARGUMENTS` = `"my-feature"`

### Positional arguments: `$1`, `$2`, ...

```markdown
---
argument-hint: <issue-number> <priority>
---
Fix GitHub issue #$1 with priority $2.
1. Read the issue description
2. Implement the fix
3. Write a test
4. Commit with message: "fix(#$1): [description] - priority $2"
```

Invoked as: `/fix-issue 42 high` → `$1`=`"42"`, `$2`=`"high"`

### No arguments

Some commands need no arguments at all — they operate on the current context (open file, git state, etc.).

```markdown
Run a security audit of this codebase:
1. Check for hardcoded secrets using `grep -r "api_key\|password\|secret" --include="*.ts"`
2. Scan for SQL injection vectors
3. List all external HTTP calls and their destinations
4. Report findings grouped by severity
```

---

## Bash injection (dynamic context)

When `allowed-tools` includes `Bash`, you can inject live shell output into the prompt using `` !`command` `` syntax. The output is inserted before Claude sees the prompt.

```markdown
---
allowed-tools: Read Grep Bash(git *)
description: Review staged changes before committing
---

## Current branch
!`git branch --show-current`

## Staged diff
!`git diff --cached`

## Files changed
!`git diff --cached --name-only`

Review the staged changes above. Check for:
1. Obvious bugs or logic errors
2. Missing error handling
3. Hardcoded values that should be env vars
4. Tests that should accompany these changes

Be concise and actionable.
```

**Security note**: `Bash(git *)` restricts bash to only `git` commands. Always scope `Bash(...)` as narrowly as possible.

---

## File and context references

### Reference a file with `@`

```markdown
Analyze @src/auth/login.ts and identify all security vulnerabilities.
```

### Dynamic file reference via argument

```markdown
---
argument-hint: <filepath>
---
Review the file @$ARGUMENTS for:
- Code quality issues
- Missing error handling
- Performance concerns
- Documentation gaps
```

### Embed file contents at write-time

```markdown
---
allowed-tools: Read
---

Read the file at path: $ARGUMENTS

Then refactor it to:
1. Extract magic numbers into named constants
2. Add JSDoc comments to all exported functions
3. Replace any `var` declarations with `const` or `let`
```

---

## Command categories & patterns

See `references/command-patterns.md` for full examples organized by category:
- **Git workflows**: commit, pr, sync, changelog
- **Code quality**: review, lint-fix, refactor, test-gen
- **Project management**: plan, estimate, standup
- **Documentation**: doc-gen, readme-update, api-docs
- **Debugging**: trace, explain-error, profile
- **Onboarding**: orientation, architecture-tour

---

## Writing effective commands

### 1. Front-load the action

Start with the verb. Claude reads the beginning first.

```markdown
# ✓ Good — action is clear immediately
Generate a commit message for the staged changes...

# ✗ Weak — buries the action
You are a helpful assistant. When the user runs this command, your job is to...
```

### 2. Explain the *why*, not just the *what*

Commands that explain reasoning are more robust than rigid checklists:

```markdown
# ✓ Good — explains purpose
Review this PR focusing on correctness and security. We care less about style
(linting handles that) and more about logic errors, missing edge cases, and
anything that could fail in production.

# ✗ Brittle — mechanical list with no context
1. Check variable names
2. Check function names
3. Check comments
4. Check imports
```

### 3. Scope `allowed-tools` tightly

```markdown
# ✓ Tight — only git read commands
allowed-tools: Bash(git log:*) Bash(git diff:*) Bash(git show:*)

# ✗ Wide — grants all bash
allowed-tools: Bash
```

### 4. Use `disable-model-invocation` for side-effect commands

Any command that writes, deploys, or sends data should not auto-trigger:

```markdown
---
disable-model-invocation: true
allowed-tools: Bash(npm *) Bash(git push:*)
---
Deploy to production...
```

### 5. Keep commands single-purpose

One command, one job. Chain them at the call site (`/commit` then `/pr`), not inside the command file.

### 6. Namespace related commands

```
.claude/commands/
├── db/
│   ├── migrate.md     → /db:migrate
│   ├── seed.md        → /db:seed
│   └── rollback.md    → /db:rollback
└── deploy/
    ├── staging.md     → /deploy:staging
    └── production.md  → /deploy:production
```

---

## Quick scaffolding workflow

When asked to create commands for a project:

1. **Audit the project** — check for existing `.claude/commands/`, `CLAUDE.md`, `package.json` scripts, common dev tasks
2. **Identify repetitive workflows** — what does the developer run / explain repeatedly?
3. **Choose scope** — project-level (`.claude/`) for team commands, personal (`~/.claude/`) for individual shortcuts
4. **Write the commands** — start from the template in `templates/command-template.md`
5. **Name deliberately** — short, verb-first, kebab-case: `gen-types`, `fix-lint`, `check-deps`
6. **Test by invocation** — mentally trace what Claude will see after bash injection and argument substitution

---

## Managing an existing command library

When asked to audit, reorganize, or improve existing commands:

1. **Read all files** in `.claude/commands/` (and `~/.claude/commands/` if relevant)
2. **Check for**: duplicate commands, overly broad `allowed-tools`, missing `description` fields, commands that should be namespaced
3. **Suggest graduation** — commands that have grown complex enough for supporting files → migrate to `.claude/skills/`
4. **Verify no conflicts** — if a skill and command share a name, the skill wins silently
5. **Update `CLAUDE.md`** to list available commands so Claude (and humans) know they exist

---

## Quick reference: where to go deeper

| Topic                                              | Reference file                                                       |
|----------------------------------------------------|----------------------------------------------------------------------|
| Complete frontmatter field docs with all options   | [references/frontmatter-reference.md](references/frontmatter-reference.md) |
| Ready-to-use command examples by category          | [references/command-patterns.md](references/command-patterns.md)     |
| Annotated template for writing a new command       | [templates/command-template.md](templates/command-template.md)       |
