# AI Rules — Developer Guide

This directory contains the rules that inform any AI assistant (Claude Code, Cursor, etc.)
working in this project. Rules are plain Markdown files — readable by any tool without
conversion or special configuration.

## Structure

```
.claude/rules/
├── README.md              ← you are here
├── common/                # Universal principles — apply to all code
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
├── bash/                  # Shell script-specific
│   ├── coding-style.md
│   └── security.md
└── markdown/              # Markdown authoring conventions
    └── conventions.md
```

## Rule priority

Language-specific rules override common rules where they conflict.

## How to write a new rule

1. Choose `common/` for language-agnostic principles, or a language directory for
   language-specific ones.
2. Use lowercase kebab-case filenames: `coding-style.md`, `testing.md`, `patterns.md`.
3. If extending a common rule, start the file with:
   `> This file extends [common/xxx.md](../common/xxx.md) with <Language> specific content.`
4. Keep rules actionable (imperatives), concise (< 150 lines per file), and concrete
   (include good/bad examples).
5. Update this README when adding new directories.

## How AI tools consume these rules

| Tool | Mechanism |
|------|-----------|
| Claude Code | Reads `CLAUDE.md`, then files you reference or load via slash commands |
| Cursor | Reads `.cursor/rules/*.mdc`; symlink or copy relevant rules there if desired |
| Generic LLM | Pass rule file contents in system prompt or context window |
