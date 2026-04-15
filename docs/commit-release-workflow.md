# Commit & Release Workflow

This document explains how `.gitmessage`, `commitizen`, `cliff.toml`, and the release pipeline work together to maintain a clean, semantic-versioned repository.

## Quick Setup

```bash
# 1. Install Python dependencies (commitizen, etc.)
just sync

# 2. Set up git hooks and commit template
just precommit-install

# 3. Install git-cliff (system binary)
#    macOS:
brew install git-cliff
#    Linux (with Rust):
cargo install git-cliff

# Verify everything is ready
just doctor
git config commit.template        # Should show .gitmessage path
command -v git-cliff              # Should show /usr/local/bin/git-cliff or similar
```

## Architecture Overview

```
User commits code
       ↓
.gitmessage (template reminder)
       ↓
git commit → commitizen pre-commit hook (validates format)
       ↓
Commit stored with conventional format (feat:, fix:, etc.)
       ↓
[Later] Developer runs: just release patch|minor|major
       ↓
Commitizen bumps [project].version (reads PEP 440)
       ↓
git-cliff parses commits since last tag
       ↓
CHANGELOG.md generated (grouped by feat, fix, refactor, etc.)
       ↓
Tag created (v0.0.8) and pushed
       ↓
Release complete
```

## Installation

### Prerequisites

**Python-based tools (installed via `just sync`):**
- Commitizen (validates & creates conventional commits)
- Ruff, pytest, mypy (linting, testing, typing)

**System tools (install separately):**
- `git-cliff` (Rust binary for changelog generation)

**Install git-cliff:**

```bash
# macOS
brew install git-cliff

# Linux (depends on distro)
cargo install git-cliff        # If Rust installed
# OR
sudo apt-get install git-cliff  # Debian/Ubuntu

# From source
https://github.com/orhun/git-cliff
```

---

## Three Tools & Their Roles

### 1. `.gitmessage` — Commit Template (Developer Convenience)

**File:** `.gitmessage`

**What it does:**
- Displays when you run `git commit` (after `just precommit-install` sets it up)
- Provides a helpful format reminder for conventional commits

**Setup:**
```bash
git config commit.template "$(git rev-parse --show-toplevel)/.gitmessage"
```

**Format enforced:**
```
<type>(<scope>): <short imperative description>

<optional body explaining WHY and context>

<optional footer: Closes #123, Breaking change: ...>
```

**Types allowed:** `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `perf`

**Example:**
```
feat(auth): add OAuth login flow

Adds support for Google and GitHub OAuth providers.
Users can now sign in without creating a password.

Closes #42
```

---

### 2. Commitizen — Validation & Interactive Commits

**Config:** `pyproject.toml` → `[tool.commitizen]`

```toml
[tool.commitizen]
name = "cz_conventional_commits"        # Use conventional commit spec
version_provider = "pep621"             # Read/write [project].version
tag_format = "v$version"                # Create tags like v0.0.8
```

**What it does:**
- **Interactive mode:** `just cz-commit` walks you through structured commit creation
- **Validation mode:** Pre-commit hook (commit-msg stage) blocks non-compliant messages
- **Release mode:** `cz bump` increments [project].version and creates a commit

**Two Ways to Commit:**

**Option A: Guided (Recommended for beginners)**
```bash
just cz-commit
# → Interactive prompts for type, scope, description, body
# → Automatically formats message
# → Enforces conventional commit syntax
```

**Option B: Manual (For experienced users)**
```bash
git commit
# → Editor opens with .gitmessage template
# → Commitizen pre-commit hook validates format
# → Accepts or rejects based on conventional commit rules
```

**Validation Hook (automatic):**
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/commitizen-tools/commitizen
  stages: [commit-msg]
  hooks:
    - id: commitizen
```

This hook runs **after** you write your commit message but **before** it's stored. If the message doesn't match conventional commit format, the commit is rejected.

---

### 3. `cliff.toml` — Changelog Generation (Release Time)

**File:** `cliff.toml`

**What it does:**
- Parses commits since the last version tag
- Groups commits by type (feat → ✨ Features, fix → 🐛 Bug Fixes, etc.)
- Generates a formatted `CHANGELOG.md`

**Key config:**
```toml
[git]
conventional_commits = true      # Only parse conventional commits
filter_unconventional = true      # Ignore non-standard commits
tag_pattern = "v[0-9]*"          # Match tags like v0.0.8
```

**Commit groups (examples):**
- `feat` → ✨ Features
- `fix` → 🐛 Bug Fixes
- `perf` → ⚡ Performance
- `refactor` → ♻️ Refactoring
- `docs` → 📚 Documentation

**Output format (CHANGELOG.md):**
```markdown
## v0.1.0 - 2026-04-15

### ✨ Features
* Add OAuth login flow
* Support custom themes

### 🐛 Bug Fixes
* Fix null pointer in parser
* Prevent race condition in cache

### ⚡ Performance
* Optimize database queries
```

---

## Release Workflow

### Prerequisite: Clean Commits
All commits must be conventional (enforced by Commitizen hook). If you've been using `git commit` with `.gitmessage`, your history should be clean.

### Step-by-Step Release

```bash
# 1. Ensure you're on main branch and synced
git checkout main
git pull origin main

# 2. Verify repo is clean (no uncommitted changes)
git status                          # Should be "nothing to commit"

# 3. Run the release pipeline
just release patch                  # Patch: v0.0.8 → v0.0.9
# OR
just release minor                  # Minor: v0.0.8 → v0.1.0
# OR
just release major                  # Major: v0.0.8 → v1.0.0
```

