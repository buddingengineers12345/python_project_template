---
name: jinja-guide
description: >-
  Expert Jinja2 template authoring, maintenance, and refactoring skill. Use
  this skill whenever the user mentions Jinja, Jinja2, .j2 files, .jinja
  files, or template files used with Flask, Ansible, dbt, SaltStack, Pelican,
  or any other Jinja-powered system. Triggers on requests to: create a Jinja
  template, update/edit an existing .j2 or .jinja file, add macros, fix
  template inheritance, debug template errors, refactor templates, add
  filters, write base/child templates, or follow Jinja best practices. Also
  triggers on phrases like "template logic", "block override", "extend base
  template", "jinja macro", "jinja filter", "whitespace control", or
  "template variable". Always consult this skill before writing any Jinja
  template code.
---

# Jinja Guide Skill

Author, maintain, and refactor Jinja2 templates for Flask, Ansible, dbt,
SaltStack, Pelican, and other Jinja-powered systems. Priorities: clean
inheritance, safe escaping, predictable whitespace, and reusable macros.

## Delimiter cheat-sheet

| Syntax                             | Purpose                                  |
|------------------------------------|------------------------------------------|
| `{{ expression }}`                 | Output — print a variable or expression  |
| `{% statement %}`                  | Logic — control flow, assignments, blocks |
| `{# comment #}`                    | Comment — stripped from output entirely  |
| `{{- … -}}` / `{%- … -%}`          | Strip whitespace on that side            |

## Workflow

### 1. Classify the task

Before writing or editing, decide which scenario applies:

- **New standalone template** → variables, filters, control structures; no
  inheritance needed unless part of a larger project
- **New template in a project** → check for a base template; use
  `{% extends %}` + `{% block %}`
- **Editing an existing template** → read the file first; preserve existing
  block structure and whitespace conventions
- **Refactoring** → extract repetition into macros; flatten over-nested
  logic; review whitespace control
- **Debugging** → check for delimiter mismatches, undefined variables, scope
  issues, block name conflicts

### 2. Use the core syntax

**Variables:**

```jinja
{{ user.name }}                         {# dot notation #}
{{ user['name'] }}                      {# bracket — identical result #}
{{ users[0].email }}                    {# index then attribute #}
{{ config.DEBUG | default(false) }}     {# safe default for optional vars #}
```

**For loops:**

```jinja
{% for item in items %}
  {{ loop.index }}. {{ item.name }}
  {% if loop.last %}<hr>{% endif %}
{% else %}
  <p>No items found.</p>
{% endfor %}
```

Loop variables: `loop.index` (1-based), `loop.index0`, `loop.revindex`,
`loop.first`, `loop.last`, `loop.length`, `loop.depth` (for nested loops),
`loop.cycle('odd','even')`.

**If / elif / else:**

```jinja
{% if user.is_admin %}
  <a href="/admin">Admin Panel</a>
{% elif user.is_staff %}
  <a href="/dashboard">Dashboard</a>
{% else %}
  <a href="/login">Log In</a>
{% endif %}
```

**Assignments** (single-line `set`, and multi-line block `set`):

```jinja
{% set title = "My Page" %}
{% set items = ['a', 'b', 'c'] %}

{% set navigation %}
  <nav>…</nav>
{% endset %}
```

**Filters** are applied with `|` and chain left-to-right:

```jinja
{{ name | upper }}
{{ text | truncate(100) }}
{{ items | length }}
{{ value | default("N/A") }}
{{ html_content | escape }}
{{ trusted_html | safe }}            {# USE WITH CAUTION #}
{{ names | join(', ') }}
{{ dict_var | items }}               {# iterate key/value pairs — Jinja 3.1+ #}
```

**Tests** use the `is` keyword:

```jinja
{% if value is defined %}
{% if value is none %}
{% if loop.index is odd %}
{% if number is divisibleby(3) %}
```

For the complete operator list, literal syntax, global functions, and line
statements, see [references/syntax.md](references/syntax.md). For the full
A–Z filter list with signatures, see
[references/filters-reference.md](references/filters-reference.md).

### 3. Build on template inheritance

Inheritance is Jinja's most powerful feature. Use it for every multi-page
project.

**Base template (`base.html`):**

```jinja
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Default Title{% endblock %}</title>
  {% block head %}{% endblock %}
</head>
<body>
  {% block header %}
    <header><h1>My Site</h1></header>
  {% endblock %}
  <main>{% block content %}{% endblock %}</main>
  {% block footer %}<footer>&copy; 2026</footer>{% endblock %}
  {% block scripts %}{% endblock %}
</body>
</html>
```

**Child template:**

