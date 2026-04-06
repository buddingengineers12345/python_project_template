# Development Workflow

> This file describes the full feature development pipeline. Git operations are
> covered in [git-workflow.md](./git-workflow.md).

## Before writing any code: research first

1. **Search the existing codebase** for similar patterns before adding new ones.
   Prefer consistency with existing code over novelty.
2. **Check third-party libraries** (PyPI, crates.io, etc.) before writing utility code.
   Prefer battle-tested libraries over hand-rolled solutions for non-trivial problems.
3. **Read the relevant rule files** in `.claude/rules/` for the language or domain
   you are working in.

## Feature implementation workflow

### 1. Understand the requirement

- Read the issue, PR description, or task thoroughly before touching code.
- Identify edge cases and failure modes upfront. Write them down as test cases.
- For large changes, sketch the data flow and affected modules before coding.

### 2. Write tests first (TDD)

See [testing.md](./testing.md) for the full TDD workflow. Summary:

- Write one failing test per requirement or edge case.
- Run `just test` to confirm the test fails for the right reason.
- Then write the implementation.

### 3. Implement

- Follow the coding style rules for the relevant language.
- Keep the diff small and focused. One PR per logical change.
- Run the language-specific PostToolUse hook output (ruff, basedpyright) after every
  file edit and fix violations before moving on.

### 4. Self-review before opening a PR

Run each check individually before the full suite so failures are isolated:

```bash
just fix        # auto-fix ruff violations
just fmt        # format with ruff formatter
just lint       # ruff lint — must be clean
just type       # basedpyright — must be clean
just docs-check # docstring completeness — must be clean
just test       # all tests — must pass
just coverage   # no module below coverage threshold
```

Or run the full pipeline:

```bash
just ci         # fix → fmt → lint → type → docs-check → test → precommit
```

### 5. Commit and open a PR

See [git-workflow.md](./git-workflow.md) for commit message format and PR conventions.

## Working in this repo vs generated projects

| Context | You are working on… | Use `just` from… |
|---------|---------------------|-----------------|
| Root repo | The Copier template itself | `/workspace/` |
| Generated project | A project produced by `copier copy` | The generated project root |

Changes to `template/` affect all future generated projects. Test template changes by
running `copier copy . /tmp/test-output --trust --defaults` and inspecting the output.
Clean up with `rm -rf /tmp/test-output`.

## Toolchain quick reference

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
| Generate test project | `copier copy . /tmp/test-output --trust --defaults` |
