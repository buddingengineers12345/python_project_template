# Jinja built-in filters reference

## Quick Index
`abs` · `attr` · `batch` · `capitalize` · `center` · `count` · `d/default` · `dictsort` ·
`e/escape` · `filesizeformat` · `first` · `float` · `forceescape` · `format` · `groupby` ·
`indent` · `int` · `items` · `join` · `last` · `length` · `list` · `lower` · `map` ·
`max` · `min` · `pprint` · `random` · `reject` · `rejectattr` · `replace` · `reverse` ·
`round` · `safe` · `select` · `selectattr` · `slice` · `sort` · `string` · `striptags` ·
`sum` · `title` · `tojson` · `trim` · `truncate` · `unique` · `upper` · `urlencode` ·
`urlize` · `wordcount` · `wordwrap` · `xmlattr`

---

## Filters A–Z

### `abs`
Absolute value of a number.
```jinja
{{ -5 | abs }}  → 5
```

### `attr(name)`
Get an attribute by name. Returns `Undefined` (not `None`) if missing, unlike dot notation.
```jinja
{{ obj | attr("name") }}
```

### `batch(linecount, fill_with=None)`
Split an iterable into chunks of `linecount`. Optionally pad last row with `fill_with`.
```jinja
{% for row in items | batch(3, '&nbsp;') %}
  <tr>{% for col in row %}<td>{{ col }}</td>{% endfor %}</tr>
{% endfor %}
```

### `capitalize`
First character uppercase, rest lowercase.
```jinja
{{ "hello world" | capitalize }}  → Hello world
```

### `center(width=80)`
Center a string in a field of given width.

### `count` — alias for `length`

### `d` / `default(value='', boolean=False)`
Return `value` if the variable is undefined. If `boolean=True`, also triggers on falsy values.
```jinja
{{ user.bio | default("No bio.") }}
{{ count | default(0, boolean=True) }}   {# catches 0, '', [], None, undefined #}
```

### `dictsort(case_sensitive=False, by='key', reverse=False)`
Sort a dict and yield (key, value) pairs.
```jinja
{% for key, val in mydict | dictsort %}{{ key }}: {{ val }}{% endfor %}
{% for key, val in mydict | dictsort(by='value', reverse=True) %}...{% endfor %}
```

### `e` / `escape`
HTML-escape a string: `&`, `<`, `>`, `"`, `'` → entities.
```jinja
{{ user_input | e }}
```

### `filesizeformat(binary=False)`
Format a byte count as human-readable file size.
```jinja
{{ 1000000 | filesizeformat }}          → 1.0 MB
{{ 1048576 | filesizeformat(binary=True) }} → 1.0 MiB
```

### `first`
Return first item of a sequence.
```jinja
{{ items | first }}
```

### `float(default=0.0)`
Convert to float. Returns `default` on failure.
```jinja
{{ "3.14" | float }}  → 3.14
```

### `forceescape`
HTML-escape and mark result as safe (bypasses auto-escape). Use when the value is already Markup and you still want to escape it.
```jinja
{{ content | forceescape }}
```

### `format(*args, **kwargs)`
Apply Python string formatting.
```jinja
{{ "%s is %s" | format("Jinja", "great") }}  → Jinja is great
```

### `groupby(attribute, default=None)`
Group a sequence of dicts/objects by an attribute. Returns `(grouper, list)` pairs.
```jinja
{% for city, people in persons | groupby("city") %}
  <h3>{{ city }}</h3>
  <ul>{% for p in people %}<li>{{ p.name }}</li>{% endfor %}</ul>
{% endfor %}
```

### `indent(width=4, first=False, blank=False)`
Indent each line. `first=True` also indents the first line. `blank=True` indents blank lines.
```jinja
{{ long_text | indent(2) }}
```

### `int(default=0, base=10)`
Convert to integer. Returns `default` on failure.
```jinja
{{ "42" | int }}       → 42
{{ "0xff" | int(base=16) }} → 255
```

### `items` *(v3.1+)*
Return `(key, value)` pairs from a mapping. Returns empty iterator if value is `Undefined`.
```jinja
{% for key, val in data | items %}{{ key }}: {{ val }}{% endfor %}
```

### `join(d='', attribute=None)`
Join items as a string. `attribute` extracts a field before joining.
```jinja
{{ words | join(', ') }}
{{ users | join(', ', attribute='name') }}
```

### `last`
Return last item of a sequence.
```jinja
{{ items | last }}
```

### `length` / `count`
Return the number of items in a sequence or string.
```jinja
{{ items | length }}
```

### `list`
Convert the value to a list.
```jinja
{{ "hello" | list }}  → ['h', 'e', 'l', 'l', 'o']
```

### `lower`
Convert to lowercase.
```jinja
{{ "HELLO" | lower }}  → hello
```

### `map(attribute=None, *args, **kwargs)` or `map(filter_name, ...)`
Apply a filter or extract an attribute from each item in a sequence.
```jinja
{{ users | map(attribute='name') | join(', ') }}
{{ numbers | map('abs') | list }}
```

### `max(attribute=None, default=None)`
Return the largest item.
```jinja
{{ values | max }}
{{ products | max(attribute='price') }}
```

### `min(attribute=None, default=None)`
Return the smallest item.
```jinja
{{ values | min }}
```