```jinja
{% extends "base.html" %}

{% block title %}About Us{% endblock %}

{% block content %}
  <h2>About</h2>
  <p>Welcome to our site.</p>
{% endblock %}
```

Rules to internalize:

- `{% extends %}` MUST be the first tag in a child template
- A child may have only ONE `{% extends %}` — no multiple inheritance
- Call `{{ super() }}` inside a block to include the parent's content
- Name end-tags for readability on long blocks: `{% endblock content %}`
- Use `self.blockname()` to re-use a block's content elsewhere in the same template

Deep patterns (`{% include %}`, `{% import %}`, `call` blocks, scoped blocks,
macro scope) are in [references/inheritance.md](references/inheritance.md).

### 4. Extract repetition into macros

Macros are template functions — define once, call many times.

```jinja
{# macros/forms.html #}
{% macro input(name, value='', type='text', label='') %}
  <div class="field">
    {% if label %}<label for="{{ name }}">{{ label }}</label>{% endif %}
    <input type="{{ type }}" id="{{ name }}" name="{{ name }}" value="{{ value }}">
  </div>
{% endmacro %}
```

Use by importing individual macros or a whole namespace:

```jinja
{% from "macros/forms.html" import input %}
{{ input('username', label='Username') }}
{{ input('password', type='password', label='Password') }}

{% import "macros/forms.html" as forms %}
{{ forms.input('email', label='Email') }}
```

For varargs/kwargs, `caller` blocks, and macro scope rules, see
[references/inheritance.md](references/inheritance.md).

### 5. Control whitespace deliberately

Jinja preserves all whitespace by default. Use `-` to strip:

```jinja
{%- for item in items -%}    {# strips newline before AND after the tag #}
  {{ item }}
{%- endfor -%}
```

Convention: use `-%}` (strip trailing only) on block tags to avoid blank lines
in output, and `{%-` (strip leading) when a tag follows meaningful content.

### 6. Escape safely

Auto-escaping in the Environment handles most cases. When you need explicit
control:

```jinja
{{ user_input | e }}                {# escape shortcut #}
{{ user_input | escape }}           {# same #}
{{ known_safe_html | safe }}        {# ONLY for content you fully control #}

{% raw %}
  {{ this will NOT be processed }}  {# output verbatim Jinja syntax #}
{% endraw %}
```

**Security rule:** never apply `| safe` to user-supplied data. If the
template engine's auto-escape is disabled in your project, escape every
variable explicitly.

## Editing existing templates

Checklist to run before touching any `.j2` / `.jinja` file:

1. **Read the file in full** before making changes
2. **Identify the inheritance chain** — does it `{% extends %}` another file?
3. **Locate all `{% block %}` definitions** — map parent vs. child overrides
4. **Preserve whitespace conventions** — if the file uses `{%- -%}`, continue
5. **Check macro imports** — find their source before changing signatures
6. **Add blocks; don't remove them** — removing breaks child templates
7. **Test undefined variable safety** — use `| default()` or
   `{% if var is defined %}` for optional context

## Framework notes

Flask, Ansible, dbt, and Salt each add their own globals, filters, and
conventions on top of Jinja. Auto-escape defaults differ (Flask: on for
`.html`; Ansible: off by default). File-extension conventions differ
(`.html.j2`, `.yaml.j2`, `.sql`). For framework-specific patterns, project
structure, and security defaults, see
[references/best-practices.md](references/best-practices.md).

## When to load references

| If the task involves…                          | Load                              |
|-------------------------------------------------|-----------------------------------|
| Operator syntax, literals, global functions    | `references/syntax.md`            |
| Filter usage beyond basics (A-Z list)          | `references/filters-reference.md` |
| Template inheritance, include, import, macros  | `references/inheritance.md`       |
| Performance, security, testing best practices  | `references/best-practices.md`    |
| Simple template edits (default)                | No reference needed — use inline  |

## Efficiency: batch edits and parallel calls

- **Batch edits:** When modifying multiple template files, read all target
  templates first, then edit each in a single Edit call per file.
- **Read before edit:** Read the base template and child templates to understand
  the inheritance chain before making block changes.

## Quick reference: where to go deeper

| Topic                                                           | Reference file                                                           |
|-----------------------------------------------------------------|--------------------------------------------------------------------------|
| Operators, literals, expressions, globals, line statements      | [references/syntax.md](references/syntax.md)                             |
| Inheritance, `include`, `import`, `call`, macro scope           | [references/inheritance.md](references/inheritance.md)                   |
| Complete A–Z filter reference with signatures                   | [references/filters-reference.md](references/filters-reference.md)       |
| Project structure, naming, security, Flask/Ansible/dbt patterns | [references/best-practices.md](references/best-practices.md)             |
