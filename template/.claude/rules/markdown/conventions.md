# Markdown Conventions

# applies-to: **/*.md

## File placement rule

Any Markdown file created as part of a workflow, analysis, or investigation output
**must be placed inside the `docs/` folder**.

**Allowed exceptions** (may be placed at the repository root or any location):
- `README.md`
- `CLAUDE.md`
- `.claude/rules/**/*.md` (rules documentation)
- `.claude/hooks/README.md` (hooks documentation)
- `.github/**/*.md` (GitHub community files)

Do **not** create free-standing files such as `ANALYSIS.md`, `NOTES.md`, or
`LOGGING_ANALYSIS.md` at the repository root or inside `src/`, `tests/`, or `scripts/`.

This rule is enforced by:
- `pre-write-doc-file-warning.sh` (PreToolUse: blocks writing `.md` outside allowed locations)
- `post-edit-markdown.sh` (PostToolUse: warns if an existing `.md` is edited in the wrong place)

## Headings

- Use ATX headings (`#`, `##`, `###`), not Setext underlines (`===`, `---`).
- One top-level heading (`# Title`) per file.
- Do not skip heading levels (e.g. `##` → `####` without a `###` in between).
- Headings should be sentence-case (capitalise first word only) unless the subject
  is a proper noun or acronym.

## Line length and wrapping

- Wrap prose at 100 characters for readability in editors and diffs.
- Do not wrap code blocks, tables, or long URLs.

## Code blocks

- Always specify the language for fenced code blocks:
  ```
  \```python
  \```bash
  \```yaml
  \```
- Use inline code (backticks) for: file names, directory names, command names,
  variable names, and short code snippets within prose.

## Lists

- Use `-` for unordered lists (not `*` or `+`).
- Use `1.` for all items in ordered lists (the renderer handles numbering).
- Nest lists with 2-space or 4-space indentation consistently within a file.

## Tables

- Align columns with spaces for readability in source (optional but preferred).
- Include a header row and a separator row.
- Keep tables narrow enough to read without horizontal scrolling.

## Links

- Use reference-style links for URLs that appear more than once.
- Use relative links for internal project files:
  `[CLAUDE.md](../CLAUDE.md)` not `https://github.com/…/CLAUDE.md`.
- Do not embed bare URLs in prose; always use `[descriptive text](url)`.

## CLAUDE.md maintenance

`CLAUDE.md` is the primary context document for AI assistants. Keep it up to date:
- Update when you add or change slash commands, hooks, tooling, or project structure.
- Do not duplicate content already in the rules files — cross-reference with a link.
