# AI Rules and Standards

## AI rules directory

Detailed coding standards are documented as plain Markdown files under `.claude/rules/`
and are readable by any AI assistant (Claude Code, Cursor, or any LLM):

```
.claude/rules/
├── README.md            ← how to read and write rules; dual-hierarchy explained
├── common/              ← language-agnostic: coding-style, git-workflow, testing, security, hooks
├── python/              ← Python: coding-style, testing, hooks
├── bash/                ← Bash: coding-style, security
├── markdown/            ← placement rules, authoring conventions
├── yaml/                ← YAML formatting for copier.yml and workflows (meta-repo only)
└── copier/              ← Copier template conventions (meta-repo only)
    └── template-conventions.md
```

Jinja2 and broader Copier how-tos live under `.claude/skills/` (for example `jinja-guide/`), not
as a separate `rules/jinja/` tree.

The `template/.claude/rules/` tree mirrors this structure for generated projects
(common, python, bash, markdown — no Jinja, yaml, or Copier-specific rules).
