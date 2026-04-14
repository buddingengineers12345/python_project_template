# YAML Conventions

# applies-to: **/*.yml, **/*.yaml

YAML files in this repository include `copier.yml`, GitHub Actions workflows
(`.github/workflows/*.yml`), `mkdocs.yml`, and `.pre-commit-config.yaml`.

## Formatting

- Indentation: 2 spaces. Never use tabs.
- No trailing whitespace on any line.
- End each file with a single newline.
- Wrap long string values with block scalars (`|` or `>`) rather than quoted strings
  when the value spans multiple lines.

```yaml
# Preferred for multiline strings
description: >-
  A long description that wraps cleanly
  and is easy to read in source.

# Avoid
description: "A long description that wraps cleanly and is easy to read in source."
```

## Quoting strings

- Quote strings that contain YAML special characters: `:`, `{`, `}`, `[`, `]`,
  `,`, `#`, `&`, `*`, `?`, `|`, `-`, `<`, `>`, `=`, `!`, `%`, `@`, `\`.
- Quote strings that could be misinterpreted as other types (`"true"`, `"1.0"`,
  `"null"`).
- Do not quote simple alphanumeric strings unnecessarily.

## Booleans and nulls

Use YAML 1.2 style (as recognised by Copier and most modern parsers):
- Boolean: `true` / `false` (lowercase, unquoted).
- Null: `null` or `~`.
- Avoid the YAML 1.1 aliases (`yes`, `no`, `on`, `off`) — they are ambiguous.

## Comments

- Use `#` comments to explain non-obvious configuration choices.
- Separate logical sections with a blank line and a comment header:

```yaml
# -------------------------------------------------------------------------
# Post-generation tasks
# -------------------------------------------------------------------------
_tasks:
  - command: uv lock
```

## GitHub Actions specific

- Pin third-party actions to a full commit SHA, not a floating tag:
  ```yaml
  uses: actions/checkout@v4         # acceptable if you review tag-SHA mapping
  uses: actions/checkout@abc1234   # preferred for production workflows
  ```
- Use `env:` at the step or job level for environment variables; avoid top-level `env:`
  unless the variable is used across all jobs.
- Name every step with a descriptive `name:` field.
- Prefer `actions/setup-python` with an explicit `python-version` matrix over hardcoded
  versions.

## copier.yml specific

See [copier/template-conventions.md](../copier/template-conventions.md) for Copier-specific
YAML conventions. Rules here cover general YAML style; Copier semantics are covered there.

## .pre-commit-config.yaml specific

- Pin `rev:` to a specific version tag, not `HEAD` or `latest`.
- Group hooks by repository with a blank line between repos.
- List hooks in logical order: formatters before linters, linters before type checkers.
