# Testing Requirements

- Minimum coverage: 85% per module; never lower an existing module's coverage.
- TDD workflow: write failing test (RED) → minimal implementation (GREEN) → refactor (REFACTOR).
- GREEN means minimal — write only enough code to make the failing test pass.
- Tests must not share mutable state; must pass when run individually or in any order.
- Every new public symbol requires at least one test. Use `just test` / `just coverage`.
