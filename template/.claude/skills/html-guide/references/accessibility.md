# HTML accessibility reference

## WCAG 2.2 Compliance Checklist

WCAG 2.2 (W3C Recommendation, October 2023) is the current baseline standard.
Levels: A (minimum) → AA (standard target) → AAA (enhanced).

---

## Perceivable

### Text Alternatives (1.1)
- [ ] Every informational image has a descriptive `alt` attribute
- [ ] Decorative images use `alt=""`
- [ ] Complex images (charts, diagrams) have extended descriptions via `<figcaption>` or `aria-describedby`
- [ ] Functional images (buttons, links with images) describe the action/destination
- [ ] CSS background images that convey meaning have text equivalents

### Time-Based Media (1.2)
- [ ] Audio-only content has a text transcript
- [ ] Video-only content has audio description or text alternative
- [ ] Synchronized captions for prerecorded audio in video (AA)
- [ ] Audio descriptions for prerecorded video (AA)
- [ ] Live audio has captions (AA)

### Adaptable (1.3)
- [ ] Page structure uses semantic HTML landmarks
- [ ] Reading order makes sense without CSS (test by disabling styles)
- [ ] No reliance on sensory characteristics alone ("click the red button")
- [ ] No reliance on orientation (portrait/landscape) to access content (AA)
- [ ] Input purpose (name, email, etc.) is identified via `autocomplete` (AA)

### Distinguishable (1.4)
- [ ] Color is not the only way to convey information
- [ ] Normal text: minimum 4.5:1 contrast ratio vs background (AA)
- [ ] Large text (≥18pt or ≥14pt bold): minimum 3:1 contrast ratio (AA)
- [ ] Audio plays for ≤3 seconds or can be paused/stopped
- [ ] Text can be resized up to 200% without loss of functionality
- [ ] Images of text avoided — use real text with CSS styling
- [ ] Non-text contrast (UI components, focus indicators): 3:1 minimum (AA)
- [ ] Line spacing: at least 1.5x font size; letter spacing: 0.12em; word spacing: 0.16em (AA)
- [ ] Content not clipped or overlapped when text spacing is adjusted (AA)

---

## Operable

### Keyboard Accessible (2.1)
- [ ] All functionality operable by keyboard alone
- [ ] No keyboard traps (focus can always be moved away)
- [ ] Keyboard shortcuts use modifiers (Alt/Ctrl) if single-key shortcuts used (AA)
- [ ] All interactive elements in logical tab order

### Timing (2.2)
- [ ] User can turn off, adjust, or extend time limits
- [ ] Moving/blinking/scrolling content can be paused, stopped, or hidden
- [ ] Auto-updating content can be paused or controlled

### Seizures and Physical Reactions (2.3)
- [ ] No content flashes more than 3 times per second

### Navigable (2.4)
- [ ] Skip navigation link is the first focusable element
- [ ] Every page has a descriptive, unique `<title>`
- [ ] Focus order preserves meaning and operability
- [ ] All link text is descriptive — no "click here" or "read more" without context
- [ ] Multiple ways to find pages: search, site map, related links (AA)
- [ ] Headings and labels are descriptive (AA)
- [ ] Keyboard focus is always visible (AA)

### Input Modalities (2.5) — WCAG 2.2 New
- [ ] All functionality using dragging has a single-pointer alternative
- [ ] Target size minimum: 24×24 CSS pixels (some exceptions apply) (AA)
- [ ] No accidental activation on pointer down — use `pointerup`/`click`
- [ ] Labels match accessible names for inputs (to support voice input)
- [ ] Motion-actuated functionality has UI alternative and can be disabled

---

## Understandable

### Readable (3.1)
- [ ] `lang` attribute on `<html>` element
- [ ] `lang` attribute on `<span>` for inline language changes
- [ ] Unusual words or jargon are explained or linked
- [ ] Abbreviations are expanded (use `<abbr title="">`)