### What `just release` Does

1. **Validates clean state:** Exits if uncommitted changes exist
2. **Runs CI:** `just ci` (lint + test + type check) must pass
3. **Bumps version:** Commitizen updates `[project].version` in `pyproject.toml`
4. **Creates changelog:** git-cliff generates/updates `CHANGELOG.md`
5. **Creates tag:** Annotated git tag (e.g., `v0.1.0`)
6. **Pushes release:** `git push origin main --tags`

---

## Usage Examples

### Example 1: Developing a New Feature

```bash
# 1. Create a feature branch
git checkout -b feat/user-profiles

# 2. Make changes...
git add .

# 3. Commit with Commitizen (guided)
just cz-commit
# → Prompts: Type? (select "feat")
# → Prompts: Scope? ("user")
# → Prompts: Description? ("Add user profile page")
# → Prompts: Body? (describe WHY)

# 4. Commit message created:
# feat(user): add user profile page
#
# Allows users to view and edit their profile information,
# including avatar upload and bio customization.

# 5. Open pull request
git push origin feat/user-profiles
```

### Example 2: Fixing a Bug

```bash
# 1. Create a fix branch
git checkout -b fix/null-pointer-error

# 2. Make changes...
git add .

# 3. Commit (using template)
git commit
# → .gitmessage template shown
# → Manual typing (or use `just cz-commit` for guidance)
# → Commitizen hook validates format

# 4. Example commit:
# fix: prevent null pointer in parser when input is empty

# 5. Open pull request
git push origin fix/null-pointer-error
```

### Example 3: Releasing v0.1.0

```bash
# 1. PR for feature is merged to main
# 2. All commits are now conventional (enforced by hook)

# 3. Start release
just release minor
# → Validates clean state
# → Runs all CI tests
# → Updates [project].version from 0.0.8 to 0.1.0
# → Generates CHANGELOG.md (groups commits by type)
# → Creates tag v0.1.0
# → Pushes to main with --tags

# 4. Verify tag was created
git describe --tags --abbrev=0    # Shows v0.1.0

# 5. Verify CHANGELOG.md
cat CHANGELOG.md
# ## v0.1.0 - 2026-04-15
# 
# ### ✨ Features
# * Add user profile page (user)
# * Add OAuth login flow (auth)
```

---

## Troubleshooting

### "Commitizen hook rejected my commit"

**Cause:** Commit message doesn't follow conventional commit format.

**Fix:** Use `just cz-commit` for guided creation, or manually fix the format:
```
<type>(<scope>): <short description>
```

Valid types: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `perf`

### "release task says 'Uncommitted changes detected'"

**Cause:** You have unstaged or untracked changes.

**Fix:**
```bash
git status                    # See what's uncommitted
git add .                     # Stage all changes
git commit                    # Commit (using Commitizen or template)
```

### "CHANGELOG.md not updating in release"

**Cause:** Commits aren't in conventional format, or tags don't match pattern.

**Fix:**
1. Verify recent commits: `git log --oneline -10`
2. Each should start with `feat:`, `fix:`, etc.
3. Verify tag pattern matches `v[0-9]*` (e.g., `v0.0.8`)

### ".gitmessage not showing in editor"

**Cause:** `git config commit.template` not set.

**Fix:**
```bash
just precommit-install   # Re-runs the config step
```

---

## Configuration Reference

### `.gitmessage`
- **Purpose:** Visual template for commit format
- **Location:** Repo root
- **Setup:** `just precommit-install` configures git to use it
- **Edit:** Safe to customize with additional hints

### `pyproject.toml` → `[tool.commitizen]`
```toml
[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "pep621"     # ← tells commitizen where version lives
tag_format = "v$version"        # ← tag format for git-cliff
```

### `.pre-commit-config.yaml`
```yaml
- repo: https://github.com/commitizen-tools/commitizen
  stages: [commit-msg]          # ← runs after you write message, before commit
  hooks:
    - id: commitizen
```

### `cliff.toml`
- **Purpose:** Changelog generation config
- **Key settings:**
  - `conventional_commits = true` — only parse compliant commits
  - `tag_pattern = "v[0-9]*"` — match version tags
  - Commit parsers define emoji groups (feat → ✨, fix → 🐛, etc.)

### `justfile` → `release` task
```bash
just release patch       # Calls all three tools in sequence
just release minor
just release major
```

---

## Semantic Versioning

Releases use **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **PATCH (0.0.x):** Bug fixes only — `just release patch`
- **MINOR (0.x.0):** New features + bug fixes — `just release minor`
- **MAJOR (x.0.0):** Breaking changes + everything — `just release major`

**Breaking change indicator:** Use `!` in commit message:
```
feat(api)!: redesign REST endpoints

BREAKING CHANGE: Old /api/users endpoint removed.
Use /api/v2/users instead.
```

---

## Summary

| Tool | Role | Trigger | Output |
|------|------|---------|--------|
| `.gitmessage` | Template reminder | `git commit` | Helpful format guide in editor |
| `commitizen` | Validation + version bump | `just cz-commit` or hook | Enforced format + version update |
| `cliff.toml` | Changelog generation | `just release` | CHANGELOG.md grouped by type |
| `justfile` release task | Orchestration | `just release patch/minor/major` | Full release workflow |

**Result:** Clean, machine-readable commit history → automated, well-organized changelogs → semantic versions.
