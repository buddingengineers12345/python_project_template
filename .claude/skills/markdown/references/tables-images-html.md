# Tables, images, and HTML

Covers: table syntax, alignment, best practices, when NOT to use tables; image
syntax, alt text, accessibility; HTML-in-Markdown rules.

**Primary source:** [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)

---

## Tables

### When to Use a Table

Use tables **only** when data is genuinely two-dimensional with:
- Relatively uniform data distribution across both dimensions
- Many parallel items each with distinct, comparable attributes
- Content that benefits from at-a-glance scanning

Tables are NOT appropriate when:
- Data could be a simple list (lists are easier to write and read)
- Several columns have the same value across rows
- Cells contain long prose
- There are very few rows relative to columns (or vice versa)
- The table has mostly empty cells

**Example of data that should be a list, not a table (from the Google style guide):**

```markdown
# ❌ Bad — this table has three specific problems
Fruit  | Metrics      | Grows on | Acute curvature    | Attributes          | Notes
------ | ------------ | -------- | ------------------ | ------------------- | -----
Apple  | Very popular | Trees    |                    | Juicy, Firm, Sweet  | Apples keep doctors away.
Banana | Very popular | Trees    | 16 degrees average | Convenient, Soft    | Most apes prefer mangoes.
```

The Google style guide names three specific table problems to watch for:

1. **Poor distribution** — Several columns don't differ across rows, and some cells
   are empty. This is usually a sign that the data may not benefit from tabular display.

2. **Unbalanced dimensions** — There are very few rows relative to columns (or very
   few columns relative to rows). When this ratio is unbalanced in either direction,
   a table becomes little more than an inflexible format for text.

3. **Rambling prose in cells** — Tables should tell a succinct story at a glance.
   Long sentences or paragraphs inside cells defeat the purpose of a table.

If any of these three problems apply, convert the table to a list with subheadings:

```markdown
# ✅ Good — list form is more readable here
## Fruits

Both are highly popular, sweet, and grow on trees.

### Apple
- Juicy, firm
- Apples keep doctors away.

### Banana
- Convenient, soft
- 16 degrees average acute curvature.
- Contrary to popular belief, most apes prefer mangoes.
```

### Table Syntax

Use pipes `|` to separate columns and hyphens `---` to create the header separator:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell     | Cell     | Cell     |
| Cell     | Cell     | Cell     |
```

The outer pipes on each row are optional but strongly recommended for consistency:

```markdown
Column 1 | Column 2    ← harder to read without outer pipes
-------- | --------
Cell     | Cell
```

### Column Alignment

Control alignment with colons in the separator row:

```markdown
| Left-aligned | Centred | Right-aligned |
|:-------------|:-------:|--------------:|
| Default      | Centred | Numbers       |
| Text         |  Text   |         12.50 |
| More text    |  More   |        100.00 |
```

- `:---` — left align (default if no colon)
- `:---:` — centre align
- `---:` — right align (use for numeric columns)

### Keeping Tables Readable

- **Keep cells short** — Markdown offers no line-break within table cells.
- **Use reference links** for any URL inside a cell (see `03-code-and-links.md`).
- **Align pipe characters vertically** in source for readability:

  ```markdown
  # ✅ Well-aligned source
  | Transport | Favored by   | Advantage          |
  |-----------|:-------------|:-------------------|
  | Bicycle   | Commuters    | Zero emissions     |
  | Train     | Travellers   | High capacity      |
  | Bus       | City riders  | Frequent stops     |
  ```

- Cell widths in source don't need to match — Markdown renders them uniformly regardless:

  ```markdown
  | Col | Col |
  | --- | --- |
  | Short | A longer cell that still renders fine |
  ```

### Inline Formatting in Tables

Bold, italic, inline code, and links all work inside table cells:

```markdown
| Command        | Description                       |
|----------------|-----------------------------------|
| `git status`   | List **new or modified** files    |
| `git diff`     | Show *unstaged* file differences  |
| `git commit`   | [Commit staged changes][git-docs] |

[git-docs]: https://git-scm.com/docs/git-commit
```

### Large Tables

If a table is unavoidably wide, it is one of the few places where exceeding
the 80-character line limit is acceptable. Even so, use reference links to
minimise cell content.

---

## Images

### Syntax

```markdown
![Alt text describing the image](path/to/image.png)

