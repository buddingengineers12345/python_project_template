# Audit examples: before & after

Real patterns from this repo. Use these as templates when applying fixes.

---

## Example 1: Description Missing NOT Clause — `pptx`

**Skill:** `pptx`

**Before (abridged):**
```yaml
description: "Use this skill any time a .pptx file is involved in any way — as input, output,
or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing,
or extracting text from any .pptx file..."
```

**Problem:** The description triggers on any `.pptx` task, including read-only analysis tasks where `file-reading` would be more appropriate as the entry point. No exclusion clause.

**After:**
```yaml
description: "Use this skill any time a .pptx file is involved in any way — as input, output,
or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing,
or extracting text from any .pptx file (even if the extracted content will be used elsewhere,
like in an email or summary); editing, modifying, or updating existing presentations; combining
or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger
whenever the user mentions 'deck,' 'slides,' 'presentation,' or references a .pptx filename.
Do NOT use if the file is .ppt (legacy) without converting first — convert to .pptx before this
skill can work. Do NOT use for Google Slides — this skill is .pptx only."
```

**What changed:** Added two explicit NOT clauses. First prevents silent failures on legacy `.ppt` files (python-pptx rejects them). Second prevents wrong triggers on Google Slides tasks.

**Lesson:** NOT clauses aren't just for collision avoidance — they also prevent silent technical failures where the skill can't handle the input format.

---

## Example 2: Description Collision Between Sibling Skills — `pdf` and `pdf-reading`

**Skills:** `pdf` and `pdf-reading`

**Before — `pdf` description (abridged):**
```yaml
description: "Use this skill whenever the user wants to do anything with PDF files.
This includes reading or extracting text/tables from PDFs..."
```

**Before — `pdf-reading` description:**
```yaml
description: "Use this skill when you need to read, inspect, or extract content from PDF files..."
```

**Problem:** Both descriptions claimed "reading PDFs." Claude was triggering `pdf` for read-only analysis tasks, routing users to the creation-focused skill with heavier dependencies.

**After — `pdf` description fix:**
Change "reading or extracting" to "processing, transforming, creating, or manipulating" and add:
> "Do NOT use for read-only PDF analysis — use the pdf-reading skill instead."

**After — `pdf-reading` description fix:**
Already has the NOT clause correctly:
> "Do NOT use this skill for PDF creation, form filling, merging, splitting, watermarking, or encryption — use the pdf skill instead."

**Lesson:** Boundary clarity must be maintained in BOTH directions. Each skill's NOT list should name the other skill explicitly, not just describe what it doesn't do.

---

## Example 3: Monolithic SKILL.md → Layered Structure — `docx`

**Skill:** `docx` — SKILL.md reached 590 lines

**The problem section:** The XML Reference (lines 455–590) contained detailed XML patterns for tracked changes, comments, and images. This content is only needed when hand-editing XML directly — maybe 10% of use cases.

**Fix:**
1. Created `references/xml-reference.md` and moved lines 455–590 there
2. Replaced the section in SKILL.md with a pointer:

```markdown
## XML Reference

For full XML patterns (tracked changes, comments, images, schema compliance):
see `references/xml-reference.md`.

Read it when: you need to hand-edit `word/document.xml` directly rather than
using the docx-js API or unpack/pack scripts.
```

**Result:** SKILL.md went from 590 → 395 lines. The XML content is still available but only loaded when actually needed.

**What to watch for:** After moving content, verify SKILL.md still has enough context that a user can accomplish the most common tasks (creating a document, basic editing) without reading the reference file. The reference is for depth, not basics.

---

## Example 4: Broken Dispatch Table — `file-reading`

**Skill:** `file-reading` dispatch table

**Before:**
```markdown
| `.pdf` | Content inventory | `/mnt/skills/public/pdf/SKILL.md` |
```

**Problem:** `pdf-reading` was added as a dedicated read-only skill after `file-reading` was written. The dispatch table still pointed all PDF tasks to the creation-focused `pdf` skill.

**Fix:**
```markdown
| `.pdf` (read/extract/analyze) | Content inventory → pdf-reading skill | `/mnt/skills/public/pdf-reading/SKILL.md` |
| `.pdf` (create/merge/split/encrypt) | — | `/mnt/skills/public/pdf/SKILL.md` |
```

