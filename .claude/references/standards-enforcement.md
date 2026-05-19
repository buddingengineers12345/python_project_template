# Standards Enforcement

Standards are enforced at four layers — during development, at commit, in review, and in CI.

## Tooling layer (always active)

| What | Tool | When |
|---|---|---|
| Lint + style | ruff | `just lint` / pre-commit / CI |
| Docstrings | ruff `D` rules (Google) | `just docs-check` / CI |
| Complexity | ruff `C90` (max 10) | `just lint` |
| Performance | ruff `PERF` | `just lint` |
| Types | basedpyright `standard` | `just type` / pre-commit / CI |
| Test coverage | pytest-cov (reported) | `just coverage` |

## Claude layer (automatic feedback during development)

Hooks are registered in `.claude/settings.json` and fire at each lifecycle event:

| Hook script | Event | Matcher | Purpose |
|---|---|---|---|
| `session-start-bootstrap.sh` | SessionStart | * | Show toolchain status + previous session snapshot |
| `pre-bash-block-no-verify.sh` | PreToolUse | Bash | Block `--no-verify` in git commands |
| `pre-bash-git-push-reminder.sh` | PreToolUse | Bash | Warn to run `just review` before push |
| `pre-bash-commit-quality.sh` | PreToolUse | Bash | Scan staged `.py` files for secrets/debug markers |
| `pre-config-protection.sh` | PreToolUse | Write\|Edit\|MultiEdit | Block weakening ruff/basedpyright config edits |
| `pre-protect-uv-lock.sh` | PreToolUse | Write\|Edit | Block direct edits to `uv.lock` |
| `pre-bash-coverage-gate.sh` | PreToolUse | Bash | Warn before `git commit` if coverage below 85% |
| `pre-write-src-require-test.sh` | PreToolUse | Write\|Edit | Block writing `src/<pkg>/<module>.py` if matching test module is missing (strict TDD; register this **or** `pre-write-src-test-reminder.sh`) |
| `pre-write-src-test-reminder.sh` | (optional) | Write\|Edit | Warn if `tests/<pkg>/test_<module>.py` missing (non-blocking alternative to strict TDD hook) |
| `pre-write-doc-file-warning.sh` | PreToolUse | Write | Block `.md` files outside `docs/` |
| `pre-write-jinja-syntax.sh` | PreToolUse | Write | Validate Jinja2 syntax before writing `.jinja` files |
| `pre-suggest-compact.sh` | PreToolUse | Edit\|Write | Suggest `/compact` every ~50 operations |
| `pre-compact-save-state.sh` | PreCompact | * | Snapshot git state before compaction |
| `post-edit-python.sh` | PostToolUse | Edit\|Write | Run ruff + basedpyright after every `.py` edit |
| `post-edit-jinja.sh` | PostToolUse | Edit\|Write | Validate Jinja2 syntax after every `.jinja` edit |
| `post-edit-markdown.sh` | PostToolUse | Edit | Warn if existing `.md` edited outside `docs/` |
| `post-edit-refactor-test-guard.sh` | PostToolUse | Edit\|Write | Remind to run tests after several `src/` or `scripts/` edits |
| `post-edit-copier-migration.sh` | PostToolUse | Edit\|Write | Remind about `_migrations` after `copier.yml` edits |
| `post-edit-template-mirror.sh` | PostToolUse | Edit\|Write | Remind to mirror `template/.claude/` ↔ root `.claude/` |
| `post-bash-pr-created.sh` | PostToolUse | Bash | Log PR URL after `gh pr create` succeeds |
| `stop-session-end.sh` | Stop | * | Persist session state JSON |
| `stop-evaluate-session.sh` | Stop | * | Extract reusable patterns from transcript |
| `stop-cost-tracker.sh` | Stop | * | Track and accumulate session token costs |
| `stop-desktop-notify.sh` | Stop | * | macOS desktop notification on completion |

See `.claude/hooks/README.md` for full details on exit codes, JSON input format, and adding hooks.

## Claude commands (on-demand workflows)

| Slash command | Purpose |
|---|---|
| `/review` | Full pre-merge checklist: lint + types + docstrings + test coverage + symbol scan |
| `/coverage` | Run coverage, identify gaps, write missing tests |
| `/docs-check` | Audit and repair Google-style docstrings across all source files |
| `/standards` | Consolidated pass/fail report across all checks — the "ready to merge?" gate |
| `/update-claude-md` | Sync CLAUDE.md against pyproject.toml + justfile to prevent drift |
| `/generate` | Generate a test project from the template into `/tmp/test-output` |
| `/release` | Orchestrate a new release: verify CI, bump version, tag, push |
| `/validate-release` | Verify release prerequisites (clean tree, passing CI, correct tag format) |
| `/ci` | Run `just ci` and report results |
| `/test` | Run `just test` and summarise failures |
| `/dependency-check` | Validate `uv.lock` is committed, in sync, and not stale |
| `/tdd-red` | Validate RED phase: confirm a test fails for the right reason |
| `/tdd-green` | Validate GREEN phase: confirm the test passes with no regressions |
| `/ci-fix` | Autonomous CI fixer: diagnose failures, apply fixes, re-run until green |

## Definition of done

A feature or fix is **done** when all of the following are true:

1. `just ci` passes with zero errors.
2. Every new public function/class/method has a Google-style docstring.
3. Every new function/method has complete type annotations (parameters + return type).
4. At least one test case covers each new public symbol.
5. `just coverage` does not show a new module below its previous coverage level.
6. No `TODO` or `FIXME` comments are left in modified files (unless tracked as issues).
7. CLAUDE.md is up to date (`/update-claude-md` shows no drift).