### Predictable (3.2)
- [ ] No unexpected context changes on focus
- [ ] No unexpected context changes on input (e.g., form submit on selection change)
- [ ] Navigation is consistent across pages (AA)
- [ ] Labels and icons are consistent across pages (AA)

### Input Assistance (3.3)
- [ ] Errors are identified in text (not just color)
- [ ] Labels and instructions are provided for inputs
- [ ] Error suggestions are provided when known (AA)
- [ ] Important transactions have confirmation step or undo (AA)
- [ ] Re-authentication: data not lost after session timeout (WCAG 2.2)
- [ ] Redundant entry: user not asked to re-enter info already provided (WCAG 2.2)

---

## Robust

### Compatible (4.1)
- [ ] HTML is valid (no duplicate IDs, proper nesting)
- [ ] All UI components have name, role, and value exposed to accessibility APIs
- [ ] Status messages are programmatically determinable (`role="status"`, `aria-live`)

---

## ARIA Patterns

### When to Use ARIA
Use ARIA ONLY when:
1. No native HTML element achieves the required semantics
2. The element's role/state cannot be conveyed any other way

**Rule**: Never use ARIA when a native HTML element works.

### Common ARIA Roles
```html
<!-- Landmark roles (prefer native elements) -->
<div role="banner">      <!-- = <header> -->
<div role="navigation">  <!-- = <nav> -->
<div role="main">        <!-- = <main> -->
<div role="contentinfo"> <!-- = <footer> -->

<!-- Widget roles -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
<div role="tablist">
<button role="tab" aria-selected="true" aria-controls="panel-1">Tab</button>
<div role="tabpanel" id="panel-1" tabindex="0">Content</div>

<!-- Alert and live regions -->
<div role="alert">Error: Please fill in all required fields.</div>
<div aria-live="polite" aria-atomic="true">Cart updated: 3 items</div>
```

### ARIA States & Properties
```html
<!-- Expanded/collapsed controls -->
<button aria-expanded="false" aria-controls="dropdown-menu">Options</button>
<ul id="dropdown-menu" hidden>...</ul>

<!-- Required fields -->
<input aria-required="true">

<!-- Invalid inputs -->
<input aria-invalid="true" aria-describedby="error-msg">
<p id="error-msg">This field is required.</p>

<!-- Current page in nav -->
<a href="/about" aria-current="page">About</a>

<!-- Hidden from assistive tech -->
<span aria-hidden="true">→</span>
```

---

## Focus Management

### Visible Focus
```css
/* NEVER do this without a replacement */
*:focus { outline: none; }

/* WCAG 2.2: focus indicator must meet 3:1 contrast and cover perimeter */
:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}
```

### Focus Trapping (Modals)
When a modal opens:
1. Move focus to the modal (`dialog.focus()` or first interactive element)
2. Trap Tab/Shift+Tab within the modal
3. Return focus to the trigger element on close

### Skip Links
```html
<!-- Must be first focusable element in <body> -->
<a class="skip-link" href="#main-content">Skip to main content</a>

<style>
.skip-link {
  position: absolute;
  left: -9999px;
}
.skip-link:focus {
  left: 0;
  top: 0;
  z-index: 9999;
  padding: 8px 16px;
  background: #000;
  color: #fff;
}
</style>
```

---

## Screen Reader Testing

Recommended testing combinations:
| Screen Reader | Browser | OS |
|---|---|---|
| NVDA (free) | Firefox or Chrome | Windows |
| JAWS | Chrome or Edge | Windows |
| VoiceOver | Safari | macOS / iOS |
| TalkBack | Chrome | Android |

### Manual Test Checklist
- [ ] Navigate with Tab only — all interactive content reachable
- [ ] All images announced with appropriate descriptions
- [ ] Form errors announced automatically or on focus
- [ ] Modals trap focus and return it on close
- [ ] Dynamic content changes announced (live regions)
- [ ] Page title announced on load
- [ ] Headings provide useful page outline (H key navigation)
