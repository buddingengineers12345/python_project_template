Detect and fix drift between CLAUDE.md and the actual project configuration files.

CLAUDE.md is the project's living standards contract. It must stay in sync with
`pyproject.toml`, `justfile`, and `copier.yml`. This command performs that sync.

## Steps

1. **Read the source-of-truth files**:
   - `pyproject.toml` — extract:
     - Active ruff rules (`[tool.ruff.lint]` select + ignore)
     - Pydocstyle convention
     - BasedPyright mode and key settings
     - pytest addopts and markers
   - `justfile` — extract all public recipe names (non-`_` prefixed) and their
     one-line description comment (the `# ...` line directly above each recipe)
   - `copier.yml` — extract all prompt variable names and `_skip_if_exists` paths

2. **Read CLAUDE.md** and identify every section that references configuration:
   - "Code style" section — ruff rules, line length, pydocstyle convention
   - "Common development commands" table — just recipes
   - Any mention of specific tool versions or settings

3. **Compare and identify drift**:
   - Are all ruff rules in CLAUDE.md's code style section accurate and complete?
   - Does the commands table include all current `just` recipes?
   - Are any new recipes added to the justfile missing from the table?
   - Are any removed recipes still listed in CLAUDE.md?
   - Does the "Recent improvements" section need a new entry for today's changes?

4. **Update CLAUDE.md** to match reality:
   - Correct any stale ruff rule lists
   - Add any missing `just` recipes to the commands table (with description)
   - Remove any obsolete entries
   - Add a new bullet to "Recent improvements" summarising what changed today
     (use today's date from `date +%Y-%m-%d`)

5. **Report** what was changed (or "CLAUDE.md is already in sync — no changes needed").

## Important

- Do not rewrite the whole file; make surgical edits to keep existing prose intact.
- Preserve the document structure and heading hierarchy.
- Do not fabricate descriptions — if a recipe's purpose is unclear, read the justfile
  recipe body to infer it.
