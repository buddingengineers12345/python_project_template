# Markdown File Placement Rule

Any Markdown (`.md`) file you create as part of a workflow, analysis, or investigation output
**must be written inside the `docs/` folder**.

**Allowed exceptions (may be placed anywhere):**
- `README.md`
- `CLAUDE.md`

Do **not** create free-standing `.md` files (e.g. `ANALYSIS.md`, `LOGGING_ANALYSIS.md`,
`NOTES.md`) at the repository root or inside `src/`, `tests/`, `scripts/`, or any directory
outside `docs/`. This rule is enforced by `.claude/hooks/post-edit-markdown.sh`, which fires
after every file write and surfaces a violation message if the rule is broken.
