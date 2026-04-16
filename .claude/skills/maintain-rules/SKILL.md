---
name: maintain-rules
description: >-
  Write, manage, audit, and organize `.claude/rules/` files for Claude Code projects. Use this skill
  whenever the user wants to create or edit rules files for Claude Code, set up a `.claude/` directory,
  write a CLAUDE.md, scope instructions to specific file paths, organize modular project memory, audit
  or clean up existing rules, share rules across projects, or set up team/org-wide Claude Code instructions.
  Also trigger when user says things like "add a rule for Claude", "Claude keeps forgetting X", "set up
  Claude memory for my project", "path-scoped rules", "Claude Code project config", or "how do I tell
  Claude to always do X".
---

# Claude Rules Skill

A skill for authoring, organizing, and managing `.claude/rules/` files and the broader Claude Code
memory system (`CLAUDE.md`, `.claude/rules/`, `CLAUDE.local.md`).

## Memory System Overview

Claude Code has **four scopes** of persistent instructions, loaded in this order (more specific = higher priority):

```
[Managed Policy]  /etc/claude-code/CLAUDE.md          ← org-wide, enforced by IT
[User-level]      ~/.claude/CLAUDE.md                  ← personal, all projects
                  ~/.claude/rules/*.md                 ← personal modular rules
[Project]         ./CLAUDE.md  or  ./.claude/CLAUDE.md ← team-shared via git
                  ./.claude/rules/*.md                 ← modular project rules
[Local]           ./CLAUDE.local.md                    ← personal+project, gitignored
```

All discovered files are **concatenated** into context — they don't override each other. More specific
scopes win on conflicts. Rules are context (guidance), not enforced configuration.

**Two mechanisms carry knowledge across sessions:**
- **CLAUDE.md files** — instructions *you* write; persistent and intentional
- **Auto memory** — notes Claude writes itself; lives in `~/.claude/projects/<repo>/memory/`

## Rules vs Skills — core philosophy

Rules and skills have strict, non-overlapping roles. **Do not duplicate content between them.**

**Rules — short, always-on, non-negotiable**
- Hard constraints: "never do X", "always use Y"
- Project context: stack, architecture, key decisions
- Guardrails: security invariants, secrets, naming conventions
- Anything Claude must know before touching any matching file
- **Max 5–7 lines per file.** If a rule needs more lines, the extra content belongs in a skill.

**Skills — rich, detailed, invoked when relevant**
- Patterns and examples
- Step-by-step how-tos and workflows
- Templates and reference structures
- Edge cases, gotchas, and troubleshooting
- Anything too long or situational to load every session

**Audit test** — for every rule line, ask: "Would Claude cause harm or break a hard constraint if it didn't know this before touching a file?" If no, move it to a skill.

## When to Use Each Mechanism

| Situation | Use |
|-----------|-----|
| Hard constraint that applies everywhere | `CLAUDE.md` or `.claude/rules/common/*.md` |
| Hard constraint scoped to a file type | `.claude/rules/<lang>/*.md` with `paths:` frontmatter |
| Pattern, example, or how-to | A **skill** (not rules — skills load on demand) |
| Project-specific standards shared with team | `.claude/rules/` committed to git |
| Personal preferences not for teammates | `CLAUDE.local.md` or `~/.claude/CLAUDE.md` |
| Something Claude discovered itself | Auto memory (let it handle it) |

**Do not add to rules or CLAUDE.md:**
- Generic instructions ("write clean code", "follow best practices")
- Code examples or before/after snippets (→ skill reference file)
- Multi-step procedures or workflows (→ skill)
- Reference tables of error codes, filter lists, command catalogues (→ skill)
- Credentials or secrets
- Things only needed occasionally

---

## Directory Structure

