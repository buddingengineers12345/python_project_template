# GitHub: PR-only workflow and squash merges

This checklist is for **repository maintainers**. Apply these settings on GitHub so that:

- No one can push directly to the default branch (`main`)
- All changes land via **pull requests**
- Merges use **squash merge** only (one commit per PR)
- Optional: CI must pass and reviews are required before merge

GitHub does not read this file automatically; use it while configuring **Settings** in the web UI (or your org’s infrastructure-as-code).

---

## 1. Protect `main`

**Settings → Rules → Rulesets** (or **Branches → Branch protection rules** for classic rules).

Add a rule that targets the branch name you use as default (usually `main`).

---

## 2. Require pull requests

Enable **Require a pull request before merging** so:

- Direct pushes to `main` are blocked
- Every change is proposed as a PR

---

## 3. Require reviews (recommended)

Under the same rule:

- Require at least **one approving review** before merge
- Optionally **dismiss stale reviews** when new commits are pushed

---

## 4. Require status checks (if you use CI)

If GitHub Actions (or other checks) run on PRs:

- Require **required status checks** to pass before merging

This repo’s workflows are intended to gate merges once checks are marked required in branch protection.

**PR template and title enforcement:** The **PR policy** workflow validates the pull request title, description (against `.github/PULL_REQUEST_TEMPLATE.md`), and commit subjects on the PR branch. In the branch protection UI, add the check named **`PR policy / pr-policy`** (workflow **PR policy**, job `pr-policy`) to your required checks. The default PR template file alone does not block merges; this workflow does.

**Squash merge:** When squash merging, GitHub often uses the **PR title** as the default squash commit subject. Use **Conventional Commits** for the title (for example `feat: add export`) so the resulting commit on the default branch matches the same policy.

---

## 5. Block unsafe updates

Enable:

- **Block force pushes**
- **Block branch deletion**

Optionally restrict who may push (if your org allows bypass lists).

---

## 6. Squash-only merges

**Settings → General → Pull Requests**:

- Enable **Allow squash merging**
- Disable **Allow merge commits** (unless your policy explicitly needs them)
- Disable **Allow rebase merging** (optional; squash-only keeps history uniform)

Each merged PR becomes a single commit on `main`.

---

## 7. Include administrators

Turn on enforcement so **admins are subject to the same rules** (no silent bypass of protection).

---

## 8. Optional: linear history

If available for your account, **require linear history** pairs well with squash merges and avoids merge commits on the default branch.

---

## New repositories

- Branch protection applies once the protected branch exists; the **first** push that creates `main` may succeed before rules are saved.
- Prefer: add an initial commit (e.g. README), then apply protection and merge settings, then collaborate via PRs.

---

## Summary

| Goal                         | Where to configure                          |
| ---------------------------- | ------------------------------------------- |
| No direct pushes to `main`   | Branch protection / rulesets                |
| PRs required                 | Branch protection / rulesets                |
| Reviews + CI                 | Branch protection / rulesets                |
| PR title/body/commits policy | Required status check **PR policy / pr-policy** |
| One commit per PR            | Repo settings: squash on, merge commits off |
| Admins follow rules          | “Include administrators” / equivalent     |
