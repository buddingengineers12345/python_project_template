---
paths:
  - "**/*.md"
  - "**/*.mdx"
---

# Markdown Conventions

- Output files belong in `docs/`. Exceptions: `README.md`, `CLAUDE.md`, `.claude/**/*.md`, `.github/**/*.md`.
- Never create free-standing files (e.g. `ANALYSIS.md`, `NOTES.md`) at the repo root, `src/`, `tests/`, or `scripts/`.
- Use ATX headings (`#`), sentence-case, one `# Title` per file; `-` for unordered lists.
- Wrap prose at 100 characters; always specify a language on fenced code blocks.
