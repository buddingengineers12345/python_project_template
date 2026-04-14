# Jinja2 Coding Style

# applies-to: **/*.jinja

Jinja2 templates are used in this repository to generate Python project files via
Copier. These rules apply to every `.jinja` file under `template/`.

## Enabled extensions

The following Jinja2 extensions are active (configured in `copier.yml`):

- `jinja2_time.TimeExtension` — provides `{% now 'utc', '%Y' %}` for date injection.
- `jinja2.ext.do` — enables `{% do list.append(item) %}` for side-effect statements.
- `jinja2.ext.loopcontrols` — enables `{% break %}` and `{% continue %}` in loops.

Always use these extensions rather than working around them with complex filter chains.

## Variable substitution

Use `{{ variable_name }}` for all substitutions. Add a trailing space inside braces
only for readability in complex expressions, not as a general rule:

```jinja
{{ project_name }}
{{ author_name | lower | replace(" ", "-") }}
{{ python_min_version }}
```

## Control structures

Indent template logic blocks consistently with the surrounding file content.
Use `{%- -%}` (dash-trimmed) tags to suppress blank lines produced by control blocks
when the rendered output should be compact:

```jinja
{%- if include_docs %}
mkdocs:
  site_name: {{ project_name }}
{%- endif %}
```

Use `{% if %}...{% elif %}...{% else %}...{% endif %}` for branching.
Avoid deeply nested conditions; extract to a Jinja macro or simplify the data model.

## Whitespace control

- Use `{%- ... -%}` to strip leading/trailing whitespace around control blocks that
  should not produce blank lines in the output.
- Never strip whitespace blindly on every tag — it makes templates hard to read.
- Test rendered output with `copier copy . /tmp/test-output --trust --defaults` and
  inspect for spurious blank lines before committing.

## Filters

Prefer built-in Jinja2 filters over custom Python logic in templates:

| Goal | Filter |
|------|--------|
| Lowercase | `\| lower` |
| Replace characters | `\| replace("x", "y")` |
| Default value | `\| default("fallback")` |
| Join list | `\| join(", ")` |
| Trim whitespace | `\| trim` |

Avoid complex filter chains longer than 3 steps; compute the value in `copier.yml`
as a computed variable instead.

## Macros

Define reusable template fragments as macros at the top of the file or in a dedicated
`_macros.jinja` file (if the project grows to warrant it):

```jinja
{% macro license_header(year, author) %}
# Copyright (c) {{ year }} {{ author }}. All rights reserved.
{% endmacro %}
```

## File naming

- Suffix: `.jinja` (e.g. `pyproject.toml.jinja`, `__init__.py.jinja`).
- File names can themselves be Jinja expressions:
  `src/{{ package_name }}/__init__.py.jinja` renders to `src/mylib/__init__.py`.
- Keep file name expressions simple: variable substitution only, no filters.

## Commenting

Use Jinja comments (`{# comment #}`) for notes that should not appear in the rendered
output. Use the target language's comment syntax for notes that should survive rendering:

```jinja
{# This block is only rendered when pandas support is requested #}
{% if include_pandas_support %}
pandas>=2.0
{% endif %}

# This Python comment will appear in the generated file
import os
```

## Do not embed logic that belongs in copier.yml

Templates should be presentation, not computation. Move conditional logic to:
- `copier.yml` computed variables (`when: false`, `default: "{% if ... %}"`)
- Copier's `_tasks` for post-generation side effects

Deeply nested `{% if %}{% if %}{% if %}` blocks in a template are a signal to refactor.
