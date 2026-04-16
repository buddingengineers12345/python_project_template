# CSS accessibility reference

Practical, WCAG 2.2-aligned CSS patterns for focus, motion, contrast, and
screen-reader-only content. Load this file whenever a CSS task involves
keyboard navigation, animations, dark mode, reduced motion, or hiding content
from sighted users only.

## Focus indicators (WCAG 2.2)

Never remove focus outlines without replacing them. WCAG 2.2 SC 2.4.11
(Focus Not Obscured) and 2.4.13 (Focus Appearance) apply.

```css
/* Remove default only if replaced immediately */
:focus { outline: none; }

/* Visible, WCAG-compliant focus ring */
:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 3px;
  border-radius: var(--radius-sm);
}

/* High-contrast boost for users who request it */
@media (prefers-contrast: more) {
  :focus-visible {
    outline-width: 4px;
    outline-color: #000;
  }
}
```

Prefer `:focus-visible` over `:focus` so the ring shows for keyboard users but
not for mouse clicks (where it looks noisy).

## Reduced motion

Respect `prefers-reduced-motion: reduce`. Wrap non-essential animations and
provide a static alternative.

```css
/* Motion only when the user has not opted out */
@media (prefers-reduced-motion: no-preference) {
  .card {
    transition: transform var(--transition-normal),
                box-shadow var(--transition-normal);
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
  }
}

/* Global safety net — near-zero duration for anything animated */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Dark mode

Two patterns — pick one per project.

```css
/* 1. System-driven */
@media (prefers-color-scheme: dark) {
  :root {
    --color-text:       var(--color-neutral-50);
    --color-background: #0f172a;
    --color-surface:    #1e293b;
    --color-border:     #334155;
  }
}

/* 2. User-toggled — attribute on <html> or <body> */
[data-theme="dark"] {
  --color-text:       var(--color-neutral-50);
  --color-background: #0f172a;
}
```

Because colors are defined as custom properties, the rest of the stylesheet
doesn't need to change.

## Visually hidden (screen-reader only)

Use when content must be announced but not shown (e.g., labels for icon-only
buttons, skip-link targets).

```css
.visually-hidden,
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}

/* Make it appear when focused via keyboard */
.visually-hidden:focus,
.sr-only:focus {
  position: static !important;
  width: auto !important;
  height: auto !important;
  overflow: visible !important;
  clip: auto !important;
  white-space: normal !important;
}
```

## Skip link

Allows keyboard users to bypass repeated navigation.

```css
.skip-link {
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
  z-index: var(--z-toast);
}

.skip-link:focus {
  left: var(--space-4);
  top: var(--space-4);
  width: auto;
  height: auto;
  overflow: visible;
  padding: var(--space-2) var(--space-4);
  background: var(--color-text);
  color: var(--color-background);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-bold);
}
```

## Color contrast minimums

- Normal text (< 18pt): **4.5:1** ratio (WCAG AA)
- Large text (≥ 18pt or ≥ 14pt bold): **3:1** ratio (WCAG AA)
- UI components (borders, icons): **3:1** ratio
- Verify with https://webaim.org/resources/contrastchecker/

When a color token fails the check, adjust the token value — never patch a
single rule. The whole token system flips with it.