### `pprint`
Pretty-print a variable (for debugging).
```jinja
<pre>{{ my_object | pprint }}</pre>
```

### `random`
Return a random item from a sequence.
```jinja
{{ ['a', 'b', 'c'] | random }}
```

### `reject(test, *args, **kwargs)`
Filter items where the test is **true** (keep items that fail the test — opposite of `select`).
```jinja
{{ numbers | reject('odd') | list }}   {# keeps even numbers #}
```

### `rejectattr(attr, test, *args, **kwargs)`
Filter objects where `object.attr` passes the test.
```jinja
{{ users | rejectattr('active') | list }}   {# keeps inactive users #}
```

### `replace(old, new, count=None)`
Replace occurrences of `old` with `new`.
```jinja
{{ "Hello World" | replace("World", "Jinja") }}  → Hello Jinja
```

### `reverse`
Reverse a string or sequence.
```jinja
{{ "abcde" | reverse }}  → edcba
{{ items | reverse | list }}
```

### `round(precision=0, method='common')`
Round a number. Methods: `'common'` (rounds half up), `'ceil'`, `'floor'`.
```jinja
{{ 3.7 | round }}              → 4.0
{{ 3.14159 | round(2) }}       → 3.14
{{ 3.5 | round(method='floor') }} → 3.0
```

### `safe`
Mark the value as safe HTML — Jinja will not auto-escape it.
```jinja
{{ trusted_html_string | safe }}
```
⚠️ **Never use on user-supplied input.**

### `select(test, *args, **kwargs)`
Keep only items where the test is **true**.
```jinja
{{ numbers | select('odd') | list }}
{{ values | select('greaterthan', 10) | list }}
```

### `selectattr(attr, test, *args, **kwargs)`
Keep objects where `object.attr` passes the test.
```jinja
{{ users | selectattr('active') | list }}
{{ products | selectattr('price', 'lessthan', 50) | list }}
```

### `slice(slices, fill_with=None)`
Split a sequence into `slices` sub-lists (for column layouts).
```jinja
{% for column in items | slice(3) %}
  <div class="col">{% for item in column %}{{ item }}{% endfor %}</div>
{% endfor %}
```

### `sort(reverse=False, case_sensitive=False, attribute=None)`
Sort a sequence.
```jinja
{{ words | sort }}
{{ products | sort(attribute='name') }}
{{ prices | sort(reverse=True) }}
```

### `string`
Convert the value to a string.
```jinja
{{ 42 | string }}  → "42"
```

### `striptags`
Strip HTML/XML tags, normalize whitespace.
```jinja
{{ "<b>Hello</b> <i>World</i>" | striptags }}  → Hello World
```

### `sum(attribute=None, start=0)`
Sum items in a sequence. Optionally sum by attribute.
```jinja
{{ [1, 2, 3, 4] | sum }}               → 10
{{ cart_items | sum(attribute='price') }}
```

### `title`
Title-case a string (first letter of each word capitalized).
```jinja
{{ "hello world" | title }}  → Hello World
```

### `tojson(indent=None)`
Serialize to JSON string and mark as safe (for embedding in `<script>` tags).
```jinja
<script>var data = {{ my_dict | tojson(indent=2) }};</script>
```

### `trim(chars=None)`
Strip leading/trailing whitespace (or `chars`).
```jinja
{{ "  hello  " | trim }}  → "hello"
```

### `truncate(length=255, killwords=False, end='...', leeway=0)`
Truncate a string. `killwords=True` cuts mid-word; `False` truncates at word boundary.
```jinja
{{ long_text | truncate(100) }}
{{ long_text | truncate(50, killwords=True, end=' [read more]') }}
```

### `unique(case_sensitive=False, attribute=None)`
Remove duplicates from a sequence.
```jinja
{{ tags | unique | list }}
{{ items | unique(attribute='id') | list }}
```

### `upper`
Convert to uppercase.
```jinja
{{ "hello" | upper }}  → HELLO
```

### `urlencode`
Encode a string or dict as URL query parameters (percent-encoding).
```jinja
{{ "hello world" | urlencode }}  → hello+world
{{ {'page': 2, 'q': 'jinja'} | urlencode }}  → page=2&q=jinja
```

### `urlize(trim_url_limit=None, nofollow=False, target=None, rel=None, extra_schemes=None)`
Convert plain-text URLs into clickable `<a>` tags.
```jinja
{{ user_comment | urlize(40, nofollow=True, target='_blank') }}
```

### `wordcount`
Count words in a string.
```jinja
{{ article.body | wordcount }}
```

### `wordwrap(width=79, break_long_words=True, wrapstring=None)`
Wrap text at word boundaries.

### `xmlattr(indent=1)`
Build an HTML/XML attribute string from a dict, filtering out `None` values.
```jinja
<ul {{ {'class': 'my-list', 'id': list_id} | xmlattr }}>
{# → <ul class="my-list" id="main"> #}
```

---

## Filter Chaining Patterns

```jinja
{# Get top 5 active users sorted by name #}
{{ users | selectattr('active') | sort(attribute='name') | list | first(5) }}

{# Build a comma-separated list of names from dicts #}
{{ records | map(attribute='name') | map('title') | join(', ') }}

{# Safe-render a nullable text field #}
{{ post.summary | default('') | truncate(150) | e }}
```