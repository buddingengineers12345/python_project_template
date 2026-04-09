# Code and links

Covers: inline code, fenced code blocks, language tags, escaping, all link types,
reference links, and automatic links.

**Primary source:** [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)

---

## Code

### Inline Code

Use single backticks for short code references, command names, file names, field
names, file extensions, paths, and environment variables:

```markdown
Run `really_cool_script.sh` before proceeding.
Update your `README.md` to reflect the new API.
Pay attention to the `user_id` field in the response.
Set the `DATABASE_URL` environment variable.
Files with `.env` extension are excluded by default.
```

#### Using Inline Code as an Escape Mechanism

Wrap anything that should **not** be parsed as Markdown in backticks — fake paths,
example URLs with query strings, template variables:

```markdown
An example path would be: `path/to/your/config.yaml`
An example query: `https://api.example.com/search?q=$TERM&page=1`
A template variable: `{{ user.name }}`
```

#### Escaping Backticks Inside Inline Code

Use double backticks to wrap inline code that itself contains a backtick:

```markdown
`` Use `backticks` for inline code ``
```

---

### Fenced Code Blocks

For any multi-line code, **always use fenced blocks** (triple backticks).

**Never use 4-space indented code blocks:**
- Cannot declare a language for syntax highlighting
- Beginning and end of the block are ambiguous
- Harder to find in code search

#### Always Declare the Language

Declare the language immediately after the opening fence:

````markdown
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```
````

````markdown
```javascript
const greet = (name) => `Hello, ${name}!`;
```
````

````markdown
```bash
git clone https://github.com/org/repo.git
cd repo && npm install
```
````

````markdown
```json
{
  "name": "my-project",
  "version": "1.0.0"
}
```
````

````markdown
```yaml
server:
  host: 0.0.0.0
  port: 8080
```
````

````markdown
```sql
SELECT user_id, email
FROM users
WHERE created_at > '2024-01-01'
ORDER BY created_at DESC;
```
````

````markdown
```diff
- removed line
+ added line
  unchanged line
```
````

Specifying no language disables syntax highlighting — only do this for plain-text
output or when no language applies:

````markdown
```
Plain text output or logs with no language.
```
````

#### Escape Long Command-Line Calls

Use a trailing backslash to break long shell commands across lines so they can be
copied and pasted directly into a terminal:

````markdown
```shell
bazel run :target -- \
  --flag \
  --foo=longlonglonglonglongvalue \
  --bar=anotherlonglonglonglonglongvalue
```
````

#### Nesting Code Blocks Inside Lists

Indent the fenced block by the same amount as the list item's text to avoid
breaking the list:

```markdown
1. Clone the repo.

    ```bash
    git clone https://github.com/org/repo.git
    ```

2. Install dependencies.

    ```bash
    npm install
    ```

3. Start the server.

    ```bash
    npm run dev
    ```
```

You can also nest a code block using **4 additional spaces** from the list
indentation (no fences required, but no language tag either):

```markdown
*   Bullet point.

        int foo;   ← indented 4 spaces beyond the bullet text

*   Next bullet.
```

Prefer the fenced approach (explicit language tag, unambiguous boundaries).
Use the 4-space approach only when the platform does not support fenced blocks.

---

## Links

> **General rule:** Long links make source Markdown difficult to read and break
> 80-character line wrapping. **Wherever possible, shorten your links.**

### Inline Links

Write the sentence naturally first, then wrap the most descriptive phrase as the
link text. Link text should describe the destination, not the act of clicking:

```markdown
# ✅ Good — descriptive link text
See the [Markdown style guide](https://google.github.io/styleguide/docguide/style.html) for details.
Read the [contributing guide](CONTRIBUTING.md) before opening a PR.

# ❌ Bad — uninformative link text
See the style guide [here](https://google.github.io/styleguide/docguide/style.html).
For more info, click [this link](https://example.com).
Check out [https://example.com/foo/bar](https://example.com/foo/bar).
```

Never use "click here", "here", "link", "this", or bare URLs as link text.

### Links Within the Same Repository

Use root-relative paths (not full URLs) for internal Markdown links:

```markdown
# ✅ Root-relative path
[Contributing Guide](/docs/CONTRIBUTING.md)
[API Reference](/docs/api/README.md)

# ✅ Same-directory relative link
[See also](other-page-in-same-dir.md)

# ❌ Full URL for an internal doc
[Contributing Guide](https://github.com/org/repo/blob/main/docs/CONTRIBUTING.md)
```

Avoid `../` relative paths across directory levels — they break when files are
moved or the doc tree is restructured:

```markdown
# ❌ Fragile cross-directory relative path
[Config Reference](../../bad/path/to/config.md)
```

### Link to a Heading Anchor

```markdown
[Jump to Installation](#installation)
[See the Configuration section](#configuration-options)
```

Anchors are auto-generated: lowercase, spaces → hyphens, punctuation removed.

### Reference-Style Links

Use reference links when:
- The URL is long enough to break the 80-character line limit.
- The same URL is used more than once in the document.
- The link appears inside a table cell.

```markdown
See the [Markdown style guide][google-style] for details.
Also read the [CommonMark spec][commonmark].

[google-style]: https://google.github.io/styleguide/docguide/style.html
[commonmark]: https://commonmark.org/
```

#### When NOT to Use Reference Links

Do not use reference links when the URL is short enough that inlining it does not
disrupt the flow of the text. Adding reference syntax for a short URL adds noise
without benefit:

```markdown
# ❌ Unnecessary — URL is short, inline is cleaner
The [style guide][style_guide] says not to over-use reference links.

[style_guide]: https://google.com/markdown-style

# ✅ Just inline it
The [style guide](https://google.com/markdown-style) says not to over-use reference links.
```

Only use reference links when the URL is genuinely long enough to hurt readability
if inlined, when the URL is reused, or when inside a table cell.

#### Where to Define Reference Links

Define reference link definitions **just before the next heading** after their first
use (treat them like footnotes anchored to the current section).

> **Note:** If your editor has its own opinion about where reference links should go,
> don't fight it — **the tools always win.** The goal is consistency; let your
> tooling enforce placement automatically.

```markdown
## Authentication

See the [OAuth 2.0 guide][oauth] for implementation details.
The [JWT specification][jwt] covers token structure.

[oauth]: https://oauth.net/2/
[jwt]: https://datatracker.ietf.org/doc/html/rfc7519

## Authorization

...
```

**Exception:** Reference links used in **multiple sections** go at the end of the file
to avoid dangling links when sections are moved or restructured.

#### Reference Links in Tables

Always use reference links inside table cells — inline URLs make tables unreadable:

```markdown
# ✅ Readable table with reference links
| Site    | Description             |
|---------|-------------------------|
| [MDN]   | Web platform reference  |
| [devdocs] | Unified API reference |

[MDN]: https://developer.mozilla.org
[devdocs]: https://devdocs.io

# ❌ Unreadable table with inline links
| Site                                    | Description             |
|-----------------------------------------|-------------------------|
| [MDN](https://developer.mozilla.org)   | Web platform reference  |
```

#### Reducing Duplication with Reference Links

When the same URL appears three or more times in a document, define it once as a
reference link and use the reference throughout.

### Automatic Links

Most modern Markdown processors auto-link bare URLs. Use angle brackets to force
a URL to render as a clickable link when auto-linking is not enabled:

```markdown
<https://www.example.com>
<user@example.com>
```

To **prevent** a URL from auto-linking, wrap it in backticks:

```markdown
`https://www.example.com/search?q=$TERM`
```

---

## Link Quality Rules (Summary)

| Rule | Rationale |
|---|---|
| Descriptive link text | Screen readers and scanners read link text in isolation |
| Root-relative paths for internal links | Portable; survives file moves |
| No bare-URL link text | Wastes space; conveys no information |
| No `../` cross-directory paths | Breaks on restructuring |
| Reference links for long URLs | Keeps body text within 80-char limit |
| Reference links in tables | Keeps table cells short and readable |
| Define reference links near first use | Easy to find; reduces "footnote overload" |
| Audit links periodically | Broken links erode reader trust |
