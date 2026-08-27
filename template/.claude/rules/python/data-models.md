---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Data Models

- Use frozen dataclasses or value objects for domain values; prefer enums over magic strings for closed sets.
- Map external payloads to domain models at boundaries; never pass raw dictionaries through core logic.
- Record-type ladder: tuple for small positional values → `NamedTuple` for immutable named records → `@dataclass` for the common case → validation models only at I/O boundaries.
- No shared mutable aliasing across ownership boundaries; copy or freeze values when crossing layers.
- Keep serialization formats separate from internal domain models; normalize external data before core logic uses it.
