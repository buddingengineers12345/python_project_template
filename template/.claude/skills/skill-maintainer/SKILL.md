---
name: skill-maintainer
description: >-
  Audit, standardize, and improve existing skills in template/.claude/skills/. Use this
  skill when the user wants to: review or audit one or more skills, do a repo-wide health
  check, standardize skills to a consistent format, fix outdated references, or improve
  skill descriptions for better triggering. Triggers: 'audit this skill', 'review skill
  quality', 'check skill health', 'standardize skills', 'skill repo maintenance', or any
  request to systematically review or improve a SKILL.md file. Do NOT use for creating
  brand-new skills from scratch — use the skill-creator skill instead.
---

# Skill Maintainer Skill

Audit, standardize, and improve existing skills. This skill provides exact rules and
commands so any model — including haiku — can maintain skills mechanically.

Skills live in `template/.claude/skills/`. Each skill is a directory:

```
template/.claude/skills/<skill-name>/
├── SKILL.md              # Required — frontmatter + instructions (< 400 lines)
├── references/            # Optional — deep-dive documents (one per topic)
│   └── <topic-name>.md   # Descriptive kebab-case names, 200-270 lines each
└── scripts/               # Optional — executable tools
    └── *.py or *.sh
```

---

## The six consistency dimensions

Every skill MUST pass all six checks. These are the primary audit criteria.

### Dimension 1 — Frontmatter block scalar

The `description` field MUST use the `>-` block scalar (folds lines, strips trailing
newline). Not `>`, not a quoted string, not a plain string.

```yaml
# CORRECT
description: >-
  Comprehensive guide for writing pytest test cases...

# WRONG — quoted string
description: "Comprehensive guide for writing pytest test cases..."

# WRONG — plain > (keeps trailing newline)
description: >
  Comprehensive guide for writing pytest test cases...
```

**Check:**
```bash
grep 'description:' template/.claude/skills/*/SKILL.md
```
Every line must show `description: >-`.

### Dimension 2 — Title format

The first H1 heading MUST be `# <Name> Skill` where `<Name>` matches the skill's
identity in sentence case.

```markdown
# Pytest Skill           ← CORRECT
# Python Code Reviewer Skill  ← CORRECT

# pytest skill           ← WRONG (not sentence case)
# Pytest                 ← WRONG (missing "Skill")
# Pytest Skill Guide     ← WRONG (extra word)
```

**Check:**
```bash
grep '^# ' template/.claude/skills/*/SKILL.md | head -1
```
Every line must end with ` Skill`.

### Dimension 3 — Reference table header

Every SKILL.md MUST contain a section with the exact header:

```markdown
## Quick reference: where to go deeper
```

This section MUST contain a pipe-delimited table with two columns:

```markdown
| Topic                  | Reference file                                       |
|------------------------|------------------------------------------------------|
| Descriptive topic name | [references/filename.md](references/filename.md)      |
```

Column 1 is a human-readable topic description. Column 2 is a Markdown link using
relative path `references/<filename>.md`. Every file in `references/` MUST appear
in this table. No orphaned reference files.

**Check:**
```bash
grep 'where to go deeper' template/.claude/skills/*/SKILL.md
```
Every skill must have exactly one match.

### Dimension 4 — Reference file naming

All files in `references/` MUST use descriptive kebab-case names. No numbered prefixes.

```
fixtures.md              ← CORRECT
anti-patterns.md         ← CORRECT
document-structure.md    ← CORRECT

01-fixtures.md           ← WRONG (numbered prefix)
Fixtures.md              ← WRONG (uppercase)
fixtures_and_more.md     ← WRONG (underscores)
```

**Check:**
```bash
find template/.claude/skills/*/references/ -name '[0-9]*' 2>/dev/null
```
Must return zero results.

### Dimension 5 — Reference H1 headings

Every reference file MUST start with a sentence-case H1 heading. Capitalize the first
word and proper nouns only.

```markdown
# Fixtures                          ← CORRECT
# Anti-patterns and fixes           ← CORRECT
# CI, coverage, and plugins         ← CORRECT

# All About Fixtures                ← WRONG (title case)
# FIXTURES                          ← WRONG (all caps)
# Python Patterns Reference (3.11+) ← WRONG (subtitle, version info)
```

**Check:**
```bash
for f in template/.claude/skills/*/references/*.md; do
    echo "$(basename "$f"): $(head -1 "$f")"
done
```
Inspect each heading for sentence case.

### Dimension 6 — SKILL.md line count

SKILL.md MUST be under 400 lines. Target range: 150-330 lines. If content exceeds
400 lines, move sections to `references/`.

**Check:**
```bash
wc -l template/.claude/skills/*/SKILL.md
```
Every file must show < 400.

---

## Full verification script

Run this after ANY skill edit. All six dimensions in one pass:

```bash
SKILLS_DIR="template/.claude/skills"

echo "=== 1. Frontmatter block scalar ==="
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    scalar=$(grep 'description:' "$f" | head -1 | sed 's/.*description: *//')
    echo "  $skill: $scalar"
done

echo ""
echo "=== 2. Title format ==="
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    echo "  $skill: $(grep '^# ' "$f" | head -1)"
done

echo ""
echo "=== 3. Reference table header ==="
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    header=$(grep 'where to go deeper' "$f" || echo "(NOT FOUND)")
    echo "  $skill: $header"
done

echo ""
echo "=== 4. Reference file naming (any numbered?) ==="
found=$(find "$SKILLS_DIR"/*/references/ -name '[0-9]*' 2>/dev/null)
[ -z "$found" ] && echo "  None found ✓" || echo "  $found"

echo ""
echo "=== 5. Reference H1 headings ==="
for f in "$SKILLS_DIR"/*/references/*.md; do
    skill=$(basename "$(dirname "$(dirname "$f")")")
    echo "  $skill/$(basename "$f"): $(head -1 "$f")"
done

echo ""
echo "=== 6. SKILL.md line counts ==="
wc -l "$SKILLS_DIR"/*/SKILL.md
```

