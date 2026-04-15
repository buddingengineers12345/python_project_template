# Formatting syntax

Covers: emphasis (bold, italic, strikethrough), lists (ordered, unordered, nested,
task), blockquotes, horizontal rules, and line-break handling.

**Primary sources:** [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html),
[Markdown Guide — Basic Syntax](https://www.markdownguide.org/basic-syntax/)

---

## Emphasis

### Bold

Use `**double asterisks**` for bold (strong importance):

```markdown
**bold text**
```

Use bold for: critical terms on first introduction, UI element labels, warnings,
key takeaways, and field/parameter names in documentation.

### Italic

Use `*single asterisks*` for italic (stress emphasis):

```markdown
*italic text*
```

Use italic for: introducing new terms, titles of books/products, technical terms
used in a non-technical context, and light stress.

### Bold + Italic

```markdown
***bold and italic***
```

Use only when both strong importance and stress emphasis are simultaneously needed.

### Strikethrough

```markdown
~~strikethrough~~
```

Use for: text that is a deliberate error or has been superseded, deprecated
features, or crossed-off items in prose.

```markdown
~~Old feature~~ replaced by new feature
Price: ~~$99~~ $79
```

### Rules for Emphasis

- **Always use asterisks**, not underscores. Underscores behave inconsistently inside
  words across parsers (e.g., `some_variable_name` may render incorrectly):

  ```markdown
  # ✅ Use asterisks
  *italic*   **bold**   ***bold italic***

  # ❌ Avoid underscores (unreliable mid-word)
  _italic_   __bold__
  ```

- **Never bold or italicise entire paragraphs.** Overuse destroys emphasis.
- Use emphasis **sparingly** — every additional use dilutes the impact of all others.
- Do not use emphasis for purely decorative formatting.

---

## Lists

### When to Use Lists

Use lists for genuinely enumerable or sequential items. Do **not** fragment flowing
prose into bullets — write prose instead. If all list items are a single short
phrase, a list is appropriate. If items need full sentences of context, consider
prose with subheadings.

### Unordered Lists

```markdown
- First item
- Second item
- Third item
```

Use `-` consistently throughout a file (do not mix `-`, `*`, and `+`).

For single-line, non-nested lists, one space after the marker suffices:

```markdown
- Foo
- Bar
- Baz
```

For wrapped text, use a 4-space total indent (3 spaces after `-`):

```markdown
-   Foo, which is a somewhat longer item that may wrap
    to a second line and needs the 4-space indent.
-   Bar.
```

### Ordered Lists

For **short, stable** lists, use explicit sequential numbers (more readable in source):

```markdown
1. First step
2. Second step
3. Third step
```

For **long or frequently changing** lists, use **lazy numbering** — Markdown renumbers
automatically, so you never have to renumber after inserting or removing an item:

```markdown
1. First item
1. Second item
1. Third item
1. Fourth item
```

For ordered list items with wrapped text, use 2 spaces after the number:

```markdown
1.  First item — text starts at column 5 (4-space total indent).
    Wrapped text also aligns here.
2.  Second item.
```

### Nested Lists

Use a **4-space indent** for both bullet and numbered nested lists:

```markdown
1.  Parent item (text at 4-space indent).
    Wrapped text aligns here.
    1.  Nested numbered item.
        Wrapped text in nested list needs an 8-space indent.
    2.  Another nested numbered item.
2.  Back to parent level.

-   Bullet parent (text at 4-space indent).
    -   Nested bullet.
    -   Another nested bullet.
-   Back to parent level.
```

**Do not mix inconsistent indentation** — it produces unpredictable rendering:

```markdown
# ❌ Messy — avoid
* One space,
with no indent for wrapped text.
     1. Irregular nesting.
```

### Task Lists (GFM)

Supported on GitHub, GitLab, and most modern Markdown renderers:

```markdown
- [x] Complete project setup
- [x] Write documentation
- [ ] Add unit tests
- [ ] Deploy to production
```

Nested task lists:

```markdown
- [ ] Top-level task
  - [x] Sub-task one
  - [ ] Sub-task two
```

---

## Blockquotes

Use `>` to call out quoted text, important notes, or external attributions:

```markdown
> This is a blockquote. It can span multiple lines.
> All lines should be prefixed with `>`.

> First paragraph of the quote.
>
> Second paragraph of the quote (blank `>` line separates paragraphs).
```

### Nested Blockquotes

```markdown
> Outer quote.
>
> > Nested quote inside the outer quote.
>
> Back to the outer quote.
```

### Blockquotes with Markdown Inside

Blockquotes can contain any Markdown:

```markdown
> **Note:** This feature requires Node.js 18 or higher.
>
> - Supported platforms: Linux, macOS, Windows
> - Minimum RAM: 512 MB
```

### Blockquote Usage Rules

- Use to highlight important side-notes, warnings, and external quotations.
- Use **moderately** — overuse dilutes their visual effect.
- Do not use for generic indentation or visual styling.
- For formal callouts (Notes, Warnings, Tips), prefer GFM alert syntax when available
  (see `05-extended-syntax.md`).

---

## Horizontal Rules

A horizontal rule is three or more hyphens, asterisks, or underscores on a line alone:

```markdown
---
***
___
```

### Usage Rules

- Use `---` as the consistent choice (matches YAML front matter delimiters; distinctive).
- Use **sparingly** — only at **major structural transitions** (e.g., between an
  introduction block and the main body).
- Do **not** use to separate every section — headings are the correct separator.
- Ensure a blank line before and after to avoid the `---` being parsed as a Setext H2.

---

## Highlight, Subscript, Superscript

These are extended syntax — not supported by all parsers. Always verify support
before using them.

### Highlight

```markdown
I need to highlight ==these very important words==.
```

### Subscript

```markdown
H~2~O        <!-- water -->
CO~2~        <!-- carbon dioxide -->
```

### Superscript

```markdown
X^2^         <!-- x squared -->
E = mc^2^
```

### Fallback HTML (when the above are unsupported)

```markdown
H<sub>2</sub>O
X<sup>2</sup>
```

---

## Escaping Characters

To display a literal Markdown character that would otherwise be interpreted as syntax,
prefix it with a backslash `\`:

```markdown
\*Not italic\*
\# Not a heading
\[Not a link\]
\`Not code\`
\> Not a blockquote
```

Characters that can be escaped:
`\` `` ` `` `*` `_` `{}` `[]` `()` `#` `+` `-` `.` `!` `|`

---

## Inline HTML

Plain Markdown handles nearly all formatting needs. Use HTML only as a last resort.
See `04-tables-images-html.md` for the complete rules on HTML in Markdown.