**Process:** After fixing `file-reading`, also updated `pdf-reading` to say "For file-reading routing, you'll arrive here from the file-reading dispatch table" so the flow is documented end-to-end.

**Lesson:** When a new skill is added that splits an existing skill's domain, update ALL dispatch tables in adjacent skills on the same day. Drift here causes user confusion that's very hard to diagnose.

---

## Example 5: Stale Dependency — `docx` npm package

**Skill:** `docx`

**Before:**
```bash
npm install -g docx@6.2.0
```
And code using:
```javascript
const { Document, Packer } = require('docx');
```

**Problem:** `docx` v7+ changed `Packer.toBuffer(doc)` to `Packer.toBuffer(doc)` returning a Buffer directly (previously returned a Promise of Buffer with different handling). Code written for v6 silently produced wrong output on v7+.

**Audit process:**
```bash
npm view docx version  # revealed: 8.5.0
```
Changelog showed v7 broke the Promise-based Packer pattern.

**Fix:**
1. Updated install: `npm install -g docx` (no pinned version)
2. Tested updated pattern in bash_tool to confirm it works
3. Updated all Packer usages in examples
4. Added version comment: `// docx@7+ API — Packer returns Buffer directly`

**Lesson:** Pin to a major version only when documenting a specific known breaking change. Omit version pins otherwise — stale installs are worse than no pin.

---

## Example 6: Missing Validation Step — `xlsx`

**Skill:** `xlsx`

**Before:** Skill had thorough instructions for creating spreadsheets with openpyxl, but ended with:
```python
wb.save("output.xlsx")
```
No validation. No mention of what to do if the file was corrupt.

**Problem:** openpyxl can create structurally valid `.xlsx` files that Excel/Google Sheets refuses to open due to formula errors, broken cell references, or missing named ranges. Without validation, users received silent corrupt outputs.

**Fix — added after the save call:**
```markdown
### Validation

After saving, verify the file has no formula errors before presenting to the user:
```python
from openpyxl import load_workbook

wb = load_workbook("output.xlsx", data_only=False)
errors = []
for sheet in wb.sheetnames:
    ws = wb[sheet]
    for row in ws.iter_rows():
        for cell in row:
            if cell.value and str(cell.value).startswith(('#REF!', '#DIV/0!', '#VALUE!', '#N/A', '#NAME?')):
                errors.append(f"{sheet}!{cell.coordinate}: {cell.value}")

if errors:
    print("Formula errors found:", errors)
    # Fix the formula or data before delivering
else:
    print("File validated — no formula errors")
```
**Zero formula errors is a hard requirement for all Excel deliverables.**
```

---

## Example 7: Passive Writing Style — Generic Example

**Pattern found across several skills:**

**Before (passive):**
```markdown
The document can be unpacked using the following command.
Content should be extracted before editing.
Styles can be overridden by using exact IDs.
```

**After (imperative):**
```markdown
Unpack the document before editing:
Extract content first, then make edits.
Override styles using exact IDs — "Heading1", "Heading2", etc.
```

**Why this matters:** The skill-creator standard says imperative form reduces cognitive load. A passive instruction ("can be done") suggests optionality. An imperative instruction ("do this") signals required steps. Skills are instructions, not descriptions — they should read like instructions.

**Quick check:** If you find yourself writing "can be", "should be", or "is able to", rewrite as a direct command.

---

## Example 8: Script Quality — Undocumented Dependency

**Skill:** `pdf` — `scripts/ocr.py`

**Before:** Script used `pytesseract` but this wasn't listed in the skill's Dependencies section and wasn't in the standard environment.

**Discovered via:**
```bash
grep "^import\|^from" /mnt/skills/public/pdf/scripts/ocr.py | grep -v "os\|sys\|json"
# Output: from pytesseract import image_to_string
```

**Fix:**
1. Added to Dependencies section: `pytesseract: OCR fallback (install: pip install pytesseract --break-system-packages)`
2. Added install-check at the top of the script:
```python
try:
    import pytesseract
except ImportError:
    raise SystemExit("pytesseract not installed. Run: pip install pytesseract --break-system-packages")
```

**Lesson:** Always grep script imports for non-stdlib packages and verify every one appears in the skill's Dependencies section. An undocumented dependency causes a `ModuleNotFoundError` with no guidance on how to fix it.
