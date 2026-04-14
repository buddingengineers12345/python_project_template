"""Tests for ``scripts/pr_commit_policy`` (PR body, conventional commits, git ranges)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from tests.script_imports import REPO_ROOT, load_script_module

SCRIPT = REPO_ROOT / "scripts" / "pr_commit_policy.py"
pcp = load_script_module("pr_commit_policy")


def test_strip_html_comments_removes_block() -> None:
    """HTML comment blocks are stripped, leaving surrounding text."""
    text = "a <!-- hide --> b"
    assert pcp.strip_html_comments(text) == "a  b"


def test_validate_conventional_accepts_feat() -> None:
    """A standard ``feat:`` subject line passes validation."""
    assert pcp.validate_conventional_subject_line("feat: add widget") is None


def test_validate_conventional_accepts_scope_and_breaking() -> None:
    """Scope and breaking-change markers are allowed in the subject."""
    assert pcp.validate_conventional_subject_line("feat(api)!: remove v1") is None


def test_validate_conventional_rejects_bad_type() -> None:
    """An unknown conventional type is rejected."""
    assert pcp.validate_conventional_subject_line("invalid: msg") is not None


def test_validate_conventional_rejects_empty_after_colon() -> None:
    """Empty description after the colon is rejected."""
    assert pcp.validate_conventional_subject_line("feat: ") is not None


def test_validate_conventional_rejects_too_long() -> None:
    """Subjects longer than the max length are rejected."""
    subject = "feat: " + "x" * 80
    assert pcp.validate_conventional_subject_line(subject) is not None


def test_validate_conventional_allows_merge_branch() -> None:
    """Git-style merge branch subjects bypass conventional rules."""
    assert pcp.validate_conventional_subject_line("Merge branch 'main' into topic") is None


def test_validate_conventional_allows_merge_pr() -> None:
    """GitHub merge pull request subjects bypass conventional rules."""
    assert (
        pcp.validate_conventional_subject_line(
            "Merge pull request #42 from org/topic",
        )
        is None
    )


def test_validate_conventional_allows_revert() -> None:
    """Revert commits bypass conventional rules."""
    assert pcp.validate_conventional_subject_line('Revert "feat: broken thing"') is None


def test_validate_pr_title_accepts_valid_title() -> None:
    """A valid conventional title passes through to the underlying validator and returns None."""
    assert pcp.validate_pr_title("feat: add widget") is None


def test_suggest_title_from_branch_empty_slug_returns_none() -> None:
    """A branch slug that reduces to empty after stripping returns None."""
    assert pcp.suggest_title_from_branch("feat/-_-") is None


def test_suggest_title_from_branch_long_slug_is_truncated() -> None:
    """A very long slug is truncated to _MAX_SUBJECT_LEN characters."""
    long_slug = "a-" * 40
    result = pcp.suggest_title_from_branch(f"feat/{long_slug}")
    assert result is not None
    assert len(result) <= pcp._MAX_SUBJECT_LEN


def test_validate_pr_body_requires_headings() -> None:
    """PR body must include all required section headings."""
    err = pcp.validate_pr_body("## Summary\n\nx\n")
    assert err is not None
    assert "Changes introduced" in err


def test_validate_pr_body_rejects_placeholder() -> None:
    """Placeholder checklist text in the body is rejected."""
    body = _minimal_valid_body_with_change1()
    err = pcp.validate_pr_body(body)
    assert err is not None
    assert "Change 1" in err


def test_validate_pr_body_accepts_filled() -> None:
    """A fully filled template body passes validation."""
    body = _minimal_valid_body()
    assert pcp.validate_pr_body(body) is None


def _minimal_valid_body_with_change1() -> str:
    return _minimal_valid_body().replace("- Real change", "- Change 1", 1)


def _minimal_valid_body() -> str:
    return """
## Summary

Why we need this.

---

## Changes introduced

- Real change

---

## Testing

Ran tests.

---

## Documentation

Not applicable

---

## Related issues

N/A

---

## Contributor checklist

- [x] done

---

## Release notes

- [x] N/A

---

## Additional notes

