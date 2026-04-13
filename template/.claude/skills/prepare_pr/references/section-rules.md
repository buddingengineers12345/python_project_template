# Section Rules

This file contains exact fill instructions for every PR section.
Work through sections **one at a time, in the order they appear in the template**.
Each section below tells you exactly: what to write, what to write if info is missing, and what NOT to write.

**Sections in this file:**
[How to mark missing information] → [Section 1: Summary] → [Section 2: Changes introduced] → [Section 3: Testing] → [Section 4: Documentation] → [Section 5: Related issues] → [Section 6: Contributor checklist] → [Section 7: Release notes] → [Section 8: Additional notes]

---

## How to mark missing information

When you have to guess or infer something, append this marker inline:
```
<!-- please verify: [describe what you assumed] -->
```

Example: `This PR fixes a login crash. <!-- please verify: confirm this is the correct issue description -->`

Never leave a section blank. Never leave template placeholder text. Always write something or use the exact fallback text shown below.

---

## Section 1: Summary

**What to write:**
Write 2–4 sentences. Every summary must answer both of these:
- Sentence 1 — *What* changed?
- Sentence 2 — *Why* was it needed or what problem does it solve?

**If information is thin:**
Infer from the branch name, file names, or commit messages. Add a `<!-- please verify -->` marker.

**Exact fallback (use if you truly cannot infer anything):**
```
This PR introduces changes to the codebase. <!-- please verify: please describe what this PR changes and why -->
```

**✅ Good example:**
```
This PR adds null-safety checks to the user login flow.
It prevents an unhandled exception that occurred when users logged in without a profile picture set.
```

**❌ Bad examples:**
- `This PR makes changes.`
- `Provide a concise summary of what this pull request changes and why the change is needed.` ← never copy placeholder text

---

## Section 2: Changes introduced

**What to write:**
Write 3–7 bullet points. Each bullet must describe a **functional outcome**, not a file edit.

**Rule — ask yourself:** "Does this bullet tell a reviewer *what the code now does differently*?"
- ✅ Yes → keep it
- ❌ No (it just names a file) → rewrite it

**If fewer than 3 clear changes are evident:**
Write what you know, then add this as the final bullet:
```
- <!-- please verify: are there additional changes to list? -->
```

**✅ Good example:**
```
- Replaced MD5 password hashing with bcrypt across all authentication flows
- Added a database migration to rehash existing user passwords on next login
- Updated login error messages to avoid revealing whether an email address exists
```

**❌ Bad examples:**
```
- Change 1
- Updated auth.py
- Modified the database
```

---

## Section 3: Testing

**Decision — use the first rule that applies:**

**Rule A** — If the user's input mentions test file names or test commands (e.g. `pytest`, `jest`, `npm test`, `just ci`, `go test`):
→ List them as bullets, exactly as mentioned.
```
- Ran `pytest tests/test_auth.py` — all tests passing
- Added unit tests in `tests/test_login.py` covering the null profile picture case
```

**Rule B** — If the diff shows changes to files matching `test_*`, `*_test.*`, `*.spec.*`, or files inside a `tests/` or `__tests__/` folder:
→ List those file names.
```
- Updated `tests/test_user.py` with new edge case coverage
```

**Rule C** — If neither Rule A nor Rule B applies:
→ Write this exact text, word for word:
```
- No testing information provided — please complete this section before merging.
```

**Never** leave this section blank.

---

## Section 4: Documentation

**Decision — use the first rule that applies:**

**Rule A** — If the diff shows changes to existing files in `docs/`, `README*`, or any `.md` file:
→ Write: `- Updated existing documentation: [list the file names]`

**Rule B** — If the diff shows new `.md` files being added:
→ Write: `- Added new documentation: [list the file names]`

**Rule C** — If neither Rule A nor Rule B applies:
→ Write: `- Not applicable`

Only ever write one of these three options. Do not write anything else in this section.

---

## Section 5: Related issues

**Scan the user's input for:** `#NNN`, `closes #NNN`, `fixes #NNN`, `resolves #NNN`, or any full GitHub/GitLab issue URL.

**If found:**
```
- Closes #NNN
```
Or if the PR is related but doesn't fully close the issue:
```
- Related to #NNN
```

**If nothing is found:**
→ Write this exact text, word for word:
```
- No related issues identified.
```

**Never** output `Closes #…` or `Related to #…` with the `…` ellipsis still in it. That is template placeholder text and must never appear in the output.

---

## Section 6: Contributor checklist

**Copy this block exactly. Do not change anything. Do not check any boxes.**

```
Please confirm the following before submitting:

- [ ] I have read and followed the [Contributing Guidelines](../CONTRIBUTING.md)
- [ ] Tests have been added or updated as appropriate
- [ ] Documentation has been updated where necessary
- [ ] Linting and formatting pass locally
- [ ] CI checks are passing
```

> Checking these boxes is the contributor's job, not yours. Never output `- [x]` in this section.

---

## Section 7: Release notes

**Copy this block exactly. Do not check any boxes.**

```
If this change affects users, please indicate whether a release note is required:

- [ ] A release note has been added
- [ ] This change does not require a release note
```

Then, on the very next line, add exactly one of these three comments:

| Situation | Comment to add |
|---|---|
| Change touches user-facing behaviour, APIs, or configuration | `<!-- likely needs a release note — confirm with maintainer -->` |
| Change is internal only: refactor, tests, CI pipeline, or docs | `<!-- likely no release note needed — confirm with maintainer -->` |
| Cannot tell from available context | `<!-- please verify: does this change affect users? -->` |

---

## Section 8: Additional notes

**If there is genuine reviewer guidance to share** (e.g. migration steps, known risks, areas needing careful review):
→ Write it here in plain prose or bullets.

**If there is nothing to add:**
→ Leave this section **completely blank**. Just the heading, then the `---` rule below it.

**Never write:**
- `No additional notes.`
- `N/A`
- `None`
- Any filler text
