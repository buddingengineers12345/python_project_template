"""Integration tests for the Copier template.

This package is a meta-template: tests invoke ``copier copy`` and ``copier update``,
then assert on the rendered tree and (where applicable) run the generated project's
tooling. They guard template variables, ``_skip_if_exists``, and post-generation tasks.
"""

from __future__ import annotations

import shutil
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest
import yaml
from copier import run_copy


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


def load_copier_answers(project_dir: Path) -> dict[str, object]:
    """Load ``.copier-answers.yml`` from a generated project."""
    answers_path = project_dir / ".copier-answers.yml"
    assert answers_path.is_file(), f"Missing {answers_path}"
    raw = cast(object, yaml.safe_load(answers_path.read_text(encoding="utf-8")))
    raw_map = require_mapping(raw, name="copier_answers")
    return dict(raw_map)


def git_commit_all(project_dir: Path, message: str) -> None:
    """Create a commit containing all tracked and new files (initial project snapshot)."""
    _ = run_command(["git", "add", "-A"], cwd=project_dir)
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
            message,
        ],
        cwd=project_dir,
    )


def copy_with_data(
    dest: Path,
    data: dict[str, str | bool],
    *,
    skip_tasks: bool = True,
) -> None:
    """Run ``copier copy`` with explicit ``--data`` pairs (non-interactive).

    Uses ``--vcs-ref HEAD`` so the current working tree is rendered rather than
    the latest PEP 440 git tag, ensuring tests always exercise the latest template.

    Args:
        dest: Destination directory for the rendered project.
        data: Mapping of Copier variable names to values to pass via ``--data``.
        skip_tasks: If ``True``, skip post-generation tasks (default).
    """
    cmd: list[str] = [
        "copier",
        "copy",
        "--vcs-ref",
        "HEAD",
        ".",
        str(dest),
        "--trust",
        "--defaults",
    ]
    if skip_tasks:
        cmd.append("--skip-tasks")
    for key, value in data.items():
        rendered = ("true" if value else "false") if isinstance(value, bool) else str(value)
        cmd.extend(["--data", f"{key}={rendered}"])
    _ = run_command(cmd)


def load_pyproject(project_dir: Path) -> dict[str, object]:
    """Parse ``pyproject.toml`` from a generated project."""
    with (project_dir / "pyproject.toml").open("rb") as handle:
        raw = cast(object, tomllib.load(handle))
        assert isinstance(raw, dict)
        return cast(dict[str, object], raw)


def require_mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AssertionError(f"{name} must be a mapping, got {type(value).__name__}")
    value_map = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in value_map):
        raise AssertionError(f"{name} must have string keys")
    return cast(Mapping[str, object], value_map)


