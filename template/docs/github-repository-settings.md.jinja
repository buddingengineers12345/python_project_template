# GitHub repository settings (maintainer checklist)

**Use this file as the only checklist** for what to configure on **github.com** for this repository (Settings UI, branch protection / rulesets, and merge options). Other docs link here instead of repeating steps.

GitHub does not read this file automatically—apply everything below in the web UI (or your org’s infrastructure-as-code).

---

## 1. Protect the default branch (`main`)

**Settings → Rules → Rulesets** (recommended), or **Settings → Branches → Branch protection rules** (classic).

Create a rule targeting your default branch (usually `main`).

---

## 2. Require pull requests

Enable **Require a pull request before merging** so:

- Direct pushes to `main` are blocked
- Every change is proposed as a PR

---

## 3. Require reviews (recommended for teams)

Under the same rule:

- Require at least **one approving review** before merge
- Optionally **dismiss stale reviews** when new commits are pushed

> **Solo maintainers:** In the usual GitHub flow you **cannot approve your own** pull request. Leaving required approvals enabled can **block merges** on a one-person repo. Omit this requirement and rely on **required status checks** (section 4), **PR policy** when you use PRs, and local habits such as `just review`. See **section 12**.

---

## 4. Require status checks (CI)

When GitHub Actions run on pull requests:

1. Open any PR (or create a test PR) and open the **Checks** tab.
2. Note the **exact** check names (for example `Workflow name / job name`).
3. In branch protection / rulesets, add those checks as **required** so failing CI blocks merge.

Typical workflow **display names** include **CI** or **CI Tests**, **Lint**, **Security** (if
present), and **PR policy**—they differ per repository. Always confirm the exact strings in a
pull request’s **Checks** tab before adding them as required.

Add **`PR policy / pr-policy`** (workflow **PR policy**, job `pr-policy`) if you want PR
title, body (against `.github/PULL_REQUEST_TEMPLATE.md`), and commit-subject rules enforced on
GitHub. The PR template file alone does not block merges; this workflow does.

**Tip:** You can also require **Dependency review**, **labeler**, or other workflows; names must match what GitHub shows on the PR.

---

## 5. Pull request titles and conventional commits

When you **squash merge**, GitHub often uses the **PR title** as the default squash commit subject.

- Use **Conventional Commits** for PR titles (for example `feat: add export`) so the resulting commit on `main` stays consistent with local **commit-msg** hooks and project policy.
- Locally, `just precommit-install` registers commit-msg hooks and Git’s **commit template** (`.gitmessage`); align PR titles with the same convention when you expect squash merges.

---

## 6. Block unsafe updates

Enable:

- **Block force pushes**
- **Block branch deletion**

Optionally restrict who may push (if your org allows bypass lists).

---

## 7. Squash-only merges

**Settings → General → Pull Requests**:

- Enable **Allow squash merging**
- Disable **Allow merge commits** (unless your policy explicitly needs them)
- Disable **Allow rebase merging** (optional; squash-only keeps history uniform)

Each merged PR becomes a single commit on `main`.

---

## 8. Include administrators

Turn on enforcement so **admins are subject to the same rules** (no silent bypass of protection).

---

## 9. Optional: linear history

If available for your account, **require linear history** pairs well with squash merges and avoids merge commits on the default branch.

---

## 10. New repositories

- Branch protection applies once the protected branch exists; the **first** push that creates `main` may succeed before rules are saved.
- Prefer: add an initial commit (e.g. README), then apply protection and merge settings, then collaborate via PRs.

---

## 11. Repository secrets and variables

Workflows that need API tokens or credentials use **Settings → Secrets and variables → Actions**
(organization secrets if applicable). Exact names and setup steps depend on the workflow—for
example Codecov is documented next to the docs CI in this template’s **`docs/ci.md`** (when
MkDocs is enabled). Never commit secrets or paste them into Copier answers.

---

## 12. Solo / personal maintainer

Personal and private repositories can still use **rulesets**, **required status checks**, and the
workflows in `.github/workflows/`—the main mismatch with this checklist is **required approvals**
(section 3) when you are the only human.

### What adds value versus ceremony (solo)

Many items above are **team gates**: they make sense when someone else merges or reviews. Alone,
you still *can* turn them on, but the **payoff** is uneven:

| Kind | Examples | Solo takeaway |
| ---- | -------- | ------------- |
| **High value** | CI on `push` / PR, **block force push** and **branch deletion**, local **pre-commit** / **`just check`** | Catches breakage and accidents **without** a second person. This is where most real enforcement lives. |
| **Useful if you like the workflow** | **Require PR**, **required status checks** on PRs, **PR policy** as a required check | Mostly **self-discipline**: you are still approving your own work. Benefits: run CI before merging to `main`, avoid direct pushes by mistake, keep PR titles/bodies consistent—not independent review. |
| **Little extra value** | **Required approvals**, **include administrators** when you are the only admin | No second human to block bad merges; “no bypass” matters when others share the repo. Safe to skip or treat as documentation for a future team. |

If GitHub settings feel like pointless clicks, lean on **CI + local hooks** and merge however you
prefer (PR or direct), as long as you accept the trade-offs.

### GitHub (when you use pull requests)

Configure a ruleset on `main` roughly as follows:

- **Require a pull request before merging** if you want the server to block direct pushes.
- **Require status checks** to pass—copy exact names from a real PR’s **Checks** tab (section 4).
- Add **`PR policy / pr-policy`** as a required check if you want PR title, body, and commit
  subjects enforced before merge.
- **Do not** require approving reviews if you cannot supply a second approver.
- Keep **block force pushes**, **block branch deletion**, and **include administrators** (sections 6
  and 8).

### Local enforcement (with or without GitHub protection)

These work entirely on your machine:

- **`no-commit-to-branch`** in `.pre-commit-config.yaml` blocks commits on `main` / `master` so
  you develop on a feature branch (pair with GitHub’s “require PR” if you want the same rule
  remotely).
- **`commit-msg`** hooks (**Conventional Commits**) run on every commit after `just precommit-install`.
- **`pre-push`** runs **`just check`** (read-only full gate: sync, lint, types, tests, pre-commit,
  audit) before `git push` succeeds—slower than commit time, but catches CI failures early.
  To bypass occasionally (not for routine use): `SKIP=just-check git push` or `git push --no-verify`.

---

## Summary

| Goal | Where to configure |
| ---- | ------------------ |
| No direct pushes to `main` | Branch protection / rulesets |
| PRs required | Branch protection / rulesets |
| Reviews + required CI | Branch protection / rulesets (skip required reviews if solo — section 12) |
| PR title / body / commits policy | Required check **PR policy / pr-policy** |
| One commit per PR | **Settings → General → Pull requests**: squash on, merge commits off |
| Admins follow rules | “Include administrators” / equivalent |
| PR title matches squash commit subject | Use Conventional Commits on PR titles (section 5) |
| Solo: parity without required approvals | Section 12 (rulesets + local hooks) |
| API tokens for workflows | **Settings → Secrets and variables → Actions** (section 11) |

---

## Workflow names on your repository

Required check names depend on which Actions workflows exist in **your** repository. **Always**
copy the exact strings from a real pull request’s **Checks** tab before adding them to branch
protection.
