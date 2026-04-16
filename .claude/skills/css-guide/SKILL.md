---
name: css-guide
description: >-
  Use this skill whenever writing, editing, updating, or reviewing CSS files.
  Triggers on any request to create stylesheets, style components or pages,
  refactor CSS, add responsive design, fix layout bugs, improve CSS
  architecture, create CSS custom properties (variables), or update existing
  .css / .scss / .sass files. Also triggers for phrases like "style this",
  "write CSS", "make it responsive", "fix the layout", "update the styles",
  "add a dark mode", "improve the CSS", or any request mentioning .css, .scss,
  or .sass files. Apply this skill even for inline style blocks,
  component-scoped CSS, and utility classes.
---

# CSS Guide Skill

Write, maintain, and update CSS to professional standards. Priorities:
architecture that scales, design tokens over hard-coded values, accessible
interaction, and responsive layouts built mobile-first. The Google HTML/CSS
Style Guide is the formatting authority.

## Pre-delivery checklist

Before handing off any CSS, confirm:

- [ ] Custom properties (`--var-name`) used for all repeated values
- [ ] No `!important` (except utility overrides with a clear comment)
- [ ] No ID selectors (`#selector`) — use classes
- [ ] No inline styles or `style=""` pushed from CSS
- [ ] Class names are semantic and hyphen-delimited (BEM preferred)
- [ ] `0` values have no units (`margin: 0`, not `0px`)
- [ ] Leading zeros on decimals (`0.8em`, not `.8em`)
- [ ] 3-char hex where possible (`#ebc`, not `#eebbcc`)
- [ ] Single quotes for strings
- [ ] 2-space indentation, semicolons after every declaration, blank line between rules
- [ ] `:focus-visible` styles defined (WCAG 2.2)
- [ ] Color contrast ≥ 4.5:1 for body text (AA)
- [ ] Media queries use `min-width` (mobile-first)

## Workflow

### 1. Start from a tokenized foundation

All design decisions — color, type, spacing, radius, shadow, motion, z-index —
belong in CSS custom properties at `:root`. Never sprinkle hard-coded values
through components.

For a production-ready token set to drop in, copy
[templates/css-tokens.css](templates/css-tokens.css). Pair it with
[templates/css-reset.css](templates/css-reset.css) for a modern reset and
[templates/css-patterns.css](templates/css-patterns.css) for common component
examples (buttons, cards, forms, nav, modals).

Minimal token example:

```css
:root {
  --color-accent:   #3b82f6;
  --color-text:     #111827;
  --color-bg:       #ffffff;
  --space-4:        1rem;
  --radius-md:      0.5rem;
  --text-base:      1rem;
  --transition-fast: 150ms ease;
}
```

Dark mode and high-contrast adjustments override tokens — the rest of the
stylesheet doesn't change. See
[references/accessibility.md](references/accessibility.md) for the patterns.

### 2. Use BEM for naming

`.block`, `.block__element`, `.block--modifier`,
`.block__element--modifier`. Lowercase, hyphenated, names reflect purpose not
appearance.

```css
.card { … }                /* Block */
.card__header { … }        /* Element */
.card__title { … }
.card--featured { … }      /* Modifier */
.card__title--large { … }
```

Avoid presentational names (`.blue-button`, `.left-column`). Avoid
over-abbreviation (`.nav-lnk`). Target by class — not by tag, not by id.

### 3. Follow the architecture that matches project size

```
Small:    styles/main.css
Medium:   styles/{base,layout,components,utilities}/_*.css + main.css imports
Large:    ITCSS — 1-settings/ 2-tools/ 3-generic/ 4-elements/
                   5-objects/ 6-components/ 7-utilities/
```

Modern projects benefit from cascade layers:

```css
@layer reset, base, layout, components, utilities;
@layer components { .card { … } }
@layer utilities { .visually-hidden { … } }
```

Layers give you a deterministic cascade independent of source order or
specificity. For an ITCSS walk-through and layer migration tips, see
[references/css-architecture.md](references/css-architecture.md).

### 4. Format consistently (Google style)

```css
/* 2 spaces, space after ":", space before "{", blank line between rules */
.rule-one {
  color: var(--color-text);
  margin: 0;
  padding: var(--space-4);
}

.rule-two {
  background: var(--color-bg);
}

/* Multiple selectors: one per line */
h1,
h2,
h3 { font-weight: 700; }
```

