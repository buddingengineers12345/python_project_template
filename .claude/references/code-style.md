# Code Style and Standards

- Line length: 100 characters (set in `pyproject.toml` under `[tool.ruff]`).
- Target Python version: 3.11.
- Active ruff rules: `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `TCH`, `PGH`, `PT`, `ARG`, `D`, `C90`, `PERF`, `T20`.
  Rule `E501` (line too long) is ignored (handled by the formatter).
- Docstring convention: **Google style** (`pydocstyle` via ruff `D` rules).
  In this meta-repo, `tests/**` and `scripts/**` enforce `D` like other Python; only `T20` (`print`) is ignored there.
  **Generated projects** (from `template/`) treat `src/**/common/bump_version.py` like other library
  code for ruff `D` (Google docstrings required); the release helper uses
  `logging_manager` (`configure_logging`, structlog events, `write_machine_stdout_line` for the
  version line consumed by release tooling). Rendered **`template/CLAUDE.md.jinja`** is the source
  of truth for generated apps: **all logging must go through `common.logging_manager` public APIs**,
  and code outside `common/` must **prefer** imports from that package's `common` subpackage (file
  I/O, decorators, utils, logging) instead of duplicating those concerns.
- McCabe complexity: max 10 per function (`C90`).
- Type annotations are required on all public functions and methods (basedpyright `standard` mode).
- BasedPyright is lenient with external packages (`reportMissingTypeStubs = false`).
- `T20` (flake8-print): `print()` is discouraged in non-test code; use structured logging instead.