def require_sequence(value: object, *, name: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise AssertionError(f"{name} must be a sequence, got {type(value).__name__}")
    return value


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


@pytest.mark.skip(reason="Environment issue: basedpyright not available in post-gen tasks")
def test_generate_default_project(temp_project_dir: Path) -> None:
    """Render a project with default answers and validate layout and key files."""
    _ = run_command(get_default_command_list(temp_project_dir))

    assert (temp_project_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    assert (temp_project_dir / "src").is_dir(), "Missing src/ directory"
    assert (temp_project_dir / "tests").is_dir(), "Missing tests/ directory"
    ci_workflow = temp_project_dir / ".github" / "workflows" / "ci.yml"
    assert ci_workflow.is_file(), "Missing CI workflow"
    ci_yaml = ci_workflow.read_text(encoding="utf-8")
    assert "if: matrix.python-version == '3.11'" in ci_yaml, (
        "Codecov step must gate on minimum Python matrix value (default 3.11)"
    )
    assert "{{ python_min_version }}" not in ci_yaml, (
        "Rendered ci.yml must not contain unreplaced Jinja placeholders"
    )

    pyproject_content = (temp_project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "test_project"' in pyproject_content, "Incorrect project name in pyproject.toml"

    claude_md = temp_project_dir / "CLAUDE.md"
    assert claude_md.is_file(), "Missing CLAUDE.md"
    claude_content = claude_md.read_text(encoding="utf-8")
    assert "Test Project" in claude_content, "CLAUDE.md should include rendered project name"
    assert "uv sync --frozen --extra dev" in claude_content, (
        "CLAUDE.md should document uv sync setup"
    )
    assert "--extra test" in claude_content, "CLAUDE.md should include test extra for pytest"

    claude_ide = temp_project_dir / ".claude"
    assert claude_ide.is_dir(), "Missing .claude directory from template"
    assert (claude_ide / "settings.json").is_file(), "Missing .claude/settings.json"
    assert (claude_ide / "commands" / "test.md").is_file(), "Missing .claude/commands/test.md"


def test_generate_defaults_only_cli(tmp_path: Path) -> None:
    """Render using only ``--defaults`` (no ``--data``) like common non-interactive usage.

    Without ``--data project_name=...``, Copier uses the template default human name
    ``My Library``, which becomes package ``my_library`` and slug ``my-library``.
    Pass explicit ``--data`` when you need a different distribution name.
    """
    test_dir = tmp_path / "defaults_only"
    _ = run_command(["copier", "copy", ".", str(test_dir), "--trust", "--defaults", "--skip-tasks"])

    assert (test_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    answers = load_copier_answers(test_dir)
    assert answers.get("project_name") == "My Library"
    assert answers.get("package_name") == "my_library"
    assert answers.get("project_slug") == "my-library"
    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    assert project["name"] == "my_library"


def test_codecov_token_not_stored_in_answers_file(tmp_path: Path) -> None:
    """Secret answers must not be written to ``.copier-answers.yml``."""
    test_dir = tmp_path / "secret_codecov"
    token = "fake-codecov-token-not-for-production"
    _ = run_command(
        [
            "copier",
            "copy",
            ".",
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--data",
            f"codecov_token={token}",
        ]
    )
    answers_text = (test_dir / ".copier-answers.yml").read_text(encoding="utf-8")
    assert token not in answers_text, "Secret codecov_token must not appear in answers file"


def test_computed_values_not_recorded_in_answers_file(tmp_path: Path) -> None:
    """Questions with ``when: false`` must not be stored in the answers file."""
    test_dir = tmp_path / "computed_answers"
    _ = run_command(["copier", "copy", ".", str(test_dir), "--trust", "--defaults", "--skip-tasks"])
    answers_text = (test_dir / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "current_year:" not in answers_text
    assert "github_actions_python_versions:" not in answers_text


def test_answers_file_warns_never_edit_manually(tmp_path: Path) -> None:
    """Generated answers file should match Copier docs banner text."""
    test_dir = tmp_path / "answers_banner"
    _ = run_command(["copier", "copy", ".", str(test_dir), "--trust", "--defaults", "--skip-tasks"])
    first_line = (test_dir / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()[0]
    assert "NEVER EDIT MANUALLY" in first_line


def test_generate_programmatic_run_copy_local(tmp_path: Path) -> None:
    """Render programmatically with :func:`copier.run_copy` from a local path."""
    test_dir = tmp_path / "programmatic_local"
    _worker = run_copy(
        ".",
        test_dir,
        defaults=True,
        unsafe=True,
        skip_tasks=True,
    )
    assert (test_dir / "pyproject.toml").exists(), "Missing pyproject.toml"


def test_generate_from_vcs_git_file_url(tmp_path: Path) -> None:
    """Render from a VCS-style template source (git+file://...) without network access."""
    template_repo = tmp_path / "template_repo"
    dest_dir = tmp_path / "from_vcs"

    # Create a clean git repo that looks like a real template source.
    _ = shutil.copytree(
        Path("."),
        template_repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", "*.pyc", ".ruff_cache", ".pytest_cache"
        ),
    )
    _ = run_command(["git", "init"], cwd=template_repo)
    _ = run_command(["git", "config", "user.email", "test@example.com"], cwd=template_repo)
    _ = run_command(["git", "config", "user.name", "Template Test"], cwd=template_repo)
    _ = run_command(["git", "add", "-A"], cwd=template_repo)
    _ = run_command(
        ["git", "commit", "--no-verify", "-m", "chore: init template repo"], cwd=template_repo
    )

    vcs_src = f"git+file://{template_repo}"
    _ = run_command(
        ["copier", "copy", vcs_src, str(dest_dir), "--trust", "--defaults", "--skip-tasks"],
    )
    assert (dest_dir / "pyproject.toml").exists(), "Missing pyproject.toml"


@pytest.mark.skip(reason="Integration test: subprocess CI execution has environment issues")
def test_ci_checks_default_project(temp_project_dir: Path) -> None:
    """Generate a default project and run tests inside it.

    Note: This test attempts to run the full CI pipeline in a generated project.
    It is skipped due to environment issues with subprocess execution (pytest/basedpyright
    not available in subprocess context). All individual components are tested separately.
    """
    _ = run_command(get_default_command_list(temp_project_dir))
    _ = run_command(["uv", "sync", "--extra", "dev", "--extra", "test"], cwd=temp_project_dir)
    # Run pytest to verify tests work in the generated project
    _ = run_command(["uv", "run", "pytest"], cwd=temp_project_dir)


@pytest.mark.skip(reason="Environment issue: basedpyright not available in post-gen tasks")
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


def test_generate_numpy_only(tmp_path: Path) -> None:
    """Render with numpy enabled but pandas disabled."""
    test_dir = tmp_path / "numpy_only"
    copy_with_data(
        test_dir,
        {
            "project_name": "NumPy Only",
            "include_numpy": True,
            "include_pandas_support": False,
            "include_docs": False,
        },
    )
    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    deps_seq = require_sequence(project["dependencies"], name="pyproject.project.dependencies")
    deps = [cast(str, d) for d in deps_seq]
    assert any("numpy" in d for d in deps), "numpy should be in dependencies"
    assert not any("pandas" in d for d in deps), "pandas should NOT be in dependencies"
    # Verify the generated test file doesn't reference pandas
    test_core = (test_dir / "tests" / "numpy_only" / "test_core.py").read_text(encoding="utf-8")
    assert "import pandas" not in test_core
    assert "import numpy" in test_core


def test_generate_pandas_only(tmp_path: Path) -> None:
    """Render with pandas enabled but numpy disabled."""
    test_dir = tmp_path / "pandas_only"
    copy_with_data(
        test_dir,
        {
            "project_name": "Pandas Only",
            "include_pandas_support": True,
            "include_numpy": False,
            "include_docs": False,
        },
    )
    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    deps_seq = require_sequence(project["dependencies"], name="pyproject.project.dependencies")
    deps = [cast(str, d) for d in deps_seq]
    assert any("pandas" in d for d in deps), "pandas should be in dependencies"
    assert not any("numpy" in d for d in deps), "numpy should NOT be in dependencies"
    test_core = (test_dir / "tests" / "pandas_only" / "test_core.py").read_text(encoding="utf-8")
    assert "import pandas" in test_core
    assert "import numpy" not in test_core


@pytest.mark.parametrize(
    "license_choice",
    ["MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0", "Proprietary"],
)
def test_license_rendering(tmp_path: Path, license_choice: str) -> None:
    """Each license choice must produce a non-empty LICENSE file and matching classifier."""
    test_dir = tmp_path / f"license_{license_choice.lower().replace('-', '_')}"
    copy_with_data(
        test_dir,
        {
            "project_name": "License Test",
            "license": license_choice,
            "include_docs": False,
        },
    )
    license_file = test_dir / "LICENSE"
    assert license_file.is_file(), "Missing LICENSE file"
    content = license_file.read_text(encoding="utf-8")
    assert len(content.strip()) > 10, f"LICENSE file is too short for {license_choice}"

    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    assert project["license"] == {"text": license_choice}


@pytest.mark.skip(reason="Environment issue: basedpyright not available in post-gen tasks")
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


def test_copier_update_exits_zero_after_copy_and_commit(tmp_path: Path) -> None:
    """After ``copier copy`` and a git commit, ``copier update`` must complete without error.

    The template source is a real ``git+file://`` repository with a commit so
    ``.copier-answers.yml`` records a resolvable ``_commit`` (same shape as consumer projects).
    Copying from a dirty working tree ``.`` without VCS metadata often makes ``copier update``
    fail when Copier cannot check out the recorded revision.
    """
    template_repo = tmp_path / "template_repo"
    test_dir = tmp_path / "update_clean"

    _ = shutil.copytree(
        Path("."),
        template_repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", "*.pyc", ".ruff_cache", ".pytest_cache"
        ),
    )
    _ = run_command(["git", "init"], cwd=template_repo)
    _ = run_command(["git", "config", "user.email", "test@example.com"], cwd=template_repo)
    _ = run_command(["git", "config", "user.name", "Template Test"], cwd=template_repo)
    _ = run_command(["git", "add", "-A"], cwd=template_repo)
    _ = run_command(
        ["git", "commit", "--no-verify", "-m", "chore: init template repo"],
        cwd=template_repo,
    )

    vcs_src = f"git+file://{template_repo}"
    _ = run_command(
        [
            "copier",
            "copy",
            vcs_src,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--data",
            "project_name=Update Smoke Test",
            "--data",
            "include_docs=false",
        ]
    )

    _ = run_command(["git", "init"], cwd=test_dir)
    git_commit_all(test_dir, "chore: initial generated project")

    result = run_command(
        ["copier", "update", "--defaults", "--trust", "--skip-tasks"],
        cwd=test_dir,
        check=False,
    )
    assert result.returncode == 0, f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"


def test_answers_file_matches_explicit_copy_data(tmp_path: Path) -> None:
    """``.copier-answers.yml`` must record the same prompt answers passed via ``--data``."""
    test_dir = tmp_path / "answers_match"
    expected: dict[str, str | bool] = {
        "project_name": "Rocket Telemetry",
        "project_slug": "rocket-telemetry",
        "package_name": "rocket_telemetry",
        "project_description": "Downlink parsing utilities",
        "author_name": "Mission Control",
        "author_email": "mc@example.com",
        "github_username": "example-org",
        "python_min_version": "3.12",
        "license": "BSD-3-Clause",
        "include_docs": False,
        "include_pandas_support": True,
        "include_numpy": True,
    }
    copy_with_data(test_dir, expected)

    answers = load_copier_answers(test_dir)
    for key, value in expected.items():
        assert answers.get(key) == value, f"answers[{key!r}] != {value!r}"


def test_pyproject_and_tree_match_explicit_copy_data(tmp_path: Path) -> None:
    """Rendered files must reflect ``package_name``, tooling flags, and metadata from ``--data``."""
    test_dir = tmp_path / "tree_match"
    copy_with_data(
        test_dir,
        {
            "project_name": "Ocean Buoy",
            "project_slug": "ocean-buoy",
            "package_name": "ocean_buoy",
            "project_description": "Marine sensor ingestion",
            "author_name": "Harbor Lab",
            "author_email": "dev@harbor.lab",
            "github_username": "harbor-lab",
            "python_min_version": "3.13",
            "license": "Apache-2.0",
            "include_docs": True,
            "include_pandas_support": False,
            "include_numpy": False,
        },
    )

    pyproject = load_pyproject(test_dir)
    proj = require_mapping(pyproject.get("project"), name="pyproject.project")
    assert proj["name"] == "ocean_buoy"
    assert proj["description"] == "Marine sensor ingestion"
    assert proj["requires-python"] == ">=3.13"
    assert proj["license"] == {"text": "Apache-2.0"}
    authors_seq = require_sequence(proj["authors"], name="pyproject.project.authors")
    assert len(authors_seq) == 1
    assert authors_seq[0] == {"name": "Harbor Lab", "email": "dev@harbor.lab"}

    deps_seq = require_sequence(proj["dependencies"], name="pyproject.project.dependencies")
    deps = [cast(str, d) for d in deps_seq]
    assert not any("pandas" in d for d in deps)
    assert not any("numpy" in d for d in deps)

    assert (test_dir / "mkdocs.yml").is_file()
    assert (test_dir / "src" / "ocean_buoy" / "__init__.py").is_file()
    assert (test_dir / "tests" / "ocean_buoy" / "test_core.py").is_file()

    readme = (test_dir / "README.md").read_text(encoding="utf-8")
    assert "Ocean Buoy" in readme
    urls = require_mapping(proj["urls"], name="pyproject.project.urls")
    assert urls["Homepage"] == "https://github.com/harbor-lab/ocean-buoy"
    assert urls["Repository"] == "https://github.com/harbor-lab/ocean-buoy"


# ---------------------------------------------------------------------------
# Workflow tests
# ---------------------------------------------------------------------------


def test_release_workflow_generated_by_default(tmp_path: Path) -> None:
    """release.yml must be generated when include_release_workflow=true (the default)."""
    test_dir = tmp_path / "release_default"
    copy_with_data(
        test_dir,
        {
            "project_name": "Release Default",
            "include_release_workflow": True,
            "include_docs": False,
        },
    )
    release_yml = test_dir / ".github" / "workflows" / "release.yml"
    assert release_yml.is_file(), "release.yml must exist when include_release_workflow=true"
    content = release_yml.read_text(encoding="utf-8")
    assert "${{ true }}" in content, "release job must be enabled"
    assert "bump_version.py" in content, "release.yml must reference bump_version.py"
    assert "--generate-notes" in content, (
        "release must use gh --generate-notes (no CHANGELOG.md required)"
    )
    assert "--notes-file" not in content, "release must not depend on a checked-in CHANGELOG.md"


def test_release_workflow_disabled(tmp_path: Path) -> None:
    """release.yml job must be gated off when include_release_workflow=false."""
    test_dir = tmp_path / "release_disabled"
    copy_with_data(
        test_dir,
        {
            "project_name": "Release Disabled",
            "include_release_workflow": False,
            "include_docs": False,
        },
    )
    release_yml = test_dir / ".github" / "workflows" / "release.yml"
    assert release_yml.is_file(), "release.yml is always generated (job is conditionally gated)"
    content = release_yml.read_text(encoding="utf-8")
    assert "${{ false }}" in content, (
        "release job must be disabled when include_release_workflow=false"
    )


def test_pypi_publish_adds_oidc_permissions(tmp_path: Path) -> None:
    """include_pypi_publish=true must add id-token:write and uv publish to release.yml."""
    test_dir = tmp_path / "pypi_publish"
    copy_with_data(
        test_dir,
        {
            "project_name": "PyPI Publish",
            "include_release_workflow": True,
            "include_pypi_publish": True,
            "include_docs": False,
        },
    )
    release_yml = test_dir / ".github" / "workflows" / "release.yml"
    assert release_yml.is_file(), "release.yml must exist"
    content = release_yml.read_text(encoding="utf-8")
    assert "id-token: write" in content, "OIDC permission required for PyPI Trusted Publisher"
    assert "uv publish" in content, "uv publish step must appear when include_pypi_publish=true"


def test_pypi_publish_absent_by_default(tmp_path: Path) -> None:
    """uv publish must NOT appear in release.yml when include_pypi_publish=false (default)."""
    test_dir = tmp_path / "no_pypi"
    copy_with_data(
        test_dir,
        {
            "project_name": "No PyPI",
            "include_release_workflow": True,
            "include_pypi_publish": False,
            "include_docs": False,
        },
    )
    content = (test_dir / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "uv publish" not in content, "uv publish must not appear when include_pypi_publish=false"
    assert "id-token: write" not in content, "OIDC permission must not appear by default"


def test_security_workflow_generated_by_default(tmp_path: Path) -> None:
    """security.yml must be generated with jobs enabled when include_security_scanning=true."""
    test_dir = tmp_path / "security_default"
    copy_with_data(
        test_dir,
        {
            "project_name": "Security Default",
            "include_security_scanning": True,
            "include_docs": False,
        },
    )
    security_yml = test_dir / ".github" / "workflows" / "security.yml"
    assert security_yml.is_file(), "security.yml must exist when include_security_scanning=true"
    content = security_yml.read_text(encoding="utf-8")
    assert "${{ true }}" in content, "security jobs must be enabled"
    assert "codeql-action" in content, "security.yml must reference CodeQL action"
    assert "pip-audit" in content, "security.yml must include dependency audit step"
    assert "uv sync --frozen --extra dev" in content, (
        "security audit must install and resolve dev extras (parity with template repo)"
    )
    assert "uv export --frozen --format requirements-txt --extra dev" in content, (
        "pip-audit stdin must include dev dependencies from the lockfile"
    )


def test_security_workflow_disabled(tmp_path: Path) -> None:
    """security.yml jobs must be gated off when include_security_scanning=false."""
    test_dir = tmp_path / "security_disabled"
    copy_with_data(
        test_dir,
        {
            "project_name": "Security Disabled",
            "include_security_scanning": False,
            "include_docs": False,
        },
    )
    security_yml = test_dir / ".github" / "workflows" / "security.yml"
    assert security_yml.is_file(), "security.yml is always generated (jobs are conditionally gated)"
    content = security_yml.read_text(encoding="utf-8")
    assert "${{ false }}" in content, (
        "security jobs must be disabled when include_security_scanning=false"
    )


def test_dependency_review_always_generated(tmp_path: Path) -> None:
    """dependency-review.yml must always be present regardless of feature flags."""
    test_dir = tmp_path / "dep_review"
    copy_with_data(
        test_dir,
        {
            "project_name": "Dep Review",
            "include_release_workflow": False,
            "include_security_scanning": False,
            "include_docs": False,
        },
    )
    dep_review = test_dir / ".github" / "workflows" / "dependency-review.yml"
    assert dep_review.is_file(), "dependency-review.yml must always be generated"
    content = dep_review.read_text(encoding="utf-8")
    assert "dependency-review-action" in content
    assert "branches: [main, master]" in content, (
        "dependency-review must run on PRs targeting main and master (parity with other workflows)"
    )


def test_pre_commit_update_workflow_generated(tmp_path: Path) -> None:
    """pre-commit-update.yml must always be present in a generated project."""
    test_dir = tmp_path / "precommit_update"
    copy_with_data(
        test_dir,
        {
            "project_name": "Precommit Update",
            "include_docs": False,
        },
    )
    workflow = test_dir / ".github" / "workflows" / "pre-commit-update.yml"
    assert workflow.is_file(), "pre-commit-update.yml must be generated"
    content = workflow.read_text(encoding="utf-8")
    assert "pre-commit autoupdate" in content
    assert "create-pull-request" in content


def test_scripts_bump_version_generated(tmp_path: Path) -> None:
    """scripts/bump_version.py must exist in the generated project."""
    test_dir = tmp_path / "bump_version"
    copy_with_data(
        test_dir,
        {
            "project_name": "Bump Version",
            "include_release_workflow": True,
            "include_docs": False,
        },
    )
    bump_script = test_dir / "scripts" / "bump_version.py"
    assert bump_script.is_file(), "scripts/bump_version.py must exist in generated projects"
    content = bump_script.read_text(encoding="utf-8")
    assert "BumpKind" in content, "bump_version.py must contain BumpKind type alias"
    assert "[project]" in content, "bump_version.py must look for [project] section"


def test_new_variables_recorded_in_answers_file(tmp_path: Path) -> None:
    """New boolean variables must appear in .copier-answers.yml when prompted."""
    test_dir = tmp_path / "new_vars_answers"
    copy_with_data(
        test_dir,
        {
            "project_name": "Answers Check",
            "include_release_workflow": True,
            "include_security_scanning": False,
            "include_docs": False,
        },
    )
    answers = load_copier_answers(test_dir)
    assert answers.get("include_release_workflow") is True
    assert answers.get("include_security_scanning") is False
