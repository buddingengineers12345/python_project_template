# Running the Full CI Pipeline

```bash
just ci
```

This runs: `fix` → `check`.

`check` bundles: `uv sync --frozen`, `fmt-check`, `ruff check`, `basedpyright`,
`sync-check`, `docs-check` (D-only; redundant with `ruff check` for enforcement), `test-ci`
(pytest with coverage on the default Python 3.11 venv — same command as the 3.11 leg of `tests.yml`),
`pre-commit run --all-files`. Dependency audit (`pip-audit`) is **not** part of `check`; run
`just audit` locally or rely on `security.yml` on GitHub (CodeQL is GHA-only). Use `just test-ci-matrix`
to exercise the full 3.11 / 3.12 / 3.13 matrix locally.

Together, `lint.yml` + `tests.yml` + `security.yml` cover the merge gate on GitHub. All steps must
pass before a PR is mergeable.
