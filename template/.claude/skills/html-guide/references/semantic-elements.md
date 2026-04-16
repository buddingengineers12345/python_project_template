# Semantic HTML5 elements reference

## Document Structure Elements

| Element | Description | When to Use |
|---------|-------------|-------------|
| `<!doctype html>` | HTML5 document type | First line of every HTML file |
| `<html lang="">` | Root element | Wraps entire document; `lang` is required |
| `<head>` | Metadata container | Contains meta, title, links |
| `<body>` | Content container | All visible page content |

## Sectioning Elements

### `<header>`
- Page-level: site logo, primary nav, search
- Section-level: heading + intro for an `<article>` or `<section>`
- Multiple allowed per page

```html
<header>
  <a href="/"><img src="logo.svg" alt="Brand – Home"></a>
  <nav aria-label="Primary">...</nav>
</header>
```

### `<nav>`
- Block of navigation links
- Use `aria-label` when more than one `<nav>` exists on a page

```html
<nav aria-label="Primary">
  <ul>
    <li><a href="/" aria-current="page">Home</a></li>
    <li><a href="/products">Products</a></li>
  </ul>
</nav>

<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/products">Products</a></li>
    <li aria-current="page">Widget Pro</li>
  </ol>
</nav>
```

### `<main>`
- **One per page** — the dominant unique content
- Skip links should point here
- Do NOT nest inside `<article>`, `<aside>`, `<header>`, `<footer>`, or `<nav>`

### `<article>`
- Self-contained, independently distributable content
- Examples: blog post, news story, product card, comment, widget
- Should have a heading (`h1`–`h6`)

```html
<article>
  <header>
    <h2>Article Title</h2>
    <p>By <a href="/author/jane">Jane Doe</a> on <time datetime="2024-03-15">March 15, 2024</time></p>
  </header>
  <p>Article body...</p>
  <footer>
    <p>Tags: <a href="/tags/html">HTML</a></p>
  </footer>
</article>
```

### `<section>`
- Thematic grouping of content within a document
- Should have a heading — if it doesn't, use `<div>` instead
- Different from `<article>`: a section is part of something larger

```html
<section aria-labelledby="features-heading">
  <h2 id="features-heading">Features</h2>
  <ul>...</ul>
</section>
```

### `<aside>`
- Content tangentially related to surrounding content
- Sidebars, pull quotes, advertising, author bio

### `<footer>`
- Footer for its nearest sectioning ancestor
- Page-level: copyright, links, contact
- Article-level: author info, tags, related articles

---

## Text-Level Elements

| Element | Use |
|---------|-----|
| `<p>` | Paragraph of text |
| `<strong>` | Strong importance (semantic bold) |
| `<em>` | Stress emphasis (semantic italic) |
| `<b>` | Stylistic bold without importance |
| `<i>` | Technical terms, foreign words, thoughts (no emphasis) |
| `<mark>` | Highlighted / search result text |
| `<small>` | Small print: legal, copyright |
| `<del>` + `<ins>` | Deleted / inserted text (edit tracking) |
| `<abbr title="">` | Abbreviation with expanded form |
| `<cite>` | Title of a creative work |
| `<q>` | Short inline quotation |
| `<blockquote>` | Extended quotation |
| `<code>` | Inline code |
| `<pre>` | Preformatted text block |
| `<kbd>` | Keyboard input |
| `<samp>` | Sample output |
| `<var>` | Mathematical/programming variable |
| `<sup>` / `<sub>` | Superscript / subscript |
| `<time datetime="">` | Machine-readable dates/times |
| `<address>` | Contact info for nearest `<article>` or body |
| `<s>` | Struck-through text (no longer accurate) |

---

## Embedded Content

### Images
```html
<!-- Standard image -->
<img src="photo.jpg" alt="Descriptive text" width="800" height="600" loading="lazy">

<!-- Responsive image with srcset -->
<img
  src="photo-800.jpg"
  srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1600.jpg 1600w"
  sizes="(max-width: 600px) 400px, (max-width: 1200px) 800px, 1600px"
  alt="Description"
  loading="lazy"
>

<!-- Art direction with <picture> -->
<picture>
  <source media="(max-width: 600px)" srcset="mobile.jpg">
  <source media="(min-width: 601px)" srcset="desktop.jpg">
  <img src="fallback.jpg" alt="Description">
</picture>
```