```
your-project/
├── CLAUDE.md                    # Root project instructions (committed)
├── CLAUDE.local.md              # Personal local overrides (gitignored)
└── .claude/
    ├── CLAUDE.md                # Alternative location for project instructions
    ├── settings.json            # Claude Code settings
    └── rules/
        ├── code-style.md        # ← Unconditional: loads every session
        ├── testing.md           # ← Unconditional: loads every session
        ├── security.md          # ← Unconditional: loads every session
        ├── api-design.md        # ← Has paths: frontmatter → conditional
        ├── frontend/
        │   └── react.md         # ← Subdirectory OK; discovered recursively
        └── backend/
            └── database.md      # ← Path-scoped to backend files
```

---

## Rule File Format

### Standard Rule (loads every session)

```markdown
# [Topic Name]

<!-- Human maintainer notes here — stripped from context, not token-costly -->

- [Concrete, verifiable instruction]
- [Another specific instruction]

## [Sub-section if needed]

- [More specific rules]
```

### Path-Scoped Rule (loads only when Claude touches matching files)

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/api/**/*.tsx"
---

# API Development Rules

> This file extends [common/coding-style.md](../common/coding-style.md) with API-specific content.

- All API endpoints must include input validation using Zod schemas
- Use the standard `ApiError` class for error responses (see `src/lib/errors.ts`)
- Include JSDoc comments for all exported handler functions
- Rate limit headers must be set on all public endpoints
```

The `> This file extends …` callout is required whenever a path-scoped rule specialises
a file in `common/`; omit it otherwise.

**Deprecated alternative:** older rule files sometimes used a `# applies-to: <glob>`
comment line instead of frontmatter. This form is no longer accepted — always use YAML
frontmatter with `paths:`, so the scope is machine-readable and consistent across
tools (Claude Code, Cursor, etc.). When auditing an existing `.claude/rules/`
directory, convert any `# applies-to:` lines to frontmatter.

### Multi-pattern Rule

```markdown
---
paths:
  - "**/*.test.{ts,tsx,js,jsx}"
  - "**/*.spec.{ts,tsx,js,jsx}"
  - "tests/**/*"
---

# Testing Rules

- Use `describe`/`it` blocks, not `test()`
- Mock external services; never hit real APIs in tests
- Each test file must import from `@/test-utils`, not directly from `@testing-library/react`
- Run `npm test -- --watch` during development
```

---

## Writing Rules: Quality Checklist

Before saving any rule, verify:

**✅ Specificity** — Is it concrete enough to verify?
- ✗ "Format code nicely"
- ✓ "Use 2-space indentation; no trailing whitespace; files end with newline"

**✅ Actionability** — Can Claude act on it without guessing?
- ✗ "Follow security best practices"
- ✓ "Never log request bodies to console; sanitize user input with `validator.escape()`"

**✅ Uniqueness** — Does it contain project-specific knowledge Claude wouldn't know?
- ✗ "Write tests for new features"
- ✓ "Run `npm run test:unit` before committing; integration tests run with `npm run test:ci` (requires Docker)"

**✅ Stability** — Will this still be true in 6 months?
- ✗ "The auth service is currently being migrated"  ← use a doc, not a rule
- ✓ "Auth tokens expire in 15 minutes; use `refreshToken()` from `src/auth/client.ts`"

**✅ Size** — Keep each rule file to **5–7 lines of content** (excluding frontmatter and title). If you need more lines, the content is how-to/reference material and belongs in a skill. Keep the whole CLAUDE.md under 200 lines.

**✅ No duplication with skills** — Before adding a rule, check whether an existing skill already covers the content. If yes, delete the rule; rely on the skill. Rules are for hard constraints that must be loaded every session; skills are for detailed guidance loaded on demand.

---

## Standard Workflow for Creating a Rules Setup

### Step 1 — Audit what exists

```bash
# Check current memory files
ls -la .claude/rules/ 2>/dev/null || echo "No rules directory"
cat CLAUDE.md 2>/dev/null || cat .claude/CLAUDE.md 2>/dev/null || echo "No CLAUDE.md"
```

### Step 2 — Create the directory structure

```bash
mkdir -p .claude/rules
touch .claude/rules/.gitkeep   # preserve directory in git if no files yet
echo "CLAUDE.local.md" >> .gitignore
```

