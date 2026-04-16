---
name: html-guide
description: >-
  Use this skill whenever writing, editing, updating, or reviewing HTML files.
  Triggers on any request to create HTML pages, templates, components, or
  documents; fix or refactor existing HTML; audit HTML for accessibility or
  quality; add semantic structure; or update markup in a codebase. Also
  triggers for phrases like "write HTML", "build a page", "update the markup",
  "fix the HTML", "make this accessible", or any request mentioning .html
  files. Apply this skill even for partial HTML snippets, email templates,
  and component markup — not just full pages.
---

# HTML Guide Skill

Write, maintain, and update HTML to professional standards. Emphasis on
semantic structure, WCAG 2.2 accessibility, and clean formatting that reads
well for humans, screen readers, and downstream tooling.

## Pre-delivery checklist

Before handing off any HTML, confirm:

- [ ] `<!doctype html>` is the very first line
- [ ] `<meta charset="utf-8">` is the first element in `<head>`
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">`
- [ ] `<title>` is descriptive and unique
- [ ] `lang` attribute on `<html>`
- [ ] All images have meaningful `alt` text (or `alt=""` for decorative)
- [ ] Heading hierarchy is sequential (no skipping levels); one `<h1>` per page
- [ ] Landmarks used: `<header>`, `<nav>`, `<main>`, `<footer>`
- [ ] Every form input is associated with a `<label>`
- [ ] No inline `style=""` or `onclick=""`
- [ ] No `type` attributes on `<script>` or `<link rel="stylesheet">`
- [ ] Double quotes on all attribute values; lowercase tags and attribute names
- [ ] 2-space indentation, UTF-8, no BOM
- [ ] Validated at https://validator.w3.org/nu/

## Workflow

### 1. Start from a valid document

For any new page, copy [templates/html-template.html](templates/html-template.html).
It contains the correct head order, landmark layout, and a skip-link stub.

Minimal structure:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Page description for SEO (150–160 chars)">
    <title>Page Title – Site Name</title>
    <link rel="stylesheet" href="styles/main.css">
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <header>
      <nav aria-label="Primary"><!-- navigation --></nav>
    </header>
    <main id="main-content">
      <h1>Page Heading</h1>
    </main>
    <footer><!-- footer --></footer>
    <script src="scripts/main.js" defer></script>
  </body>
</html>
```

Head rules: `charset` FIRST, always include `viewport`, use the pattern
`Page Name – Site Name` for titles, load CSS in `<head>` and scripts at the end
of `<body>` (or with `defer`), use HTTPS for externals, omit `type="text/css"`
and `type="text/javascript"` (HTML5 defaults apply).

### 2. Reach for semantic elements first

Use the element built for the job. Semantic HTML gives you keyboard support,
screen reader hints, and document structure for free.

| Element                       | Purpose                                          |
|-------------------------------|--------------------------------------------------|
| `<header>` / `<footer>`       | Page or section header/footer                    |
| `<nav>`                       | Navigation links (`aria-label` when multiple)    |
| `<main>`                      | Primary content — only one per page              |
| `<article>`                   | Self-contained: blog post, card, news story      |
| `<section>`                   | Thematic grouping — should have a heading        |
| `<aside>`                     | Complementary: sidebars, pull-quotes, ads        |
| `<figure>` + `<figcaption>`   | Images/diagrams with captions                    |
| `<address>`                   | Contact info for nearest `<article>` / `<body>`  |
| `<time>`                      | Machine-readable dates/times                     |

```html
<!-- WRONG: non-semantic clickable div -->
<div onclick="goTo('/about')">About us</div>

<!-- RIGHT: use the element built for the job -->
<a href="/about">About us</a>

<!-- WRONG: div as button -->
<div class="btn" onclick="submitForm()">Submit</div>

<!-- RIGHT: native button — keyboard accessible by default -->
<button type="submit">Submit</button>
```

Full element cheat-sheet with use cases in
[references/semantic-elements.md](references/semantic-elements.md).

### 3. Respect heading hierarchy

Only one `<h1>` per page (the page topic). Don't skip levels. Headings describe
structure, not visual size — control appearance in CSS.

```html
<!-- WRONG: skipped heading -->
<h1>Dashboard</h1>
<h3>Recent Activity</h3>

<!-- RIGHT -->
<h1>Dashboard</h1>
  <h2>Recent Activity</h2>
    <h3>Today</h3>
    <h3>This Week</h3>
```

### 4. Use lists and tables correctly

```html
<ul><li>Unordered — no sequence</li></ul>
<ol><li>Ordered — sequence matters</li></ol>
<dl><dt>Term</dt><dd>Definition</dd></dl>

<!-- Tables ONLY for tabular data -->
<table>
  <caption>Q3 Sales by Region</caption>
  <thead>
    <tr><th scope="col">Region</th><th scope="col">Revenue</th></tr>
  </thead>
  <tbody>
    <tr><td>North</td><td>$42,000</td></tr>
  </tbody>
