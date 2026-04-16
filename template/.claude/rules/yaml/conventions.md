---
paths:
  - "**/*.yml"
  - "**/*.yaml"
---

# YAML Conventions

- Indentation: 2 spaces; never tabs. No trailing whitespace. End files with a newline.
- Booleans: `true`/`false` (YAML 1.2 lowercase); avoid `yes`/`no`/`on`/`off`.
- Quote strings containing YAML special characters; do not over-quote simple alphanumeric strings.
- GitHub Actions: pin third-party actions to a full commit SHA; name every step with `name:`.
