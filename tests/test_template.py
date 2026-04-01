"""Test cases for validating the Copier template."""

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


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Fixture to provide a temporary directory for project generation."""
    return tmp_path / "test_project"


def test_prerequisites() -> None:
    """Test that required tools are available."""
    for package in ["uv", "copier"]:
        result = run_command(["which", package])
        assert result.returncode == 0, f"{package} not found"


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

    # Make a user change
    readme = test_dir / "README.md"
    with readme.open("a") as f:
        f.write("\n# User change\n")

    # Change to project directory and try update
    # Try to update (should skip README.md)
    run_command(["copier", "update", "--defaults", "--trust"], cwd=test_dir, check=False)

    # Check user change is preserved
    updated_content = readme.read_text()
    assert "# User change" in updated_content, "Update overwrote user changes"


def test_copy_from_github(tmp_path: Path) -> None:
    """Test copying template directly from GitHub shortcut."""
    target = tmp_path / "my-new-project"
    cmd = [
        "copier",
        "copy",
        "gh:balajiselvaraj1601/python_project_template",
        str(target),
        "--trust",
        "--defaults",
        "--data",
        "project_name=GitHub Project",
    ]
    run_command(cmd)

    # Verify structure from GitHub copy
    assert (target / "pyproject.toml").exists(), "Missing pyproject.toml from GitHub copy"
    assert (target / "src").is_dir(), "Missing src/ directory from GitHub copy"
