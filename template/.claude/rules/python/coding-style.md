---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python Coding Style

- All public functions, methods, and classes require complete type annotations and a Google-style docstring; docstrings state the contract (side effects, failure modes, constraints) and must be updated when the contract changes.
- Prefer `X | Y` union syntax; basedpyright `standard` mode enforced - run `just type` after edits.
- Run `just fmt` and `just lint` after edits; active ruff rules include `D`, `C90`, `PERF`, `T20`.
- Outside `common/`, prefer imports from `my_library.common` over reimplementing file I/O, decorators, or utils.
- Use consistent domain vocabulary throughout the codebase (one term per concept); reference the project glossary when adding new terms.
- Prefer EAFP (Easier to Ask for Forgiveness than Permission) by default; use LBYL (Look Before You Leap) only at trust boundaries where pre-check races are impossible.
- Performance complexity optimizations must be justified by a measurement; do not add them speculatively.
- Suppression comments carry the rule code and reason (e.g., `# noqa: F401 external_lib imported for type checking`).
