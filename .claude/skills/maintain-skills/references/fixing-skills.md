# Fixing skills step by step

Complete procedures for standardizing and auditing individual skills and entire skill repositories.

## Step-by-step: standardize a single skill

Follow these steps exactly. Do not skip any step.

### Step 1 — Inventory

```bash
SKILLS_DIR="${SKILLS_DIR:-.claude/skills}"
SKILL="<skill-name>"
SKILL_DIR="$SKILLS_DIR/$SKILL"

# Check what exists
ls -la "$SKILL_DIR"/
wc -l "$SKILL_DIR/SKILL.md"
for sub in references scripts templates assets; do
    ls "$SKILL_DIR/$sub/" 2>/dev/null || echo "No $sub/ directory"
done
```

### Step 2 — Read SKILL.md and note violations

Read the full SKILL.md. Check each dimension against the rules in the main skill. Write down every violation found.

### Step 3 — Fix frontmatter (dimension 1)

If the description uses a quoted string or `>` instead of `>-`, replace it.

### Step 4 — Fix title (dimension 2)

If the H1 heading does not end with ` Skill`, fix it. Remove version numbers, subtitles, and parenthetical notes. Move that information into the intro paragraph.

### Step 5 — Fix reference table (dimension 3)

Replace any non-standard reference section with the exact header `## Quick reference: where to go deeper` and a two-column pipe table (`Topic | Reference file`) using Markdown links.

### Step 6 — Fix file and folder names (dimension 4)

Rename anything non-kebab-case across the folder, `references/`, `templates/`, and `assets/`. This includes numbered prefixes, underscores, and uppercase.

```bash
# Rename numbered reference files
cd "$SKILL_DIR/references/"
mv 01-document-structure.md document-structure.md

# Rename an underscore folder
cd "$SKILLS_DIR"
git mv claude_hooks claude-hooks    # or plain mv if not in git
```

After renaming, update ALL links in SKILL.md (and any cross-linking reference files) that point at the old names. Also update the `name:` frontmatter field so it matches the new folder name.

### Step 7 — Fix reference H1 headings (dimension 5)

Read line 1 of each reference file. If not sentence case, fix it.

**Before:**
```markdown
# Python Review Checklist — Full Detail (Python 3.11+)
```

**After:**
```markdown
# Review checklist
```

Rules for sentence case: capitalize first word and proper nouns (Python, Django, FastAPI, GitHub, etc.) only. Everything else is lowercase.

### Step 8 — Fix line count (dimension 6)

If SKILL.md exceeds 400 lines, identify sections that are:
- Detailed reference material (not needed on every invocation) — move to `references/`
- Long code example blocks — move to `references/patterns.md` (or similar)
- Copy-paste starter files — move to `templates/` or `assets/templates/`
- Extended checklists or tables — move to `references/`

Add a row to the quick-reference table for each new file.

### Step 9 — Check asset layout (dimension 7)

If the skill has both `templates/` (top-level) and `assets/templates/`, consolidate into one. Prefer `assets/templates/` when the skill also ships other asset categories (icons, fonts, settings starters); prefer top-level `templates/` for simple skills that only ship a handful of Markdown starters.

### Step 10 — Fix lazy reference loading (dimension 8)

Audit every line in SKILL.md that says "load", "read", or "consult" a reference file.
Each must have a conditional trigger. Fix unconditional loads:

**Before (unconditional):**
```markdown
1. Load the `pytest` skill (read `.claude/skills/pytest/SKILL.md`).
2. For fixture patterns, read `.claude/skills/pytest/references/fixtures.md`.
   For mocking guidance, read `.claude/skills/pytest/references/mocking.md`.
```

**After (conditional):**
```markdown
1. Load the `pytest` skill (read `.claude/skills/pytest/SKILL.md`).
2. If writing tests that need fixtures beyond basic `@pytest.fixture`:
   read `.claude/skills/pytest/references/fixtures.md`.
   If using mocks or test doubles:
   read `.claude/skills/pytest/references/mocking.md`.
   Otherwise: use inline guidance from the pytest skill's core principles.
```

