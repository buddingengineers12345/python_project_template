---
name: maintain-skills
description: >-
  Audit, standardize, and improve existing skills in a skills directory (commonly
  `.claude/skills/` or `template/.claude/skills/`). Use for 'audit this skill', 'review
  skill quality', 'standardize skills', or any request to systematically review or
  improve a SKILL.md file. Validates all nine consistency dimensions: frontmatter block
  scalars, title format, reference table headers, bundled-file naming, H1 headings, line
  count, bundled-asset layout, lazy reference loading, and batch tool calls. Provides
  step-by-step fix instructions for each violation. Do NOT use for creating new skills
  from scratch — use skill-creator instead.
---

# Maintain Skills Skill

Audit, standardize, and improve existing skills. This skill provides exact rules and
commands so any model — including haiku — can maintain skills mechanically. Covers nine
consistency dimensions including lazy reference loading and batch tool call guidance.

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

## The nine consistency dimensions

Every skill MUST pass all nine checks. These are the primary audit criteria.

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

### Dimension 8 — Lazy reference loading

Skills MUST load reference files **on demand**, not eagerly. SKILL.md MUST contain a
**conditional loading table** (or decision tree) that maps task contexts to specific
references. The most common use case MUST be handled by inline guidance in SKILL.md
itself, so simple tasks require **zero** reference file loads.

**Pattern — conditional loading table:**

```markdown
## When to load references

| If the task involves…               | Load                               |
|--------------------------------------|------------------------------------|
| Writing async tests                  | `references/async-testing.md`      |
| Using mocks or test doubles          | `references/mocking.md`            |
| Fixture scopes or factory fixtures   | `references/fixtures.md`           |
| Simple test writing (default)        | No reference needed — use inline   |
```

**Pattern — decision tree (alternative):**

```markdown
## Reference loading

├── Writing a new test file?
│   └── Use inline guidance below (AAA, naming, assertions)
├── Need fixtures beyond basic `@pytest.fixture`?
│   └── Load `references/fixtures.md`
├── Need mocking guidance?
│   └── Load `references/mocking.md`
└── Debugging flaky tests?
    └── Load `references/anti-patterns.md`
```

**Rules:**

- Never instruct "Load reference X" without a condition or context.
- The words "read", "load", or "consult" for a reference file MUST be preceded by
  a conditional ("if", "when", "for `<context>`").
- Inline guidance in SKILL.md must cover the 80% case. References are for depth,
  not basics.
- Skills with a single reference file: the condition can be simple ("For the full
  config reference, see…") but must still exist — never "always load X first".
- Orchestrator skills (sdlc-workflow, tdd-workflow) load sub-skill SKILL.md files
  at the **start of the stage that needs them**, not all upfront. Each stage's load
  instruction is itself a conditional.

**Check:**
```bash
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    # Find unconditional "load/read" instructions for reference files
    hits=$(grep -n -iE '(^[0-9]+\.|^- ).*\b(load|read)\b.*references/' "$f" \
        | grep -viE '(if |when |for |only|conditional)' || true)
    [ -n "$hits" ] && echo "  $skill: unconditional reference loads found:" \
        && echo "$hits"
done
```
Ideally returns empty — all reference loads are conditional.

### Dimension 9 — Batch tool calls

Skills that involve editing files or running commands MUST include explicit **batch
edit guidance** instructing the executing model to minimize API calls.

**Required guidance block** — add this verbatim or adapted to the skill's domain:

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

**Rules:**

- Every skill that instructs the model to edit files (write code, fix issues,
  apply docstrings, etc.) MUST contain batch edit guidance.
- Every skill that instructs the model to run multiple independent commands
  MUST mention parallel execution.
- Orchestrator skills (sdlc-workflow, tdd-workflow) that launch Agent calls
  already handle parallelism via multiple Agent invocations — add batch guidance
  for within-agent edits.
- Skills that are read-only or informational (no file edits, no command runs)
  are exempt.

**Check:**
```bash
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    # Check for batch/parallel guidance
    has_batch=$(grep -cilE '(batch edit|parallel call|single edit|minimize.*call)' \
        "$f" || true)
    has_edits=$(grep -cilE '(edit|write|fix|apply|create file|modify)' "$f" || true)
    if [ "$has_edits" -gt 0 ] && [ "$has_batch" -eq 0 ]; then
        echo "  $skill: edits files but has no batch guidance"
    fi
done
```
Ideally returns empty — all editing skills have batch guidance.

---

## Full verification script

Run the script in [references/verification-script.md](references/verification-script.md)
after ANY skill edit. It checks all nine dimensions in one pass.

---

For detailed step-by-step instructions on standardizing individual skills, auditing
entire skill repositories, SKILL.md structure, and writing style guidelines, see
[references/fixing-skills.md](references/fixing-skills.md).

---

## When to load references

| If the task involves…                      | Load                              |
|---------------------------------------------|-----------------------------------|
| Step-by-step standardization of one skill  | `references/fixing-skills.md`     |
| Full 11-area deep audit of a skill         | `references/audit-checklist.md`   |
| Before/after fix examples for reference    | `references/audit-examples.md`    |
| Logging a completed audit session          | `references/maintenance-log.md`   |
| Running the 9-dimension verification check | `references/verification-script.md` |
| Quick dimension check (default)            | No reference needed — use inline  |

## Efficiency: batch edits and parallel calls

- **Batch edits:** When fixing multiple dimensions in a single SKILL.md, combine
  all fixes (frontmatter, title, references, etc.) into a single Edit call.
- **Parallel audits:** When auditing multiple skills, run dimension checks for
  independent skills in parallel.
- **Read before edit:** Read the full SKILL.md once, note all violations, then
  apply all fixes in the fewest Edit calls possible.

## Quick reference: where to go deeper

| Topic                                              | Reference file                                                       |
|----------------------------------------------------|----------------------------------------------------------------------|
| Step-by-step fixing, auditing, and style guide    | [references/fixing-skills.md](references/fixing-skills.md)           |
| Full 11-area deep audit checklist                 | [references/audit-checklist.md](references/audit-checklist.md)       |
| Annotated before/after fix examples               | [references/audit-examples.md](references/audit-examples.md)         |
| Running log of all audit sessions                 | [references/maintenance-log.md](references/maintenance-log.md)       |
| Full verification script (all 9 dimensions)       | [references/verification-script.md](references/verification-script.md) |
