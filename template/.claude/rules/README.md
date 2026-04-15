# AI Rules — Developer Guide

This directory contains the rules that inform any AI assistant (Claude Code, Cursor, etc.)
working in this project. Rules are plain Markdown files — readable by any tool without
conversion or special configuration.

The format, scoping, and organisation conventions below are the canonical reference; they
match the `maintain-rules` skill. When adding or editing rules, follow this document.

## Philosophy — rules vs skills

Rules and skills serve strict, non-overlapping roles:

- **Rules** (this directory) are **short, always-on, non-negotiable**. They hold hard
  constraints ("never do X", "always use Y"), project invariants, and guardrails. Target
  **5–7 lines per file**. If it's longer, it belongs in a skill.
- **Skills** (`.claude/skills/`) are **rich and invoked when relevant**. They hold
  patterns, examples, step-by-step how-tos, templates, and edge cases.

Before writing a new rule, check whether a skill already covers the content. If yes,
delete or shrink the rule — do not duplicate.

## Structure

```
.claude/rules/
├── README.md              ← you are here
├── common/                # Universal hard constraints — apply to all code
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── testing.md
│   ├── security.md
│   └── hooks.md
├── python/                # Python-specific (extends common/)
├── bash/                  # Shell script-specific
├── yaml/                  # YAML authoring conventions
├── markdown/              # Markdown authoring conventions
└── copier/                # Copier template-repo conventions
```

Detailed how-to content that previously lived here has moved to skills:

| Former rule | Now lives in |
|---|---|
| `common/development-workflow.md` | `skills/sdlc-workflow/`, `skills/tdd-workflow/` |
| `common/code-review.md` | `skills/python-code-reviewer/` |
| `python/security.md` | `skills/security/` |
| `python/patterns.md` | `skills/python-code-quality/` |
| `jinja/coding-style.md`, `jinja/testing.md` | `skills/jinja-guide/` |

## Rule priority

Language-specific rules override common rules where they conflict.

## Standard rule format

Every rule file follows one of two shapes.

### Unconditional rule — `common/*.md`

Loads on every session. No frontmatter.

```markdown
# [Topic Name]

- Concrete, verifiable instruction.
- Another specific instruction.
```

### Path-scoped rule — language/topic directories

Loads only when Claude touches files matching the globs. Uses YAML frontmatter with a
`paths:` key.

```markdown
---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# [Topic Name]

- Rule 1
- Rule 2
```

Notes:
- `paths:` values are glob patterns, always double-quoted.
- Do **not** use the legacy `# applies-to:` comment syntax. Always use YAML frontmatter.

## Authoring rules — checklist

Before committing a rule, verify:

1. **Location** — `common/` for language-agnostic, language directory otherwise.
2. **Filename** — lowercase kebab-case (`coding-style.md`, `testing.md`).
3. **Frontmatter** — present with `paths:` for path-scoped; absent for unconditional.
4. **Title** — single `#` heading matching the topic.
5. **Content** — hard constraints only; imperatives; concrete.
6. **Size** — **5–7 lines per file** (excluding frontmatter and title). Longer content goes in a skill.
7. **No duplication** — if a skill already covers it, remove the rule.
8. **README** — update this file when adding a new directory.

## How AI tools consume these rules

| Tool | Mechanism |
|------|-----------|
| Claude Code | Loads `CLAUDE.md` plus every `.claude/rules/**/*.md`; path-scoped files activate when matching files are touched |
| Cursor | Reads `.cursor/rules/*.mdc`; symlink or copy relevant rules there if desired |
| Generic LLM | Pass rule file contents in the system prompt or context window |

## Related skill

The `maintain-rules` skill (at `.claude/skills/maintain-rules/`) contains the full
reference for authoring, auditing, and organising these files.