**Pass criteria:** ALL of these must be true:

- Dimension 1: every skill shows `>-`
- Dimension 2: every title ends with ` Skill`
- Dimension 3: every skill has exactly one `where to go deeper` match
- Dimension 4: zero numbered files found
- Dimension 5: every H1 heading is sentence case
- Dimension 6: every SKILL.md is under 400 lines

---

## Step-by-step: standardize a single skill

Follow these steps exactly. Do not skip any step.

### Step 1 — Inventory

```bash
SKILL="<skill-name>"
SKILL_DIR="template/.claude/skills/$SKILL"

# Check what exists
ls -la "$SKILL_DIR"/
wc -l "$SKILL_DIR/SKILL.md"
ls "$SKILL_DIR/references/" 2>/dev/null || echo "No references/ directory"
ls "$SKILL_DIR/scripts/" 2>/dev/null || echo "No scripts/ directory"
```

### Step 2 — Read SKILL.md and note violations

Read the full SKILL.md. Check each dimension against the rules above. Write down
every violation found.

### Step 3 — Fix frontmatter (dimension 1)

If the description uses a quoted string or `>` instead of `>-`, replace it. See
Dimension 1 above for CORRECT/WRONG examples.

### Step 4 — Fix title (dimension 2)

If the H1 heading does not end with ` Skill`, fix it. Remove version numbers,
subtitles, and parenthetical notes. Move that information into the intro paragraph.
See Dimension 2 above for CORRECT/WRONG examples.

### Step 5 — Fix reference table (dimension 3)

Replace any non-standard reference section with the exact header
`## Quick reference: where to go deeper` and a two-column pipe table
(`Topic | Reference file`) using Markdown links. See Dimension 3 above.

If other sections use "Quick reference", rename them (e.g., `## Scope dispatch`).

### Step 6 — Fix reference file names (dimension 4)

If any reference files have numbered prefixes, rename them.

```bash
# Rename numbered files
cd "$SKILL_DIR/references/"
mv 01-document-structure.md document-structure.md
mv 02-formatting-syntax.md formatting-syntax.md
```

After renaming, update ALL links in SKILL.md that reference the old filenames.

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

Rules for sentence case: capitalize first word and proper nouns (Python, Django,
FastAPI, GitHub, etc.) only. Everything else is lowercase.

### Step 8 — Fix line count (dimension 6)

If SKILL.md exceeds 400 lines, identify sections that are:
- Detailed reference material (not needed on every invocation)
- Long code example blocks
- Extended checklists or tables

Move those sections to new files in `references/`. Add a row to the quick-reference
table for each new file.

### Step 9 — Run verification

Run the full verification script from above. ALL six dimensions must pass.

---

## Step-by-step: repo-wide audit

```bash
# List all skills
ls template/.claude/skills/

# Run full verification (all six dimensions)
# Copy and run the verification script above

# Check for broken reference links
for f in template/.claude/skills/*/SKILL.md; do
    skill_dir=$(dirname "$f")
    grep -oP 'references/[a-z0-9-]+\.md' "$f" | while read ref; do
        [ -f "$skill_dir/$ref" ] || echo "BROKEN: $skill_dir/$ref"
    done
done

# Check for orphaned reference files (not linked from SKILL.md)
for dir in template/.claude/skills/*/references; do
    skill_md="$(dirname "$dir")/SKILL.md"
    for ref in "$dir"/*.md; do
        basename_ref=$(basename "$ref")
        grep -q "$basename_ref" "$skill_md" || echo "ORPHANED: $ref"
    done
done
```

Fix issues in priority order: broken links first, then dimension violations,
then orphaned files.

---

## SKILL.md section order

When restructuring a SKILL.md, use this standard order:

1. YAML frontmatter (`---` block with `name` and `description: >-`)
2. `# <Name> Skill` title
3. 1-3 line intro paragraph
4. Core content sections (main workflows, principles, checklists)
5. `## Quick reference: where to go deeper` (reference table)
6. Optional: `## Bundled scripts` (if `scripts/` exists)

---

## Writing style rules

Apply these when editing any skill content:

- **Sentence case headings** — capitalize first word and proper nouns only
- **Imperative voice** — "Run this command" not "This command can be run"
- **Short paragraphs** — 3-5 lines max; use tables for parallel items
- **100-character line width** — wrap prose, not code blocks or tables
- **No emoji in headings** — emoji are allowed in table cells for quick scanning
- **Relative links** — use `[references/file.md](references/file.md)`, not absolute paths

---

## Quick reference: where to go deeper

| Topic                                | Reference file                                                             |
|--------------------------------------|----------------------------------------------------------------------------|
| Full 9-area deep audit checklist     | [references/audit-checklist.md](references/audit-checklist.md)             |
| Annotated before/after fix examples  | [references/audit-examples.md](references/audit-examples.md)               |
| Running log of all audit sessions    | [references/maintenance-log.md](references/maintenance-log.md)             |
