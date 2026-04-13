#!/usr/bin/env python3
"""Validate PR descriptions and commit subjects for policy compliance."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

# Conventional commit types (aligned with Commitizen ``cz_conventional_commits`` / commit-msg hook).
_TYPES: Final = "bump|build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
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


def suggest_title_from_branch(branch: str) -> str | None:
    """Derive a Conventional-Commits title from ``type/slug-slug`` branch names.

    Args:
        branch: Short branch name (no ``refs/heads/``) or full ref.

    Returns:
        A title such as ``chore: sync skip list``, or ``None`` if the branch does not
        start with a known conventional type prefix.
    """
    b = branch.strip()
    if b.startswith("refs/heads/"):
        b = b[11:]
    m = re.match(rf"^({_TYPES})/(.+)$", b)
    if not m:
        return None
    typ, tail = m.group(1), m.group(2)
    subject = tail.replace("/", " ")
    subject = re.sub(r"[-_]+", " ", subject)
    subject = re.sub(r"\s+", " ", subject).strip()
    if not subject:
        return None
    line = f"{typ}: {subject}"
    if len(line) > _MAX_SUBJECT_LEN:
        line = line[: _MAX_SUBJECT_LEN].rstrip()
    return line


def suggest_title_from_git(repo_cwd: Path) -> str | None:
    """Return the latest commit subject if it already satisfies conventional rules."""
    result = subprocess.run(
        ["git", "-C", str(repo_cwd), "log", "-1", "--format=%s"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    subject = result.stdout.strip()
    if validate_conventional_subject_line(subject) is None:
        return subject
    return None


def changes_introduced_markdown(repo_cwd: Path, base_ref: str, head_ref: str) -> str:
    """Build bullet lines from ``git log`` for the PR template *Changes introduced* section."""
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo_cwd),
            "log",
            "--reverse",
            "--format=- %s",
            f"{base_ref}..{head_ref}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "- (could not list commits; describe changes here)"
    lines = [ln.rstrip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return "- (no commits ahead of base; describe changes here)"
    return "\n".join(lines)


def draft_pr_body(repo_root: Path, base_ref: str, head_ref: str) -> str:
    """Return PR body text from the template with placeholders replaced."""
    template_path = repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    text = template_path.read_text(encoding="utf-8")
    bullets = changes_introduced_markdown(repo_root, base_ref, head_ref)
    block = (
        "- Change 1\n"
        "- Change 2\n"
        "- Change 3 (if applicable)"
    )
    if block not in text:
        return text
    return text.replace(block, bullets, 1)


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


def _git_toplevel() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("not a git repository (git rev-parse --show-toplevel failed)")
    return Path(result.stdout.strip())


def _resolve_base_ref(repo: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    for ref in ("origin/main", "main"):
        chk = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if chk.returncode == 0:
            return ref
    raise RuntimeError(
        "could not resolve base ref (try: git fetch origin main && "
        "pr_commit_policy.py draft --base origin/main)",
    )


def _current_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("git rev-parse --abbrev-ref HEAD failed")
    return result.stdout.strip()


def _cmd_draft(
    repo: Path,
    base_ref: str | None,
    head_ref: str | None,
    title_only: bool,
    body_only: bool,
) -> int:
    """Print a policy-compliant PR title and body for copy-paste or ``gh pr edit``."""
    base = _resolve_base_ref(repo, base_ref)
    head = head_ref or "HEAD"
    branch = _current_branch(repo)
    title = suggest_title_from_branch(branch) or suggest_title_from_git(repo)
    if not title:
        title = "chore: describe this pull request"
    body = draft_pr_body(repo, base, head)
    if title_only and body_only:
        print(title)
        print("\n---\n")
        print(body)
        return 0
    if not title_only and not body_only:
        print("Suggested PR title (GitHub UI or: gh pr edit --title '...'):\n")
        print(title)
        print("\n---\n\nSuggested PR body (paste in GitHub or: gh pr edit --body-file ...):\n")
        print(body)
        return 0
    if title_only:
        print(title)
        return 0
    print(body)
    return 0


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
    """CLI entry: dispatch ``pr`` or ``commits`` subcommands for CI and local use."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("pr", help="validate PR_TITLE and PR_BODY environment variables")

    p_draft = sub.add_parser(
        "draft",
        help="print a conventional PR title and filled template body (local automation)",
    )
    p_draft.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="repository root (default: git top-level of cwd)",
    )
    p_draft.add_argument(
        "--base",
        default=None,
        help="base ref for git log (default: origin/main or main)",
    )
    p_draft.add_argument(
        "--head",
        default=None,
        help="head ref (default: HEAD)",
    )
    p_draft.add_argument(
        "--title-only",
        action="store_true",
        help="print only the suggested title line",
    )
    p_draft.add_argument(
        "--body-only",
        action="store_true",
        help="print only the suggested body",
    )

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
    if args.command == "draft":
        try:
            repo = args.repo.resolve() if args.repo else _git_toplevel()
        except RuntimeError as exc:
            print(f"pr_commit_policy: draft: {exc}", file=sys.stderr)
            return 1
        try:
            return _cmd_draft(
                repo,
                args.base,
                args.head,
                title_only=args.title_only,
                body_only=args.body_only,
            )
        except RuntimeError as exc:
            print(f"pr_commit_policy: draft: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"pr_commit_policy: draft: {exc}", file=sys.stderr)
            return 1
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
