#!/usr/bin/env python3
"""Validate PR descriptions and commit subjects for policy compliance."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import Final

# Conventional commit types (aligned with .claude/rules/common/git-workflow.md and pre-commit hook).
_TYPES: Final = "feat|fix|refactor|docs|test|chore|perf|ci|build"
# First line: type, optional scope, optional !, colon, space, non-empty subject.
_CONVENTIONAL_SUBJECT: Final[re.Pattern[str]] = re.compile(
    rf"^({_TYPES})(\([^)]+\))?(!)?: [^\s].*$",
)
_MAX_SUBJECT_LEN: Final = 72

_MERGE_SUBJECT: Final[re.Pattern[str]] = re.compile(
    r"^Merge (branch |pull request |remote-tracking branch )",
    re.IGNORECASE,
)
_REVERT_SUBJECT: Final[re.Pattern[str]] = re.compile(r"^Revert [\"']", re.IGNORECASE)

_HTML_COMMENT: Final[re.Pattern[str]] = re.compile(r"<!--.*?-->", re.DOTALL)

_REQUIRED_PR_HEADINGS: Final[tuple[str, ...]] = (
    "Summary",
    "Changes introduced",
    "Testing",
    "Documentation",
    "Related issues",
    "Contributor checklist",
    "Release notes",
    "Additional notes",
)

_BOILERPLATE_CHANGE1: Final = "- Change 1"


def strip_html_comments(text: str) -> str:
    """Remove HTML comment blocks from PR bodies."""
    return _HTML_COMMENT.sub("", text)


def validate_conventional_subject_line(line: str) -> str | None:
    """Return an error message if the subject line is not allowed; else None."""
    stripped = line.strip()
    if not stripped:
        return "commit subject is empty"
    if _MERGE_SUBJECT.match(stripped) or _REVERT_SUBJECT.match(stripped):
        return None
    if len(stripped) > _MAX_SUBJECT_LEN:
        return f"subject exceeds {_MAX_SUBJECT_LEN} characters (got {len(stripped)})"
    if not _CONVENTIONAL_SUBJECT.match(stripped):
        return (
            "subject must match Conventional Commits, e.g. 'feat: add thing' or "
            "'fix(scope): handle edge case'"
        )
    return None


def validate_pr_title(title: str) -> str | None:
    """Return an error message if the PR title is invalid; else None."""
    if not title.strip():
        return "PR title is empty"
    return validate_conventional_subject_line(title.split("\n", maxsplit=1)[0])


def validate_pr_body(body: str | None) -> str | None:
    """Return an error message if the PR body does not follow the template; else None."""
    if body is None or not body.strip():
        return "PR body is empty"
    cleaned = strip_html_comments(body)
    if _BOILERPLATE_CHANGE1 in cleaned:
        return "PR body still contains template placeholder '- Change 1'; replace with real changes"
    for heading in _REQUIRED_PR_HEADINGS:
        if not re.search(rf"^## {re.escape(heading)}\s*$", cleaned, flags=re.MULTILINE):
            return f"PR body missing required section heading: ## {heading}"
    return None


def _git_first_parent_subject(sha: str) -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%s", sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git log failed for {sha}: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_commit_range(base: str, head: str) -> str | None:
    """Return an error message if any commit in base..head fails validation; else None."""
    rev_list = subprocess.run(
        ["git", "rev-list", "--reverse", f"{base}..{head}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if rev_list.returncode != 0:
        return f"git rev-list failed: {rev_list.stderr.strip()}"
    for sha in rev_list.stdout.splitlines():
        sha = sha.strip()
        if not sha:
            continue
        try:
            subject = _git_first_parent_subject(sha)
        except RuntimeError as exc:
            return str(exc)
        err = validate_conventional_subject_line(subject)
        if err:
            return f"commit {sha[:7]}: {err} (subject: {subject!r})"
    return None


def _cmd_pr() -> int:
    title = os.environ.get("PR_TITLE", "")
    body = os.environ.get("PR_BODY")
    err = validate_pr_title(title)
    if err:
        print(f"pr_commit_policy: invalid PR title: {err}", file=sys.stderr)
        return 1
    err = validate_pr_body(body)
    if err:
        print(f"pr_commit_policy: invalid PR body: {err}", file=sys.stderr)
        return 1
    return 0


def _cmd_commits(base: str, head: str) -> int:
    err = validate_commit_range(base, head)
    if err:
        print(f"pr_commit_policy: {err}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("pr", help="validate PR_TITLE and PR_BODY environment variables")

    p_commits = sub.add_parser("commits", help="validate git commits in a range")
    p_commits.add_argument(
        "--base",
        default=os.environ.get("PR_BASE_SHA", ""),
        help="merge-base side SHA (default: PR_BASE_SHA env)",
    )
    p_commits.add_argument(
        "--head",
        default=os.environ.get("PR_HEAD_SHA", ""),
        help="branch tip SHA (default: PR_HEAD_SHA env)",
    )

    args = parser.parse_args()
    if args.command == "pr":
        return _cmd_pr()
    if args.command == "commits":
        if not args.base or not args.head:
            print(
                "pr_commit_policy: commits requires --base and --head "
                "(or PR_BASE_SHA and PR_HEAD_SHA)",
                file=sys.stderr,
            )
            return 1
        return _cmd_commits(args.base, args.head)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
