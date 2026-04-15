#!/usr/bin/env python3
"""Validate root/template sync policy mappings."""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regexes (workflows, TOML)
# ---------------------------------------------------------------------------

SECTION_HEADER_RE = re.compile(r"^\[([^\]]+)\]\s*$", flags=re.MULTILINE)
USES_RE = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)@([^\s]+)")
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=", flags=re.MULTILINE)
QUOTED_TOKEN_RE = re.compile(r'"([^"]+)"')


# ---------------------------------------------------------------------------
# Violation model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    """Single sync violation emitted by one check."""

    check_id: str
    message: str


# ---------------------------------------------------------------------------
# Map loading and pair validation
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Read UTF-8 text with normalized newlines."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _load_map(path: Path) -> dict[str, Any]:
    """Parse the mapping file (JSON content; file may use ``.yaml`` extension)."""
    try:
        raw = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON/YAML mapping file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("mapping root must be an object")
    return raw


def _validate_pairs_object(check_id: str, obj: Any) -> list[dict[str, str]]:
    """Return normalized root/template pairs; raise if none are valid."""
    if not isinstance(obj, list):
        return []
    valid: list[dict[str, str]] = []
    for item in obj:
        if not isinstance(item, dict):
            continue
        root_path = item.get("root")
        tpl_path = item.get("template")
        if isinstance(root_path, str) and isinstance(tpl_path, str):
            valid.append({"root": root_path, "template": tpl_path})
    if not valid:
        raise ValueError(f"{check_id}: pairs must contain at least one root/template mapping")
    return valid


# ---------------------------------------------------------------------------
# Workflow action pin checks
# ---------------------------------------------------------------------------


def _extract_workflow_actions(text: str) -> dict[str, set[str]]:
    """Extract GitHub Actions and their versions from workflow YAML text.

    Args:
        text: Workflow file contents containing ``uses:`` directives.

    Returns:
        A dict mapping action names (e.g., ``actions/checkout``) to a set of
        version/tag strings found for that action.
    """
    actions: dict[str, set[str]] = {}
    for action, version in USES_RE.findall(text):
        versions = actions.setdefault(action, set())
        versions.add(version.strip())
    return actions


def _workflow_pair_violations(
    check_id: str, pair: dict[str, str], repo_root: Path
) -> list[Violation]:
    """Check if root and template workflows use the same action versions.

    Args:
        check_id: Identifier for violation reporting.
        pair: Dict with ``root`` and ``template`` file paths to compare.
        repo_root: Repository root for resolving relative paths.

    Returns:
        List of violations (empty if workflows match on shared actions).
    """
    root_path = repo_root / pair["root"]
    tpl_path = repo_root / pair["template"]
    if not root_path.is_file():
        return [Violation(check_id, f"missing file: {pair['root']}")]
    if not tpl_path.is_file():
        return [Violation(check_id, f"missing file: {pair['template']}")]

    root_actions = _extract_workflow_actions(_read_text(root_path))
    tpl_actions = _extract_workflow_actions(_read_text(tpl_path))
    shared = sorted(set(root_actions).intersection(tpl_actions))
    if not shared:
        return [
            Violation(
                check_id,
                f"{pair['root']} <-> {pair['template']}: no shared actions to compare",
            )
        ]

    violations: list[Violation] = []
    for action in shared:
        if root_actions[action] == tpl_actions[action]:
            continue
        violations.append(
            Violation(
                check_id,
                (
                    f"{pair['root']} <-> {pair['template']}: action {action} mismatch "
                    f"(root={sorted(root_actions[action])}, template={sorted(tpl_actions[action])})"
                ),
            )
        )
    return violations


