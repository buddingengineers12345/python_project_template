# Enforcing PR-Only Workflow and Squash Merges on GitHub

This document explains how to configure a repository so that:
- No one can push directly to the `main` branch
- All changes must go through Pull Requests (PRs)
- Merges are only allowed via **squash and merge**

---

## Overview

Using built-in repository settings in GitHub, you can enforce a controlled workflow that improves code quality, review processes, and commit history.

These controls are implemented through:
- Branch protection rules
- Repository merge settings

---

## 1. Protect the `main` Branch

Navigate to your repository settings and locate the branch protection section.

Create a rule targeting the `main` branch.

This rule is the foundation for preventing direct changes.

---

## 2. Require Pull Requests

Enable the requirement that all changes must be made through pull requests.

This ensures:
- No direct pushes to `main`
- All changes go through review and validation

---

## 3. Require Reviews (Recommended)

Configure pull request review requirements:
- Require at least one approval
- Optionally dismiss approvals when new commits are pushed

This ensures code is reviewed before merging.

---

## 4. Require Status Checks (CI/CD)

If your project uses automated testing or linting:
- Require all checks to pass before merging

This prevents broken or untested code from entering `main`.

---

## 5. Prevent Direct and Unsafe Changes

Enable protections to:
- Block force pushes
- Block branch deletion

Optionally:
- Restrict who can push to the branch (for stricter control)

---

## 6. Enforce Squash-Only Merges

In repository settings (Pull Request section):
- Enable squash merging
- Disable merge commits
- Disable rebase merging

This ensures:
- Each PR results in a single, clean commit
- History remains linear and readable

---

## 7. Prevent Rule Bypass

Enable enforcement so that:
- Even administrators must follow the rules

This guarantees consistent enforcement across all users.

---

## 8. Optional: Require Linear History

Enable linear history to:
- Prevent merge commits
- Ensure a clean commit graph

This works naturally with squash merging.

---

## 9. Behavior for New Repositories

### First Commit

- The very first commit is **not blocked**
- Branch protection only applies after the `main` branch exists

### Important Notes

- If the repository is initialized with a README, the first commit is created automatically
- If the repository is empty, the first push will succeed before protections apply

---

## 10. Recommended Setup Workflow

To ensure consistent enforcement:

### Preferred Approach
1. Create the repository with an initial file (e.g., README)
2. Apply branch protection rules
3. Configure merge settings

### Alternative Approach
1. Create repository
2. Add initial commit
3. Apply protections

---

## Final Result

Once configured:
- Direct pushes to `main` are blocked
- All changes must go through pull requests
- Code must be reviewed and pass checks
- Only squash merges are allowed
- Commit history remains clean and controlled

---

## Summary

This setup enforces a safe and structured development workflow by:
- Eliminating unreviewed changes
- Standardizing merge behavior
- Maintaining a clean commit history

It is considered a best practice for teams of all sizes.