</table>
```

### 5. Build accessibility in, not on

Follow POUR: **P**erceivable, **O**perable, **U**nderstandable, **R**obust.

Key patterns every page needs:

```html
<!-- Informational image -->
<img src="chart.png" alt="Bar chart showing 40% growth in Q3 2024">

<!-- Decorative image -->
<img src="divider.png" alt="">

<!-- Labelled form field -->
<label for="email">Email address</label>
<input type="email" id="email" name="email" autocomplete="email" required>

<!-- Error messaging -->
<input id="email" aria-describedby="email-error" aria-invalid="true">
<p id="email-error" role="alert">Please enter a valid email address.</p>

<!-- Grouped inputs -->
<fieldset>
  <legend>Preferred contact method</legend>
  <label><input type="radio" name="contact" value="email"> Email</label>
  <label><input type="radio" name="contact" value="phone"> Phone</label>
</fieldset>

<!-- Inline language switch -->
<p>The French say <span lang="fr">bonjour</span>.</p>
```

ARIA is a last resort — native elements already carry role, state, and
keyboard behavior. Reach for ARIA only for custom widgets with no semantic
equivalent (tabs, combobox, dialog, live regions).

Keyboard rules: everything interactive must be reachable with `Tab`, focus
order matches visual order, never remove `outline` without a visible
replacement in CSS, never use `tabindex` values greater than 0.

Full WCAG 2.2 checklist, ARIA patterns, and screen-reader testing notes in
[references/accessibility.md](references/accessibility.md).

### 6. Format consistently

- **Indentation**: 2 spaces, never tabs
- **Case**: all element names, attributes, and attribute values in lowercase
  (natural-language values like `alt` and `title` are exempt)
- **Quotes**: always double quotes on attribute values
- **Line wrapping**: no strict column limit, but wrap long attribute lists

```html
<!-- Long attributes: wrap consistently -->
<button
  type="button"
  class="btn btn-primary"
  aria-label="Open navigation menu"
  data-target="nav-drawer"
>
  Menu
</button>
```

### 7. Attribute hygiene

- **Boolean attributes**: no value needed — `<input required>`, `<button disabled>`
- **IDs**: hyphenated, unique per page, avoid when a class will do. Use
  `id="user-profile"` not `userProfile` (the camelCase form leaks as a global
  in JS)
- **Data attributes**: `data-*` for scripting hooks, not styling
- **Type attributes**: omit `type="text/javascript"` and `type="text/css"` —
  HTML5 assumes them

## Maintaining existing HTML

### Before editing

1. Match existing indentation even if it's not 2-space (consistency beats
   preference for partial edits).
2. Identify the doctype and HTML version.
3. Note any templating syntax (`{{ }}`, `{% %}`, `<% %>`) — preserve it.
4. Scan for existing IDs/classes your new code must integrate with.
5. Check the linked CSS — new class names must align.

### While editing

- Change only what is necessary — don't reformat unrelated code.
- Preserve existing comments and TODO markers.
- If fixing a bug, add a comment explaining what was wrong and why.
- Never silently remove markup you don't understand — ask first.

### After editing

Verify: indentation consistent through the changed sections, no new trailing
whitespace, attribute quote style matches the file, no duplicate IDs
introduced, heading hierarchy still intact.

### Refactoring div-soup to semantic markup

1. Identify the PURPOSE of each div (header? nav? list? section?).
2. Map to the correct semantic element.
3. Move inline styles to a CSS class.
4. Verify visual output is unchanged before claiming "done".

```html
<!-- BEFORE -->
<div class="top-bar">
  <div class="logo-wrap"><img src="logo.png"></div>
  <div class="menu">…</div>
</div>

<!-- AFTER -->
<header>
  <a href="/"><img src="logo.png" alt="Acme Co – Home"></a>
  <nav aria-label="Primary">…</nav>
</header>
```

## Validation and tooling

- Validator: https://validator.w3.org/nu/
- Accessibility audits: **axe DevTools**, **WAVE**, **Lighthouse**
- Linting: **HTMLHint** (`.htmlhintrc`), **Prettier**, and
  **ESLint + eslint-plugin-jsx-a11y** for JSX projects

Recommended `.htmlhintrc`:

```json
{
  "doctype-first": true,
  "doctype-html5": true,
  "attr-lowercase": true,
  "attr-value-double-quotes": true,
  "tag-pair": true,
  "id-unique": true,
  "src-not-empty": true,
  "alt-require": true,
  "spec-char-escape": true
}
```

## Quick reference: where to go deeper

| Topic                                                    | Reference file                                                     |
|----------------------------------------------------------|--------------------------------------------------------------------|
| WCAG 2.2 checklist, ARIA patterns, screen reader testing | [references/accessibility.md](references/accessibility.md)         |
| Complete element reference with use cases                | [references/semantic-elements.md](references/semantic-elements.md) |
| Production-ready HTML boilerplate                        | [templates/html-template.html](templates/html-template.html)       |
