---
name: python-docstrings
description: >-
  Write, audit, generate, fix, or review Google-style docstrings for any Python code.
  Trigger this skill for any of: "add docstrings", "document this function/class/module",
  "fix my docstrings", "are my docstrings correct", "write docs for this code", "missing
  docstrings", "docstring format", "Google style docs", "update docstrings", "check pydoc",
  or any task involving __doc__ or inline Python documentation. Always load this skill
  before writing any Python docstring — it contains all rules, templates, and reference
  pointers needed to produce correct, complete, Google-style documentation.
---

# Python Docstrings Skill

Based on [Google Python Style Guide §3.8](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

---

## Step 1 — Identify What Needs Documenting → Load the Right Reference

Read the task, identify the construct(s) involved, then **load only the relevant reference(s)** before writing anything.

| Construct | Reference to load |
|---|---|
| Function, method, or callable | `references/functions.md` |
| Class (including dataclasses, exceptions) | `references/classes.md` |
| Module or package `__init__.py` | `references/modules.md` |
| Generator function (`yield`) | `references/generators.md` + `references/functions.md` |
| `@property` (getter / setter / deleter) | `references/properties.md` |
| Overriding a base class method | `references/overrides.md` |
| Auditing or reviewing an entire file | `references/auditing.md` |
| Mixed task (e.g. "document this whole file") | Load all relevant references before starting |

**Do not write a single docstring before loading the appropriate reference.**

---

## Step 2 — Universal Rules (apply to everything)

These rules apply to every docstring regardless of construct. Internalize them before reading any reference file.

### Format
- Always use **triple double-quotes** `"""` — never `'''`, never `"`.
- **Summary line**: one physical line, ≤ 80 characters, ends with `.`, `?`, or `!`.
- **If body follows**: blank line after summary, then body at same indentation as the opening `"""`.
- **No blank line** between a `def` / `class` line and its docstring.
- Docstring `"""` must use `"""` regardless of the file's choice of `'` vs `"` for regular strings.

### Style consistency
Pick **one style** per file and use it everywhere:
- **Descriptive**: `"""Fetches rows from a Bigtable."""`
- **Imperative**: `"""Fetch rows from a Bigtable."""`

Do not mix styles within a file.

### Types in docstrings
- **Type annotations present** → do NOT repeat types in `Args:` or `Returns:`. The signature carries them.
- **No type annotations** → include types inline in the description: `param (list[str]): …`

### Punctuation, spelling, grammar
Docstrings are narrative text. Use proper capitalization, punctuation, and complete sentences. Reviewers will flag grammar issues — treat docstrings like prose, not code comments.

---

## Step 3 — Common Mistakes at a Glance

| ❌ Wrong | ✅ Fix |
|---|---|
| `'''` instead of `"""` | Always `"""` for docstrings |
| Summary line > 80 chars | Move detail to body after blank line |
| No period/punct at end of summary | Add `.`, `?`, or `!` |
| `Returns:` in a generator | Change to `Yields:` |
| `@property` says "Returns the …" | Attribute style: "The …" |
| Class docstring says "Class that …" | Remove "Class that" — describe the concept |
| Exception docstring says "Raised when …" | Describe what it *represents*, not the trigger |
| Blank line between `def` and `"""` | Remove it |
| Tuple return documented as multiple values | Document as "A tuple (a, b), where …" |
| Documenting exceptions from API misuse | Remove — only document interface-level exceptions |
| Types duplicated when annotations exist | Remove from docstring; annotation already has them |

---

## Efficiency: batch edits and parallel calls

- **Batch edits:** When adding docstrings to multiple functions in the same file,
  combine all docstring additions into a single Edit tool call. Do not make one
  edit per function.
- **Read before edit:** Read the entire file first, identify all constructs needing
  docstrings, draft all docstrings mentally, then apply in one Edit call per file.
- **Multi-file tasks:** When auditing multiple files, read all target files first,
  then edit each file once with all its docstrings in a single call.

## Quick reference: where to go deeper

| Topic                                           | Reference file                                       |
|-------------------------------------------------|------------------------------------------------------|
| Functions, methods, and callables               | [references/functions.md](references/functions.md)   |
| Classes and class docstrings                    | [references/classes.md](references/classes.md)       |
| Module and package docstrings                   | [references/modules.md](references/modules.md)       |
| Generator functions and yields                  | [references/generators.md](references/generators.md) |
| Properties, getters, setters, and deleters      | [references/properties.md](references/properties.md) |
| Overriding base class methods                   | [references/overrides.md](references/overrides.md)   |
| Docstring sections and structure                | [references/sections.md](references/sections.md)     |
| Docstring examples: before and after            | [references/examples.md](references/examples.md)     |
| Auditing Python files for docstring compliance  | [references/auditing.md](references/auditing.md)     |
