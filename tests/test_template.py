"""Test cases for validating the Copier template."""

import shutil
import subprocess
from pathlib import Path

import pytest


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def get_default_command_list(test_dir: Path) -> list[str]:
    """Get the default command list for running copier."""
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
    """Regression guard: README must stay in _skip_if_exists so copier update skips it."""
    copier_yaml = Path(__file__).resolve().parent.parent / "copier.yml"
    text = copier_yaml.read_text()
    assert "README.md" in text
    assert "_skip_if_exists:" in text


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Fixture to provide a temporary directory for project generation."""
    return tmp_path / "test_project"


def test_prerequisites() -> None:
    """Test that required tools are available."""
    for exe in ("uv", "copier"):
        assert shutil.which(exe) is not None, f"{exe} not found on PATH"


def test_generate_default_project(temp_project_dir: Path) -> None:
    """Test generating a project with default configuration."""
    # Generate project
    run_command(get_default_command_list(temp_project_dir))

    # Verify structure
    assert (temp_project_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    assert (temp_project_dir / "src").is_dir(), "Missing src/ directory"
    assert (temp_project_dir / "tests").is_dir(), "Missing tests/ directory"
    assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists(), "Missing CI workflow"

    # Check pyproject.toml content
    pyproject_content = (temp_project_dir / "pyproject.toml").read_text()
    assert 'name = "test_project"' in pyproject_content, "Incorrect project name in pyproject.toml"


def test_ci_checks_default_project(temp_project_dir: Path) -> None:
    """Test running CI checks on default generated project."""
    # Generate project
    run_command(get_default_command_list(temp_project_dir))

    # Sync dependencies
    run_command(["uv", "sync", "--extra", "dev", "--extra", "test"], cwd=temp_project_dir)

    # Type check
    run_command(["uv", "run", "basedpyright"], cwd=temp_project_dir)

    # Run tests
    run_command(["uv", "run", "pytest"], cwd=temp_project_dir)


def test_generate_full_featured_project(tmp_path: Path) -> None:
    """Test generating a project with all features enabled."""
    test_dir = tmp_path / "test_full"

    # Generate project with all features
    run_command(
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

    # Verify full features
    assert (test_dir / "mkdocs.yml").exists(), "Missing mkdocs.yml for docs"

    # Check pandas in dependencies
    pyproject_content = (test_dir / "pyproject.toml").read_text()
    assert "pandas" in pyproject_content, "pandas not in dependencies"


def test_update_workflow(tmp_path: Path) -> None:
    """Test that update workflow preserves user changes."""
    test_dir = tmp_path / "test_update"

    # Generate project
    run_command(get_default_command_list(test_dir))

    # Post-copy tasks may modify files (e.g. ruff); commit a clean baseline for copier update.
    run_command(["git", "add", "-A"], cwd=test_dir)
    run_command(
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

    # Make a user change
    readme = test_dir / "README.md"
    with readme.open("a") as f:
        f.write("\n# User change\n")

    # Copier refuses to update a dirty working tree; commit the local edit first.
    run_command(["git", "add", "README.md"], cwd=test_dir)
    run_command(
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

    # Update should skip README.md (see _skip_if_exists in copier.yml).
    result = run_command(["copier", "update", "--defaults", "--trust"], cwd=test_dir, check=False)
    if result.returncode != 0 and (
        "pathspec" in result.stderr or "did not match any file" in result.stderr
    ):
        pytest.skip(
            "Copier could not check out the template commit in its temp clone "
            "(e.g. git partial clone); README preservation was not exercised."
        )
    assert result.returncode == 0, result.stderr

    # Check user change is preserved
    updated_content = readme.read_text()
    assert "# User change" in updated_content, "Update overwrote user changes"