def _check_workflow_action_versions(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Run workflow action version checks on all pairs in the check configuration.

    Args:
        check: Check configuration dict with ``id`` and ``pairs`` keys.
        repo_root: Repository root for resolving file paths.

    Returns:
        List of violations across all pairs.
    """
    check_id = str(check.get("id", "workflow_action_versions"))
    pairs = _validate_pairs_object(check_id, check.get("pairs"))
    violations: list[Violation] = []
    for pair in pairs:
        violations.extend(_workflow_pair_violations(check_id, pair, repo_root))
    return violations


# ---------------------------------------------------------------------------
# Exact file pair checks
# ---------------------------------------------------------------------------


def _normalize_for_exact_compare(text: str) -> str:
    r"""Normalize line endings to LF for consistent text comparison.

    Args:
        text: Text with potentially mixed line endings (CRLF or LF).

    Returns:
        Text with all line endings normalized to LF (\n).
    """
    return text.replace("\r\n", "\n")


def _short_diff(left: str, right: str, *, max_lines: int = 12) -> str:
    """Produce a short unified diff summary for violation reporting.

    Args:
        left: Left-side text (root file).
        right: Right-side text (template file).
        max_lines: Maximum number of diff lines to include in summary.

    Returns:
        A pipe-separated single-line summary of diff lines, or "content differs"
        if no specific lines are different.
    """
    lines = list(
        difflib.unified_diff(
            left.splitlines(),
            right.splitlines(),
            fromfile="root",
            tofile="template",
            lineterm="",
        )
    )
    if not lines:
        return "content differs"
    return " | ".join(lines[:max_lines])


def _check_exact_file_pairs(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Compare root and template file pairs byte-for-byte.

    Args:
        check: Check configuration dict with ``id`` and ``pairs`` keys.
        repo_root: Repository root for resolving file paths.

    Returns:
        List of violations for mismatched or missing file pairs.
    """
    check_id = str(check.get("id", "exact_file_pairs"))
    pairs = _validate_pairs_object(check_id, check.get("pairs"))
    violations: list[Violation] = []

    for pair in pairs:
        root_path = repo_root / pair["root"]
        tpl_path = repo_root / pair["template"]
        if not root_path.is_file():
            violations.append(Violation(check_id, f"missing file: {pair['root']}"))
            continue
        if not tpl_path.is_file():
            violations.append(Violation(check_id, f"missing file: {pair['template']}"))
            continue

        root_text = _normalize_for_exact_compare(_read_text(root_path))
        tpl_text = _normalize_for_exact_compare(_read_text(tpl_path))
        if root_text != tpl_text:
            diff = _short_diff(root_text, tpl_text)
            violations.append(
                Violation(
                    check_id,
                    f"{pair['root']} <-> {pair['template']}: exact mismatch ({diff})",
                )
            )
    return violations


# ---------------------------------------------------------------------------
# pyproject.toml section parity
# ---------------------------------------------------------------------------


def _strip_jinja_lines(text: str) -> str:
    """Remove Jinja2 directives and comments from text.

    Removes lines containing Jinja2 ``{%..%}`` directives and ``{#..#}``
    comments while preserving all other content.

    Args:
        text: Text potentially containing Jinja2 directives.

    Returns:
        Text with Jinja2 directives removed, preserving blank lines.
    """
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{%") and stripped.endswith("%}"):
            continue
        if stripped.startswith("{#") and stripped.endswith("#}"):
            continue
        kept.append(line)
    return "\n".join(kept) + "\n"


def _extract_section_text(text: str, section_name: str) -> str | None:
    """Extract TOML section content between headers.

    Args:
        text: TOML-formatted text containing section headers like ``[section]``.
        section_name: Name of the section to extract (without brackets).

    Returns:
        Text from the end of the section header through the start of the next
        section (or end of file), or ``None`` if the section is not found.
    """
    matches = list(SECTION_HEADER_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip() != section_name:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        return text[start:end]
    return None


def _extract_assignment_keys(section_text: str) -> set[str]:
    """Extract all assignment keys from a TOML section.

    Args:
        section_text: Text from a TOML section containing assignments like
            ``key = value``.

    Returns:
        Set of all assignment keys found in the section.
    """
    return {m.group(1).strip() for m in ASSIGNMENT_RE.finditer(section_text)}


def _extract_select_codes(section_text: str) -> set[str]:
    """Extract quoted strings from a Ruff ``select`` list.

    Args:
        section_text: TOML section text potentially containing
            ``select = ["CODE1", "CODE2", ...]``.

    Returns:
        Set of quoted code strings, or empty set if no select list is found.
    """
    select_match = re.search(
        r"^\s*select\s*=\s*\[(.*?)\]", section_text, flags=re.MULTILINE | re.DOTALL
    )
    if not select_match:
        return set()
    body = select_match.group(1)
    return {token.strip() for token in QUOTED_TOKEN_RE.findall(body)}


def _collect_pyproject_section_violations(
    check_id: str,
    sections: list[Any],
    root_text: str,
    template_text: str,
) -> list[Violation]:
    """Check all configured TOML sections for parity.

    Args:
        check_id: Identifier for violation reporting.
        sections: List of section configuration dicts.
        root_text: Root ``pyproject.toml`` text.
        template_text: Template ``pyproject.toml`` text (with Jinja stripped).

    Returns:
        List of violations across all sections.
    """
    violations: list[Violation] = []
    for section_def in sections:
        violations.extend(
            _pyproject_section_violations(check_id, section_def, root_text, template_text)
        )
    return violations


def _pyproject_section_violations(
    check_id: str,
    section_def: Any,
    root_text: str,
    template_text: str,
) -> list[Violation]:
    """Check a single TOML section for required keys and codes.

    Args:
        check_id: Identifier for violation reporting.
        section_def: Configuration for this section (with ``name``,
            ``required_keys``, ``required_select_codes``).
        root_text: Root ``pyproject.toml`` text.
        template_text: Template ``pyproject.toml`` text (with Jinja stripped).

    Returns:
        List of violations (empty if section passes all checks).
    """
    if not isinstance(section_def, dict):
        return [Violation(check_id, "section definition must be an object")]

    section_name = section_def.get("name")
    if not isinstance(section_name, str):
        return [Violation(check_id, "section is missing name")]

    root_section = _extract_section_text(root_text, section_name)
    template_section = _extract_section_text(template_text, section_name)
    if root_section is None:
        return [Violation(check_id, f"missing root section: [{section_name}]")]
    if template_section is None:
        return [Violation(check_id, f"missing template section: [{section_name}]")]

    violations: list[Violation] = []
    violations.extend(
        _required_key_violations(
            check_id, section_name, root_section, template_section, section_def
        )
    )
    violations.extend(
        _required_select_code_violations(
            check_id, section_name, root_section, template_section, section_def
        )
    )
    return violations


def _required_key_violations(
    check_id: str,
    section_name: str,
    root_section: str,
    template_section: str,
    section_def: dict[str, Any],
) -> list[Violation]:
    """Check if required keys are present in both sections.

    Args:
        check_id: Identifier for violation reporting.
        section_name: Name of the TOML section being checked.
        root_section: Content of the section in root ``pyproject.toml``.
        template_section: Content of the section in template ``pyproject.toml``.
        section_def: Section definition with optional ``required_keys`` list.

    Returns:
        Violations for missing keys in either root or template.
    """
    required_keys = section_def.get("required_keys", [])
    if not isinstance(required_keys, list):
        return []

    root_keys = _extract_assignment_keys(root_section)
    template_keys = _extract_assignment_keys(template_section)
    violations: list[Violation] = []
    for key in required_keys:
        if not isinstance(key, str):
            continue
        if key not in root_keys:
            violations.append(
                Violation(check_id, f"[{section_name}] missing key in root baseline: {key}")
            )
        if key not in template_keys:
            violations.append(
                Violation(check_id, f"[{section_name}] missing key in template: {key}")
            )
    return violations


def _required_select_code_violations(
    check_id: str,
    section_name: str,
    root_section: str,
    template_section: str,
    section_def: dict[str, Any],
) -> list[Violation]:
    """Check if required lint codes are present in both ``select`` lists.

    Args:
        check_id: Identifier for violation reporting.
        section_name: Name of the TOML section being checked.
        root_section: Content of the section in root ``pyproject.toml``.
        template_section: Content of the section in template ``pyproject.toml``.
        section_def: Section definition with optional ``required_select_codes`` list.

    Returns:
        Violations for missing codes in either root or template select list.
    """
    required_codes = section_def.get("required_select_codes", [])
    if not isinstance(required_codes, list):
        return []

    root_codes = _extract_select_codes(root_section)
    template_codes = _extract_select_codes(template_section)
    violations: list[Violation] = []
    for code in required_codes:
        if not isinstance(code, str):
            continue
        if code not in root_codes:
            violations.append(
                Violation(check_id, f"[{section_name}] root select list missing code: {code}")
            )
        if code not in template_codes:
            violations.append(
                Violation(check_id, f"[{section_name}] template select list missing code: {code}")
            )
    return violations


def _check_pyproject_sections(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Check TOML section parity between root and template ``pyproject.toml`` files.

    Args:
        check: Check configuration with ``root``, ``template``, and ``sections`` keys.
        repo_root: Repository root for resolving file paths.

    Returns:
        List of violations (empty if all sections match policy).
    """
    check_id = str(check.get("id", "pyproject_sections"))
    root_rel = check.get("root")
    template_rel = check.get("template")
    sections = check.get("sections")
    if (
        not isinstance(root_rel, str)
        or not isinstance(template_rel, str)
        or not isinstance(sections, list)
    ):
        raise ValueError(f"{check_id}: root/template/sections are required")

    root_path = repo_root / root_rel
    template_path = repo_root / template_rel
    if not root_path.is_file():
        return [Violation(check_id, f"missing file: {root_rel}")]
    if not template_path.is_file():
        return [Violation(check_id, f"missing file: {template_rel}")]

    root_text = _read_text(root_path)
    template_text = _strip_jinja_lines(_read_text(template_path))
    return _collect_pyproject_section_violations(check_id, sections, root_text, template_text)


# ---------------------------------------------------------------------------
# Check dispatch
# ---------------------------------------------------------------------------


def _run_check(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Dispatch a check dict to the appropriate handler.

    Args:
        check: Check configuration with a ``type`` key indicating the check function.
        repo_root: Repository root for resolving file paths.

    Returns:
        List of violations from the appropriate check handler.
    """
    check_type = check.get("type")
    if check_type == "workflow_action_versions":
        return _check_workflow_action_versions(check, repo_root)
    if check_type == "exact_file_pairs":
        return _check_exact_file_pairs(check, repo_root)
    if check_type == "pyproject_sections":
        return _check_pyproject_sections(check, repo_root)
    check_id = str(check.get("id", "unknown"))
    return [Violation(check_id, f"unsupported check type: {check_type!r}")]


def run_all_checks(mapping: dict[str, Any], repo_root: Path) -> list[Violation]:
    """Run every check in ``mapping['checks']`` and return all violations.

    Precondition: ``mapping['checks']`` is a non-empty ``list`` (validated in :func:`main`).
    """
    checks = mapping["checks"]
    violations: list[Violation] = []
    for raw_check in checks:
        if not isinstance(raw_check, dict):
            violations.append(Violation("mapping", "each check entry must be an object"))
            continue
        try:
            violations.extend(_run_check(raw_check, repo_root))
        except ValueError as exc:
            check_id = str(raw_check.get("id", "invalid-check"))
            violations.append(Violation(check_id, str(exc)))
    return violations


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the sync checker.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments with ``repo_root`` and ``map`` attributes.
    """
    parser = argparse.ArgumentParser(description="Check root/template sync policy mappings.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root containing mapped files (defaults to script parent).",
    )
    parser.add_argument(
        "--map",
        default="assets/root-template-sync-map.yaml",
        help="Mapping file path (JSON content in YAML file supported).",
    )
    return parser.parse_args(argv)


def _resolve_repo_root(arg: str | None) -> Path:
    """Resolve the repository root from a provided path or script location.

    Args:
        arg: An explicit repository root path, or ``None`` to use script parent.

    Returns:
        The resolved absolute path to the repository root.
    """
    if isinstance(arg, str) and arg:
        return Path(arg).resolve()
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    """CLI entry: load the sync map, run checks, print PASS or violations."""
    args = _parse_cli_args(argv)
    repo_root = _resolve_repo_root(args.repo_root)
    map_path = (repo_root / args.map).resolve()
    if not map_path.is_file():
        logger.error(f"mapping file not found: {map_path}")
        return 2

    try:
        mapping = _load_map(map_path)
    except ValueError as exc:
        logger.error(str(exc))
        return 2

    checks = mapping.get("checks", [])
    if not isinstance(checks, list) or not checks:
        logger.error("mapping must define a non-empty checks list")
        return 2

    violations = run_all_checks(mapping, repo_root)

    if violations:
        logger.error(f"found {len(violations)} sync violation(s)")
        for item in violations:
            logger.error(f"[{item.check_id}] {item.message}")
        return 1

    logger.info("root/template sync map checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
