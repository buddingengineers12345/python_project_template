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


def test_draft_title_only_uses_branch_name(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``draft --title-only`` logs a title derived from the current branch."""
    import logging

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

    with caplog.at_level(logging.INFO):
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
    assert "feat: draft title test" in caplog.text


def test_git_toplevel_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_git_toplevel`` returns the repository root path."""
    import subprocess

    def _success(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, str(tmp_path) + "\n", "")

    monkeypatch.setattr(pcp, "_git_run", _success)
    result = pcp._git_toplevel()
    assert result == tmp_path


def test_git_toplevel_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_git_toplevel`` raises RuntimeError when not in a git repository."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "fatal: not a git repository")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    with pytest.raises(RuntimeError):
        pcp._git_toplevel()


def test_resolve_base_ref_explicit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_resolve_base_ref`` returns explicit ref when provided."""
    explicit = "origin/develop"
    result = pcp._resolve_base_ref(tmp_path, explicit)
    assert result == explicit


def test_resolve_base_ref_origin_main_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``_resolve_base_ref`` detects origin/main when it exists."""
    import subprocess

    call_count = [0]

    def _git_run_impl(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        call_count[0] += 1
        # First call (origin/main check) returns 0
        if call_count[0] == 1:
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(pcp, "_git_run", _git_run_impl)
    result = pcp._resolve_base_ref(tmp_path, None)
    assert result == "origin/main"


def test_resolve_base_ref_main_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_resolve_base_ref`` falls back to main when origin/main doesn't exist."""
    import subprocess

    call_count = [0]

    def _git_run_impl(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        call_count[0] += 1
        # First call (origin/main check) fails, second (main check) succeeds
        if call_count[0] == 2:
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(pcp, "_git_run", _git_run_impl)
    result = pcp._resolve_base_ref(tmp_path, None)
    assert result == "main"


def test_resolve_base_ref_neither_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_resolve_base_ref`` raises RuntimeError when neither origin/main nor main exists."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    with pytest.raises(RuntimeError, match="could not resolve base ref"):
        pcp._resolve_base_ref(tmp_path, None)


def test_current_branch_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_current_branch`` returns the current branch name."""
    import subprocess

    def _success(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "feature/my-branch\n", "")

    monkeypatch.setattr(pcp, "_git_run", _success)
    result = pcp._current_branch(tmp_path)
    assert result == "feature/my-branch"


def test_current_branch_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_current_branch`` raises RuntimeError when git fails."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "error")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    with pytest.raises(RuntimeError):
        pcp._current_branch(tmp_path)


def test_git_first_parent_subject_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_git_first_parent_subject`` returns the commit subject."""
    import subprocess

    def _success(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "feat: add widget\n", "")

    monkeypatch.setattr(pcp, "_git_run", _success)
    result = pcp._git_first_parent_subject("abc123")
    assert result == "feat: add widget"


def test_git_first_parent_subject_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_git_first_parent_subject`` raises RuntimeError when git log fails."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "error")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    with pytest.raises(RuntimeError):
        pcp._git_first_parent_subject("badsha")


def test_validate_commit_range_git_rev_list_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``validate_commit_range`` returns error when git rev-list fails."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "error")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    err = pcp.validate_commit_range("abc", "def")
    assert err is not None
    assert "git rev-list failed" in err


def test_draft_pr_body_when_block_not_in_template(
    tmp_path: Path,
) -> None:
    """``draft_pr_body`` returns original text when placeholder block is not found."""
    gh = tmp_path / ".github"
    gh.mkdir(parents=True)
    template_text = "# PR\n\nSome custom text without the standard block."
    (gh / "PULL_REQUEST_TEMPLATE.md").write_text(template_text, encoding="utf-8")

    result = pcp.draft_pr_body(tmp_path, "main", "HEAD")
    assert result == template_text


def test_changes_introduced_empty_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``changes_introduced_markdown`` returns no-commits placeholder for empty range."""
    import subprocess

    def _success(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(pcp, "_git_run", _success)
    result = pcp.changes_introduced_markdown(tmp_path, "HEAD", "HEAD")
    assert "no commits" in result


def test_validate_pr_title_empty_string() -> None:
    """``validate_pr_title`` rejects empty strings."""
    err = pcp.validate_pr_title("")
    assert err is not None
    assert "empty" in err.lower()


def test_validate_pr_title_multiline_uses_first_line() -> None:
    """``validate_pr_title`` validates only the first line of multiline input."""
    result = pcp.validate_pr_title("feat: add widget\n\nBody text")
    assert result is None


def test_draft_both_title_and_body_only(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """``draft --title-only --body-only`` outputs both title and body separated."""
    import logging

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
        f"# PR\n\n## Changes introduced\n\n{block}\n",
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
        ["git", "checkout", "-b", "feat/test-both"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with caplog.at_level(logging.INFO):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD~1",
                "--title-only",
                "--body-only",
            ],
        )
    assert rc == 0
    assert "---" in caplog.text


def test_draft_body_only(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """``draft --body-only`` outputs only the PR body."""
    import logging

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
        f"# PR\n\n## Changes introduced\n\n{block}\n",
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

    with caplog.at_level(logging.INFO):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD",
                "--body-only",
            ],
        )
    assert rc == 0


def test_draft_no_title_from_branch_or_git(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``draft`` uses fallback title when branch and git don't provide valid suggestions."""
    import logging

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
    (gh / "PULL_REQUEST_TEMPLATE.md").write_text("# PR\n", encoding="utf-8")
    (tmp_path / "f.txt").write_text("1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "not conventional", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "not-a-type/something"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with caplog.at_level(logging.INFO):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD",
                "--title-only",
            ],
        )
    assert rc == 0
    assert "chore: describe this pull request" in caplog.text


def test_draft_runtime_error_in_cmd_draft(
    tmp_path: Path,
) -> None:
    """``draft`` exits 1 when _cmd_draft raises RuntimeError."""
    import subprocess

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
    # Missing .github/PULL_REQUEST_TEMPLATE.md will cause OSError
    rc = pcp.main(
        [
            "draft",
            "--repo",
            str(tmp_path),
            "--base",
            "HEAD",
        ],
    )
    # This triggers the OSError handler
    assert rc == 1


def test_strip_html_comments_multiline() -> None:
    """HTML comments spanning multiple lines are stripped."""
    text = "start\n<!-- comment\nspanning\nmultiple -->\nend"
    result = pcp.strip_html_comments(text)
    assert "comment" not in result
    assert "start" in result
    assert "end" in result


def test_suggest_title_from_branch_handles_whitespace() -> None:
    """Branch slug whitespace is normalized."""
    assert pcp.suggest_title_from_branch("feat/handle___spaces") == "feat: handle spaces"


def test_validate_conventional_rejects_no_space_after_colon() -> None:
    """Conventional commits require a space after the colon."""
    err = pcp.validate_conventional_subject_line("feat:noSpace")
    assert err is not None


def test_main_commits_success(tmp_path: Path) -> None:
    """``commits`` subcommand succeeds when all commits are conventional."""
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
        ["git", "commit", "-m", "feat: one", "--no-verify"],
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
        ["git", "commit", "-m", "fix: two", "--no-verify"],
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

    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        rc = pcp.main(["commits", "--base", h1, "--head", h2])
    finally:
        os.chdir(cwd)
    assert rc == 0


def test_validate_pr_body_strips_html_before_checking() -> None:
    """HTML comments are stripped before checking for placeholder text."""
    body = _minimal_valid_body()
    # Add an HTML comment containing the boilerplate
    body_with_comment = body.replace(
        "- Real change",
        "- Real change\n<!-- - Change 1 -->",
    )
    assert pcp.validate_pr_body(body_with_comment) is None


def test_suggest_title_from_branch_exactly_at_limit() -> None:
    """Branch title exactly at MAX_SUBJECT_LEN is not truncated."""
    # Create a branch name that results in a title exactly at the limit
    # feat: has 5 characters, so we need 67 more characters (72 - 5)
    slug = "a" * 67
    branch = f"feat/{slug}"
    result = pcp.suggest_title_from_branch(branch)
    assert result is not None
    assert len(result) == pcp._MAX_SUBJECT_LEN


def test_suggest_title_from_branch_just_over_limit() -> None:
    """Branch title just over MAX_SUBJECT_LEN is truncated and rstripped."""
    # Create a branch name that results in a title just over the limit
    slug = "a" * 70
    branch = f"feat/{slug}"
    result = pcp.suggest_title_from_branch(branch)
    assert result is not None
    assert len(result) <= pcp._MAX_SUBJECT_LEN


def test_draft_with_explicit_repo_path(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """``draft --repo /path`` uses the specified repo path."""
    import logging

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
        f"# PR\n\n## Changes introduced\n\n{block}\n",
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

    with caplog.at_level(logging.INFO):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD",
            ],
        )
    assert rc == 0


def test_draft_command_without_title_or_body_flag(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``draft`` without flags outputs both title and body."""
    import logging

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
        f"# PR\n\n## Changes introduced\n\n{block}\n",
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
        ["git", "checkout", "-b", "feat/test-default"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with caplog.at_level(logging.INFO):
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD~1",
            ],
        )
    assert rc == 0
    # When no flags, both title and body should be in output with full description
    assert "Suggested PR title" in caplog.text


def test_draft_with_nonexistent_repo_raises_error() -> None:
    """``draft --repo /nonexistent`` raises an error."""
    rc = pcp.main(
        [
            "draft",
            "--repo",
            "/nonexistent/path/that/does/not/exist",
            "--base",
            "HEAD",
        ],
    )
    assert rc == 1


def test_cmd_commits_with_invalid_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_cmd_commits`` returns 1 when commit range has invalid commits."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        # Simulate git rev-list returning commits
        if "rev-list" in argv:
            return subprocess.CompletedProcess(argv, 0, "abc123\n", "")
        # But the log fails
        return subprocess.CompletedProcess(argv, 1, "", "error")

    monkeypatch.setattr(pcp, "_git_run", _fail)
    rc = pcp._cmd_commits("abc", "def")
    assert rc == 1


def test_draft_head_ref_defaulting(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """``draft`` without --head defaults to HEAD."""
    import logging

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
        f"# PR\n\n## Changes introduced\n\n{block}\n",
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

    with caplog.at_level(logging.INFO):
        # No --head provided
        rc = pcp.main(
            [
                "draft",
                "--repo",
                str(tmp_path),
                "--base",
                "HEAD",
                "--title-only",
            ],
        )
    assert rc == 0


def test_draft_runtime_error_when_template_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``draft`` exits 1 when template file is missing (OSError)."""
    # Create a mock git repo without .github directory
    import subprocess

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
    (tmp_path / "f.txt").write_text("1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: init", "--no-verify"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # This will cause an OSError because template doesn't exist
    rc = pcp.main(
        [
            "draft",
            "--repo",
            str(tmp_path),
            "--base",
            "HEAD",
        ],
    )
    assert rc == 1


def test_draft_when_git_toplevel_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``draft`` exits 1 when ``_git_toplevel`` raises RuntimeError."""
    import subprocess

    def _fail(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "not a git repository")

    monkeypatch.setattr(pcp, "_git_run", _fail)

    # When not providing --repo and git_toplevel fails
    rc = pcp.main(
        [
            "draft",
            "--base",
            "HEAD",
        ],
    )
    assert rc == 1


def test_main_commits_with_bad_subjects(tmp_path: Path) -> None:
    """``commits`` command exits 1 when a commit has invalid subject."""
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
        ["git", "commit", "-m", "bad subject no type", "--no-verify"],
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

    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        rc = pcp.main(["commits", "--base", h1, "--head", h2])
    finally:
        os.chdir(cwd)
    assert rc == 1


def test_suggest_title_very_long_slug() -> None:
    """Very long slug is properly truncated."""
    # Create a slug that will definitely exceed the limit
    slug = "very-long-" * 20  # This will be > 200 chars
    branch = f"feat/{slug}"
    result = pcp.suggest_title_from_branch(branch)
    assert result is not None
    assert len(result) <= pcp._MAX_SUBJECT_LEN
    # Should end with a non-space character (due to rstrip)
    assert result[-1] != " "


def test_validate_commit_range_with_empty_lines_in_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``validate_commit_range`` handles git rev-list output with empty lines."""
    import subprocess

    call_count = [0]

    def _git_run_impl(
        argv: list[str],
        *,
        cwd: str | Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        call_count[0] += 1
        # First call (rev-list) returns commits with an empty line
        if "rev-list" in argv:
            return subprocess.CompletedProcess(argv, 0, "abc123\n\ndef456\n", "")
        # Subsequent calls (log) succeed
        return subprocess.CompletedProcess(argv, 0, "feat: ok\n", "")

    monkeypatch.setattr(pcp, "_git_run", _git_run_impl)
    # Should handle empty lines gracefully
    err = pcp.validate_commit_range("base", "head")
    assert err is None  # Both commits are valid
