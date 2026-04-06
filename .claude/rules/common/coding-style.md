# Coding Style — Common Principles

These principles apply to all languages in this repository. Language-specific directories
extend or override individual rules where language idioms differ.

## Naming

- Use descriptive, intention-revealing names. Abbreviations are acceptable only when
  universally understood in the domain (e.g. `url`, `id`, `ctx`).
- Functions and variables: `snake_case` for Python/Bash, follow language convention otherwise.
- Constants: `UPPER_SNAKE_CASE`.
- Avoid single-letter names except for short loop counters and mathematical variables.

## Function size and focus

- Functions should do one thing. If you need "and" to describe what a function does,
  split it.
- Target ≤ 40 lines per function body; hard limit 80 lines. Exceeding this is a signal
  to extract helpers.
- McCabe cyclomatic complexity ≤ 10 (enforced by ruff `C90`).

## File size and cohesion

- Keep files cohesive — one module, one concern.
- Target ≤ 400 lines per file; treat 600 lines as a trigger to extract a submodule.

## Immutability preference

- Prefer immutable data structures and values. Mutate in place only when necessary for
  correctness or performance.
- **Language note**: overridden in languages where mutation is idiomatic (e.g. Go pointer
  receivers).

## Error handling

- Never silently swallow exceptions or errors. Either handle them explicitly or propagate.
- Log errors with sufficient context to diagnose the issue without a debugger.
- Do not use bare `except:` / catch-all blocks unless re-raising immediately.

## No magic values

- Replace bare literals (`0`, `""`, `"pending"`) with named constants or enums.
- Document the origin of non-obvious numeric thresholds in a comment.

## No debug artefacts

- Remove `print()`, `console.log()`, `debugger`, and temporary debug variables before
  committing. Use the project's logging infrastructure instead.

## Comments

- Comments explain *why*, not *what*. Code should be self-documenting.
- Avoid comments that merely restate what the code does ("increment counter", "return result").
- Use `TODO(username): description` for tracked work items; never leave bare `TODO` or
  `FIXME` in committed code.

## Line length

- 100 characters (enforced by ruff formatter for Python). Wrap long expressions clearly.

## Imports

- Group and sort imports: standard library → third-party → local. One blank line between groups.
- Absolute imports preferred over relative imports except within the same package.
