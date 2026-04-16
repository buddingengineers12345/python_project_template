---
name: maintain-skills
description: >-
  Audit, standardize, and improve existing skills in a skills directory (commonly
  `.claude/skills/` or `template/.claude/skills/`). Use for 'audit this skill', 'review
  skill quality', 'standardize skills', or any request to systematically review or
  improve a SKILL.md file. Validates all seven consistency dimensions: frontmatter block
  scalars, title format, reference table headers, bundled-file naming, H1 headings, line
  count, and bundled-asset layout. Provides step-by-step fix instructions for each
  violation. Do NOT use for creating new skills from scratch — use skill-creator instead.
---

# Maintain Skills Skill

Audit, standardize, and improve existing skills. This skill provides exact rules and
commands so any model — including haiku — can maintain skills mechanically.

Skills live under a skills root directory. The canonical path in this repo is
`.claude/skills/` (Claude Code / Cowork default); older layouts used
`template/.claude/skills/`. Set `SKILLS_DIR` once and every check below works:

```bash
SKILLS_DIR=".claude/skills"          # or template/.claude/skills, adjust as needed
```

Each skill is a directory with this canonical layout:

```
<SKILLS_DIR>/<skill-name>/
├── SKILL.md               # Required — frontmatter + instructions (< 400 lines)
├── references/            # Optional — deep-dive documents, one per topic
│   └── <topic-name>.md    # Descriptive kebab-case names, 200-270 lines each
├── scripts/               # Optional — executable tools (*.py, *.sh)
├── templates/             # Optional — copy-paste starter files (top-level)
│   └── <name>-template.md
└── assets/                # Optional — non-doc files used in output or bundled with SKILL
    └── templates/         #   sub-grouped by type (templates/, icons/, fonts/, …)
        └── <file>
```

**Directory naming** — skill folder names use kebab-case (`claude-hooks`,
`python-docstrings`). Do not use underscores or camelCase. If you encounter a
folder like `claude_hooks`, rename it to `claude-hooks` and update any links.
The `name:` frontmatter field must match the folder name exactly.

**Where bundled files live** — all three directories (`references/`, `templates/`,
`assets/`) are valid. Every file in any of them must appear in the SKILL.md
reference table (dimension 3). No orphans, regardless of directory.

---

## The seven consistency dimensions

Every skill MUST pass all seven checks. These are the primary audit criteria.

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
grep 'where to go deeper' "$SKILLS_DIR"/*/SKILL.md
```
Every skill must have exactly one match.

**Every bundled file is linked.** Every file in `references/`, `templates/`, and
`assets/` (including nested subdirectories) MUST appear in this table using a
relative Markdown link, e.g. `[references/events.md](references/events.md)` or
`[assets/templates/hook-template.sh](assets/templates/hook-template.sh)`. Files
not linked are "orphans" and must either be linked or deleted.

### Dimension 4 — Bundled file naming

All files in `references/`, `templates/`, and `assets/` MUST use descriptive
kebab-case names. No numbered prefixes, no uppercase, no underscores. The
skill folder itself also follows kebab-case.

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
find "$SKILLS_DIR"/*/references "$SKILLS_DIR"/*/templates "$SKILLS_DIR"/*/assets \
  -name '[0-9]*' -o -name '*_*' -o -name '[A-Z]*' 2>/dev/null
