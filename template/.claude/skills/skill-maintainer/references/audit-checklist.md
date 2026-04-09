# Audit checklist

Full 9-area deep audit. Run all areas for each skill, top to bottom. Use for
thorough reviews, repo-wide sweeps, or when unsure about a specific quality area.

The six consistency dimensions (in SKILL.md) are the minimum bar. This checklist
goes deeper into content quality, technical accuracy, and cross-skill health.

---

## Severity rubric

Use consistently when labelling issues:

| Severity | Definition | Examples |
|----------|------------|---------|
| **HIGH** | Skill won't trigger, produces broken output, or has broken links | Missing/vague description, dangling reference, corrupt script |
| **MED** | Degrades quality, causes confusion, or routes to wrong skill | Stale examples, missing NOT triggers, passive writing style |
| **LOW** | Cosmetic, organizational, or future-proofing | Line count creep, minor heading case error, hypothetical examples |

---

## Area 1 — Frontmatter quality

Read the YAML frontmatter at the top of SKILL.md.

**Required fields:** `name` (lowercase, hyphenated) and `description` (using `>-`).

**Description quality checklist:**

| Criterion | Good | Bad |
|-----------|------|-----|
| Specific trigger phrases | "triggers on 'Word doc', '.docx'" | "use for document tasks" |
| Explicit NOT/DO NOT list | "Do NOT use for PDFs" | no exclusions at all |
| Covers implicit requests | "If user asks for a 'report' as a Word file" | only explicit mentions |
| Imperative phrasing | "Use this skill whenever..." | "This skill can be used..." |
| Word count | 80-150 words | < 30 or > 200 |

**Collision check** — compare descriptions across skills for overlapping triggers:

```bash
grep -A5 "^description:" template/.claude/skills/*/SKILL.md
```

If two skills claim the same trigger, both need NOT clauses naming the other.

---

## Area 2 — Structure and navigation

- **Clear intro** — 1-3 lines after the title explaining what the skill does
- **Logical headers** — H2 for major sections, H3 for subsections, no skipped levels
- **Under 400 lines** — if longer, move content to `references/`
- **Reference table present** — `## Quick reference: where to go deeper` with table
- **No dangling references** — every linked file actually exists

```bash
SKILL_DIR="template/.claude/skills/<skill-name>"

# Line count
wc -l "$SKILL_DIR/SKILL.md"

# Check all reference links resolve
grep -oP 'references/[a-z0-9-]+\.md' "$SKILL_DIR/SKILL.md" | while read ref; do
    [ -f "$SKILL_DIR/$ref" ] || echo "BROKEN: $ref"
done
```

**Writing style** — instructions use imperative form ("Run this command", "Set the
page size"), not passive ("This command can be run", "The page size should be set").
Flag skills that mix tenses or are mostly passive.

---

## Area 3 — Technical accuracy

The most perishable part of any skill.

**Package versions and install commands:**
```bash
# pip packages
pip index versions <package-name> --break-system-packages 2>/dev/null | head -3

# npm packages
npm view <package-name> version
```

Flag when a skill pins an old major version and the new version has breaking changes.

**Script paths** — verify every script reference exists:
```bash
ls template/.claude/skills/<skill-name>/scripts/ 2>/dev/null
```

**API/syntax accuracy** — spot-check 2-3 code examples against the current library
API. Flag method renames, removed parameters, or changed import paths.

---

## Area 4 — Script quality

For skills with a `scripts/` directory:

**Runnability:**
```bash
python template/.claude/skills/<skill>/scripts/<script>.py --help 2>&1 | head -5
```

**Error handling** — scripts should fail with clear messages, not Python tracebacks.

**Undocumented dependencies:**
```bash
grep -E "^import|^from" template/.claude/skills/<skill>/scripts/*.py \
    | grep -v "os\|sys\|json\|re\|pathlib\|argparse\|dataclasses"
```

Every non-stdlib import must be mentioned in the skill's documentation or have a
try/import guard with an install instruction.

**pip convention** — scripts that install packages must use `--break-system-packages`.

---

## Area 5 — Cross-skill consistency

Skills sometimes reference each other. Stale cross-references cause wrong routing.

**Verify all cross-references:**
```bash
grep -rn "skills/" template/.claude/skills/ --include="*.md" | grep -v ".skill:"
```

When a new skill splits an existing skill's domain, update ALL related skills'
descriptions and reference tables on the same day.

---

## Area 6 — Progressive disclosure compliance

| Layer | Location | Target size | Check |
|-------|----------|-------------|-------|
| Metadata | YAML frontmatter | 80-150 words | Not a wall of text |
| Core | SKILL.md body | < 400 lines | `wc -l` |
| Deep reference | `references/` | 200-270 lines each | Per-file check |
| Scripts | `scripts/` | Unlimited | Documented in SKILL.md |

**Red flags:**
- SKILL.md > 400 lines with no `references/` directory
- Critical info buried past line 300 with no reference table near the top
- Same gotcha repeated 3+ times instead of consolidated
- Reference files listed in SKILL.md but never linked with Markdown links

---

## Area 7 — Critical rules and pitfall coverage

Every practical skill should have a section surfacing 5-10 non-obvious gotchas.

Quality check: are rules specific and actionable?

```
VAGUE: "Always validate output"
ACTIONABLE: "After saving, load the file back with openpyxl and check for #REF! errors"
```

---

## Area 8 — Output and validation

For skills that produce files or modify code:

- Is there a validation step after the action?
- Do code examples include error handling?
- Is there guidance on what to do when something fails?

**Template for adding a missing validation step:**
```markdown
### Validation

After creating the file, validate before delivering:
[specific command or code block]
If validation fails: [specific recovery steps]
```

---

## Area 9 — Security review

Quick pass — flag anything surprising for human review:

- Bash commands that send data to external servers
- Code that accesses credentials or sensitive files
- Description that does not accurately reflect what the skill does
- Scripts that download or execute code from the network

---

## Producing an audit report

After completing all 9 areas:

```markdown
## Skill audit: <skill-name>
**Reviewed:** <date>

### Overall health: [Good / Needs work / Critical issues]

### Issues found
| # | Area | Severity | Description |
|---|------|----------|-------------|
| 1 | Frontmatter | HIGH | Description uses quoted string, not >- |
| 2 | Structure | MED | SKILL.md is 480 lines, needs reference extraction |
| 3 | Headings | LOW | Reference file uses title case instead of sentence case |

### Recommended fixes (priority order)
1. [HIGH] Change description to >- block scalar
2. [MED] Move lines 300-480 to references/deep-dive.md
3. [LOW] Change "# All About Fixtures" to "# Fixtures"

### Strengths to preserve
- Excellent reference table with clear topic descriptions
- Scripts are well-documented with --help flags
```

For repo-wide audits, lead with a summary:

```markdown
## Repo health summary — <date>
| Skill | Health | High | Med | Low | Top issue |
|-------|--------|------|-----|-----|-----------|
| pytest | Good | 0 | 0 | 1 | Minor heading case |
| markdown | Good | 0 | 0 | 0 | Clean |
| python-code-quality | Good | 0 | 1 | 0 | Section header inconsistency |
```
