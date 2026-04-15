# Layout and responsive design reference

Modern CSS layout patterns (Grid, Flexbox, container) and mobile-first
responsive techniques. Load this file when you're laying out pages, building
responsive components, or deciding between Grid and Flexbox.

## CSS Grid — use for 2D layout

```css
/* Page layout: header / main / footer */
.page-layout {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}

/* Content column with flexible side margins */
.content-grid {
  display: grid;
  grid-template-columns: 1fr min(65ch, 100%) 1fr;
}

/* Card grid — responsive without media queries */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-6);
}
```

`auto-fill` + `minmax()` eliminates most breakpoints for card layouts: tracks
grow/shrink automatically.

## Flexbox — use for 1D layout

```css
/* Navigation row */
.nav__list {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  list-style: none;
  margin: 0;
  padding: 0;
}

/* Card that sticks its footer to the bottom */
.card {
  display: flex;
  flex-direction: column;
}
.card__body { flex: 1; }

/* Center anything in both axes */
.centered {
  display: grid;           /* grid works better than flex for centering */
  place-items: center;
}
```

Rule of thumb: if you're laying out a row/column of items, reach for Flexbox.
If you're controlling rows AND columns, reach for Grid.

## Container

```css
.container {
  width: min(100% - 2rem, 1200px);
  margin-inline: auto;
}
```

`min()` gives you a fluid-then-capped container with one line. `margin-inline`
is the logical equivalent of `margin-left` and `margin-right` — it works in
right-to-left languages too.

## Mobile-first media queries

Always author for the smallest viewport first, then progressively enhance with
`min-width` queries. Avoid `max-width` except for rare override cases.

```css
.nav {
  display: flex;
  flex-direction: column;
}

@media (min-width: 768px) {
  .nav { flex-direction: row; }
}

@media (min-width: 1024px) {
  .nav { gap: var(--space-8); }
}
```

Standard breakpoints (match your design system):

```
sm   640px
md   768px
lg  1024px
xl  1280px
2xl 1536px
```

## Fluid typography and spacing

`clamp(min, preferred, max)` scales a value between the viewport extremes.
Fewer breakpoints, smoother transitions.

```css
h1 {
  font-size: clamp(var(--text-2xl), 5vw, var(--text-4xl));
}

body {
  font-size: clamp(var(--text-base), 1.2vw, var(--text-lg));
}

.section {
  padding-block: clamp(var(--space-8), 10vw, var(--space-24));
}
```

## Container queries (when supported)

When a component needs to respond to its container rather than the viewport:

```css
.card-parent {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 500px) {
  .card { flex-direction: row; }
}
```

Reach for container queries in design-system components that will be dropped
into unknown layouts (sidebars, modals, embedded widgets).

## Performance notes for layout

- Avoid the universal selector in component rules: `* { box-sizing: border-box; }`
  is fine in the reset, but `.card * { … }` invalidates more of the layout tree.
- Don't chain deep descendants (`.nav .list .item .link span`) — target classes
  directly. It's faster and less coupled.
- Use `contain: layout paint` on isolated widgets (modals, cards with complex
  internals) so style/layout work doesn't cascade to the whole page.
- `will-change: transform` should go on elements about to animate, and be
  removed after. Leaving it on forever is a memory leak.
