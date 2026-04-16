# Security

- Never hardcode secrets (API keys, passwords, tokens) in source, config, or docs.
- Load secrets via `os.environ["KEY"]` (fail-fast); never `os.environ.get("KEY", "")`.
- Validate all external inputs at the boundary; use parameterised queries for SQL.
- Pin all dependency versions in `pyproject.toml`; commit `uv.lock`.
