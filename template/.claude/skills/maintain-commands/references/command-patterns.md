# Command patterns

Ready-to-use command examples organized by category. Copy, adapt, and drop into `.claude/commands/`.

---

## Git Workflows

### `/commit` — Smart commit message generator

```markdown
---
description: Generate a conventional commit message from staged changes
allowed-tools: Bash(git diff:*) Bash(git log:*)
---

## Staged changes
!`git diff --cached`

## Recent commit style (for reference)
!`git log --oneline -5`

Generate a conventional commit message for the staged changes above.

Format: `<type>(<scope>): <description>`

Types: feat, fix, docs, style, refactor, perf, test, chore, ci

Rules:
- Subject line under 72 chars
- Use imperative mood ("add" not "added")
- If the change is complex, add a blank line then a short body
- Do NOT include "Co-authored-by" or AI attribution lines

Output only the commit message, nothing else.
```

### `/pr` — PR description writer

```markdown
---
description: Write a pull request title and description from branch changes
argument-hint: [base-branch]
allowed-tools: Bash(git log:*) Bash(git diff:*)
---

## Branch changes vs $ARGUMENTS
!`git log $ARGUMENTS..HEAD --oneline 2>/dev/null || git log main..HEAD --oneline`

## Full diff
!`git diff $ARGUMENTS..HEAD 2>/dev/null || git diff main..HEAD`

Write a GitHub pull request description.

Structure:
## What
One sentence: what does this PR do?

## Why
Why is this change needed? What problem does it solve?

## How
Brief explanation of the approach taken (skip if obvious from the diff).

## Testing
How was this tested? What should reviewers verify?

Keep it factual and concise. No fluff.
```

### `/changelog` — Changelog entry from commits

```markdown
---
description: Generate a changelog entry from recent commits
argument-hint: [from-tag-or-commit]
allowed-tools: Bash(git log:*) Bash(git tag:*)
---

## Recent commits
!`git log $ARGUMENTS..HEAD --pretty=format:"%h %s" 2>/dev/null || git log --oneline -20`

## Latest tags
!`git tag --sort=-version:refname | head -5`

Generate a changelog entry in Keep a Changelog format (https://keepachangelog.com).

Group commits under:
- **Added** — new features
- **Changed** — changes to existing functionality
- **Fixed** — bug fixes
- **Removed** — removed features
- **Security** — security fixes

Skip chore/ci/style commits. Use user-facing language, not technical jargon.
```

---

## Code Quality

### `/review` — In-depth code review

```markdown
---
description: Thorough code review of a file or directory
argument-hint: <filepath>
allowed-tools: Read Grep Glob
disable-model-invocation: true
model: claude-opus-4-6
---

Review the code at @$ARGUMENTS

Focus areas (in priority order):
1. **Correctness** — Does the logic match the intent? Any edge cases missed?
2. **Security** — Input validation, auth checks, injection risks, exposed data
3. **Error handling** — Unhandled exceptions, missing null checks, silent failures
4. **Performance** — Unnecessary work, blocking calls, memory leaks
5. **Readability** — Is the intent clear without over-commenting?

For each issue found:
- Cite the exact line(s)
- Explain the problem
- Suggest the fix

Skip pure style issues (naming conventions, formatting) — those belong in linting config.
```

### `/refactor` — Targeted refactor

```markdown
---
description: Refactor a file or function for clarity and maintainability
argument-hint: <filepath> [focus-area]
allowed-tools: Read Edit Write
---

Refactor @$1

Goal: improve readability and maintainability without changing external behavior.

Steps:
1. Read the full file first
2. Identify: magic numbers, duplicated logic, deeply nested conditionals, long functions
3. Apply refactors one at a time
4. Verify the public API / exports are unchanged
5. Add or update inline comments where the logic is genuinely non-obvious

Do NOT: change algorithms, rename public exports, or add new features.
Show a summary of what you changed and why.
```

### `/test-gen` — Generate missing tests

```markdown
---
description: Generate unit tests for a file or function
argument-hint: <filepath>
allowed-tools: Read Grep Glob Write
---

Generate tests for @$ARGUMENTS

Steps:
1. Read the source file to understand what needs testing
2. Check for existing test files (`*.test.*`, `*.spec.*`, `__tests__/`)
3. Identify the testing framework in use (Jest, Vitest, pytest, etc.)
4. Write tests that cover:
   - Happy path for each exported function
   - Edge cases: empty input, null, zero, max values
   - Error cases: invalid input, missing required fields
   - Any business logic with multiple branches

Match the existing test style (imports, assertion style, describe/it vs test).
Place tests in the appropriate file/directory for this project.
```

---

## Debugging

### `/trace` — Trace an error to its root

```markdown
---
description: Debug an error message or unexpected behavior
argument-hint: <error-message-or-description>
allowed-tools: Read Grep Glob Bash(git log:*)
---

Debug this issue: $ARGUMENTS

Investigation steps:
1. Search for the error string or relevant keywords in the codebase
2. Trace the call stack from the error site upward
3. Identify what data/state could cause this
4. Check recent changes to relevant files: `git log --oneline -10 -- <relevant-files>`
5. Propose the most likely cause and a fix

Be systematic. Show your reasoning. If multiple causes are possible, rank them.
```

### `/explain-error` — Plain-language error explanation

```markdown
---
description: Explain what an error means and how to fix it
argument-hint: <error-text>
---

Explain this error in plain language:

```
$ARGUMENTS
```

Tell me:
1. What this error means
2. What usually causes it
3. How to fix it (most common fix first)
4. How to prevent it going forward

Assume I understand the language but may not know this specific error.
```

