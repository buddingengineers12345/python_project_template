# Jinja syntax reference

## Table of Contents
1. [Literals](#literals)
2. [Operators — Math](#operators--math)
3. [Operators — Comparison](#operators--comparison)
4. [Operators — Logic](#operators--logic)
5. [Operators — Other](#operators--other)
6. [If Expressions (Ternary)](#if-expressions-ternary)
7. [Tests (is keyword)](#tests-is-keyword)
8. [Global Functions](#global-functions)
9. [Line Statements](#line-statements)
10. [Undefined Variable Handling](#undefined-variable-handling)

---

## Literals

```jinja
"Hello"          {# string — double or single quotes #}
42               {# integer #}
42.5             {# float #}
['a', 'b', 'c']  {# list (tuple notation also works) #}
{'key': 'value'} {# dict #}
true / false     {# booleans (lowercase in Jinja) #}
none             {# Python None #}
```

---

## Operators — Math

| Operator | Meaning | Example | Result |
|----------|---------|---------|--------|
| `+` | Add / concatenate | `{{ 1 + 1 }}` | `2` |
| `-` | Subtract | `{{ 5 - 2 }}` | `3` |
| `*` | Multiply | `{{ 2 * 3 }}` | `6` |
| `/` | Divide (float) | `{{ 1 / 2 }}` | `0.5` |
| `//` | Floor divide | `{{ 7 // 2 }}` | `3` |
| `%` | Modulo | `{{ 11 % 3 }}` | `2` |
| `**` | Power | `{{ 2 ** 8 }}` | `256` |

> **Note:** Do not use `+` for string concatenation. Use `~` instead:
> `{{ "Hello" ~ " " ~ name }}` — the `~` operator converts operands to string first.

---

## Operators — Comparison

```jinja
==   !=   <   >   <=   >=
```

All return `true` or `false`. Usable in `{% if %}` and filter expressions.

---

## Operators — Logic

```jinja
and   or   not
```

```jinja
{% if user.active and not user.banned %}
  Welcome, {{ user.name }}!
{% endif %}
```

---

## Operators — Other

| Operator | Purpose | Example |
|----------|---------|---------|
| `~` | String concatenate | `{{ first ~ " " ~ last }}` |
| `\|` | Apply filter | `{{ name \| upper }}` |
| `is` | Test | `{% if x is defined %}` |
| `in` | Membership | `{% if 'admin' in user.roles %}` |
| `not in` | Negated membership | `{% if item not in blacklist %}` |
| `\|attr("x")` | Safe attribute access | `{{ obj \| attr("name") }}` |

---

## If Expressions (Ternary)

Inline conditional — useful inside output tags or assignments:
```jinja
{{ "yes" if user.active else "no" }}

{% set css_class = "active" if page == "home" else "inactive" %}

{{ value if value is defined else "default" }}
{# Equivalent to: #}
{{ value | default("default") }}
```

---

## Tests (`is` keyword)

Tests evaluate a variable against a condition. Use in `{% if %}` or `{% elif %}`.

### Built-in Tests

| Test | Returns true when... |
|------|----------------------|
| `is defined` | Variable exists in context |
| `is undefined` | Variable does NOT exist |
| `is none` | Value is `None` |
| `is boolean` | Value is `true` or `false` |
| `is integer` | Value is an integer |
| `is float` | Value is a float |
| `is number` | Value is integer or float |
| `is string` | Value is a string |
| `is sequence` | Value is iterable (list, tuple, string) |
| `is mapping` | Value is a dict-like object |
| `is iterable` | Value can be iterated |
| `is callable` | Value is callable |
| `is sameas X` | `value is X` (identity, like `is` in Python) |
| `is odd` | Integer is odd |
| `is even` | Integer is even |
| `is divisibleby(n)` | Integer divisible by n |
| `is upper` | String is all uppercase |
| `is lower` | String is all lowercase |
| `is escaped` | Value is already HTML-escaped Markup |
| `is in X` | Value is in collection X |
| `is filter(name)` | Named filter exists in environment |
| `is test(name)` | Named test exists in environment |

```jinja
{# Negate a test with 'not' #}
{% if value is not none %}
{% if name is not defined %}
```

---

## Global Functions

These are available in all templates without importing:

### `range(start=0, stop, step=1)`
```jinja
{% for i in range(5) %}{{ i }}{% endfor %}     {# 0 1 2 3 4 #}
{% for i in range(2, 10, 2) %}{{ i }} {% endfor %}  {# 2 4 6 8 #}
```

### `lipsum(n=5, html=True, min=20, max=100)`
Generates lorem ipsum text. Useful for prototyping.

### `dict(**items)`
```jinja
{% set d = dict(name='Alice', age=30) %}
```

### `class(name, bases=(), **attrs)`
Creates a new class object. Rarely needed in templates.

### `joiner(sep=', ')`
Stateful helper to insert a separator between items (skips on first call):
```jinja
{% set comma = joiner() %}
{% for tag in tags %}{{ comma() }}<a href="#">{{ tag }}</a>{% endfor %}
{# Output: <a>tag1</a>, <a>tag2</a>, <a>tag3</a> #}
```

### `cycler(*items)`
Cycles through values repeatedly:
```jinja
{% set row_class = cycler("odd", "even") %}
{% for item in items %}
  <tr class="{{ row_class.next() }}">...</tr>
{% endfor %}
```

### `namespace(**kwargs)`
Creates a mutable object to work around Jinja's scoping rules in loops:
```jinja
{% set ns = namespace(found=false, total=0) %}
{% for item in items %}
  {% if item.active %}
    {% set ns.found = true %}
    {% set ns.total = ns.total + item.value %}
  {% endif %}
{% endfor %}
Total active value: {{ ns.total }}
```
> **Important:** Regular `{% set %}` inside a loop does NOT persist outside the loop. Use `namespace()` when you need loop-scoped mutations to be visible after the loop.

---

## Line Statements

When enabled in the `Environment`, the `#` character starts a line statement:
```jinja
# for item in items
  - {{ item }}
# endfor
```
This is optional and not enabled by default. Prefer `{% %}` block tags for clarity.

---

## Undefined Variable Handling

Jinja's default behavior renders `Undefined` silently as an empty string. Stricter modes exist at the `Environment` level (`StrictUndefined`, `DebugUndefined`).

**In templates, always guard optional variables:**
```jinja
{# Option 1: default filter #}
{{ user.bio | default("No bio provided.") }}

{# Option 2: defined test #}
{% if user.bio is defined and user.bio %}
  <p>{{ user.bio }}</p>
{% endif %}

{# Option 3: ternary inline #}
{{ user.bio if user.bio is defined else "No bio." }}
```

**Never silently rely on undefined variables resolving to empty string** in production templates — use `default()` or explicit guards for all optional context values.