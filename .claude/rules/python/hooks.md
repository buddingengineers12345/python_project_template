---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python Hooks

- `post-edit-python.sh` runs ruff + basedpyright after every `.py` edit — fix all violations before moving on.
- `pre-write-src-require-test.sh` blocks writing `src/<pkg>/<module>.py` if a matching test file is missing.
- `pre-bash-coverage-gate.sh` warns before `git commit` if coverage is below 85%.
- Do not weaken `typeCheckingMode` in `pyproject.toml`; never add broad `# type: ignore` without a specific error code.
