# Just Recipes — Common Commands

| Task | Command |
|---|---|
| List recipes (default) | `just` or `just default` |
| Run all tests | `just test` |
| Run tests in parallel | `just test-parallel` |
| Run slow tests only | `just slow` |
| Fast unit tests (no slow/integration) | `just test-fast` |
| Integration tests only | `just test-integration` |
| Tests for changed files only | `just test-changed` |
| Verbose tests | `just test-verbose` |
| Full debug test output | `just test-debug` |
| Re-run last failed tests | `just test-lf` |
| Re-run last failed tests (max verbosity) | `just test-failed-verbose` |
| Stop on first test failure | `just test-first-fail` |
| CI-style tests + coverage XML (3.11 only) | `just test-ci` |
| Full tests.yml Python matrix (3.11–3.13) | `just test-ci-matrix` |
| Coverage report | `just coverage` |
| Lint | `just lint` |
| Lint changed files only | `just lint-changed` |
| Format | `just fmt` |
| Format check (read-only) | `just fmt-check` |
| Auto-fix lint issues | `just fix` |
| Type check | `just type` |
| Docstring check | `just docs-check` |
| MkDocs recipes (generated projects only) | `just docs-help` |
| Pre-merge review (fix + lint + type + docs) | `just review` |
| Full CI locally (fix → check) | `just ci` |
| Read-only CI check (no auto-fix) | `just check` |
| Run pre-commit on all files | `just precommit` |
| Register git hooks | `just precommit-install` |
| Interactive conventional commit (Commitizen) | `just cz-commit` |
| Sync deps after lockfile change | `just sync` |
| Upgrade all deps | `just update` |
| Check for outdated dependencies | `just deps-outdated` |
| Verify lockfile integrity | `just lock-check` |
| Dependency security audit | `just audit` |
| Install all deps + pre-commit | `just install` |
| One-command developer onboarding | `just bootstrap` |
| Diagnose environment | `just doctor` |
| Generate freshness dashboard | `just freshness` |
| Root ↔ template sync validation | `just sync-check` |
| Suggested PR title + body (PR policy) | `just pr-draft` |
| Clean build artifacts | `just clean` |
| Build distribution | `just build` |
| Validate built distribution | `just check-dist` |
| Publish package | `just publish` |

**Always use `just` recipes.** Do not call `uv run ruff`, `pytest`, etc. directly —
the justfile handles the correct flags and order.
