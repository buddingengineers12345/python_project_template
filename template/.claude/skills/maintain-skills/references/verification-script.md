# Verification script

Run this after ANY skill edit. All nine dimensions in one pass. Set `SKILLS_DIR`
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

echo ""
echo "=== 8. Lazy reference loading (unconditional loads?) ==="
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    hits=$(grep -n -iE '(^[0-9]+\.|^- ).*\b(load|read)\b.*references/' "$f" \
        | grep -viE '(if |when |for |only|conditional)' || true)
    [ -n "$hits" ] && echo "  $skill: unconditional reference loads:" \
        && echo "$hits"
done

echo ""
echo "=== 9. Batch tool call guidance ==="
for f in "$SKILLS_DIR"/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    has_batch=$(grep -cilE '(batch edit|parallel call|single edit|minimize.*call)' \
        "$f" || true)
    has_edits=$(grep -cilE '(edit|write|fix|apply|create file|modify)' "$f" || true)
    if [ "$has_edits" -gt 0 ] && [ "$has_batch" -eq 0 ]; then
        echo "  $skill: edits files but has no batch guidance"
    fi
done
```

## Pass criteria

ALL of these must be true:

- Dimension 1: every skill shows `>-`
- Dimension 2: every title ends with ` Skill`
- Dimension 3: every skill has exactly one `where to go deeper` match, and every
  file under `references/`, `templates/`, `assets/` is linked from that table
- Dimension 4: every folder and bundled file is kebab-case (no numbers, no
  underscores, no uppercase)
- Dimension 5: every H1 heading is sentence case
- Dimension 6: every SKILL.md is under 400 lines
- Dimension 7: no skill mixes top-level `templates/` with `assets/templates/`
- Dimension 8: no unconditional reference loads — every "load/read reference"
  instruction has a conditional trigger
- Dimension 9: every skill that edits files or runs commands has batch edit
  and/or parallel call guidance
