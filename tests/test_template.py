"""Integration tests for the Copier template.

This package is a meta-template: tests invoke ``copier copy`` and ``copier update``,
then assert on the rendered tree and (where applicable) run the generated project's
tooling. They guard template variables, ``_skip_if_exists``, and post-generation tasks.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest
import yaml
from copier import run_copy

TEMPLATE_GIT_SRC = f"git+{Path('.').resolve().as_uri()}"


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
        "--vcs-ref",
        "HEAD",
        TEMPLATE_GIT_SRC,
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


def _prune_docs_when_disabled(dest: Path, data: dict[str, str | bool]) -> None:
    """Remove MkDocs output when ``include_docs`` is false (mirrors post-gen tasks)."""
    if data.get("include_docs", True):
        return
    mk = dest / "mkdocs.yml"
    if mk.is_file():
        mk.unlink()
    docs_dir = dest / "docs"
    if not docs_dir.is_dir():
        return
    for name in ("index.md", "ci.md"):
        path = docs_dir / name
        if path.is_file():
            path.unlink()
    with contextlib.suppress(OSError):
        docs_dir.rmdir()


def _remove_empty_optional_artifacts(dest: Path, data: dict[str, str | bool]) -> None:
    """Delete zero-byte optional files left when ``--skip-tasks`` skips post-gen ``rm`` tasks."""
    pkg = data.get("package_name")
    if not isinstance(pkg, str):
        return
    # Optional artifacts are now conditionally named in the template, so Copier won't
    # emit empty files for disabled features. Keep this hook as a no-op for now
    # (it remains useful if we add any future optional whole-file templates).


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
        TEMPLATE_GIT_SRC,
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
    if skip_tasks:
        _remove_empty_optional_artifacts(dest, data)
        _prune_docs_when_disabled(dest, data)


def copy_with_data_from_worktree(
    dest: Path,
    data: dict[str, str | bool],
    *,
    skip_tasks: bool = True,
) -> None:
    """Run ``copier copy`` from the local worktree (includes uncommitted template edits).

    This complements :func:`copy_with_data`, which intentionally renders from ``--vcs-ref HEAD``.
    Use this helper for regression tests that should fail immediately during local development
    before a commit is created.
    """
    template_root = Path(__file__).resolve().parent.parent
    cmd: list[str] = [
        "copier",
        "copy",
        "--vcs-ref",
        "HEAD",
        str(template_root),
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
    if skip_tasks:
        _remove_empty_optional_artifacts(dest, data)
        _prune_docs_when_disabled(dest, data)


def load_pyproject(project_dir: Path) -> dict[str, object]:
    """Parse ``pyproject.toml`` from a generated project."""
    with (project_dir / "pyproject.toml").open("rb") as handle:
        raw = cast(object, tomllib.load(handle))
        assert isinstance(raw, dict)
        return cast(dict[str, object], raw)


def require_mapping(value: object, *, name: str) -> Mapping[str, object]:
    """Assert ``value`` is a mapping with string keys; return it typed for callers."""
    if not isinstance(value, Mapping):
        raise AssertionError(f"{name} must be a mapping, got {type(value).__name__}")
    value_map = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in value_map):
        raise AssertionError(f"{name} must have string keys")
    return cast(Mapping[str, object], value_map)


def require_sequence(value: object, *, name: str) -> Sequence[object]:
    """Assert ``value`` is a non-string sequence; return it for further parsing."""
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
    assert "CONTRIBUTING.md" in text
    assert "SECURITY.md" in text
    assert "CLAUDE.md" in text
    assert "env.example" in text
    assert "_skip_if_exists:" in text
    assert '"*.md"' not in text
    assert "codecov_token:" not in text


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
    assert (claude_ide / "commands" / "tdd-red.md").is_file(), "Missing .claude/commands/tdd-red.md"
    assert (claude_ide / "commands" / "tdd-green.md").is_file(), (
        "Missing .claude/commands/tdd-green.md"
    )
    assert (claude_ide / "commands" / "ci-fix.md").is_file(), "Missing .claude/commands/ci-fix.md"
    assert (claude_ide / "hooks" / "pre-write-src-require-test.sh").is_file(), (
        "Missing .claude/hooks/pre-write-src-require-test.sh"
    )
    assert (claude_ide / "hooks" / "pre-bash-coverage-gate.sh").is_file(), (
        "Missing .claude/hooks/pre-bash-coverage-gate.sh"
    )
    assert (claude_ide / "hooks" / "post-edit-refactor-test-guard.sh").is_file(), (
        "Missing .claude/hooks/post-edit-refactor-test-guard.sh"
    )
    assert (claude_ide / "skills" / "tdd-workflow" / "SKILL.md").is_file(), (
        "Missing .claude/skills/tdd-workflow/SKILL.md"
    )
    assert (claude_ide / "skills" / "tdd-test-planner" / "SKILL.md").is_file(), (
        "Missing .claude/skills/tdd-test-planner/SKILL.md"
    )
    assert (claude_ide / "skills" / "test-quality-reviewer" / "SKILL.md").is_file(), (
        "Missing .claude/skills/test-quality-reviewer/SKILL.md"
    )


def test_generate_defaults_only_cli(tmp_path: Path) -> None:
    """Render using only ``--defaults`` (no ``--data``) like common non-interactive usage.

    Without ``--data project_name=...``, Copier uses the template default human name
    ``My Library``, which becomes package ``my_library`` and slug ``my-library``.
    Pass explicit ``--data`` when you need a different distribution name.
    """
    test_dir = tmp_path / "defaults_only"
    _ = run_command(
        [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            TEMPLATE_GIT_SRC,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
        ]
    )
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "my_library",
            "include_cli": False,
            "include_git_cliff": True,
        },
    )

    assert (test_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    assert (test_dir / "cliff.toml").is_file(), (
        "cliff.toml expected when include_git_cliff defaults to true"
    )
    answers = load_copier_answers(test_dir)
    assert answers.get("project_name") == "My Library"
    assert answers.get("package_name") == "my_library"
    assert answers.get("project_slug") == "my-library"
    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    assert project["name"] == "my_library"


def test_copier_yaml_has_no_codecov_token_prompt() -> None:
    """Codecov must be documented for CI secrets only — no Copier prompt for tokens."""
    copier_yaml = Path(__file__).resolve().parent.parent / "copier.yml"
    text = copier_yaml.read_text(encoding="utf-8")
    assert "codecov_token:" not in text


def test_package_name_validator_rejects_leading_digit(tmp_path: Path) -> None:
    """Digit-leading ``package_name`` values must fail Copier validation."""
    test_dir = tmp_path / "bad_pkg"
    proc = run_command(
        [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            TEMPLATE_GIT_SRC,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--data",
            "package_name=1bad",
        ],
        check=False,
    )
    assert proc.returncode != 0, "copier should reject package_name starting with a digit"


def test_computed_values_not_recorded_in_answers_file(tmp_path: Path) -> None:
    """Questions with ``when: false`` must not be stored in the answers file."""
    test_dir = tmp_path / "computed_answers"
    _ = run_command(
        [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            TEMPLATE_GIT_SRC,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
        ]
    )
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "my_library",
            "include_cli": False,
            "include_git_cliff": False,
        },
    )
    answers_text = (test_dir / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "current_year:" not in answers_text
    assert "github_actions_python_versions:" not in answers_text


def test_answers_file_warns_never_edit_manually(tmp_path: Path) -> None:
    """Generated answers file should match Copier docs banner text."""
    test_dir = tmp_path / "answers_banner"
    _ = run_command(
        [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            TEMPLATE_GIT_SRC,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
        ]
    )
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "my_library",
            "include_cli": False,
            "include_git_cliff": True,
        },
    )
    first_line = (test_dir / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()[0]
    assert "NEVER EDIT MANUALLY" in first_line


def test_generate_programmatic_run_copy_local(tmp_path: Path) -> None:
    """Render programmatically with :func:`copier.run_copy` from a local path."""
    test_dir = tmp_path / "programmatic_local"
    # Use a VCS-style local source to avoid git hardlink issues that can occur with
    # local clones in some container/filesystem setups.
    _worker = run_copy(
        TEMPLATE_GIT_SRC,
        test_dir,
        defaults=True,
        unsafe=True,
        skip_tasks=True,
    )
    assert (test_dir / "pyproject.toml").exists(), "Missing pyproject.toml"
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "my_library",
            "include_cli": False,
            "include_git_cliff": False,
        },
    )


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
            ".git",
            ".venv",
            "__pycache__",
            "*.pyc",
            ".ruff_cache",
            ".pytest_cache",
            "files.zip",
            "temp",
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
        [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            vcs_src,
            str(dest_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
        ],
    )
    _remove_empty_optional_artifacts(
        dest_dir,
        {
            "package_name": "my_library",
            "include_cli": False,
            "include_git_cliff": True,
        },
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
        ]
    )

    assert (test_dir / "mkdocs.yml").exists(), "Missing mkdocs.yml for docs"

    justfile_content = (test_dir / "justfile").read_text(encoding="utf-8")
    assert "docs-serve:" in justfile_content, "just docs-serve expected when include_docs"
    claude_full = (test_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "--extra docs" in claude_full, "CLAUDE.md should include docs extra when docs enabled"
    assert "docs-serve" in claude_full, "CLAUDE.md should reference docs-serve when docs enabled"

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


def test_env_example_rendered(tmp_path: Path) -> None:
    """Verify that env.example is rendered in the generated project.

    The `env.example` file should be copied to projects so contributors
    can see what environment variables are needed. It's named env.example
    (not .env.example) because Copier excludes .env* files as a safety feature.

    Uses :func:`copy_with_data_from_worktree` so the latest ``template/env.example.jinja``
    is exercised (``copy_with_data`` renders from the last git commit only).
    """
    test_dir = tmp_path / "test_env_example"
    copy_with_data_from_worktree(
        test_dir,
        {
            "project_name": "Env Example Test",
            "include_docs": False,
        },
    )
    env_example = test_dir / "env.example"
    assert env_example.is_file(), "Missing env.example file"
    content = env_example.read_text(encoding="utf-8")
    # Verify file has meaningful content
    assert len(content.strip()) > 0, "env.example file is empty"
    # Logging manager contract (template/src/.../common/logging_manager.py.jinja)
    assert "EXECUTION_CONTEXT" in content
    assert "HUMAN_LOG_LEVEL" in content
    assert "LLM_LOG_LEVEL" in content
    assert "ANTHROPIC_API_KEY" in content
    assert "HUMAN_DEV" in content


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
            ".git",
            ".venv",
            "__pycache__",
            "*.pyc",
            ".ruff_cache",
            ".pytest_cache",
            "files.zip",
            "temp",
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
            "--vcs-ref",
            "HEAD",
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
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "update_smoke_test",
            "include_cli": False,
            "include_git_cliff": True,
        },
    )
    _prune_docs_when_disabled(
        test_dir,
        {"include_docs": False},
    )

    _ = run_command(["git", "init"], cwd=test_dir)
    git_commit_all(test_dir, "chore: initial generated project")

    result = run_command(
        ["copier", "update", "--defaults", "--trust", "--skip-tasks"],
        cwd=test_dir,
        check=False,
    )
    assert result.returncode == 0, f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"


def test_copier_recopy_respects_skip_if_exists_for_user_edited_files(tmp_path: Path) -> None:
    """Skipped paths survive ``copier recopy``; other rendered files come from the template.

    ``copier update`` attempts to preserve git diffs and may emit inline merge conflicts on changed
    files. ``copier recopy`` reapplies the template as on first copy (keeping answers) while still
    honouring ``_skip_if_exists``, which matches the contract for README, ``env.example``, and
    template-owned modules such as ``core.py``.
    """
    template_repo = tmp_path / "template_repo"
    test_dir = tmp_path / "update_skip_contract"

    _ = shutil.copytree(
        Path("."),
        template_repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            "*.pyc",
            ".ruff_cache",
            ".pytest_cache",
            "files.zip",
            "temp",
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
            "--vcs-ref",
            "HEAD",
            vcs_src,
            str(test_dir),
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--data",
            "project_name=Skip Contract",
            "--data",
            "include_docs=false",
        ]
    )
    _remove_empty_optional_artifacts(
        test_dir,
        {
            "package_name": "skip_contract",
            "include_cli": False,
            "include_git_cliff": True,
        },
    )
    _prune_docs_when_disabled(test_dir, {"include_docs": False})

    _ = run_command(["git", "init"], cwd=test_dir)
    git_commit_all(test_dir, "chore: initial generated project")

    readme = test_dir / "README.md"
    env_example = test_dir / "env.example"
    core_py = test_dir / "src" / "skip_contract" / "core.py"
    assert core_py.is_file(), f"expected {core_py}"

    for path, marker in (
        (readme, "\n# USER_README_MARKER\n"),
        (env_example, "\n# USER_ENV_MARKER\n"),
        (core_py, "\n# USER_CORE_MARKER\n"),
    ):
        with path.open("a", encoding="utf-8") as handle:
            _ = handle.write(marker)

    git_commit_all(test_dir, "chore: user markers before recopy")

    result = run_command(
        [
            "copier",
            "recopy",
            "--force",
            "--trust",
            "--skip-tasks",
            "--vcs-ref",
            "HEAD",
        ],
        cwd=test_dir,
        check=False,
    )
    if result.returncode != 0 and (
        "pathspec" in result.stderr or "did not match any file" in result.stderr
    ):
        pytest.skip(
            "Copier could not check out the template commit in its temp clone; "
            "skip-if-exists contract was not exercised."
        )
    assert result.returncode == 0, f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"

    assert "# USER_README_MARKER" in readme.read_text(encoding="utf-8")
    assert "# USER_ENV_MARKER" in env_example.read_text(encoding="utf-8")
    core_text = core_py.read_text(encoding="utf-8")
    assert "# USER_CORE_MARKER" not in core_text
    assert "<<<<<<<" not in core_text and ">>>>>>>" not in core_text


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
        "include_cli": False,
        "include_git_cliff": False,
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


def test_include_cli_adds_console_script(tmp_path: Path) -> None:
    """``include_cli=true`` must add Typer CLI module and ``[project.scripts]`` entry."""
    test_dir = tmp_path / "with_cli"
    copy_with_data(
        test_dir,
        {
            "project_name": "CLI Project",
            "package_name": "cli_project",
            "include_docs": False,
            "include_cli": True,
        },
    )
    cli_py = test_dir / "src" / "cli_project" / "cli.py"
    assert cli_py.is_file()
    assert "typer" in cli_py.read_text(encoding="utf-8")
    pyproject = load_pyproject(test_dir)
    proj = require_mapping(pyproject.get("project"), name="pyproject.project")
    st = proj.get("scripts")
    assert isinstance(st, dict), "project.scripts missing"
    assert "cli_project" in st


def test_include_git_cliff_adds_dependency_group(tmp_path: Path) -> None:
    """``include_git_cliff=true`` must add a changelog dependency group and cliff.toml."""
    test_dir = tmp_path / "with_cliff"
    copy_with_data(
        test_dir,
        {
            "project_name": "Cliff Project",
            "package_name": "cliff_project",
            "include_docs": False,
            "include_git_cliff": True,
        },
    )
    cliff = test_dir / "cliff.toml"
    assert cliff.is_file()
    assert "[changelog]" in cliff.read_text(encoding="utf-8")
    raw = (test_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependency-groups" in raw
    assert "git-cliff" in raw


def test_include_docs_and_git_cliff_keep_docs_extra_in_optional_dependencies(
    tmp_path: Path,
) -> None:
    """Template order must keep ``docs`` in optional dependencies before ``[dependency-groups]``."""
    _ = tmp_path  # keep fixture signature consistent with neighboring tests
    template = (
        Path(__file__).resolve().parent.parent / "template" / "pyproject.toml.jinja"
    ).read_text(encoding="utf-8")
    docs_idx = template.index("docs = [")
    dep_groups_idx = template.index("[dependency-groups]")
    assert docs_idx < dep_groups_idx, (
        "docs extra must be declared before [dependency-groups] so it stays under "
        "[project.optional-dependencies]"
    )


def test_include_docs_and_git_cliff_render_docs_extra_in_generated_pyproject(
    tmp_path: Path,
) -> None:
    """Rendered project must keep ``docs`` under ``project.optional-dependencies``."""
    test_dir = tmp_path / "docs_and_cliff_rendered"
    copy_with_data_from_worktree(
        test_dir,
        {
            "project_name": "Docs and Cliff Rendered",
            "package_name": "docs_and_cliff_rendered",
            "include_docs": True,
            "include_git_cliff": True,
        },
    )

    pyproject = load_pyproject(test_dir)
    project = require_mapping(pyproject.get("project"), name="pyproject.project")
    optional_deps = require_mapping(
        project.get("optional-dependencies"), name="pyproject.project.optional-dependencies"
    )
    docs_deps = require_sequence(
        optional_deps.get("docs"), name="pyproject.project.optional-dependencies.docs"
    )
    docs_dep_strings = [cast(str, dep) for dep in docs_deps]
    assert any(dep.startswith("mkdocs>=") for dep in docs_dep_strings)

    dependency_groups = require_mapping(
        pyproject.get("dependency-groups"), name="pyproject.dependency-groups"
    )
    changelog = require_sequence(
        dependency_groups.get("changelog"), name="pyproject.dependency-groups.changelog"
    )
    assert any("git-cliff" in cast(str, dep) for dep in changelog)


def test_no_logging_config_module_logging_in_common(tmp_path: Path) -> None:
    """Logging setup lives only in ``common/logging_manager.py`` — no ``logging_config.py``."""
    test_dir = tmp_path / "logging_single_source"
    copy_with_data(
        test_dir,
        {
            "project_name": "Log Project",
            "package_name": "log_project",
            "include_docs": False,
        },
    )
    assert not (test_dir / "src" / "log_project" / "logging_config.py").exists()
    lm = test_dir / "src" / "log_project" / "common" / "logging_manager.py"
    assert lm.is_file()
    assert "def configure_logging" in lm.read_text(encoding="utf-8")


def test_root_contributing_and_security_rendered(tmp_path: Path) -> None:
    """Repository root should include ``CONTRIBUTING.md`` and ``SECURITY.md``."""
    test_dir = tmp_path / "contrib_sec"
    copy_with_data(
        test_dir,
        {"project_name": "Open Project", "include_docs": False},
    )
    contributing = test_dir / "CONTRIBUTING.md"
    security = test_dir / "SECURITY.md"
    assert contributing.is_file()
    assert security.is_file()
    assert "Submitting a Pull Request" in contributing.read_text(encoding="utf-8")
    assert "Reporting a Vulnerability" in security.read_text(encoding="utf-8")


def test_docs_ci_page_when_docs_enabled(tmp_path: Path) -> None:
    """MkDocs nav should include the CI / Codecov documentation page."""
    test_dir = tmp_path / "docs_ci"
    copy_with_data(
        test_dir,
        {"project_name": "Docs CI", "include_docs": True},
    )
    ci_doc = test_dir / "docs" / "ci.md"
    assert ci_doc.is_file()
    assert "CODECOV_TOKEN" in ci_doc.read_text(encoding="utf-8")
    mkdocs = (test_dir / "mkdocs.yml").read_text(encoding="utf-8")
    assert "ci.md" in mkdocs


def test_github_repository_settings_doc_in_generated_project(tmp_path: Path) -> None:
    """GitHub Settings checklist ships under docs/ even when MkDocs pages are omitted.

    Uses :func:`copy_with_data_from_worktree` so ``template/docs/github-repository-settings.md.jinja``
    is exercised before it appears in the last git commit (same pattern as ``test_env_example_rendered``).
    """
    test_dir = tmp_path / "branch_prot_doc"
    copy_with_data_from_worktree(
        test_dir,
        {"project_name": "Branch Prot", "include_docs": False, "include_git_cliff": False},
    )
    doc = test_dir / "docs" / "github-repository-settings.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "squash" in text.lower()
    assert "pull request" in text.lower()
    assert "only checklist" in text.lower()
    assert "## 12. solo / personal maintainer" in text.lower()
    assert "what adds value versus ceremony" in text.lower()


def test_generated_pr_policy_and_templates(tmp_path: Path) -> None:
    """Generated projects ship PR template, commit template, policy script, and workflow."""
    test_dir = tmp_path / "pr_policy_ship"
    copy_with_data_from_worktree(
        test_dir,
        {"project_name": "PR Pol", "include_docs": False, "include_git_cliff": False},
    )
    pr_tpl = test_dir / ".github" / "PULL_REQUEST_TEMPLATE.md"
    assert pr_tpl.is_file()
    assert "## Summary" in pr_tpl.read_text(encoding="utf-8")
    assert (test_dir / ".gitmessage").is_file()
    script = test_dir / "scripts" / "pr_commit_policy.py"
    assert script.is_file()
    assert "validate_pr_body" in script.read_text(encoding="utf-8")
    wf = test_dir / ".github" / "workflows" / "pr-policy.yml"
    assert wf.is_file()
    wf_text = wf.read_text(encoding="utf-8")
    assert "pr_commit_policy.py" in wf_text
    assert "PR policy" in wf_text


def test_generated_pyproject_basedpyright_standard_mode(tmp_path: Path) -> None:
    """Generated projects should configure basedpyright in standard mode (per template contract)."""
    test_dir = tmp_path / "bp_std"
    copy_with_data(
        test_dir,
        {"project_name": "BP Test", "include_docs": False, "include_git_cliff": False},
    )
    raw = (test_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'typeCheckingMode = "standard"' in raw
    assert "reportMissingImports = true" in raw


def test_generated_pyproject_ruff_includes_print_rules(tmp_path: Path) -> None:
    """Generated projects should enable Ruff T20 (flake8-print) with sensible per-file ignores."""
    test_dir = tmp_path / "ruff_t20"
    copy_with_data_from_worktree(test_dir, {"project_name": "Ruff T20", "include_docs": False})
    data = tomllib.loads((test_dir / "pyproject.toml").read_text(encoding="utf-8"))
    ruff_lint = cast(Mapping[str, object], cast(Mapping[str, object], data["tool"])["ruff"])
    lint = cast(Mapping[str, object], ruff_lint["lint"])
    select = cast(list[str], lint["select"])
    assert "T20" in select
    per_file = cast(Mapping[str, list[str]], lint["per-file-ignores"])
    assert "T20" in per_file["tests/**"]
    assert "D" not in per_file["tests/**"]
    assert "T20" in per_file["scripts/**"]
    assert "D" not in per_file["scripts/**"]
    assert "src/**/bump_version.py" not in per_file


def test_generated_pyproject_pytest_markers_and_asyncio(tmp_path: Path) -> None:
    """Generated projects register layered-test markers and ship pytest-asyncio for async tests."""
    test_dir = tmp_path / "pytest_markers_async"
    copy_with_data_from_worktree(
        test_dir,
        {"project_name": "Pytest Markers", "include_docs": False},
    )
    data = tomllib.loads((test_dir / "pyproject.toml").read_text(encoding="utf-8"))
    project = require_mapping(data.get("project"), name="pyproject.project")
    optional = require_mapping(
        project.get("optional-dependencies"), name="pyproject.project.optional-dependencies"
    )
    test_deps = cast(
        Sequence[str], require_sequence(optional.get("test"), name="optional-dependencies.test")
    )
    assert any(dep.startswith("pytest-asyncio") for dep in test_deps)

    tool = require_mapping(data.get("tool"), name="pyproject.tool")
    pytest_ini = require_mapping(tool.get("pytest"), name="tool.pytest")
    ini_options = require_mapping(pytest_ini.get("ini_options"), name="pytest.ini_options")
    markers = cast(
        Sequence[str],
        require_sequence(ini_options.get("markers"), name="pytest.ini_options.markers"),
    )
    joined = "\n".join(markers)
    for marker in ("e2e:", "integration:", "regression:", "slow:", "smoke:", "unit:"):
        assert marker in joined


def test_generated_pre_commit_includes_detect_secrets(tmp_path: Path) -> None:
    """Pre-commit config in generated projects should run detect-secrets with a baseline."""
    test_dir = tmp_path / "secrets_hook"
    copy_with_data_from_worktree(
        test_dir,
        {"project_name": "Secrets Hook", "include_docs": False, "include_git_cliff": False},
    )
    cfg = (test_dir / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "detect-secrets" in cfg
    assert ".secrets.baseline" in cfg
    assert "commitizen-tools/commitizen" in cfg
    assert "id: commitizen" in cfg
    assert "commit-msg" in cfg
    assert "no-commit-to-branch" in cfg
    assert "just-ci-check" in cfg
    assert "just ci-check" in cfg
    assert (test_dir / ".secrets.baseline").is_file()


def test_generated_renovate_enables_pre_commit(tmp_path: Path) -> None:
    """Renovate should manage pre-commit hook revisions in generated projects."""
    test_dir = tmp_path / "renovate_pc"
    copy_with_data(
        test_dir,
        {"project_name": "Renovate Test", "include_docs": False, "include_git_cliff": False},
    )
    import json

    data = json.loads((test_dir / ".github" / "renovate.json").read_text(encoding="utf-8"))
    assert data.get("pre-commit", {}).get("enabled") is True


@pytest.mark.parametrize(
    "flags",
    [
        {
            "include_docs": True,
            "include_numpy": True,
            "include_pandas_support": False,
            "include_cli": True,
            "include_git_cliff": True,
        },
        {
            "include_docs": False,
            "include_numpy": False,
            "include_pandas_support": True,
            "include_cli": False,
            "include_git_cliff": False,
        },
    ],
)
def test_boolean_feature_combinations_render(tmp_path: Path, flags: dict[str, bool]) -> None:
    """Spot-check two opposite feature bundles for a consistent tree."""
    test_dir = tmp_path / f"combo_{hash(frozenset(flags.items())) % 10000}"
    data: dict[str, str | bool] = {"project_name": "Combo Project", **flags}
    copy_with_data(test_dir, data)
    assert (test_dir / "pyproject.toml").is_file()
    pkg = "combo_project"
    assert (test_dir / "src" / pkg / "__init__.py").is_file()
    if flags["include_docs"]:
        assert (test_dir / "mkdocs.yml").is_file()
    else:
        assert not (test_dir / "mkdocs.yml").exists()


@pytest.mark.skipif(
    os.environ.get("RUN_TEMPLATE_INTEGRATION") != "1",
    reason="Set RUN_TEMPLATE_INTEGRATION=1 for uv lock+sync smoke (network, slower).",
)
def test_generated_project_uv_lock_and_sync_smoke(tmp_path: Path) -> None:
    """After render, ``uv lock`` and ``uv sync --frozen`` must succeed (integration gate)."""
    test_dir = tmp_path / "uv_sync_smoke"
    copy_with_data(
        test_dir,
        {
            "project_name": "UV Sync Smoke",
            "include_docs": False,
        },
    )
    _ = run_command(["uv", "lock"], cwd=test_dir)
    _ = run_command(
        ["uv", "sync", "--frozen", "--extra", "dev", "--extra", "test"],
        cwd=test_dir,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_TEMPLATE_INTEGRATION") != "1",
    reason="Set RUN_TEMPLATE_INTEGRATION=1 for uv lock+sync smoke (network, slower).",
)
def test_generated_project_uv_sync_docs_with_git_cliff_smoke(tmp_path: Path) -> None:
    """When docs and git-cliff are enabled, uv sync must accept docs extra + changelog group."""
    test_dir = tmp_path / "uv_sync_docs_cliff_smoke"
    copy_with_data(
        test_dir,
        {
            "project_name": "UV Sync Docs Cliff Smoke",
            "include_docs": True,
            "include_git_cliff": True,
        },
    )
    _ = run_command(["uv", "lock"], cwd=test_dir)
    _ = run_command(
        [
            "uv",
            "sync",
            "--frozen",
            "--extra",
            "dev",
            "--extra",
            "test",
            "--extra",
            "docs",
            "--group",
            "changelog",
        ],
        cwd=test_dir,
    )


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
    assert "src/release_default/common/bump_version.py" in content, (
        "release.yml must reference src/<package>/common/bump_version.py"
    )
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
    """The ``uv publish`` step must not appear when PyPI publish is disabled (default)."""
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
    # Worktree render: assert on template edits (e.g. pip-audit invocation) before they are committed.
    copy_with_data_from_worktree(
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
        "pip-audit must audit dev dependencies exported from the lockfile"
    )
    assert "--requirement /dev/stdin" in content, (
        "pip-audit must read exported requirements via --requirement /dev/stdin (not removed --stdin)"
    )
    assert "uv run --with pip-audit pip-audit" in content, (
        "pip-audit must match `just audit` (project interpreter via uv run --with)"
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


def test_ci_workflow_aligns_with_just_ci(tmp_path: Path) -> None:
    """``ci.yml`` and ``just ci`` must stay aligned (pre-commit job, ruff paths, pytest flags)."""
    test_dir = tmp_path / "ci_just_align"
    # Worktree render: ``copy_with_data`` uses ``git+file`` at HEAD, which omits uncommitted template edits.
    copy_with_data_from_worktree(
        test_dir,
        {
            "project_name": "CI Just Align",
            "include_docs": False,
        },
    )
    ci_yml = test_dir / ".github" / "workflows" / "ci.yml"
    assert ci_yml.is_file(), "ci.yml must be generated"
    workflow = ci_yml.read_text(encoding="utf-8")
    assert "needs: [lint, typecheck, precommit, test]" in workflow, (
        "Aggregate check must gate on pre-commit alongside lint, typecheck, and tests"
    )
    assert "uv run pre-commit run --all-files --verbose" in workflow
    assert "uv run ruff format --check src tests" in workflow
    assert "uv run ruff check src tests" in workflow
    assert "uv run pytest -n auto --cov --cov-report=xml --cov-report=term" in workflow

    justfile = (test_dir / "justfile").read_text(encoding="utf-8")
    assert "test-ci:" in justfile
    assert "pytest -n auto --cov --cov-report=xml --cov-report=term" in justfile
    assert "@just test-ci" in justfile

    lint_yml = (test_dir / ".github" / "workflows" / "lint.yml").read_text(encoding="utf-8")
    assert "uv run ruff format --check src tests" in lint_yml
    assert "uv run ruff check src tests" in lint_yml


def test_common_bump_version_generated(tmp_path: Path) -> None:
    """``src/<package>/common/bump_version.py`` must exist in the generated project."""
    test_dir = tmp_path / "bump_version"
    copy_with_data_from_worktree(
        test_dir,
        {
            "project_name": "Bump Version",
            "package_name": "bump_version_pkg",
            "include_release_workflow": True,
            "include_docs": False,
        },
    )
    bump_script = test_dir / "src" / "bump_version_pkg" / "common" / "bump_version.py"
    assert bump_script.is_file(), "common/bump_version.py must exist in generated projects"
    content = bump_script.read_text(encoding="utf-8")
    assert "BumpKind" in content, "bump_version.py must contain BumpKind type alias"
    assert "[project]" in content, "bump_version.py must look for [project] section"
    assert "write_machine_stdout_line" in content, (
        "bump_version must emit version via logging_manager"
    )
    assert "print(" not in content, "bump_version must not use print(); use logging_manager instead"


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