### Step 3 — Identify rule categories

Ask (or infer from codebase):
1. What are the build/test/run commands?
2. What coding style conventions are enforced (linter, formatter, style guide)?
3. What architectural patterns must be followed?
4. What security/compliance requirements exist?
5. Are there areas of the codebase with special handling?

### Step 4 — Write the rules

Use the templates in `assets/templates/` (see below) as starting points. One file per topic.

### Step 5 — Decide: path-scoped or unconditional?

- **Unconditional** if the rule applies everywhere (code style, git workflow, naming)
- **Path-scoped** if the rule only applies in specific directories/file types (API, frontend, tests)

### Step 6 — Validate

```bash
# List all discovered rules
cat .claude/rules/*.md

# Check CLAUDE.md loads correctly by reviewing /memory in Claude Code session
# Or: check with InstructionsLoaded hook in settings.json
```

---

## Common Rule Categories & Templates

See `references/categories.md` for detailed per-category templates covering:
- `code-style.md` — formatting, naming, imports
- `testing.md` — test frameworks, patterns, commands
- `security.md` — secrets, validation, auth
- `git-workflow.md` — branching, commit messages, PR process
- `api-design.md` — REST/GraphQL conventions
- `architecture.md` — module structure, patterns, DI
- `documentation.md` — JSDoc, README standards
- `performance.md` — bundling, caching, query patterns

---

## Glob Patterns Reference

```
**/*.ts          → All TypeScript files in any directory
src/**/*         → All files under src/
*.md             → Markdown in project root only
src/**/*.{ts,tsx}→ TypeScript and TSX under src/
tests/**/*.test.ts → Test files under tests/
!**/node_modules/**→ Exclusion (prefix with !)
```

---

## Path-Scoped vs Unconditional Decision Tree

```
Does this rule apply to ALL files in the project?
├── YES → No paths: frontmatter (unconditional)
└── NO  → Does it apply to a specific directory/type?
          ├── YES → Add paths: frontmatter with matching glob
          └── ONLY SOMETIMES → Split into conditional + unconditional sections
                                OR use a skill (for task-specific guidance)
```

---

## Sharing Rules Across Projects

Use symlinks to share a common ruleset:

```bash
# Create shared rules repo at ~/shared-claude-rules/
mkdir -p ~/shared-claude-rules

# Link into project
ln -s ~/shared-claude-rules .claude/rules/shared

# Link a single file
ln -s ~/company-standards/security.md .claude/rules/security.md
```

Symlinks are resolved and loaded normally; circular symlinks are handled gracefully.

---

## Troubleshooting

**Rule not being followed:**
1. Run `/memory` inside Claude Code → check the file is listed
2. Is the instruction specific and concrete? Vague rules are often ignored
3. Check for conflicting rules across files — Claude may pick arbitrarily
4. Keep CLAUDE.md under 200 lines; adherence drops with length
5. For critical rules: repeat key instructions in CLAUDE.md AND the relevant rule file

**Path-scoped rule not triggering:**
1. Verify glob pattern syntax — test with `micromatch` or similar
2. Rule triggers when Claude *reads* matching files, not on every tool use
3. Check via `InstructionsLoaded` hook for debug logging

**CLAUDE.md too large:**
1. Move detailed content to `@import` references
2. Split into `.claude/rules/*.md` files
3. Target <200 lines; move procedures to skills

**After `/compact`, instructions lost:**
- Project-root CLAUDE.md re-injects after compact ✓
- Nested CLAUDE.md files only reload when Claude reads files in that subdirectory
- Conversation-only instructions don't survive — add them to CLAUDE.md

---

## Quick reference: where to go deeper

| Topic                                              | Reference file                                           |
|----------------------------------------------------|----------------------------------------------------------|
| Full per-category rule templates                   | [references/categories.md](references/categories.md)     |
| Real-world example rules for common stacks         | [references/examples.md](references/examples.md)         |
| Copy-paste starter files for each rule category    | [assets/templates/starters.md](assets/templates/starters.md) |
