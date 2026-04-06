# Development Workflow

> Git operations are covered in [git-workflow.md](./git-workflow.md).

## Before writing any code

1. Search the codebase for similar patterns before adding new ones.
2. Check third-party libraries (PyPI) before writing utility code.
3. Read the relevant rule files in `.claude/rules/` for the language you are working in.

## Feature implementation workflow

### 1. Understand the requirement

- Read the issue or task thoroughly.
- Identify edge cases upfront and write them down as test cases.

### 2. Write tests first (TDD)

See [testing.md](./testing.md). Summary: write a failing test, then write the implementation.

### 3. Implement

- Follow the coding style rules for the relevant language.
- Fix PostToolUse hook violations (ruff, basedpyright) after every file edit.

### 4. Self-review before opening a PR

```bash
just fix        # auto-fix ruff violations
just fmt        # format
just lint       # lint — must be clean
just type       # basedpyright — must be clean
just docs-check # docstring completeness — must be clean
just test       # all tests — must pass
just coverage   # no module below 85 %
just ci         # full pipeline
```

## Toolchain reference

| Task | Command |
|------|---------|
| Run tests | `just test` |
| Coverage report | `just coverage` |
| Lint | `just lint` |
| Format | `just fmt` |
| Type check | `just type` |
| Docstring check | `just docs-check` |
| Full CI | `just ci` |
| Diagnose environment | `just doctor` |
