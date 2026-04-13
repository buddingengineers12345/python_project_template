---
name: pr-template
description: >
  Enforce a strict PR (pull request) description template every time one is generated, written, or drafted.
  Use this skill whenever the user asks to: generate a PR, write a PR description, draft a pull request,
  create a PR for a branch or commit, summarize changes as a PR, or fill in a PR template.
  Also trigger when the user says things like "make a PR for this", "write up the PR", "PR description for
  these changes", "help me open a PR", or pastes a diff/commit log and asks for a PR.
  ALWAYS use this skill for any PR-related generation task — never freeform a PR description without it.
---

# PR Template Skill

> **One rule above all:** Never write a PR description without following every step below in order.
> Never skip a step. Never skip a section. Never invent your own structure.

---

## STEP 1 — Get the template

The PR template lives at `.github/PULL_REQUEST_TEMPLATE.md` in the user's repository.
Obtain it using whichever situation applies — check in order:

| Situation | What to do |
|---|---|
| **User pasted the template** in their message | Use that content directly as your skeleton |
| **File access is available** (e.g. Claude Code, filesystem tools) | Read `.github/PULL_REQUEST_TEMPLATE.md` from the repo root |
| **Neither of the above** | Use the fallback skeleton at the bottom of this document |

- Do **not** modify the template's headings, section order, or structure.
- Do **not** mix the fallback with a user-provided template. Use exactly one source.

> ⚠️ Do not proceed to Step 2 until you have the template loaded.

---

## STEP 2 — Extract signals from the user's input

Scan everything the user provided. Find these signals:

| Signal | Look for |
|---|---|
| **What changed** | diff, file names, commit messages, branch name |
| **Why it changed** | issue title, commit body, user's description |
| **Tests** | words like `pytest`, `jest`, `npm test`, test file names, `tests/` folder |
| **Issue numbers** | patterns like `#123`, or words `closes`, `fixes`, `resolves` |
| **Docs changed** | paths containing `docs/`, `README`, or files ending in `.md` |

**Rule:** If a signal is missing, do NOT ask the user. Infer from context and mark it (Step 3 explains how).

---

## STEP 3 — Fill each section

Read `references/section-rules.md` now.
It contains exact fill instructions, fallback text, and examples for every section.
Work through each section **one at a time, in template order**.

---

## STEP 4 — Validate

Before outputting anything, check each item below. If a check fails, fix it first.

| # | Check | Fix if failing |
|---|---|---|
| 1 | If the loaded template begins with `<!--`, your output must also begin with that same comment block | Copy the opening comment from the template to the top of your output |
| 2 | All sections from the loaded template are present in original order | Add any missing section in the correct position |
| 3 | No raw placeholder text remains (e.g. `Change 1`, `Closes #…`) | Replace with real content or the correct fallback string from `section-rules.md` |
| 4 | Contributor checklist boxes are all unchecked (`- [ ]`) | Change any `- [x]` back to `- [ ]` |
| 5 | Output ends with `Thank you for your contribution.` | Add it as the final line |
| 6 | Entire output is wrapped in a ` ```markdown ``` ` code block | Wrap it |

**Do not output until all 6 checks pass.**

---

## STEP 5 — Add a notice (only if needed)

After the code block:
- **If any section contains `<!-- please verify`** → write a plain-text note listing each flagged section by name so the user knows what to fix before submitting.
- **If no `<!-- please verify` markers exist** → output nothing after the code block.

---

## Fallback template skeleton

Use this only if `.github/PULL_REQUEST_TEMPLATE.md` cannot be found.

```markdown
<!--
Thank you for opening a pull request!
Please provide clear and complete information to help reviewers
understand, review, and merge your changes efficiently.
-->

## Summary

---

## Changes introduced

---

## Testing

---

## Documentation

---

## Related issues

---

## Contributor checklist

Please confirm the following before submitting:

- [ ] I have read and followed the [Contributing Guidelines](../CONTRIBUTING.md)
- [ ] Tests have been added or updated as appropriate
- [ ] Documentation has been updated where necessary
- [ ] Linting and formatting pass locally
- [ ] CI checks are passing

---

## Release notes

If this change affects users, please indicate whether a release note is required:

- [ ] A release note has been added
- [ ] This change does not require a release note

---

## Additional notes

---

Thank you for your contribution.
```
