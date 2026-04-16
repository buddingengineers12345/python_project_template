"""Tests for ``scripts/check_root_template_sync`` policy checks."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from tests.script_imports import REPO_ROOT, load_script_module

_SCRIPT = REPO_ROOT / "scripts" / "check_root_template_sync.py"
crs = load_script_module("check_root_template_sync")


@dataclass
class _Result:
    returncode: int
    stdout: str
    stderr: str = ""


def write_file(path: Path, content: str) -> None:
    """Create parent directories and write ``content`` to ``path`` as UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_sync_check(repo_root: Path, map_rel: str = "docs/map.yaml") -> _Result:
    """Run the sync checker in-process and return a result with returncode + stdout."""
    buf = io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT), "--repo-root", str(repo_root), "--map", map_rel]
        with contextlib.redirect_stdout(buf):
            try:
                returncode = crs.main()
            except SystemExit as exc:
                returncode = int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = saved_argv
    return _Result(returncode=returncode, stdout=buf.getvalue())


def test_sync_check_passes_for_matching_pairs_and_sections(tmp_path: Path) -> None:
    """Matching workflow, hook, and pyproject sections yield exit code 0."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "workflow_versions",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/lint.yml",
                        "template": "template/.github/workflows/lint.yml.jinja",
                    }
                ],
            },
            {
                "id": "hooks",
                "type": "exact_file_pairs",
                "pairs": [
                    {
                        "root": ".claude/hooks/pre-bash-block-no-verify.sh",
                        "template": "template/.claude/hooks/pre-bash-block-no-verify.sh",
                    }
                ],
            },
            {
                "id": "pyproject",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [
                    {"name": "tool.ruff", "required_keys": ["line-length", "target-version"]},
                    {
                        "name": "tool.ruff.lint",
                        "required_keys": ["select", "ignore"],
                        "required_select_codes": ["D", "T20"],
                    },
                ],
            },
        ],
    }
    write_file(repo / "docs" / "map.yaml", json.dumps(map_data, indent=2))

    write_file(
        repo / ".github/workflows/lint.yml",
        "jobs:\n  lint:\n    steps:\n      - uses: actions/checkout@v6\n",
    )
    write_file(
        repo / "template/.github/workflows/lint.yml.jinja",
        "jobs:\n  lint:\n    steps:\n      - uses: actions/checkout@v6\n",
    )

    hook_content = "#!/usr/bin/env bash\necho ok\n"
    write_file(repo / ".claude/hooks/pre-bash-block-no-verify.sh", hook_content)
    write_file(repo / "template/.claude/hooks/pre-bash-block-no-verify.sh", hook_content)

    write_file(
        repo / "pyproject.toml",
        (
            "[tool.ruff]\n"
            "line-length = 100\n"
            'target-version = "py311"\n\n'
            "[tool.ruff.lint]\n"
            'select = ["D", "T20"]\n'
            'ignore = ["E501"]\n'
        ),
    )
    write_file(
        repo / "template/pyproject.toml.jinja",
        (
            "{% if true %}\n{% endif %}\n"
            "[tool.ruff]\n"
            "line-length = 100\n"
            "target-version = \"py{{ python_min_version | replace('.', '') }}\"\n\n"
            "[tool.ruff.lint]\n"
            'select = ["D", "T20", "UP"]\n'
            'ignore = ["E501"]\n'
        ),
    )

    result = run_sync_check(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[sync-check] PASS" in result.stdout


def test_sync_check_fails_on_workflow_action_version_drift(tmp_path: Path) -> None:
    """Mismatched ``uses:`` versions between root and template fail the check."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "workflow_versions",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/security.yml",
                        "template": "template/.github/workflows/security.yml.jinja",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / ".github/workflows/security.yml",
        "jobs:\n  s:\n    steps:\n      - uses: github/codeql-action/init@v4\n",
    )
    write_file(
        repo / "template/.github/workflows/security.yml.jinja",
        "jobs:\n  s:\n    steps:\n      - uses: github/codeql-action/init@v3\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "workflow_versions" in result.stdout
    assert "mismatch" in result.stdout


def test_sync_check_fails_when_required_pyproject_key_missing(tmp_path: Path) -> None:
    """Missing required TOML keys in the template fail the pyproject section check."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproject",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.basedpyright", "required_keys": ["typeCheckingMode"]}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "pyproject.toml", '[tool.basedpyright]\ntypeCheckingMode = "standard"\n')
    write_file(
        repo / "template/pyproject.toml.jinja", '[tool.basedpyright]\npythonVersion = "3.11"\n'
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "missing key in template" in result.stdout


def test_load_map_rejects_invalid_json(tmp_path: Path) -> None:
    """``_load_map`` raises when the file is not valid JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        crs._load_map(bad)


def test_load_map_rejects_non_object_root(tmp_path: Path) -> None:
    """Top-level JSON must be an object."""
    p = tmp_path / "list.json"
    p.write_text("[1]", encoding="utf-8")
    with pytest.raises(ValueError, match="object"):
        crs._load_map(p)


def test_main_empty_checks_returns_exit_code_2(tmp_path: Path) -> None:
    """An empty ``checks`` array is a fatal mapping error (exit 2)."""
    repo = tmp_path / "repo"
    write_file(repo / "docs/map.yaml", json.dumps({"version": 1, "checks": []}, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 2
    assert "non-empty checks" in result.stdout


def test_main_malformed_map_json_returns_exit_code_2(tmp_path: Path) -> None:
    """Invalid JSON in the map file yields exit code 2."""
    repo = tmp_path / "repo"
    write_file(repo / "docs/map.yaml", "{")
    result = run_sync_check(repo)
    assert result.returncode == 2
    assert "invalid JSON" in result.stdout


def test_unsupported_check_type_is_a_violation(tmp_path: Path) -> None:
    """Unknown ``type`` values surface as a check violation (exit 1)."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [{"id": "weird", "type": "not_a_real_check_type"}],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "weird" in result.stdout
    assert "unsupported check type" in result.stdout


def test_invalid_pairs_raises_as_check_violation(tmp_path: Path) -> None:
    """Workflow check with no valid root/template pairs fails via that check's id."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "wf_bad_pairs",
                "type": "workflow_action_versions",
                "pairs": [{"root": 1, "template": 2}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "wf_bad_pairs" in result.stdout
    assert "pairs must contain" in result.stdout


# ============================================================================
# Additional coverage tests for uncovered code paths
# ============================================================================


def test_workflow_pair_no_shared_actions(tmp_path: Path) -> None:
    """Workflow check fails when root and template have no shared actions."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "wf_no_shared",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/test.yml",
                        "template": "template/.github/workflows/test.yml.jinja",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / ".github/workflows/test.yml",
        "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v6\n",
    )
    write_file(
        repo / "template/.github/workflows/test.yml.jinja",
        "jobs:\n  test:\n    steps:\n      - uses: actions/setup-node@v4\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "wf_no_shared" in result.stdout
    assert "no shared actions" in result.stdout


def test_workflow_pair_missing_root_file(tmp_path: Path) -> None:
    """Workflow check fails when root file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "wf_missing_root",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/missing.yml",
                        "template": "template/.github/workflows/missing.yml.jinja",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / "template/.github/workflows/missing.yml.jinja",
        "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v6\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "wf_missing_root" in result.stdout
    assert "missing file" in result.stdout
    assert ".github/workflows/missing.yml" in result.stdout


def test_workflow_pair_missing_template_file(tmp_path: Path) -> None:
    """Workflow check fails when template file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "wf_missing_tpl",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/missing.yml",
                        "template": "template/.github/workflows/missing.yml.jinja",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / ".github/workflows/missing.yml",
        "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v6\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "wf_missing_tpl" in result.stdout
    assert "missing file" in result.stdout
    assert "template" in result.stdout


def test_exact_file_pair_missing_root_file(tmp_path: Path) -> None:
    """Exact file pair check fails when root file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "exact_missing_root",
                "type": "exact_file_pairs",
                "pairs": [
                    {
                        "root": ".hooks/missing.sh",
                        "template": "template/.hooks/missing.sh",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "template/.hooks/missing.sh", "#!/bin/bash\necho hi\n")

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "exact_missing_root" in result.stdout
    assert "missing file" in result.stdout
    assert ".hooks/missing.sh" in result.stdout


def test_exact_file_pair_missing_template_file(tmp_path: Path) -> None:
    """Exact file pair check fails when template file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "exact_missing_tpl",
                "type": "exact_file_pairs",
                "pairs": [
                    {
                        "root": ".hooks/missing.sh",
                        "template": "template/.hooks/missing.sh",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / ".hooks/missing.sh", "#!/bin/bash\necho hi\n")

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "exact_missing_tpl" in result.stdout
    assert "missing file" in result.stdout
    assert "template" in result.stdout


def test_exact_file_pair_content_differs(tmp_path: Path) -> None:
    """Exact file pair check detects content differences."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "exact_diff",
                "type": "exact_file_pairs",
                "pairs": [
                    {
                        "root": ".hooks/script.sh",
                        "template": "template/.hooks/script.sh",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / ".hooks/script.sh", "#!/bin/bash\necho 'root version'\n")
    write_file(
        repo / "template/.hooks/script.sh",
        "#!/bin/bash\necho 'template version'\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "exact_diff" in result.stdout
    assert "exact mismatch" in result.stdout


def test_strip_jinja_lines_removes_directives(tmp_path: Path) -> None:
    """``_strip_jinja_lines`` removes lines with only {% %} and {# #} directives."""
    text = "line1\n{% if true %}\nline2\n{% endif %}\n{# comment #}\nline4\n"
    result = crs._strip_jinja_lines(text)
    # Verify content lines remain
    assert "line1" in result
    assert "line2" in result
    assert "line4" in result
    # Verify lines with only Jinja are removed
    lines = result.splitlines()
    assert "line1" in lines
    assert "line2" in lines
    assert "line4" in lines
    assert "{%" not in result  # No Jinja directives remain
    assert "{#" not in result  # No Jinja comments remain


def test_extract_section_text_finds_section(tmp_path: Path) -> None:
    """``_extract_section_text`` extracts content between section headers."""
    text = "[tool.a]\nkey1 = 1\n\n[tool.b]\nkey2 = 2\n\n[tool.c]\nkey3 = 3\n"
    result = crs._extract_section_text(text, "tool.b")
    assert result is not None
    assert "key2" in result
    assert "key1" not in result
    assert "key3" not in result


def test_extract_section_text_returns_none_for_missing_section(tmp_path: Path) -> None:
    """``_extract_section_text`` returns None when section is not found."""
    text = "[tool.a]\nkey1 = 1\n"
    result = crs._extract_section_text(text, "tool.missing")
    assert result is None


def test_extract_assignment_keys_finds_all_keys(tmp_path: Path) -> None:
    """``_extract_assignment_keys`` extracts all assignment keys from section."""
    section_text = "key1 = 1\nkey2 = 2\n  key3  = 3\n"
    result = crs._extract_assignment_keys(section_text)
    assert result == {"key1", "key2", "key3"}


def test_extract_select_codes_with_select_list(tmp_path: Path) -> None:
    """``_extract_select_codes`` extracts quoted codes from select list."""
    section_text = 'select = ["D", "T20", "UP"]\n'
    result = crs._extract_select_codes(section_text)
    assert result == {"D", "T20", "UP"}


def test_extract_select_codes_without_select_list(tmp_path: Path) -> None:
    """``_extract_select_codes`` returns empty set when no select list exists."""
    section_text = "ignore = ['E501']\n"
    result = crs._extract_select_codes(section_text)
    assert result == set()


def test_extract_workflow_actions_multiple_versions(tmp_path: Path) -> None:
    """``_extract_workflow_actions`` collects multiple versions of same action."""
    text = (
        "- uses: actions/checkout@v6\n- uses: actions/setup-node@v4\n- uses: actions/checkout@v5\n"
    )
    result = crs._extract_workflow_actions(text)
    assert result["actions/checkout"] == {"v6", "v5"}
    assert result["actions/setup-node"] == {"v4"}


def test_extract_workflow_actions_empty_file(tmp_path: Path) -> None:
    """``_extract_workflow_actions`` returns empty dict for file with no actions."""
    text = "jobs:\n  test:\n    steps:\n      - run: echo test\n"
    result = crs._extract_workflow_actions(text)
    assert result == {}


def test_validate_pairs_object_with_non_list(tmp_path: Path) -> None:
    """``_validate_pairs_object`` returns empty list for non-list input."""
    result = crs._validate_pairs_object("test", "not a list")
    assert result == []


def test_validate_pairs_object_with_empty_pairs(tmp_path: Path) -> None:
    """``_validate_pairs_object`` raises when pairs list is empty."""
    with pytest.raises(ValueError, match="pairs must contain"):
        crs._validate_pairs_object("test", [])


def test_validate_pairs_object_with_non_dict_items(tmp_path: Path) -> None:
    """``_validate_pairs_object`` skips non-dict items and raises if none valid."""
    with pytest.raises(ValueError, match="pairs must contain"):
        crs._validate_pairs_object("test", [1, 2, "three"])


def test_validate_pairs_object_with_missing_keys(tmp_path: Path) -> None:
    """``_validate_pairs_object`` skips items missing root/template and raises if none valid."""
    with pytest.raises(ValueError, match="pairs must contain"):
        crs._validate_pairs_object("test", [{"root": "only_root"}, {"template": "only_tpl"}])


def test_pyproject_section_violations_missing_root_file(tmp_path: Path) -> None:
    """Pyproject check fails when root file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_missing_root",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.ruff"}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "template/pyproject.toml.jinja", "[tool.ruff]\nline-length = 100\n")

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_missing_root" in result.stdout
    assert "missing file" in result.stdout


def test_pyproject_section_violations_missing_template_file(tmp_path: Path) -> None:
    """Pyproject check fails when template file is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_missing_tpl",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.ruff"}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "pyproject.toml", "[tool.ruff]\nline-length = 100\n")

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_missing_tpl" in result.stdout
    assert "missing file" in result.stdout


def test_pyproject_section_missing_in_root(tmp_path: Path) -> None:
    """Pyproject check fails when required section is missing in root."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_sect_missing",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.pytest"}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "pyproject.toml", "[tool.ruff]\nline-length = 100\n")
    write_file(
        repo / "template/pyproject.toml.jinja",
        "[tool.pytest]\naddopts = '-v'\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_sect_missing" in result.stdout
    assert "missing root section" in result.stdout


def test_pyproject_section_missing_in_template(tmp_path: Path) -> None:
    """Pyproject check fails when required section is missing in template."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_sect_tpl_missing",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.pytest"}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "pyproject.toml", "[tool.pytest]\naddopts = '-v'\n")
    write_file(
        repo / "template/pyproject.toml.jinja",
        "[tool.ruff]\nline-length = 100\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_sect_tpl_missing" in result.stdout
    assert "missing template section" in result.stdout


def test_pyproject_missing_required_select_code(tmp_path: Path) -> None:
    """Pyproject check fails when required select code is missing."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_code_missing",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [
                    {
                        "name": "tool.ruff.lint",
                        "required_select_codes": ["D", "MISSING_CODE"],
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / "pyproject.toml",
        '[tool.ruff.lint]\nselect = ["D"]\n',
    )
    write_file(
        repo / "template/pyproject.toml.jinja",
        '[tool.ruff.lint]\nselect = ["D"]\n',
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_code_missing" in result.stdout
    assert "root select list missing code" in result.stdout


def test_check_with_non_dict_entry(tmp_path: Path) -> None:
    """Check list with non-dict entry yields violation."""
    repo = tmp_path / "repo"
    map_data = {"version": 1, "checks": ["not a dict"]}
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "each check entry must be an object" in result.stdout


def test_main_missing_mapping_file_returns_exit_2(tmp_path: Path) -> None:
    """Main exits with code 2 when mapping file doesn't exist."""
    repo = tmp_path / "repo"
    result = run_sync_check(repo, "nonexistent.yaml")
    assert result.returncode == 2
    assert "mapping file not found" in result.stdout


def test_resolve_repo_root_with_explicit_path() -> None:
    """``_resolve_repo_root`` resolves an explicit path."""
    explicit = Path("/tmp/test_repo")
    result = crs._resolve_repo_root(str(explicit))
    assert result == explicit.resolve()


def test_resolve_repo_root_with_none() -> None:
    """``_resolve_repo_root`` uses script parent when arg is None."""
    result = crs._resolve_repo_root(None)
    # Should be parent of scripts directory
    assert "python_starter_template" in str(result) or "scripts" in str(result.parent)


def test_resolve_repo_root_with_empty_string() -> None:
    """``_resolve_repo_root`` uses script parent when arg is empty string."""
    result = crs._resolve_repo_root("")
    # Should be parent of scripts directory
    assert "python_starter_template" in str(result) or "scripts" in str(result.parent)


# ============================================================================
# Additional edge case tests for remaining coverage gaps
# ============================================================================


def test_short_diff_with_no_diff_lines(tmp_path: Path) -> None:
    """``_short_diff`` returns 'content differs' when no unified diff lines exist."""
    # When texts are identical, difflib produces no diff lines
    result = crs._short_diff("same content", "same content")
    assert result == "content differs"


def test_pyproject_section_definition_not_dict(tmp_path: Path) -> None:
    """Pyproject section definition that is not a dict yields a violation."""
    # This is harder to trigger through the public API, so we test the internal function
    result = crs._pyproject_section_violations("test_id", "not_a_dict", "", "")
    assert len(result) == 1
    assert "section definition must be an object" in result[0].message


def test_pyproject_section_missing_name(tmp_path: Path) -> None:
    """Pyproject section definition missing name field yields a violation."""
    result = crs._pyproject_section_violations("test_id", {}, "", "")
    assert len(result) == 1
    assert "missing name" in result[0].message


def test_required_keys_with_non_string_items(tmp_path: Path) -> None:
    """Required keys list with non-string items is handled gracefully."""
    section_text = "key1 = 1\n"
    # Mix of strings and non-strings
    violations = crs._required_key_violations(
        "test_id",
        "tool.test",
        section_text,
        section_text,
        {"required_keys": ["key1", 123, None]},
    )
    # Should only check "key1", ignore 123 and None
    assert len(violations) == 0


def test_required_select_codes_with_non_string_items(tmp_path: Path) -> None:
    """Required select codes with non-string items is handled gracefully."""
    section_text = 'select = ["D", "UP"]\n'
    violations = crs._required_select_code_violations(
        "test_id",
        "tool.ruff.lint",
        section_text,
        section_text,
        {"required_select_codes": ["D", 123]},
    )
    # Should only check "D", ignore 123
    assert len(violations) == 0


def test_required_keys_with_non_list(tmp_path: Path) -> None:
    """Section with non-list required_keys is handled gracefully."""
    section_text = "key1 = 1\n"
    violations = crs._required_key_violations(
        "test_id",
        "tool.test",
        section_text,
        section_text,
        {"required_keys": "not_a_list"},
    )
    # Should return empty list when required_keys is not a list
    assert len(violations) == 0


def test_required_select_codes_with_non_list(tmp_path: Path) -> None:
    """Section with non-list required_select_codes is handled gracefully."""
    section_text = 'select = ["D"]\n'
    violations = crs._required_select_code_violations(
        "test_id",
        "tool.ruff.lint",
        section_text,
        section_text,
        {"required_select_codes": "not_a_list"},
    )
    # Should return empty list when required_select_codes is not a list
    assert len(violations) == 0


def test_pyproject_check_invalid_root_template_sections(tmp_path: Path) -> None:
    """Pyproject check with invalid root/template/sections raises ValueError."""
    check = {
        "id": "bad_pyproj",
        "type": "pyproject_sections",
        "root": ".github/config.toml",  # missing template
        "sections": [],
    }
    repo = tmp_path / "repo"
    write_file(repo / ".github/config.toml", "[tool.test]\n")

    with pytest.raises(ValueError, match="root/template/sections are required"):
        crs._check_pyproject_sections(check, repo)


def test_extract_select_codes_with_multiline_list(tmp_path: Path) -> None:
    """``_extract_select_codes`` handles multiline select lists."""
    section_text = 'select = [\n    "D",\n    "UP",\n    "T20",\n]\n'
    result = crs._extract_select_codes(section_text)
    assert result == {"D", "UP", "T20"}


def test_validate_pairs_object_filters_non_string_values(tmp_path: Path) -> None:
    """``_validate_pairs_object`` only accepts pairs with string root/template."""
    pairs = [
        {"root": "path1", "template": "path2"},  # valid
        {"root": 123, "template": "path"},  # invalid: root not string
        {"root": "path", "template": None},  # invalid: template not string
        {"root": "path3", "template": "path4"},  # valid
    ]
    result = crs._validate_pairs_object("test", pairs)
    assert len(result) == 2
    assert result[0] == {"root": "path1", "template": "path2"}
    assert result[1] == {"root": "path3", "template": "path4"}


def test_parse_cli_args_with_custom_map_path() -> None:
    """``_parse_cli_args`` accepts custom map file path."""
    args = crs._parse_cli_args(["--map", "custom/path.yaml"])
    assert args.map == "custom/path.yaml"


def test_parse_cli_args_with_custom_repo_root() -> None:
    """``_parse_cli_args`` accepts custom repo root."""
    args = crs._parse_cli_args(["--repo-root", "/custom/root"])
    assert args.repo_root == "/custom/root"


def test_main_invalid_mapping_type(tmp_path: Path) -> None:
    """Main handles mapping files with checks not being a list."""
    repo = tmp_path / "repo"
    # checks is a dict instead of list
    map_data = {"version": 1, "checks": {"id": "test"}}
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))

    result = run_sync_check(repo)
    assert result.returncode == 2
    assert "non-empty checks" in result.stdout


def test_pyproject_key_missing_only_in_template(tmp_path: Path) -> None:
    """Pyproject check detects when required key is missing only in template."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproj_key_tpl_missing",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [
                    {
                        "name": "tool.ruff",
                        "required_keys": ["line-length", "target-version"],
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / "pyproject.toml",
        "[tool.ruff]\nline-length = 100\ntarget-version = 'py311'\n",
    )
    write_file(
        repo / "template/pyproject.toml.jinja",
        "[tool.ruff]\nline-length = 100\n",  # missing target-version
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "pyproj_key_tpl_missing" in result.stdout
    assert "missing key in template" in result.stdout