### Figure and Caption
```html
<figure>
  <img src="chart.png" alt="Chart showing 30% growth year over year">
  <figcaption>Figure 1: Annual revenue growth 2020–2024. Source: Finance Report.</figcaption>
</figure>
```

### Video
```html
<video controls width="720" poster="thumbnail.jpg">
  <source src="video.webm" type="video/webm">
  <source src="video.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English" default>
  <p>Your browser doesn't support HTML video. <a href="video.mp4">Download the video</a>.</p>
</video>
```

---

## Forms

### Complete Form Example
```html
<form action="/submit" method="post" novalidate>
  <fieldset>
    <legend>Personal Information</legend>

    <div class="form-group">
      <label for="full-name">Full name <span aria-hidden="true">*</span></label>
      <input
        type="text"
        id="full-name"
        name="full_name"
        autocomplete="name"
        required
        aria-required="true"
      >
    </div>

    <div class="form-group">
      <label for="email">Email address <span aria-hidden="true">*</span></label>
      <input
        type="email"
        id="email"
        name="email"
        autocomplete="email"
        required
        aria-required="true"
        aria-describedby="email-hint"
      >
      <p id="email-hint" class="hint">We'll never share your email.</p>
    </div>

    <div class="form-group">
      <label for="message">Message</label>
      <textarea id="message" name="message" rows="5"></textarea>
    </div>
  </fieldset>

  <p><span aria-hidden="true">*</span> Required fields</p>
  <button type="submit">Send message</button>
</form>
```

### Input Types (use the right one)
```html
<input type="text">        <!-- Generic text -->
<input type="email">       <!-- Email (validates format, mobile keyboard) -->
<input type="tel">         <!-- Phone number (numeric mobile keyboard) -->
<input type="url">         <!-- URL -->
<input type="number">      <!-- Numeric (use sparingly — type="text" + inputmode often better) -->
<input type="password">    <!-- Hidden text -->
<input type="search">      <!-- Search (adds clear button in some browsers) -->
<input type="date">        <!-- Date picker -->
<input type="checkbox">    <!-- Multi-select -->
<input type="radio">       <!-- Single-select from group -->
<input type="file">        <!-- File upload -->
<input type="range">       <!-- Slider -->
<input type="hidden">      <!-- Hidden data -->
<input type="submit">      <!-- Submit button (prefer <button type="submit">) -->
```

---

## Interactive Elements

### Dialog (Modal)
```html
<dialog id="modal" aria-labelledby="modal-title">
  <h2 id="modal-title">Confirm deletion</h2>
  <p>Are you sure you want to delete this item? This cannot be undone.</p>
  <div>
    <button type="button" onclick="document.getElementById('modal').close()">Cancel</button>
    <button type="button" class="btn-danger">Delete</button>
  </div>
</dialog>

<button onclick="document.getElementById('modal').showModal()">Delete item</button>
```

### Details / Summary (Accordion)
```html
<details>
  <summary>What is your return policy?</summary>
  <p>We accept returns within 30 days of purchase with the original receipt.</p>
</details>
```

---

## Meta Tags Reference

```html
<head>
  <!-- Required -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page Title – Site Name</title>

  <!-- SEO -->
  <meta name="description" content="150–160 char page description">
  <link rel="canonical" href="https://example.com/page">

  <!-- Social / Open Graph -->
  <meta property="og:title" content="Page Title">
  <meta property="og:description" content="Description">
  <meta property="og:image" content="https://example.com/og-image.jpg">
  <meta property="og:url" content="https://example.com/page">
  <meta property="og:type" content="website">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Page Title">

  <!-- Icons -->
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">

  <!-- Stylesheets: load in <head> -->
  <link rel="stylesheet" href="styles/main.css">

  <!-- Preconnect for performance -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
</head>
```
