"""Tests for ``scripts/pr_commit_policy`` (PR body, conventional commits, git ranges)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = _REPO_ROOT / "scripts" / "pr_commit_policy.py"
_SPEC = importlib.util.spec_from_file_location("pr_commit_policy", SCRIPT)
assert _SPEC and _SPEC.loader
_pcp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_pcp)
pcp = _pcp


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
    assert (
        pcp.validate_conventional_subject_line("Merge branch 'main' into topic") is None
    )


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
    assert (
        pcp.validate_conventional_subject_line('Revert "feat: broken thing"') is None
    )


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
    rc = subprocess.run(
        [sys.executable, str(SCRIPT), "pr"],
        check=False,
    ).returncode
    assert rc == 0


def test_main_pr_subcommand_bad_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """``pr`` subcommand exits 1 when the title is not conventional."""
    monkeypatch.setenv("PR_TITLE", "not conventional")
    monkeypatch.setenv("PR_BODY", _minimal_valid_body())
    rc = subprocess.run(
        [sys.executable, str(SCRIPT), "pr"],
        check=False,
    ).returncode
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
