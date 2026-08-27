---
paths:
  - "src/**/config.py"
  - "src/**/settings.py"
  - "**/config/**/*.py"
---

# Configuration

- Validate all configuration at startup and fail fast on missing or invalid keys; treat config as immutable thereafter.
- Use a typed settings model (pydantic, dataclass) validated once at initialization; never scattered `os.environ` access outside config modules.
- Precedence order: defaults → config file → environment → CLI; document where each is overridden in `AGENTS.md`.
- Separate secrets from non-secret config; never commit API keys or credentials; store them in a secrets manager only.
- Config modules must be import-light with no side effects at import time; initialization and startup validation belong at the entrypoint.
