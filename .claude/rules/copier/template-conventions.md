---
paths:
  - "copier.yml"
  - "template/**"
---

# Copier Template Conventions

- Never edit `.copier-answers.yml` by hand — managed by Copier's update algorithm.
- Computed variables (not prompted) use `when: false`; not stored in answers or shown to users.
- Do not prompt for API tokens or secrets; use CI encrypted secrets instead.
- Dual-hierarchy: changes affecting both meta-repo and generated projects go in both `.claude/` and `template/.claude/`.
- Every `copier.yml` or template file change requires a test update in `tests/integration/test_template.py`.
