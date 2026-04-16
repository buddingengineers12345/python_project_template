# Jinja inheritance, includes, imports, and macros

## Table of Contents
1. [Template Inheritance — Full Patterns](#template-inheritance--full-patterns)
2. [Block Scoping & Nesting](#block-scoping--nesting)
3. [super() — Preserve Parent Content](#super---preserve-parent-content)
4. [Multi-Level Inheritance](#multi-level-inheritance)
5. [Scoped Blocks](#scoped-blocks)
6. [Include](#include)
7. [Import](#import)
8. [Import Context Behavior](#import-context-behavior)
9. [Macros — Advanced Patterns](#macros--advanced-patterns)
10. [Call Blocks](#call-blocks)

---

## Template Inheritance — Full Patterns

### Anatomy of a Well-Structured Base Template

```jinja
{# templates/base.html #}
<!DOCTYPE html>
<html lang="{{ lang | default('en') }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}{% endblock %} — {{ site_name }}</title>
  {% block meta %}{% endblock %}
  {% block styles %}
    <link rel="stylesheet" href="/static/css/main.css">
  {% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
  {% block header %}
    <header>
      <nav>{% block nav %}{% endblock %}</nav>
    </header>
  {% endblock %}

  <main id="content">
    {% block content %}{% endblock %}
  </main>

  {% block sidebar %}{% endblock %}

  {% block footer %}
    <footer>{% block footer_content %}&copy; {{ year }}{% endblock %}</footer>
  {% endblock %}

  {% block scripts %}{% endblock %}
</body>
</html>
```

### Named End-Tags for Readability
Always name end-tags in complex templates:
```jinja
{% block content %}
  {% for item in items %}
    {# ... #}
  {% endfor %}
{% endblock content %}   {# ← name makes it clear what's closing #}
```

---

## Block Scoping & Nesting

Blocks can be nested. Each block is independently overridable:
```jinja
{# base.html #}
{% block outer %}
  <div class="outer">
    {% block inner %}Default inner content{% endblock %}
  </div>
{% endblock %}
```

```jinja
{# child.html #}
{% extends "base.html" %}
{% block inner %}Custom inner only — outer <div> is preserved{% endblock %}
```

**Rule:** A block defined in a parent creates an override point. The child can override any block at any nesting level independently.

**You cannot define the same block name twice** in one template. If you need to render a block's content in multiple places, use `self`:
```jinja
<title>{% block title %}Page{% endblock %}</title>
<h1>{{ self.title() }}</h1>   {# re-renders the title block #}
```

---

## super() — Preserve Parent Content

`super()` renders the parent's block content, then you append/prepend:
```jinja
{# Append to parent styles block #}
{% block styles %}
  {{ super() }}
  <link rel="stylesheet" href="/static/css/page-specific.css">
{% endblock %}

{# Prepend to parent nav block #}
{% block nav %}
  <a href="/">Home</a>
  {{ super() }}
{% endblock %}
```

---

## Multi-Level Inheritance

Inheritance chains can be arbitrarily deep. Each level only overrides what it needs:

```
base.html
  └── layout.html  (adds two-column layout)
        └── page.html  (fills content blocks)
```

```jinja
{# layout.html — intermediate layer #}
{% extends "base.html" %}

{% block content %}
  <div class="two-col">
    <section>{% block main %}{% endblock %}</section>
    <aside>{% block sidebar %}{% endblock %}</aside>
  </div>
{% endblock %}
```

```jinja
{# page.html — leaf template #}
{% extends "layout.html" %}

{% block title %}My Page{% endblock %}
{% block main %}<p>Main content here.</p>{% endblock %}
{% block sidebar %}<p>Sidebar here.</p>{% endblock %}
```

---

## Scoped Blocks

By default, blocks do not have access to variables set in the surrounding scope (loop variables, etc.). Use the `scoped` modifier:

```jinja
{% for item in items %}
  {% block item_row scoped %}
    <tr><td>{{ item.name }}</td></tr>
  {% endblock %}
{% endfor %}
```

Without `scoped`, `item` would not be accessible inside the block when it's overridden by a child.

---

## Include

`{% include %}` embeds another template and renders it with the **current context** (all variables are shared):

```jinja
{% include "partials/_header.html" %}
{% include "partials/_footer.html" %}

{# Ignore if template doesn't exist: #}
{% include "optional_banner.html" ignore missing %}

{# Include one of several options, use first found: #}
{% include ['custom_header.html', 'default_header.html'] %}
```

**Use include for:**
- Static partials (nav, footer, sidebar) shared across many templates
- Content that always uses the parent context unchanged

**Do NOT use include when:**
- The partial needs different data each call → use a macro instead
- You're importing reusable logic/macros → use import instead

---

## Import

Import loads a template for its **exported macros and variables** without rendering it. Imported templates do NOT share the caller's context by default.

```jinja
{# Full namespace import #}
{% import "macros/ui.html" as ui %}
{{ ui.button('Save', type='submit') }}
{{ ui.alert('Warning!', level='warn') }}

{# Selective import — no namespace prefix #}
{% from "macros/forms.html" import input, textarea, select %}
{{ input('username', label='Username') }}
```

**Import context behavior:**
- By default, imported templates are **context-isolated** — they cannot access the current template's variables
- This is intentional: macros should be self-contained
- To share context explicitly (use sparingly):
```jinja
{% from "macros/ui.html" import card with context %}
```

---

## Import Context Behavior

Understanding what is exported from an import target:

```jinja
{# macros/helpers.html #}
{% macro format_date(d) %}{{ d | strftime('%Y-%m-%d') }}{% endmacro %}
{% set ICON_PATH = "/static/icons/" %}
{# ↑ Both the macro and the top-level set variable are exported and importable #}
```

**What IS exported:** macros, top-level `{% set %}` variables

**What is NOT exported:** output rendered inside the template, loop variables, block-level assignments

---

## Macros — Advanced Patterns

### Basic Macro with Defaults
```jinja
{% macro render_card(title, body, footer='', css_class='card') %}
  <div class="{{ css_class }}">
    <h3>{{ title }}</h3>
    <p>{{ body }}</p>
    {% if footer %}
      <small>{{ footer }}</small>
    {% endif %}
  </div>
{% endmacro %}
```

### Variadic Arguments
```jinja
{% macro tag(name, *content, **attrs) %}
  <{{ name }}
  {%- for key, val in attrs.items() %} {{ key }}="{{ val }}"{% endfor %}>
    {{ content | join(' ') }}
  </{{ name }}>
{% endmacro %}

{{ tag('a', 'Click me', href='/path', class='btn') }}
```

**Special macro variables:**
| Variable | Meaning |
|----------|---------|
| `varargs` | Extra positional args as tuple |
| `kwargs` | Extra keyword args as dict |
| `caller()` | Content from a `{% call %}` block |

### Recursive Macros
```jinja
{% macro render_tree(nodes) %}
  <ul>
  {% for node in nodes %}
    <li>
      {{ node.label }}
      {% if node.children %}
        {{ render_tree(node.children) }}
      {% endif %}
    </li>
  {% endfor %}
  </ul>
{% endmacro %}
```

### Macro Introspection
```jinja
{{ my_macro.name }}        {# "my_macro" #}
{{ my_macro.arguments }}   {# list of argument names #}
{{ my_macro.catch_kwargs }} {# True if macro accepts **kwargs #}
```

---

## Call Blocks

`{% call %}` lets you pass a block of template content into a macro as `caller()`. Use for wrapper components (modals, panels, cards that wrap arbitrary content):

```jinja
{# Define a macro that wraps content #}
{% macro modal(title, id='modal') %}
  <div class="modal" id="{{ id }}">
    <div class="modal-header"><h2>{{ title }}</h2></div>
    <div class="modal-body">
      {{ caller() }}       {# ← renders the call block content #}
    </div>
  </div>
{% endmacro %}
```

```jinja
{# Use it with a call block #}
{% call modal("Confirm Delete") %}
  <p>Are you sure you want to delete this item?</p>
  <button>Yes, delete</button>
{% endcall %}
```

**Caller with arguments:**
```jinja
{% macro render_list(items) %}
  <ul>
  {% for item in items %}
    <li>{{ caller(item) }}</li>   {# ← pass current item to caller #}
  {% endfor %}
  </ul>
{% endmacro %}

{% call(item) render_list(products) %}
  <strong>{{ item.name }}</strong> — ${{ item.price }}
{% endcall %}
```

---

## Recursive For Loops

The `recursive` modifier + `loop()` call enables tree traversal without macros:

```jinja
<ul>
{% for item in sitemap recursive %}
  <li>
    <a href="{{ item.url }}">{{ item.title }}</a>
    {% if item.children %}
      <ul>{{ loop(item.children) }}</ul>
    {% endif %}
  </li>
{% endfor %}
</ul>
```

---

## Loop Controls (Extension)

When `jinja2.ext.loopcontrols` is enabled:
```jinja
{% for item in items %}
  {% if item.skip %}{% continue %}{% endif %}
  {% if item.stop_here %}{% break %}{% endif %}
  {{ item.value }}
{% endfor %}
```

---

## Null-Master Fallback Pattern

When a template may or may not extend a base (useful for AJAX partial rendering):
```jinja
{# In the template, check if a master layout exists #}
{% if master is defined %}
  {% extends master %}
{% endif %}
```