---

## Project Management

### `/standup` — Generate standup notes

```markdown
---
description: Generate yesterday/today/blockers from recent git activity
allowed-tools: Bash(git log:*) Bash(git diff:*)
---

## My recent commits (last 2 days)
!`git log --author="$(git config user.name)" --since="2 days ago" --oneline`

## Current branch and status
!`git branch --show-current`
!`git status --short`

Generate a standup update from the activity above.

Format:
**Yesterday**: What I worked on
**Today**: What I plan to work on
**Blockers**: Anything blocking me (say "None" if nothing)

Keep it brief — 2-3 bullet points per section max.
Use natural language, not commit message syntax.
```

### `/estimate` — Task size estimation

```markdown
---
description: Estimate effort for a task or feature
argument-hint: <task-description>
---

Estimate the effort for: $ARGUMENTS

Given this codebase, provide:
1. **T-shirt size**: XS / S / M / L / XL
2. **Hour range**: rough low-high estimate
3. **Key unknowns**: what would make this take longer?
4. **Suggested breakdown**: 3-5 subtasks

Be honest about uncertainty. If you need to see specific files to estimate, ask.
```

---

## Documentation

### `/doc-gen` — Generate JSDoc / docstrings

```markdown
---
description: Add documentation comments to a file
argument-hint: <filepath>
allowed-tools: Read Edit
---

Add documentation to @$ARGUMENTS

Rules:
- Add JSDoc (JS/TS), docstrings (Python), or equivalent for the language
- Document every exported function, class, and type
- Each doc must include: description, @param (with types), @returns, @throws (if applicable)
- For complex functions, add a one-line @example
- Do NOT document obvious internal helpers — only public API surfaces
- Preserve all existing code exactly; only add/modify comments
```

### `/readme-update` — Sync README with codebase

```markdown
---
description: Update README to match current codebase state
allowed-tools: Read Glob
---

Review the README and update it to match the current codebase.

Steps:
1. Read README.md
2. Read package.json or equivalent for actual scripts/dependencies
3. Check entry points and key files
4. Update sections that are stale:
   - Installation instructions
   - Available scripts / commands
   - Configuration options
   - API reference (if present)

Keep the existing tone and structure. Only change what's factually incorrect or missing.
Flag any sections you're unsure about rather than guessing.
```

---

## Onboarding & Navigation

### `/architecture` — Explain project structure

```markdown
---
description: Explain the codebase architecture and key components
allowed-tools: Read Glob Grep
---

Explain the architecture of this codebase.

Cover:
1. **Purpose**: What does this project do?
2. **Structure**: Major directories and what lives in each
3. **Entry points**: Where does execution begin? (main file, API routes, etc.)
4. **Key layers**: How is the code layered? (e.g., API → service → repository)
5. **Data flow**: How does a typical request/operation flow through the system?
6. **External dependencies**: Key libraries, databases, services

Draw an ASCII diagram showing how components relate.
Flag anything unusual or that took you a moment to understand — that's what new devs will also find confusing.
```

### `/find` — Find where something is implemented

```markdown
---
description: Find where a feature, function, or concept is implemented
argument-hint: <what-to-find>
allowed-tools: Grep Glob Read
---

Find where "$ARGUMENTS" is implemented in this codebase.

Search strategy:
1. Grep for the exact term and close synonyms
2. Check index/barrel files for exports
3. Look at the most likely directories based on project structure
4. Trace from entry points if needed

Report:
- The primary file(s) where this lives
- Any related files (tests, types, config)
- A brief explanation of how it works
```

---

## Security

### `/security-scan` — Vulnerability audit

```markdown
---
description: Scan codebase for common security vulnerabilities
allowed-tools: Read Grep Glob Bash(git log:*)
disable-model-invocation: true
model: claude-opus-4-6
context: fork
---

Perform a security audit of this codebase.

Check for:
1. **Secrets/credentials** — hardcoded API keys, passwords, tokens
2. **Injection risks** — SQL, command, template injection
3. **Auth gaps** — unprotected endpoints, missing authorization checks
4. **Input validation** — untrusted data used without sanitization
5. **Dependency risks** — check package.json for known vulnerable patterns
6. **XSS** (if web app) — unescaped user content rendered as HTML
7. **CORS/CSP misconfiguration** — overly permissive origins

For each finding:
- Severity: Critical / High / Medium / Low
- File and line number
- Description of the risk
- Recommended fix

Report "None found" for categories with no issues.
```

---

## Workflow Recipes

### Multi-step: "ship it" workflow

```markdown
---
name: ship
description: Run full pre-ship checklist: tests, lint, build, then commit and PR
allowed-tools: Bash(npm *) Bash(git *)
disable-model-invocation: true
---

Run the complete ship workflow:

1. **Lint**: `npm run lint` — fix any errors, warn about warnings
2. **Test**: `npm test` — do not proceed if tests fail
3. **Build**: `npm run build` — confirm it compiles cleanly
4. **Commit**: Generate and apply a conventional commit for staged changes
5. **Push**: `git push origin HEAD`
6. **PR**: Summarize what's in this branch for a PR description

Stop and report if any step fails. Do not continue past failures.
```

### Template command for project-specific tasks

```markdown
---
name: task-name
description: [One line: what it does. When to use it.]
argument-hint: [arg description if needed]
allowed-tools: Read   # add only what's needed
disable-model-invocation: true  # if has side effects
---

[Main prompt here]

$ARGUMENTS
```
