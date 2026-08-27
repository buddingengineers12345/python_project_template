---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Serialization

- Use parser/gateway functions to own deserialization at I/O boundaries; convert untrusted data into trusted internal models before core logic.
- Schema changes are versioned and backward-tolerated: add-only fields with explicit version markers; never silent best-effort parsing.
- Safe loaders only: no `yaml.load` or `pickle` on untrusted input; use `yaml.safe_load` and structured validation models (pydantic, `TypedDict`).
- Preserve numeric precision, timezone offsets, binary data, and ordering when they affect correctness; test empty, missing, malformed, and oversized inputs.
- Keep golden files small; update only when the serialized contract changes intentionally; keep external and internal model separation clear.
