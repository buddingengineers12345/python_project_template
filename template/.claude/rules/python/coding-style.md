---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python Coding Style

- All public functions, methods, and classes require complete type annotations and a Google-style docstring.
- Use `structlog.get_logger()` for logging in `src/`; never `print()`, `logging.getLogger()`, or `logging.basicConfig()`.
- Call `configure_logging()` once at entry point; use public APIs from `my_library.common.logging_manager`.
- Prefer `X | Y` union syntax; basedpyright `standard` mode enforced — run `just type` after edits.
- Run `just fmt` and `just lint` after edits; active ruff rules include `D`, `C90`, `PERF`, `T20`.
- Outside `common/`, prefer imports from `my_library.common` over reimplementing file I/O, decorators, or utils.