ls -d "$SKILLS_DIR"/*/ | grep -E '[_A-Z]'    # folder naming
```
Must return zero results (empty output).

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
for f in "$SKILLS_DIR"/*/references/*.md; do
    echo "$(basename "$f"): $(head -1 "$f")"
done
```
Inspect each heading for sentence case.

### Dimension 6 — SKILL.md line count

SKILL.md MUST be under 400 lines. Target range: 150-330 lines. If content exceeds
400 lines, move sections to `references/` (deep-dive docs) or `templates/` /
`assets/` (copy-paste starter files).

**Check:**
```bash
wc -l "$SKILLS_DIR"/*/SKILL.md
```
Every file must show < 400.

### Dimension 7 — Bundled asset layout

Skills that bundle non-doc resources (templates, settings starters, icons, fonts)
use one of two valid layouts:

- **Top-level `templates/`** — for a small set of copy-paste Markdown/code
  starters referenced directly from SKILL.md (e.g., `templates/command-template.md`).
- **`assets/<category>/`** — for richer bundles grouped by type. The canonical
  sub-grouping is `assets/templates/` (starter files like `hook-template.sh`,
  `settings-example.json`). Other categories (`assets/icons/`, `assets/fonts/`)
  follow the same pattern.

Pick one layout per skill — do not mix a top-level `templates/` with
`assets/templates/` in the same skill. Every file in these directories must
appear in the reference table (dimension 3) and must use kebab-case names
(dimension 4).

**Check:**
```bash
for dir in "$SKILLS_DIR"/*/; do
    skill=$(basename "$dir")
    has_top=$([ -d "$dir/templates" ] && echo yes || echo no)
    has_assets_tpl=$([ -d "$dir/assets/templates" ] && echo yes || echo no)
    if [ "$has_top" = yes ] && [ "$has_assets_tpl" = yes ]; then
        echo "  $skill: MIXED LAYOUT (both templates/ and assets/templates/)"
    fi
done
```
Output must be empty.

---

## Full verification script

Run this after ANY skill edit. All seven dimensions in one pass. Set `SKILLS_DIR`
to match your layout (`.claude/skills` or `template/.claude/skills`).

```bash
SKILLS_DIR="${SKILLS_DIR:-.claude/skills}"

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
echo "=== 4. Bundled file + folder naming (non-kebab?) ==="
bad_folders=$(ls -d "$SKILLS_DIR"/*/ 2>/dev/null | grep -E '[_A-Z]' || true)
bad_files=$(find "$SKILLS_DIR"/*/references "$SKILLS_DIR"/*/templates \
  "$SKILLS_DIR"/*/assets -type f \
  \( -name '[0-9]*' -o -name '*_*' -o -name '[A-Z]*' \) 2>/dev/null || true)
[ -z "$bad_folders$bad_files" ] && echo "  None found ✓" \
  || { echo "  folders: $bad_folders"; echo "  files:   $bad_files"; }

echo ""
echo "=== 5. Reference H1 headings ==="
for f in "$SKILLS_DIR"/*/references/*.md; do
    [ -f "$f" ] || continue
    skill=$(basename "$(dirname "$(dirname "$f")")")
    echo "  $skill/$(basename "$f"): $(head -1 "$f")"
done

echo ""
echo "=== 6. SKILL.md line counts ==="
wc -l "$SKILLS_DIR"/*/SKILL.md

echo ""
echo "=== 7. Bundled asset layout (no mixing templates/ and assets/templates/) ==="
for dir in "$SKILLS_DIR"/*/; do
    skill=$(basename "$dir")
    if [ -d "$dir/templates" ] && [ -d "$dir/assets/templates" ]; then
        echo "  $skill: MIXED LAYOUT"
    fi
done
```

**Pass criteria:** ALL of these must be true:

- Dimension 1: every skill shows `>-`
- Dimension 2: every title ends with ` Skill`
- Dimension 3: every skill has exactly one `where to go deeper` match, and every
  file under `references/`, `templates/`, `assets/` is linked from that table
- Dimension 4: every folder and bundled file is kebab-case (no numbers, no
  underscores, no uppercase)
- Dimension 5: every H1 heading is sentence case
- Dimension 6: every SKILL.md is under 400 lines
- Dimension 7: no skill mixes top-level `templates/` with `assets/templates/`

---

For detailed step-by-step instructions on standardizing individual skills, auditing
entire skill repositories, SKILL.md structure, and writing style guidelines, see
[references/fixing-skills.md](references/fixing-skills.md).

---

## Quick reference: where to go deeper

| Topic                                              | Reference file                                                       |
|----------------------------------------------------|----------------------------------------------------------------------|
| Step-by-step fixing, auditing, and style guide    | [references/fixing-skills.md](references/fixing-skills.md)           |
| Full 9-area deep audit checklist                  | [references/audit-checklist.md](references/audit-checklist.md)       |
| Annotated before/after fix examples               | [references/audit-examples.md](references/audit-examples.md)         |
| Running log of all audit sessions                 | [references/maintenance-log.md](references/maintenance-log.md)       |