Declaration order: alphabetical (Google default) or grouped (positioning → box
model → typography → visual → interaction). Pick one per codebase and stick
with it.

Values: `0` without units, leading zero on decimals, 3-char hex when possible,
single quotes for strings (`font-family: 'Inter', sans-serif;`).

### 5. Control specificity

Specificity ranks low→high: type (0,0,1) < class/attr/pseudo (0,1,0) < id
(1,0,0) < inline (1,0,0,0) < `!important`.

```css
/* AVOID: id selectors (hard to override) */
#header { … }

/* AVOID: over-qualifying with tag */
ul.nav { … }
div.card { … }

/* AVOID: deep descendant chains — brittle and slow */
.page .sidebar .widget .widget__title a { … }

/* PREFER: flat BEM */
.widget__title-link { … }
```

`!important` is acceptable only in utility classes (`.visually-hidden`) where
overriding is the explicit intent.

Style all interactive states together: `:hover`, `:focus-visible`, `:active`,
`:disabled`. Use `::before`/`::after` (double colon) for pseudo-elements.

### 6. Layout with Grid and Flexbox

```css
/* 2D — Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-6);
}

/* 1D — Flexbox */
.nav__list {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* Container */
.container {
  width: min(100% - 2rem, 1200px);
  margin-inline: auto;
}
```

Write mobile-first with `min-width` queries, and use `clamp()` for fluid type
and spacing. Full patterns and container queries are in
[references/layout-responsive.md](references/layout-responsive.md).

### 7. Ship accessible defaults

These must be in every stylesheet:

- `:focus-visible` ring (never just `outline: none`)
- `@media (prefers-reduced-motion: reduce)` safety net
- `.visually-hidden` / `.sr-only` utility
- Color tokens that meet 4.5:1 contrast for body text

Complete patterns (skip links, dark mode, high-contrast boost) are in
[references/accessibility.md](references/accessibility.md).

## Maintaining existing stylesheets

### Before editing

1. Identify the architecture — BEM? SMACSS? utility-first? no pattern?
2. Scan for existing custom properties — reuse them, don't redefine.
3. Find ALL rules for the component you're modifying.
4. Check specificity of existing selectors — match or beat appropriately.
5. Search for `!important` and understand why before adding more.

### While editing

- Match existing indentation (2-space, 4-space, or tab) and declaration order.
- Match selector and comment style.
- Edit only what's required — don't reformat unrelated rules.
- Add new rules AFTER existing rules for the same component.
- Never silently delete rules you don't understand — comment them out with
  an explanation and ask the user.

### After editing

- Could this change affect other elements using the same class?
- Did you increase specificity in a way that blocks future overrides?
- Do breakpoint changes hold across the full responsive range?

### Common update patterns

```css
/* New modifier — added below existing rules */
.btn--danger { background: var(--color-error); }
.btn--large  { font-size: var(--text-lg); padding: var(--space-3) var(--space-6); }

/* Add responsive behaviour at matching breakpoint */
@media (min-width: 768px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Refactor a magic number into a token */
:root { --header-height: 64px; }
.header    { height: var(--header-height); }
.page-main { padding-top: var(--header-height); }
```

## Tooling

- Validator: https://jigsaw.w3.org/css-validator/
- Linter: **stylelint** with `stylelint-config-standard`
- Formatter: **Prettier** (`tabWidth: 2`, `singleQuote: true`, `printWidth: 100`)

Recommended stylelint rules: `color-named: "never"`, `color-no-invalid-hex`,
`declaration-no-important`, a BEM-compatible `selector-class-pattern`, and
`no-duplicate-selectors`.

## Quick reference: where to go deeper

| Topic                                                    | Reference file                                                         |
|----------------------------------------------------------|------------------------------------------------------------------------|
| ITCSS, BEM, SMACSS, and cascade-layer architecture       | [references/css-architecture.md](references/css-architecture.md)       |
| Focus, reduced motion, dark mode, sr-only, contrast      | [references/accessibility.md](references/accessibility.md)             |
| Grid, Flexbox, mobile-first, fluid type, container queries | [references/layout-responsive.md](references/layout-responsive.md)   |
| Design token system — copy into projects                 | [templates/css-tokens.css](templates/css-tokens.css)                   |
| Modern CSS reset                                         | [templates/css-reset.css](templates/css-reset.css)                     |
| Common component patterns (button, card, form, nav, modal) | [templates/css-patterns.css](templates/css-patterns.css)             |