For skills with many references, create a **conditional loading table**:

```markdown
## When to load references

| If the task involves…             | Load                            |
|------------------------------------|---------------------------------|
| <specific context A>               | `references/a.md`              |
| <specific context B>               | `references/b.md`              |
| Simple / default case              | No reference needed — use inline |
```

**Rules for the 80% case:** The most common use case must be covered by inline
guidance already in SKILL.md. A user doing the most typical task should never need
to load a reference file. References are for depth, advanced cases, and edge cases.

For orchestrator skills (sdlc-workflow, tdd-workflow): ensure each stage loads its
dependencies at the start of that stage, not all upfront. Each stage's load
instruction must include "if entering this stage" as the condition.

### Step 11 — Fix batch tool call guidance (dimension 9)

If the skill instructs the model to edit files or run commands, add a batch guidance
section. Use the standard block or adapt it to the skill's domain:

```markdown
## Efficiency: batch edits and parallel calls

- **Batch edits:** When making multiple changes to the same file, combine them
  into a single Edit tool call where possible. Do not make incremental
  single-line changes.
- **Parallel calls:** When running independent checks (e.g., lint + type-check),
  make all tool calls in a single message rather than sequentially.
- **Read before edit:** Read each file once, plan all changes, then apply them
  in the fewest possible Edit calls.
```

Place this section after the main workflow but before the "Quick reference" table.

For skills that are read-only or purely informational (no file edits, no command
runs), this dimension does not apply — skip it.

For orchestrator skills: add batch guidance for within-agent edits. The Agent-level
parallelism is already handled by multiple Agent calls — the batch guidance targets
edits within each agent's scope.

### Step 12 — Run verification

Run the full verification script from the main skill. ALL nine dimensions must pass.

---

## Step-by-step: repo-wide audit

```bash
SKILLS_DIR="${SKILLS_DIR:-.claude/skills}"

# List all skills
ls "$SKILLS_DIR"/

# Run full verification (all seven dimensions)
# Copy and run the verification script from the main skill

# Check for broken links to any bundled file
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill_dir=$(dirname "$f")
    grep -oE '(references|templates|assets)/[a-z0-9/-]+\.[a-z]+' "$f" | while read ref; do
        [ -f "$skill_dir/$ref" ] || echo "BROKEN: $skill_dir/$ref"
    done
done

# Check for orphaned bundled files (not linked from SKILL.md)
for skill_dir in "$SKILLS_DIR"/*/; do
    skill_md="$skill_dir/SKILL.md"
    [ -f "$skill_md" ] || continue
    find "$skill_dir/references" "$skill_dir/templates" "$skill_dir/assets" \
         -type f 2>/dev/null | while read f; do
        rel="${f#$skill_dir}"
        grep -q "$rel" "$skill_md" || echo "ORPHANED: $f"
    done
done
```

Fix issues in priority order: broken links first, then dimension violations, then orphaned files.

---

## SKILL.md section order

When restructuring a SKILL.md, use this standard order:

1. YAML frontmatter (`---` block with `name` and `description: >-`)
2. `# <Name> Skill` title
3. 1-3 line intro paragraph
4. Core content sections (main workflows, principles, checklists)
5. Conditional reference loading table or decision tree (dimension 8)
6. Efficiency: batch edits and parallel calls (dimension 9, if applicable)
7. `## Quick reference: where to go deeper` (reference table covering every file under `references/`, `templates/`, and `assets/`)
8. Optional: `## Bundled scripts` (if `scripts/` exists)

---

## Writing style rules

Apply these when editing any skill content:

- **Sentence case headings** — capitalize first word and proper nouns only
- **Imperative voice** — "Run this command" not "This command can be run"
- **Short paragraphs** — 3-5 lines max; use tables for parallel items
- **100-character line width** — wrap prose, not code blocks or tables
- **No emoji in headings** — emoji are allowed in table cells for quick scanning
- **Relative links** — use `[references/file.md](references/file.md)`, not absolute paths
