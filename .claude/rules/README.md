# AI Rules — Developer Guide

This directory contains the rules that inform any AI assistant (Claude Code, Cursor, etc.)
working on this codebase. Rules are plain Markdown files — no tool-specific frontmatter or
format is required. Any AI that can read context from a directory will benefit from them.

## Structure

Rules are organised into a **common** layer plus **language/tool-specific** directories:

```
.claude/rules/
├── README.md              ← you are here
├── common/                # Universal principles — apply to all code in this repo
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── testing.md
│   ├── security.md
│   ├── development-workflow.md
│   └── code-review.md
├── python/                # Python-specific (extends common/)
│   ├── coding-style.md
│   ├── testing.md
│   ├── patterns.md
│   ├── security.md
│   └── hooks.md
├── jinja/                 # Jinja2 template-specific
│   ├── coding-style.md
│   └── testing.md
├── bash/                  # Shell script-specific
│   ├── coding-style.md
│   └── security.md
├── markdown/              # Markdown authoring conventions
│   └── conventions.md
├── yaml/                  # YAML file conventions (copier.yml, workflows, etc.)
│   └── conventions.md
└── copier/                # Copier template-specific rules (this repo only)
    └── template-conventions.md
```

## Rule priority

When language-specific rules and common rules conflict, **language-specific rules take
precedence** (specific overrides general). This mirrors CSS specificity and `.gitignore`
precedence.

- `common/` defines universal defaults.
- Language directories (`python/`, `jinja/`, `bash/`, …) override those defaults where
  language idioms differ.

## Dual-hierarchy reminder

This Copier meta-repo has **two parallel rule trees**:

```
.claude/rules/            ← active when DEVELOPING this template repo
template/.claude/rules/   ← rendered into every GENERATED project
```

When you add or modify a rule:
- Changes to `template/.claude/rules/` affect every project generated from this
  template going forward.
- Changes to the root `.claude/rules/` affect only this meta-repo.
- Many rules belong in **both** trees (e.g. Python coding style, security).
- Copier-specific rules (`copier/`) belong only in the root tree.
- Jinja rules belong only in the root tree (generated projects do not contain Jinja files).

## How to write a new rule

1. **Choose the right directory** — `common/` for language-agnostic principles,
   a language directory for language-specific ones. Create a new directory if a
   language or domain does not exist yet.

2. **File name** — use lowercase kebab-case matching the topic: `coding-style.md`,
   `testing.md`, `patterns.md`, `security.md`, `hooks.md`, `performance.md`.

3. **Opening line** — if the file extends a common counterpart, start with:
   ```
   > This file extends [common/xxx.md](../common/xxx.md) with <Language> specific content.
   ```

4. **Content guidelines**:
   - State rules as actionable imperatives ("Always …", "Never …", "Prefer …").
   - Use concrete code examples (correct and incorrect) wherever possible.
   - Keep each file under 150 lines; split into multiple files if a topic grows larger.
   - Do not repeat content already covered in the common layer — cross-reference instead.
   - Avoid tool-specific configuration syntax in rule prose; describe intent, not config.

5. **File patterns annotation** (optional but helpful) — add a YAML comment block at the
   top listing which glob patterns the rule applies to. AI tools that understand frontmatter
   can use this; tools that do not will simply skip the comment:
   ```yaml
   # applies-to: **/*.py, **/*.pyi
   ```

6. **Mirror to `template/.claude/rules/`** if the rule is relevant to generated projects.

7. **Update this README** when adding a new language directory or a new top-level file.

## How AI tools consume these rules

| Tool | Mechanism |
|------|-----------|
| Claude Code | Reads `CLAUDE.md` (project root), then any file you reference or load via slash commands |
| Cursor | Reads `.cursor/rules/*.mdc`; symlink or copy relevant rules there if desired |
| Generic LLM | Pass rule file contents in system prompt or context window |

Because rules are plain Markdown, they are readable by any tool without conversion.
