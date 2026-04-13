# Git Workflow

## Commit message format

```
<type>: <short imperative description>

<optional body — explain WHY, not what>

<optional footer: Closes #123, Breaking change: …>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`

Rules:
- Subject line ≤ 72 characters; use imperative mood ("Add feature", not "Added feature").
- Body wraps at 80 characters.
- Reference issues in the footer (`Closes #123`), not the subject.
- One logical change per commit. Do not bundle unrelated fixes.

## Branch naming

```
<type>/<short-description>         # e.g. feat/add-logging-manager
<type>/<issue-number>-description  # e.g. fix/42-null-pointer
```

## What never goes in a commit

- Hardcoded secrets, API keys, tokens, or passwords.
- Generated artefacts that are reproducible from source (build output, `*.pyc`, `.venv/`).
- Merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- `*.rej` files left by Copier update conflicts.
- Debug statements (`print()`, `debugger`, `pdb.set_trace()`).

The `pre-bash-commit-quality.sh` hook scans staged files for the above before every commit.

## Protected operations

These commands are **blocked** by pre-commit hooks and must not be run without explicit
justification:
- `git commit --no-verify` — bypasses quality gates.
- `git push --force` — rewrites shared history.
- `git push` directly to `main` — use pull requests.

**Maintainers:** enforce PR-only `main` and squash merges in GitHub **Settings** / branch
protection; see `docs/github-repository-settings.md` in this repository (single checklist).

## TDD commit conventions

When committing TDD work, structure commits to reflect the discipline:

- Use `test:` type for RED commits (failing test added).
- Use `feat:` or `fix:` type for GREEN commits (implementation that makes tests pass).
- Use `refactor:` type for REFACTOR commits (no behaviour change).
- Include test context in the commit body: which scenarios are covered, what edge
  cases were tested, and why the implementation approach was chosen.

Example:
```
feat: add discount calculation for premium users

Implements tiered discount logic. TDD cycle covered:
- Happy path: 10% discount for premium tier
- Edge cases: zero-item cart, negative prices rejected
- Boundary: exactly-at-threshold cart values

Tests: test_calculate_discount_* in tests/test_pricing.py
```

## Pull request workflow

1. Run `just review` (lint + types + docstrings + tests) before opening a PR.
2. Use `git diff main...HEAD` to review all changes since branching.
3. Write a PR description that explains the *why* behind the change, not just the *what*.
4. Include a test plan: which scenarios were verified manually or with automated tests.
5. All CI checks must be green before requesting review.
6. Squash-merge feature branches; preserve merge commits for release branches.

## Copier template repos — additional rules

- Never edit `.copier-answers.yml` by hand — the update algorithm depends on it.
- Resolve `*.rej` conflict files before committing; they indicate unreviewed merge conflicts.
- Tag releases with PEP 440-compatible versions (`1.2.3`, `1.2.3a1`) for `copier update` to work.
