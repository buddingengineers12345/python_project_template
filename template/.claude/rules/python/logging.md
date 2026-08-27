---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Logging

- Use `structlog.get_logger()` for logging in `src/`; never `print()`, `logging.getLogger()`, or `logging.basicConfig()`.
- Call `configure_logging()` once at entry point; use public APIs from `my_library.common.logging_manager`.
- Use stable snake_case event names; renaming is a breaking change for log consumers. Use log levels consistently: debug, info, warning, error.
- Keep event messages static and place variable data in structured keyword arguments; never f-string interpolate into messages.
- Consistent field vocabulary across all events (one name per concept); include correlation, identity, timing, and operation context fields.
- Use `logger.exception()` inside exception handlers; never log passwords, secrets, API keys, tokens, credentials, or sensitive payloads.
