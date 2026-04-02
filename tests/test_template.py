"""Integration tests for the Copier template.

This package is a meta-template: tests invoke ``copier copy`` and ``copier update``,
then assert on the rendered tree and (where applicable) run the generated project's
tooling. They guard template variables, ``_skip_if_exists``, and post-generation tasks.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture stdout/stderr as text.

    Args:
        cmd: Argument list passed to :func:`subprocess.run` (executable first).
        cwd: Working directory for the child process. ``None`` uses the current
            process directory.
        check: If ``True``, raise :class:`subprocess.CalledProcessError` on non-zero exit.

    Returns:
        The completed process result with ``stdout`` and ``stderr`` populated when
        capture is enabled.

    Raises:
        subprocess.CalledProcessError: When ``check`` is ``True`` and the command exits
            with a non-zero status.
        FileNotFoundError: When the executable (first element of ``cmd``) is missing.
    """
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def get_default_command_list(test_dir: Path) -> list[str]:
    """Build the Copier CLI invocation used by most tests.

    Args:
        test_dir: Destination directory for the rendered project.

    Returns:
        A list suitable as the first argument to :func:`run_command`, including
        ``--trust`` and ``--defaults`` for non-interactive runs.
    """
    return [
        "copier",
        "copy",
        ".",
        str(test_dir),
        "--data",
        "project_name=Test Project",
        "--trust",
        "--defaults",
    ]


def test_skip_if_exists_preserves_readme_on_update() -> None:
    """Ensure critical paths remain under ``_skip_if_exists`` in ``copier.yml``.

    Copier must not overwrite user-edited files such as ``README.md`` or
    ``CLAUDE.md`` when the user runs ``copier update``.
    """
    copier_yaml = Path(__file__).resolve().parent.parent / "copier.yml"
    text = copier_yaml.read_text(encoding="utf-8")
    assert "README.md" in text
    assert "CLAUDE.md" in text
    assert "_skip_if_exists:" in text


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Return a dedicated subdirectory under pytest's ``tmp_path`` for one test.

    Args:
        tmp_path: Pytest fixture providing a per-test temporary directory.

    Returns:
        Path to ``tmp_path / "test_project"``.
    """
    return tmp_path / "test_project"


def test_prerequisites() -> None:
    """Assert host tooling required by the test suite is on ``PATH``."""
    for exe in ("uv", "copier"):
        assert shutil.which(exe) is not None, f"{exe} not found on PATH"


def test_generate_default_project(temp_project_dir: Path) -> None:
    """Render a project with default answers and validate layout and key files."""
    _ = run_command(get_default_command_list(temp_project_dir))

    assert (temp_project_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    assert (temp_project_dir / "src").is_dir(), "Missing src/ directory"
    assert (temp_project_dir / "tests").is_dir(), "Missing tests/ directory"
    assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists(), "Missing CI workflow"

    pyproject_content = (temp_project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "test_project"' in pyproject_content, "Incorrect project name in pyproject.toml"

    claude_md = temp_project_dir / "CLAUDE.md"
    assert claude_md.is_file(), "Missing CLAUDE.md"
    claude_content = claude_md.read_text(encoding="utf-8")
    assert "Test Project" in claude_content, "CLAUDE.md should include rendered project name"
    assert "uv sync --frozen --extra dev" in claude_content, (
        "CLAUDE.md should document uv sync setup"
    )


def test_ci_checks_default_project(temp_project_dir: Path) -> None:
    """Generate a default project and run sync, type-check, and tests inside it."""
    _ = run_command(get_default_command_list(temp_project_dir))

    _ = run_command(["uv", "sync", "--extra", "dev", "--extra", "test"], cwd=temp_project_dir)

    _ = run_command(["uv", "run", "basedpyright"], cwd=temp_project_dir)

    _ = run_command(["uv", "run", "pytest"], cwd=temp_project_dir)


def test_generate_full_featured_project(tmp_path: Path) -> None:
    """Render with optional features enabled and assert docs, CLAUDE, and pandas wiring."""
    test_dir = tmp_path / "test_full"

    _ = run_command(
        [
            "copier",
            "copy",
            ".",
            str(test_dir),
            "--trust",
            "--defaults",
            "--data",
            "project_name=Full Test Project",
            "--data",
            "include_pandas_support=true",
            "--data",
            "include_docs=true",
            "--data",
            "include_numpy=true",
            "--data",
            "codecov_token=",
        ]
    )

    assert (test_dir / "mkdocs.yml").exists(), "Missing mkdocs.yml for docs"

    justfile_content = (test_dir / "justfile").read_text(encoding="utf-8")
    assert "docs:" in justfile_content, "just docs recipe expected when include_docs"
    claude_full = (test_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "--extra docs" in claude_full, "CLAUDE.md should include docs extra when docs enabled"
    assert "just docs" in claude_full, "CLAUDE.md should reference just docs when docs enabled"

    pyproject_content = (test_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "pandas" in pyproject_content, "pandas not in dependencies"


def test_update_workflow(tmp_path: Path) -> None:
    """Confirm ``copier update`` keeps user edits to ``README.md`` when it is skipped."""
    test_dir = tmp_path / "test_update"

    _ = run_command(get_default_command_list(test_dir))

    _ = run_command(["git", "add", "-A"], cwd=test_dir)
    _ = run_command(
        [
            "git",
            "-c",
            "user.name=Template Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--no-verify",
            "-m",
            "chore: initial generated project",
        ],
        cwd=test_dir,
    )

    readme = test_dir / "README.md"
    with readme.open("a", encoding="utf-8") as handle:
        _ = handle.write("\n# User change\n")

    _ = run_command(["git", "add", "README.md"], cwd=test_dir)
    _ = run_command(
        [
            "git",
            "-c",
            "user.name=Template Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--no-verify",
            "-m",
            "chore: user readme edit",
        ],
        cwd=test_dir,
    )

    result = run_command(["copier", "update", "--defaults", "--trust"], cwd=test_dir, check=False)
    if result.returncode != 0 and (
        "pathspec" in result.stderr or "did not match any file" in result.stderr
    ):
        pytest.skip(
            "Copier could not check out the template commit in its temp clone "
            + "(e.g. git partial clone); README preservation was not exercised."
        )
    assert result.returncode == 0, result.stderr

    updated_content = readme.read_text(encoding="utf-8")
    assert "# User change" in updated_content, "Update overwrote user changes"
