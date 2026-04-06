# Markdown Conventions

# applies-to: **/*.md

## File placement rule

Any Markdown file created as part of a workflow, analysis, or investigation output
**must be placed inside the `docs/` folder**.

**Allowed exceptions** (may be placed anywhere):
- `README.md`
- `CLAUDE.md`
- `.claude/rules/**/*.md`
- `.github/**/*.md`

Do **not** create free-standing files such as `ANALYSIS.md` or `NOTES.md` at the
repository root or inside `src/`, `tests/`, or `scripts/`.

This is enforced by `.claude/hooks/post-edit-markdown.sh`.

## Headings

- ATX headings (`#`, `##`, `###`), not Setext underlines.
- One `# Title` per file.
- Do not skip heading levels.
- Sentence-case headings (capitalise first word and proper nouns only).

## Code blocks

Always specify the language:
```
\```python
\```bash
\```yaml
```

## Lists

- Use `-` for unordered lists.
- Use `1.` for all ordered list items.

## Links

- Relative links for internal files: `[CLAUDE.md](../CLAUDE.md)`.
- Descriptive link text: `[setup guide](./setup.md)`, not `[click here](./setup.md)`.

## CLAUDE.md maintenance

`CLAUDE.md` is the primary context document for AI assistants. Keep it up to date:
- Update when you add or change slash commands, hooks, tooling, or project structure.
- Do not duplicate content already in the rules files — cross-reference with a link.
