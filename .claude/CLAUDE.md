# .claude/ — Claude Code Configuration (Meta-Repo)

This directory contains all Claude Code configuration for **this Copier template repository**
(the meta-repo). It is active when you are developing the template itself.

> [!IMPORTANT]
> **Dual-hierarchy:** This repo has two parallel `.claude/` trees:
> - `.claude/` ← active when **developing this template** (you are here)
> - `template/.claude/` ← rendered into every **generated project**
>
> When adding or modifying hooks, commands, or rules, decide which tree (or both) the
> change belongs in. See `rules/README.md` for the split rules.

## Directory layout

```
.claude/
├── CLAUDE.md          ← this file
├── settings.json      ← hook registrations and permission allow/deny lists
├── hooks/             ← shell hook scripts
│   ├── README.md      ← full hook developer guide (events, matchers, exit codes, templates)
│   └── *.sh           ← individual hook scripts
├── commands/          ← slash command prompt files
│   └── *.md           ← one file per slash command
└── rules/             ← AI coding rules
    ├── README.md      ← rule developer guide (structure, priority, dual-hierarchy)
    ├── common/        ← language-agnostic rules
    ├── python/        ← Python-specific rules
    ├── jinja/         ← Jinja2 rules (meta-repo only)
    ├── bash/          ← Bash rules
    ├── markdown/      ← Markdown placement and authoring rules
    ├── yaml/          ← YAML conventions for copier.yml + workflows (meta-repo only)
    └── copier/        ← Copier template conventions (meta-repo only)
        └── template-conventions.md
```

## `settings.json` — permissions and hooks

The `settings.json` file:
- **`permissions.allow`** — Bash commands Claude is allowed to run without user approval
  (`just:*`, `uv:*`, `copier:*`, standard git read commands, `python3:*`).
- **`permissions.deny`** — Bash commands that are always blocked (`git push`, `uv publish`,
  `git commit --no-verify`, `git push --force`).
- **`hooks`** — lifecycle hook registrations (see hooks/ section below).

## hooks/

Shell scripts that integrate with Claude Code's lifecycle events. See `hooks/README.md`
for the full developer guide.

### Hooks registered in this tree

| Script | Event | Matcher | Purpose |
|---|---|---|---|
| `session-start-bootstrap.sh` | SessionStart | * | Toolchain status + previous session snapshot |
| `pre-bash-block-no-verify.sh` | PreToolUse | Bash | Block `--no-verify` in git commands |
| `pre-bash-git-push-reminder.sh` | PreToolUse | Bash | Warn to run `just review` before push |
| `pre-bash-commit-quality.sh` | PreToolUse | Bash | Scan staged `.py` files for secrets/debug markers |
| `pre-config-protection.sh` | PreToolUse | Write\|Edit\|MultiEdit | Block weakening ruff/pyright config edits |
| `pre-protect-uv-lock.sh` | PreToolUse | Write\|Edit | Block direct edits to `uv.lock` |
| `pre-write-src-test-reminder.sh` | PreToolUse | Write\|Edit | Warn if test file missing for new source module |
| `pre-write-doc-file-warning.sh` | PreToolUse | Write | Block `.md` files written outside `docs/` |
| `pre-write-jinja-syntax.sh` | PreToolUse | Write | Validate Jinja2 syntax before writing `.jinja` files |
| `pre-suggest-compact.sh` | PreToolUse | Edit\|Write | Suggest `/compact` every ~50 operations |
| `pre-compact-save-state.sh` | PreCompact | * | Snapshot git state before context compaction |
| `post-edit-python.sh` | PostToolUse | Edit\|Write | ruff + basedpyright after every `.py` edit |
| `post-edit-jinja.sh` | PostToolUse | Edit\|Write | Jinja2 syntax check after every `.jinja` edit |
| `post-edit-markdown.sh` | PostToolUse | Edit | Warn if existing `.md` edited outside `docs/` |
| `post-edit-copier-migration.sh` | PostToolUse | Edit\|Write | Migration checklist after `copier.yml` edits |
| `post-edit-template-mirror.sh` | PostToolUse | Edit\|Write | Remind to mirror `template/.claude/` ↔ root |
| `post-bash-pr-created.sh` | PostToolUse | Bash | Log PR URL after `gh pr create` |
| `stop-session-end.sh` | Stop | * | Persist session state JSON |
| `stop-evaluate-session.sh` | Stop | * | Extract reusable patterns from transcript |
| `stop-cost-tracker.sh` | Stop | * | Accumulate session token costs |
| `stop-desktop-notify.sh` | Stop | * | macOS desktop notification on completion |

### Key differences vs `template/.claude/hooks/`

The template hooks are a **subset** — generated projects do not need:
- `SessionStart` hooks (no session state tracking)
- `pre-write-doc-file-warning.sh` (no doc-file restriction)
- `pre-write-jinja-syntax.sh` (no Jinja files in generated projects)
- `pre-suggest-compact.sh`
- `pre-compact-save-state.sh`
- `post-edit-jinja.sh`
- `post-edit-copier-migration.sh`
- `post-edit-template-mirror.sh`
- `post-bash-pr-created.sh`
- All `stop-*` hooks

## commands/

One Markdown file per slash command. Claude Code reads these files when you invoke
`/command-name`. The filename (without `.md`) is the slash command name.

| Command | Purpose |
|---|---|
| `/review` | Full pre-merge checklist (lint + types + docstrings + coverage + symbol scan) |
| `/coverage` | Run coverage, identify gaps, write missing tests |
| `/docs-check` | Audit and repair Google-style docstrings |
| `/standards` | Consolidated pass/fail report — "ready to merge?" gate |
| `/update-claude-md` | Sync CLAUDE.md against pyproject.toml + justfile to prevent drift |
| `/generate` | Render the template into `/tmp/test-output` and inspect it |
| `/release` | Orchestrate a new release: CI → version bump → tag → push |
| `/validate-release` | Verify release prerequisites (clean tree, CI passing, correct tag) |
| `/ci` | Run `just ci` and report results |
| `/test` | Run `just test` and summarise failures |
| `/dependency-check` | Validate `uv.lock` is committed, in sync, and not stale |

## rules/

Plain Markdown files documenting coding standards. See `rules/README.md` for the
full guide on rule priority, the dual-hierarchy, and how to write new rules.

### Rule directories in this tree (meta-repo)

| Directory | Scope |
|---|---|
| `common/` | Language-agnostic: coding-style, git-workflow, testing, security, development-workflow, code-review |
| `python/` | Python: coding-style, testing, patterns, security, hooks |
| `jinja/` | Jinja2: coding-style, testing — **meta-repo only** |
| `bash/` | Bash: coding-style, security |
| `markdown/` | Markdown placement and authoring conventions |
| `yaml/` | YAML conventions for `copier.yml` and GitHub Actions — **meta-repo only** |
| `copier/` | Copier template conventions — **meta-repo only** |

Rules in `jinja/`, `yaml/`, and `copier/` are **not** propagated to generated projects.

## Adding new hooks, commands, or rules

1. **Hook** — write the script in `hooks/`, register it in `settings.json`, test with a
   sample JSON payload. Mirror to `template/.claude/hooks/` if relevant for generated projects.
2. **Command** — create a `.md` file in `commands/`. Mirror as `.md.jinja` in
   `template/.claude/commands/` if the command is useful in generated projects.
3. **Rule** — create a `.md` file in the appropriate `rules/` subdirectory. Mirror to
   `template/.claude/rules/` if the rule applies to generated projects too.
