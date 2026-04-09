# Document structure

Covers: document layout, front matter / metadata, headings, table of contents,
paragraphs, spacing, and capitalization.

**Primary source:** [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)

---

## The Better/Best Rule (Documentation Review Culture)

The standards for a documentation review are different from code reviews. The
Google Markdown Style Guide defines the "Better/Best Rule" — fast iteration
produces better long-term quality than perfection on every change.

> **"A small improvement shipped is better than a perfect doc never merged."**

### As a reviewer

1. When reasonable, **LGTM immediately** and trust that comments will be fixed appropriately.
2. **Prefer to suggest an alternative** rather than leaving a vague comment.
3. For substantial changes, **start your own follow-up CL** instead of blocking the author. Especially avoid comments of the form "You should *also*…".
4. On rare occasions, **hold up submission only if the CL actually makes the docs worse**. It's okay to ask the author to revert.

### As an author

1. **Avoid wasting cycles with trivial argument.** Capitulate early and move on.
2. **Cite the Better/Best Rule** as often as needed when reviewers ask for more than is necessary.

Fast iteration is your friend. To get long-term improvement, **authors must stay
productive** when making short-term improvements. Set lower standards for each
change so that more such changes can happen.

---

## Standard Document Layout

Every well-formed Markdown document follows this skeleton:

```markdown
# Document Title

Short introduction (1–3 sentences). What is this? Who is it for?

[TOC]

## First Major Section

Content.

## Second Major Section

Content.

## See Also

- [Related resource](https://example.com)
- [Another link](https://example.com)
```

### Layout Rules

| Element | Rule |
|---|---|
| `# H1` | Exactly **one** per document — the page title |
| Introduction | 1–3 sentences high-level overview, before any TOC or section |
| `[TOC]` | After introduction, before first H2 (accessibility: screen readers read it in DOM order) |
| Subsequent headings | Start at H2; never skip levels (H2 → H4 is invalid) |
| `## See Also` | Last section; collect miscellaneous outbound links here |
| Author field | Optional, below the title — revision history usually suffices |

> **TOC placement matters for accessibility.** The `[TOC]` directive inserts HTML into
> the DOM exactly where it appears. Placing it at the bottom means screen readers won't
> reach it until the end of the document. Always place it after the introduction.

---

## Front Matter (YAML Metadata)

When the target platform supports it (Jekyll, Hugo, Docusaurus, GitHub Pages, MkDocs):

```markdown
---
title: "Introduction to Python"
author: "Jane Smith"
date: "2024-08-03"
description: "An introductory guide covering basic concepts and syntax."
tags: ["python", "programming", "beginner"]
category: "Programming Tutorials"
version: "1.0.0"
last_updated: "2024-08-03"
---
```

### Front Matter Rules

- Always place front matter at the **very top** of the file, before any Markdown content.
- Use triple dashes (`---`) as opening and closing delimiters.
- Keep keys **lowercase** and **snake_cased**.
- Include `version` and `last_updated` for versioned API or library docs.
- The `description` field feeds SEO meta tags on documentation sites.
- `tags` and `category` improve discoverability in doc search systems.

---

## Headings

### Use ATX-Style Only

```markdown
# H1 — Document Title
## H2 — Major Section
### H3 — Subsection
#### H4 — Sub-subsection
##### H5
###### H6
```

**Never** use Setext (underline) style — it is ambiguous, fragile, and hard to maintain:

```markdown
Heading — DO NOT USE
--------------------
```

An editor cannot tell at a glance whether `---` means H2 or a horizontal rule.

### Heading Rules (Google Style Guide)

1. **One H1 per document.** It becomes the page `<title>`.
2. **Never skip levels.** H2 → H3 is valid. H2 → H4 is not.
3. **Unique, fully descriptive names.** Anchor links are auto-generated from heading text.
   Generic repeated names (`### Summary` under multiple H2s) produce anchor collisions:

   ```markdown
   # ❌ BAD — duplicate anchors break navigation
   ## Foo
   ### Summary
   ## Bar
   ### Summary

   # ✅ GOOD — unique, descriptive
   ## Foo
   ### Foo Summary
   ### Foo Example
   ## Bar
   ### Bar Summary
   ### Bar Example
   ```

4. **Add blank lines** before and after every heading — required for consistent parsing.

   ```markdown
   ...text before.

   ## Heading 2

   Text after...
   ```

5. **Sentence case** headings unless the target style guide mandates title case.
   - Capitalise the first word and proper nouns only.
   - Exception: product/tool names must preserve their exact capitalisation
     (`GitHub`, `macOS`, `Node.js`, `TypeScript`).

---

## Table of Contents

### When to Include a TOC

Include a TOC whenever the document has content "below the fold" on a typical laptop
screen (i.e., more than ~2 screens of content).

### Manual TOC (universal Markdown)

```markdown
## Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
   - [Environment Variables](#environment-variables)
   - [Config File](#config-file)
3. [Usage](#usage)
4. [API Reference](#api-reference)
```

Anchor links are generated by:
- Converting heading text to lowercase
- Replacing spaces with hyphens
- Removing all punctuation except hyphens

```markdown
## My Section Title   →   #my-section-title
## API: v2.0          →   #api-v20
```

### Directive TOC (platform-specific)

```markdown
[TOC]          <!-- Gitiles, MkDocs -->
[[toc]]        <!-- VuePress -->
{:toc}         <!-- Kramdown / Jekyll -->
```

---

## Paragraphs and Line Length

### 80-Character Line Limit

Body text follows an 80-character line limit (matches code conventions; improves
diff readability in version control).

**Exceptions** that may exceed 80 characters:
- URLs and hyperlinks
- Table cells
- Headings
- Code blocks

### Paragraph Rules

- Separate paragraphs with **a single blank line**.
- Do not use trailing spaces or `<br>` for paragraph breaks — use blank lines.
- Each paragraph should focus on **one central idea**.
- Aim for **3–5 sentences** (100–200 words) per paragraph. Technical docs may stretch
  to 300 words maximum; longer than that, split the paragraph.
- Use transitional sentences to connect consecutive paragraphs.

### Line Breaks Within a Paragraph

Avoid forced line breaks (`\` or two trailing spaces) within paragraphs. Rewrite
the sentence instead. If a hard break is genuinely needed, use a trailing backslash
(`\`) sparingly — it is more portable than two trailing spaces, which are invisible
and may be silently stripped by editors.

```markdown
For some reason I really need a break here,\
though it is probably not necessary.
```

---

## Capitalization

Use the **original capitalisation** of all products, tools, and binaries:

```markdown
# ✅ Correct
`Markdown`, `GitHub`, `macOS`, `Node.js`, `npm`, `PostgreSQL`, `OAuth`

# ❌ Wrong
`markdown`, `Github`, `MacOS`, `node.js`, `NPM`, `Postgresql`, `oauth`
```

---

## Document Hygiene

- **Delete stale content frequently** in small batches — a small accurate doc beats a
  large outdated one.
- Identify what you truly need: release docs, API docs, testing guidelines.
- Avoid "documentation" in disrepair. Own your docs the same way you own your tests.
- When a document exceeds ~500 lines, split it into focused sub-documents with an index:

  ```markdown
  ## Documentation Index

  1. [Overview](./overview.md) — Concepts and introduction
  2. [Quick Start](./quickstart.md) — Up and running in 5 minutes
  3. [Tutorial](./tutorial.md) — Full walkthrough
  4. [API Reference](./api-reference.md) — Complete API reference
  5. [Troubleshooting](./troubleshooting.md) — Common issues and fixes
  ```