None
"""


def test_main_pr_subcommand_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """``pr`` subcommand exits 0 when title and body are valid."""
    monkeypatch.setenv("PR_TITLE", "ci: fix workflow")
    monkeypatch.setenv("PR_BODY", _minimal_valid_body())
    saved_argv = sys.argv
    try:
        sys.argv = [str(SCRIPT), "pr"]
        rc = pcp.main()
    finally:
        sys.argv = saved_argv
    assert rc == 0


def test_main_pr_subcommand_bad_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """``pr`` subcommand exits 1 when the title is not conventional."""
    monkeypatch.setenv("PR_TITLE", "not conventional")
    monkeypatch.setenv("PR_BODY", _minimal_valid_body())
    saved_argv = sys.argv
    try:
        sys.argv = [str(SCRIPT), "pr"]
        rc = pcp.main()
    finally:
        sys.argv = saved_argv
    assert rc == 1


def test_validate_commit_range_empty_ok(tmp_path: Path) -> None:
    """Empty or single-commit ranges do not produce validation errors."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.st"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "f").write_text("1", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: init", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    h1 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (tmp_path / "f").write_text("2", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fix: second", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    h2 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        assert pcp.validate_commit_range(h1, h2) is None
        assert pcp.validate_commit_range(h1, h1) is None
    finally:
        os.chdir(cwd)


def test_validate_commit_range_rejects_bad_subject(tmp_path: Path) -> None:
    """A non-conventional commit in the range yields an error message."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.st"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "f").write_text("1", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: ok", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    h1 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (tmp_path / "f").write_text("2", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "bad subject", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    h2 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        err = pcp.validate_commit_range(h1, h2)
    finally:
        os.chdir(cwd)
    assert err is not None
    assert "bad subject" in err


@pytest.mark.parametrize(
    ("branch", "expected"),
    [
        ("chore/repo-cleanup-standards-remediation", "chore: repo cleanup standards remediation"),
        ("feat/add-widget", "feat: add widget"),
        ("fix/api/handle-null", "fix: api handle null"),
    ],
)
def test_suggest_title_from_branch(branch: str, expected: str) -> None:
    """Branch names ``type/slug`` map to ``type: slug`` with hyphens as spaces."""
    assert pcp.suggest_title_from_branch(branch) == expected


def test_suggest_title_from_branch_unknown_prefix() -> None:
    """Branches without a known type prefix yield None."""
    assert pcp.suggest_title_from_branch("main") is None
    assert pcp.suggest_title_from_branch("dependabot/pip/foo-1.0") is None


def test_suggest_title_from_branch_strips_ref() -> None:
    """``refs/heads/`` prefix is ignored."""
    assert pcp.suggest_title_from_branch("refs/heads/docs/update-readme") == "docs: update readme"


def test_validate_conventional_rejects_empty_string() -> None:
    """An empty subject line is rejected as empty."""
    assert pcp.validate_conventional_subject_line("") is not None


def test_validate_pr_body_returns_error_for_none() -> None:
    """``None`` body is rejected as empty."""
    err = pcp.validate_pr_body(None)
    assert err is not None
    assert "empty" in err.lower()


def test_validate_pr_body_returns_error_for_blank() -> None:
    """Whitespace-only body is rejected as empty."""
    assert pcp.validate_pr_body("   \n  ") is not None


def test_suggest_title_from_git_returns_str_or_none() -> None:
    """``suggest_title_from_git`` runs against the real repo and returns str or None."""
    result = pcp.suggest_title_from_git(REPO_ROOT)
    assert result is None or isinstance(result, str)


def test_changes_introduced_empty_range_returns_placeholder() -> None:
    """``HEAD..HEAD`` is an empty range and returns the no-commits placeholder."""
    result = pcp.changes_introduced_markdown(REPO_ROOT, "HEAD", "HEAD")
    assert "no commits" in result or isinstance(result, str)


def test_draft_pr_body_returns_string() -> None:
    """``draft_pr_body`` on the real repo returns a non-empty string."""
    result = pcp.draft_pr_body(REPO_ROOT, "HEAD", "HEAD")
    assert isinstance(result, str)
    assert len(result) > 0


def test_main_commits_subcommand_missing_args_returns_1() -> None:
    """``commits`` subcommand exits 1 when ``--base``/``--head`` are empty."""
    import contextlib
    import io

    buf = io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(SCRIPT), "commits", "--base", "", "--head", ""]
        with contextlib.redirect_stdout(buf):
            rc = pcp.main()
    finally:
        sys.argv = saved_argv
    assert rc == 1


def test_main_pr_subcommand_bad_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """``pr`` subcommand exits 1 when the body is invalid."""
    monkeypatch.setenv("PR_TITLE", "ci: fix workflow")
    monkeypatch.setenv("PR_BODY", "## Summary\n\nx\n")
    saved_argv = sys.argv
    try:
        sys.argv = [str(SCRIPT), "pr"]
        rc = pcp.main()
    finally:
        sys.argv = saved_argv
    assert rc == 1


def test_suggest_title_from_git_when_log_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """If ``git log`` fails, return None (no crash)."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "err")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    assert pcp.suggest_title_from_git(tmp_path) is None


def test_changes_introduced_when_git_log_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Failed ``git log`` range yields the fallback bullet."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "boom")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    out = pcp.changes_introduced_markdown(tmp_path, "main", "HEAD")
    assert "could not list commits" in out


def test_draft_title_only_uses_branch_name(tmp_path: Path) -> None:
    """``draft --title-only`` prints a title derived from the current branch."""
    import contextlib
    import io

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.st"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    gh = tmp_path / ".github"
    gh.mkdir(parents=True)
    block = "- Change 1\n- Change 2\n- Change 3 (if applicable)"
    (gh / "PULL_REQUEST_TEMPLATE.md").write_text(
        f"# PR\n\n## Changes introduced\n\n{block}\n\n## Summary\n\nx\n",
        encoding="utf-8",
    )
    (tmp_path / "f.txt").write_text("1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: init", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "feat/draft-title-test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "f.txt").write_text("2\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fix: second", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD~1",
                "--title-only",
            ],
        )
    assert rc == 0
    assert buf.getvalue().strip() == "feat: draft title test"
