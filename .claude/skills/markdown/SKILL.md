---
name: markdown
description: >-
  Expert guidance for writing, editing, managing, and handling Markdown (.md) files
  to a professional standard. Use this skill whenever the user wants to: create or
  write a new Markdown file, edit or improve an existing .md file, review Markdown
  for style/consistency, convert content into well-structured Markdown, build README
  files, technical docs, changelogs, wikis, or any documentation in .md format.
  Also trigger for requests involving front matter/metadata, table formatting, code
  blocks, link hygiene, accessibility in Markdown, GitHub-flavored Markdown (GFM),
  or best practices for Markdown documentation systems. If the user mentions .md,
  README, CHANGELOG, docs, or wiki, use this skill.
---

# Markdown Skill

A comprehensive skill for producing, editing, and managing Markdown files that are
readable, portable, accessible, and maintainable over time.

## Quick reference: where to go deeper

| Topic                              | Reference file                                                                |
|------------------------------------|-------------------------------------------------------------------------------|
| Document structure and front matter | [references/document-structure.md](references/document-structure.md)         |
| Formatting syntax (emphasis, lists) | [references/formatting-syntax.md](references/formatting-syntax.md)           |
| Code blocks and links              | [references/code-and-links.md](references/code-and-links.md)                 |
| Tables, images, and HTML           | [references/tables-images-html.md](references/tables-images-html.md)         |
| Extended syntax (GFM, callouts)    | [references/extended-syntax.md](references/extended-syntax.md)               |
| File management and doc systems    | [references/file-management.md](references/file-management.md)               |
| Anti-patterns and cheat sheet      | [references/anti-patterns-cheatsheet.md](references/anti-patterns-cheatsheet.md) |

Read the relevant reference file before working on a specific area. For a new README,
skim `document-structure.md` first. For table formatting or GFM features, check the
corresponding reference.

---

## Primary references

This skill is grounded in the **Google Markdown Style Guide** and extended with best
practices from CommonMark, Markdown Guide, and the GitHub Flavored Markdown Spec.

---

## Core philosophy

Three goals govern every Markdown file:

1. **Source text is readable and portable** — raw `.md` source should be legible as
   plain text without rendering.
2. **The corpus is maintainable over time** — consistent conventions let any author
   pick up where another left off.
3. **Syntax is simple and memorable** — favour standard Markdown over HTML hacks or
   exotic extensions.

---

## Essential rules

### Document structure

Every well-formed Markdown document follows this skeleton:

```markdown
# Document Title

Short introduction (1-3 sentences). Explain what this document is and who it is for.

## First Topic

Content.

## Second Topic

Content.

## See Also

- [Link to related resource](https://example.com)
```

- Exactly one `# H1` per document — the page title.
- 1-3 sentence introduction before any sections.
- Start subsequent headings at `## H2`; never skip levels.
- Sentence-case headings (capitalise first word and proper nouns only).

### Headings

Use ATX-style (`#`, `##`, `###`). Never use Setext (underline) style. Add blank lines
before and after every heading. Give headings unique, descriptive names to avoid anchor
collisions.

### Line length

80-character limit for body text. Exceptions: links, table cells, headings, and code
blocks. Use a blank line to separate paragraphs — do not rely on trailing whitespace.

### Emphasis

- `**bold**` for critical terms, UI labels, and warnings.
- `*italic*` for introducing new terms and light emphasis.
- Never bold or italicise entire paragraphs — overuse kills emphasis.
- Use `*asterisks*` not `_underscores_` for mid-word emphasis.

### Lists

- Use `-` consistently for unordered lists.
- Use explicit numbers (`1.`, `2.`, `3.`) for short stable lists.
- Use lazy numbering (`1.`, `1.`, `1.`) for long or frequently changing lists.
- 4-space indent for wrapped text and nested lists.

### Code

Always use fenced blocks with a language tag. Never use 4-space indented blocks:

````markdown
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```
````

Use backticks for inline code: commands, function names, file names, paths.

### Links

Write the sentence naturally, then wrap the most descriptive phrase as the link text.
Never use "click here" or "here" as link text. Use relative paths for internal links:

```markdown
See the [contributing guide](docs/CONTRIBUTING.md) for details.
```

### Tables

Use tables only when data is genuinely two-dimensional. Keep cells short. Use
reference links for URLs in table cells. If a table has only 1-2 columns, prefer a
list instead.

### Images

Always write descriptive alt text. Store images in a dedicated `images/` or `assets/`
directory. Prefer SVG for diagrams and PNG for screenshots.

### HTML

Strongly prefer plain Markdown over HTML. Acceptable uses: `<br>`, `<details>`,
`<sub>`/`<sup>` — only as a last resort.

### Accessibility

- Descriptive alt text on every meaningful image.
- Meaningful link text (not "here" or bare URLs).
- Logical heading hierarchy for assistive navigation.
- Semantic emphasis (`**important**`) rather than formatting for decoration.

---

## Common anti-patterns

| Anti-pattern                     | Fix                                    |
|----------------------------------|----------------------------------------|
| Multiple H1s                     | Keep exactly one — the page title       |
| Skipping heading levels          | Follow strict hierarchy                 |
| `[click here](url)`             | Write descriptive link text             |
| 4-space indented code blocks     | Use fenced blocks with language tag     |
| Mixing `*` and `-` for bullets   | Pick one style per file                 |
| HTML `<b>`, `<i>` tags           | Use `**` and `*`                        |
| Tables for simple lists          | Use a list instead                      |
| Empty alt text on images         | Always write descriptive alt text       |

---

## See Also

- [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)
- [CommonMark Specification](https://commonmark.org/)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Flavored Markdown Spec](https://github.github.com/gfm/)
