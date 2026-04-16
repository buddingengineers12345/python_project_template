# CSS architecture reference

## Choosing a CSS Architecture

| Factor | Utility-First | BEM | SMACSS | ITCSS |
|--------|--------------|-----|--------|-------|
| **Best for** | Rapid prototyping, Tailwind | Component libraries | Content sites | Large codebases |
| **Naming** | Utility classes | `.block__el--mod` | `.l-layout .m-module` | Layered |
| **Learning curve** | Low | Medium | Medium | High |
| **Maintainability** | High | High | Medium | Very high |
| **CSS bundle size** | Small (purged) | Grows with components | Medium | Medium |

**Recommendation**: BEM naming + ITCSS layer organization covers 80% of project types.

---

## ITCSS — Inverted Triangle CSS

Organizes CSS from least to most specific. Rules lower in the triangle affect fewer elements but with more specificity.

```
         ████████████████████████
         Settings (widest reach)
        ██████████████████████████
        Tools
       ████████████████████████████
       Generic
      ██████████████████████████████
      Elements
     ████████████████████████████████
     Objects
    ██████████████████████████████████
    Components
   ████████████████████████████████████
   Utilities (narrowest — highest specificity)
```

### Layer Descriptions

**1. Settings** — Global variables, design tokens, configuration
```css
/* _settings.css */
:root {
  --color-primary: #3b82f6;
  --font-body: system-ui, sans-serif;
}
```

**2. Tools** — Mixins, functions (Sass only; skip for plain CSS)
```scss
// _tools.scss
@mixin respond-to($breakpoint) { ... }
@function rem($px) { ... }
```

**3. Generic** — Resets, normalize. Affects broad HTML elements.
```css
/* _generic.css */
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; }
```

**4. Elements** — Unclassed HTML element defaults
```css
/* _elements.css */
a { color: var(--color-primary); }
img { max-width: 100%; display: block; }
```

**5. Objects** — Class-based layout patterns. No cosmetics.
```css
/* _objects.css */
.container { width: min(100%, 1200px); margin-inline: auto; }
.grid { display: grid; }
```

**6. Components** — Discrete UI components. The bulk of your CSS.
```css
/* _button.css */
.btn { ... }
.btn--primary { ... }
```

**7. Utilities** — Single-purpose, often `!important`. Overrides.
```css
/* _utilities.css */
.visually-hidden { position: absolute !important; ... }
.text-center { text-align: center !important; }
```

---

## BEM — Block Element Modifier

### Full Rules

**Blocks** are standalone components. They:
- Have no outside geometry (no `margin`, `position: absolute`)
- Can be nested or moved anywhere in the DOM
- Are named as single concepts: `.card`, `.nav`, `.form`, `.modal`

**Elements** are parts that make sense only in context of their block:
- Named: `.block__element`
- Double underscore separator
- NEVER: `.block__elem1__elem2` (flatten the chain, use single level)

```css
/* WRONG: chained elements */
.card__body__title { }

/* RIGHT: element references its block directly */
.card__title { }
```

**Modifiers** are variants or states of a block or element:
- Named: `.block--modifier` or `.block__element--modifier`
- Double hyphen separator
- Never use alone — always combined with base class

```html
<!-- WRONG -->
<div class="btn--primary">

<!-- RIGHT -->
<div class="btn btn--primary">
```

### BEM + State Classes

For JavaScript-toggled states, use a separate state class:
```css
.is-open { }
.is-active { }
.is-loading { }
.has-error { }
```

These are combined with BEM classes:
```html
<div class="dropdown is-open">
```

### When BEM Gets Complex: Use Context Classes

Instead of super-long BEM chains, use a context modifier on the parent:
```css
/* Context: inside a featured card, headings are larger */
.card--featured .card__title {
  font-size: var(--text-2xl);
}
```

---

## SMACSS — Scalable and Modular Architecture for CSS

Five categories:

1. **Base** — Element defaults (like ITCSS Elements)
2. **Layout** — Major page sections, prefixed `.l-`
3. **Module** — Reusable UI components (no prefix or `.m-`)
4. **State** — State rules, prefixed `.is-`
5. **Theme** — Theme variations

```css
/* Layout */
.l-header { }
.l-sidebar { }
.l-main { }

/* Module */
.nav { }
.nav-item { }

/* State */
.is-hidden { display: none; }
.is-active { }
```

---

## CSS Cascade Layers (Modern CSS — 2023+)

Layers explicitly control the order of the cascade, eliminating specificity wars.

```css
/* Declare layer order at the very top of your entry file */
/* Earlier = lower priority; later = higher priority */
@layer reset, base, layout, components, utilities;

/* Styles outside any layer take highest priority */

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
}

@layer base {
  :root { --color-text: #111; }
  body { font-family: system-ui; }
}

@layer components {
  .btn { padding: 0.5rem 1rem; }
  .btn--primary { background: var(--color-primary); }
}

@layer utilities {
  /* !important not needed — utilities layer wins via layer order */
  .hidden { display: none; }
}
```

**Browser support**: 93%+ (2024). Safe to use with fallback plan.

---

## CSS Architecture Decision Checklist

Before starting a project, decide:

- [ ] Single file or multi-file? (multi-file for anything beyond a landing page)
- [ ] Will you use a preprocessor (Sass/SCSS)? Or plain CSS with custom properties?
- [ ] Will you use CSS Modules, CSS-in-JS, or global stylesheets?
- [ ] Will you use a utility framework (Tailwind) or write component CSS?
- [ ] What naming convention? (BEM recommended for teams)
- [ ] Will you use Cascade Layers? (recommended for new projects)
- [ ] What is the design token strategy? (always use custom properties)
- [ ] How will dark mode be handled? (`prefers-color-scheme` vs `.dark` class toggle)
- [ ] What are the breakpoints? (document in the tokens file)
- [ ] What linter config? (Stylelint with config-standard)

---

## Handling Specificity Conflicts

When you need to override a style and can't change the source:

**Option 1: Increase specificity with a compound selector** (last resort)
```css
/* Original */
.btn { color: red; }

/* Override — add another class for context */
.modal .btn { color: blue; }
```

**Option 2: Use Cascade Layers** (preferred in modern CSS)
```css
@layer base { .btn { color: red; } }
@layer components { .btn--modal { color: blue; } }
/* components layer wins regardless of specificity */
```

**Option 3: CSS Custom Property override**
```css
/* Base component uses a variable */
.btn { color: var(--btn-color, var(--color-primary)); }

/* Override in specific context — no specificity issue */
.modal { --btn-color: white; }
```
