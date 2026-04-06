# Git Workflow

## Commit message format

```
<type>: <short imperative description>

<optional body — explain WHY, not what>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`

Rules:
- Subject line ≤ 72 characters; imperative mood ("Add feature", not "Added feature").
- Reference issues in the footer (`Closes #123`), not the subject.
- One logical change per commit.

## What never goes in a commit

- Hardcoded secrets, API keys, passwords, or tokens.
- Generated artefacts reproducible from source (`.pyc`, `.venv/`, `dist/`).
- Merge-conflict markers or `*.rej` files.
- Debug statements (`print()`, `pdb.set_trace()`).

The `pre-bash-commit-quality.sh` hook scans staged files before every commit.

## Protected operations

These commands are blocked by hooks and must not be run without explicit justification:
- `git commit --no-verify` — bypasses quality gates.
- `git push --force` — rewrites shared history.

## Pull request workflow

1. Run `just review` (lint + types + docstrings + tests) before opening a PR.
2. Write a PR description explaining the *why*, not just the *what*.
3. All CI checks must be green before requesting review.