<!-- With an optional title tooltip on hover -->
![Dashboard screenshot showing user statistics](images/dashboard.png "Main dashboard")

<!-- Reference-style image (for long paths or reuse) -->
![Alt text][dashboard]

[dashboard]: images/dashboard.png "Main dashboard"
```

### Clickable Images

Wrap an image in a link to make it clickable:

```markdown
[![Django logo — click to open documentation](img/django.png)](https://docs.djangoproject.com/)
```

### Alt Text Rules

Alt text is **mandatory for all meaningful images**. It is used by:
- Screen readers for visually impaired users
- Browsers when the image fails to load
- Search engines for image indexing

**Writing good alt text:**

```markdown
# ✅ Good — describes what the image shows and why it matters
![Bar chart showing Q4 revenue up 23% compared to Q3](images/q4-revenue.png)
![Screenshot of the Settings > Privacy panel with Location toggle highlighted](images/privacy-settings.png)
![Flowchart: user request → auth check → cache lookup → database → response](images/request-flow.png)

# ❌ Bad — uninformative
![image](images/q4-revenue.png)
![chart](images/chart1.png)
![screenshot](images/screen.png)
```

Guidelines for alt text:
- Describe **what the image shows** and **why it is relevant** in that context.
- Keep alt text concise — 1–2 sentences maximum.
- Do not start with "Image of…" or "Picture of…" (screen readers already announce it's an image).
- For **purely decorative** images (dividers, backgrounds), use empty alt text: `![](...)`
  so screen readers skip them.
- For **complex diagrams** (architecture diagrams, flowcharts), provide a caption or
  prose description in the surrounding text in addition to alt text.
- For **screenshots of UI**, describe the key element and what state it is in.

### Image Storage

- Store images in a dedicated `images/` or `assets/` subdirectory adjacent to the doc.
- For large documentation sites, use a top-level `assets/` or `static/` folder.
- **Prefer SVG** for diagrams and icons (scales without blurring, small file size).
- **Use PNG** for screenshots (lossless, renders text crisply).
- **Use JPEG** for photographs (efficient compression for photographic content).
- Use descriptive file names: `auth-flow-diagram.svg`, not `img1.png`.

### When to Use Images

- When it is genuinely **easier to show than to describe** (UI navigation, visual layouts).
- Architecture diagrams, flowcharts, and data visualisations that would be verbose as text.
- **Use sparingly** — excessive images distract, slow page load, and are inaccessible
  without good alt text. When in doubt, write prose.

---

## HTML in Markdown

### Core Rule: Strongly Prefer Markdown

Every HTML tag in a Markdown file reduces portability and readability. Some renderers
(e.g., Gitiles) ignore HTML entirely. Markdown meets almost all formatting needs
without HTML.

> If you find yourself reaching for HTML, first ask: do I really need this?
> Can I restructure the content to express it in plain Markdown?

### Acceptable HTML Uses (as a last resort)

These are the narrow cases where HTML is permitted:

```markdown
<!-- Hard line break when backslash isn't supported -->
Line one<br>Line two

<!-- Subscript / superscript (when ~ and ^ aren't supported) -->
H<sub>2</sub>O
E = mc<sup>2</sup>

<!-- Collapsible section (GFM, GitHub only) -->
<details>
<summary>Click to expand</summary>

Collapsed content goes here. Full Markdown works inside.

</details>

<!-- Keyboard key styling -->
Press <kbd>Ctrl</kbd> + <kbd>C</kbd> to copy.

<!-- Inline colour — only on platforms that render it (e.g., GitHub) -->
<span style="color:red">Warning text</span>
```

### What HTML Must Never Be Used For

- Page layout or multi-column layouts
- Font size, font family, or colour styling (except `<span>` for one-off critical warnings)
- `<b>` or `<i>` instead of `**` and `*`
- `<h1>`–`<h6>` instead of `#` syntax
- `<ul>`, `<ol>`, `<li>` instead of Markdown list syntax
- `<a href>` instead of Markdown link syntax
- `<img>` instead of `![]()` syntax
- `<table>` instead of pipe-table syntax (except when the table is genuinely too complex)

### HTML Commenting

HTML comments are invisible in rendered output and valid in all processors:

```markdown
<!-- TODO: add diagram here -->
<!-- This section needs review by the security team -->
```

Use sparingly for author notes, reminders, or section markers not meant for readers.
