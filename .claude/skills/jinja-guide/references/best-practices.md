# Jinja best practices and patterns

## Table of Contents
1. [Project Structure & File Naming](#project-structure--file-naming)
2. [Template Design Principles](#template-design-principles)
3. [Naming Conventions](#naming-conventions)
4. [Whitespace & Formatting Conventions](#whitespace--formatting-conventions)
5. [Security Rules](#security-rules)
6. [Performance](#performance)
7. [Maintainability & Refactoring](#maintainability--refactoring)
8. [Debugging Templates](#debugging-templates)
9. [Platform-Specific Patterns](#platform-specific-patterns)
   - [Flask / Web HTML](#flask--web-html)
   - [Ansible](#ansible)
   - [dbt (SQL macros)](#dbt-sql-macros)
   - [Salt / Config files](#salt--config-files)

---

## Project Structure & File Naming

### Recommended Directory Layout

```
templates/
├── base.html                  # root base layout
├── _layout/                   # intermediate layout layers
│   ├── two-column.html
│   └── full-width.html
├── partials/                  # reusable partial includes
│   ├── _header.html           # prefix _ = include-only, not a standalone page
│   ├── _footer.html
│   ├── _pagination.html
│   └── _flash-messages.html
├── macros/                    # macro libraries (never rendered directly)
│   ├── forms.html
│   ├── ui.html
│   └── utils.html
├── auth/                      # feature grouping
│   ├── login.html
│   └── register.html
└── blog/
    ├── list.html
    └── detail.html
```

**Key conventions:**
- Prefix partial/include files with `_` to signal they are never rendered as standalone pages
- Group macros into topical files inside `macros/` — never scatter macros across page templates
- Group page templates by feature/section, not by template level
- Use `.j2` extension for non-HTML Jinja files (configs, SQL, YAML, etc.)

---

## Template Design Principles

### 1. Keep Logic in Python, Not Templates
Templates should **transform** data, not **compute** it.

❌ **Wrong — complex computation in template:**
```jinja
{% set total = 0 %}
{% for item in cart %}
  {% set total = total + (item.price * item.quantity) %}  {# scope bug! #}
{% endfor %}
Total: {{ total }}
```

✅ **Right — pass computed data from Python:**
```python
total = sum(item.price * item.quantity for item in cart)
return render_template("cart.html", cart=cart, total=total)
```

### 2. DRY — Extract Repetition
If you copy-paste 3+ lines of Jinja into two or more templates → create a macro.

### 3. Single Responsibility Blocks
Each `{% block %}` should do one thing. Don't put entire pages in a single `content` block.

### 4. Fail Visibly During Development
Use `StrictUndefined` in development so missing variables raise errors rather than silently rendering empty:
```python
from jinja2 import Environment, StrictUndefined
env = Environment(undefined=StrictUndefined)
```

### 5. One `{% extends %}` Per Template
Jinja does not support multiple inheritance. If you need shared behavior across multiple inheritance chains, use macros and includes.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Template files | `kebab-case.html` | `user-profile.html` |
| Partial/include files | `_kebab-case.html` | `_pagination.html` |
| Macro files | `kebab-case.html` in `macros/` | `macros/forms.html` |
| Jinja config files | `service-name.j2` | `nginx.conf.j2` |
| Block names | `snake_case` | `{% block page_title %}` |
| Macro names | `snake_case` | `{% macro render_card(...) %}` |
| Variables in templates | `snake_case` | `{{ user_profile.full_name }}` |

---

## Whitespace & Formatting Conventions

### Rule: One Blank Line Between Blocks
```jinja
{% block header %}...{% endblock header %}

{% block content %}...{% endblock content %}
```

### Rule: Indent Template Logic to Match Output Indentation
```jinja
<ul>
  {% for item in items %}
  <li>{{ item.name }}</li>
  {% endfor %}
</ul>
```

### Rule: Use `{%- -%}` Only When Blank Lines Would Appear in Output
Overusing whitespace stripping makes templates unreadable. Only strip when the rendered output has unwanted blank lines.

```jinja
{# BAD — hard to read, strips everything #}
{%- if x -%}{%- for y in x -%}{{ y }}{%- endfor -%}{%- endif -%}

{# GOOD — strip only the newline after block tags #}
{% if x %}
  {% for item in x %}
  {{ item }}
  {%- endfor %}
{% endif %}
```

### Rule: Always Close Blocks Explicitly
```jinja
{% endfor %}        ✓
{% endblock %}      ✓
{% endblock content %}  ✓ (preferred for long blocks)
{% endif %}         ✓
{% endmacro %}      ✓
```

---

## Security Rules

### Rule 1: Never Use `| safe` on User Data
```jinja
{# DANGEROUS — XSS vulnerability #}
{{ request.args.get('message') | safe }}

{# SAFE — escape user input #}
{{ request.args.get('message') | e }}
```

### Rule 2: Enable Autoescaping in HTML Contexts
```python
env = Environment(autoescape=select_autoescape(['html', 'xml']))
```

### Rule 3: Use `| tojson` for Embedding Data in `<script>` Tags
```jinja
{# SAFE — tojson escapes for JavaScript context #}
<script>var config = {{ app_config | tojson }};</script>

{# DANGEROUS — raw dict output is not JS-safe #}
<script>var config = {{ app_config }};</script>
```

### Rule 4: Use `{% raw %}` When Showing Jinja Code
```jinja
{% raw %}
  <p>Template variables look like {{ this }}</p>
{% endraw %}
```

### Rule 5: Validate Input Before Passing to Templates
Do not rely on templates as a security layer. Validate and sanitize in application code.

---

## Performance

### Use Bytecode Caching in Production
```python
from jinja2 import Environment, FileSystemBytecodeCache
bc = FileSystemBytecodeCache('/tmp/jinja_cache')
env = Environment(loader=..., bytecode_cache=bc)
```

### Avoid Expensive Operations Inside Loops
```jinja
{# BAD — calling an expensive function N times #}
{% for item in items %}
  {{ item | expensive_custom_filter }}
{% endfor %}

{# GOOD — pre-process in Python, pass clean data #}
{# In Python: items = [process(i) for i in raw_items] #}
{% for item in items %}
  {{ item.processed_value }}
{% endfor %}
```

### Use `selectattr` / `rejectattr` Instead of If Inside Loops
```jinja
{# Less efficient #}
{% for user in all_users %}
  {% if user.active %}{{ user.name }}{% endif %}
{% endfor %}

{# More readable and avoids empty loop iterations #}
{% for user in all_users | selectattr('active') %}
  {{ user.name }}
{% endfor %}
```

---

## Maintainability & Refactoring

### When to Extract a Macro
Extract into a macro when you see any of these:
- The same 3+ lines appear in 2+ templates
- A conditional block renders differently based on a parameter
- A form field pattern repeats with minor variations

### When to Create an Intermediate Base Template
Create a layout layer (`_layout/two-column.html`) when:
- Multiple page templates need the same structural variant
- You'd otherwise `{{ super() }}` the same content in many children

### Updating a Template Without Breaking Children

1. **Adding a new block to a base template:** Safe — children that don't override it inherit the default content
2. **Renaming a block:** Breaking change — update all child templates before renaming
3. **Removing a block:** Breaking change — check all child templates for overrides first
4. **Changing a macro signature (adding required arg):** Breaking change — add a default value to avoid breaking callers
5. **Changing a macro signature (adding optional arg with default):** Safe

### Template Auditing Checklist (for existing templates)
- [ ] Does every child template's `{% extends %}` still point to the correct base?
- [ ] Are there blocks defined in children that no longer exist in the parent?
- [ ] Are macros imported but unused (dead imports)?
- [ ] Are there `| safe` usages? Audit each one — is it truly safe content?
- [ ] Are there undefined-variable risks? Add `| default()` guards.
- [ ] Is whitespace control consistent throughout the file?

---

## Debugging Templates

### Print All Context Variables
```jinja
<pre>{{ joiner() }}</pre>
{# Or in a debug block: #}
{% for key, value in [] | items %}{% endfor %}
```

Better: add this to any template during debugging:
```jinja
{% if debug %}
  <details>
    <summary>Template Context</summary>
    <pre>{{ context | pprint }}</pre>
  </details>
{% endif %}
```

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `UndefinedError: 'X' is undefined` | Variable missing from context | Add `| default()` or pass variable from Python |
| `TemplateSyntaxError: unexpected '}'` | Delimiter mismatch | Check for unclosed `{{` or `{%` |
| Block content not appearing | Wrong block name in child | Verify name matches exactly (case-sensitive) |
| `super()` renders nothing | `super()` called in a block that has no parent content | Expected behavior — parent block is empty |
| Loop variable scope issue | `{% set %}` inside loop not visible outside | Use `namespace()` — see `references/syntax.md` |
| Double-escaped output `&amp;lt;` | `| safe` + autoescape conflict | Remove redundant `| safe` or `| escape` |
| Included template can't access variable | Variable set after `{% include %}` | Set variables before include, or use macros instead |

---

## Platform-Specific Patterns

### Flask / Web HTML

```jinja
{# url_for generates URLs from route names #}
<a href="{{ url_for('auth.login') }}">Login</a>
<img src="{{ url_for('static', filename='img/logo.png') }}">

{# Flash messages pattern #}
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
  {% endfor %}
{% endwith %}

{# CSRF token in forms #}
<form method="post">
  {{ csrf_token() }}
  {# ... #}
</form>
```

### Ansible

Ansible uses Jinja2 for variable interpolation in playbooks and templates (`.j2` config files).

```jinja
{# ansible.cfg.j2 — typical config template #}
[defaults]
inventory = {{ ansible_inventory_path }}
remote_user = {{ ansible_user | default('ansible') }}
private_key_file = {{ ssh_key_path }}

{# Use 'is defined' guards — Ansible variables are often optional #}
{% if nginx_worker_processes is defined %}
worker_processes {{ nginx_worker_processes }};
{% else %}
worker_processes auto;
{% endif %}

{# Ansible-specific: use filters provided by Ansible, e.g. #}
{{ list_of_hosts | join('\n') }}
{{ my_var | mandatory }}        {# fails if variable is not set #}
{{ path | basename }}
{{ path | dirname }}
```

**Ansible-specific rules:**
- Always guard optional variables with `| default()` or `is defined` — Ansible contexts are variable by host
- Use `| mandatory` on required variables to get clear errors instead of silent empty values
- Never use `| safe` in Ansible templates — output goes to config files, not HTML
- Prefer `{%- -%}` whitespace stripping for config file templates where blank lines matter

### dbt (SQL Macros)

dbt uses Jinja2 in SQL files. Macros generate SQL fragments; `ref()` and `source()` are core dbt functions.

```jinja
{# models/orders.sql #}
with orders as (
  select * from {{ ref('stg_orders') }}
),
customers as (
  select * from {{ ref('stg_customers') }}
)
select
  o.id,
  o.amount,
  c.name as customer_name
from orders o
join customers c on o.customer_id = c.id
{% if is_incremental() %}
  where o.updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

```jinja
{# macros/generate_schema_name.sql #}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- set default_schema = target.schema -%}
  {%- if custom_schema_name is none -%}
    {{ default_schema }}
  {%- else -%}
    {{ default_schema }}_{{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
```

**dbt-specific rules:**
- Always use `{%- -%}` (strip all whitespace) in SQL macros — extra whitespace can break SQL formatting
- Use `ref()` for model references; never hard-code table names
- Use `{{ this }}` only inside incremental models
- Keep macro files in `macros/` directory at project root
- Add docstrings to macros using `{% docs %}` blocks

### Salt / Config Files

```jinja
{# /etc/nginx/nginx.conf.j2 #}
worker_processes {{ grains['num_cpus'] }};

events {
  worker_connections {{ pillar.get('nginx:worker_connections', 1024) }};
}

http {
{% for vhost in pillar.get('nginx:vhosts', []) %}
  server {
    listen {{ vhost.port | default(80) }};
    server_name {{ vhost.hostname }};
    root {{ vhost.root }};
  }
{% endfor %}
}
```

**Salt/config-specific rules:**
- Use `pillar.get('key', default)` instead of `{{ pillar['key'] }}` to avoid errors on missing pillars
- Use `grains` for machine-specific facts
- Apply `{%- -%}` whitespace stripping to avoid blank lines in generated config files
- Test rendered output with `salt-call slsutil.renderer` before deploying