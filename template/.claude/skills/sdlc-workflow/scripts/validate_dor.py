#!/usr/bin/env python3
"""Validate a task YAML file against the Definition of Ready schema."""

import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

VALID_TYPES = {"feature", "fix", "refactor", "chore", "perf", "docs"}
VALID_STATUSES = {"draft", "ready", "in-progress", "review", "done", "blocked"}


def _check_required_fields(data: dict, errors: list[str]) -> None:
    """Check required string fields."""
    for field in ("task_id", "title", "requirement"):
        value = data.get(field, "")
        if not value or not str(value).strip():
            errors.append(f"{field}: must be non-empty")


def _check_title_length(data: dict, errors: list[str]) -> None:
    """Check title does not exceed 72 characters."""
    title = data.get("title", "")
    if len(str(title)) > 72:
        errors.append(f"title: exceeds 72 characters ({len(title)})")


def _check_type_enum(data: dict, errors: list[str]) -> None:
    """Check type is valid enum value."""
    task_type = data.get("type", "")
    if task_type not in VALID_TYPES:
        errors.append(f"type: '{task_type}' not in {VALID_TYPES}")


def _check_status_enum(data: dict, errors: list[str]) -> None:
    """Check status is valid enum value."""
    status = data.get("status", "")
    if status not in VALID_STATUSES:
        errors.append(f"status: '{status}' not in {VALID_STATUSES}")


def _check_acceptance_criteria(data: dict, errors: list[str]) -> None:
    """Check acceptance criteria have required fields."""
    ac = data.get("acceptance_criteria", [])
    if not ac:
        errors.append("acceptance_criteria: must have at least 1 item")
        return

    for i, criterion in enumerate(ac):
        for key in ("id", "given", "when", "then"):
            if not criterion.get(key):
                msg = f"acceptance_criteria[{i}].{key}: must be non-empty"
                errors.append(msg)


def _check_definition_of_ready(data: dict, errors: list[str]) -> None:
    """Check all definition of ready flags are true."""
    dor = data.get("definition_of_ready", {})
    for flag, value in dor.items():
        if value is not True:
            msg = f"definition_of_ready.{flag}: must be true (got {value})"
            errors.append(msg)


def _check_dependencies(data: dict, errors: list[str]) -> None:
    """Warn about dependencies."""
    deps = data.get("depends_on", [])
    if deps:
        msg = f"depends_on: has {len(deps)} dependencies -- verify they are done"
        errors.append(msg)


def validate(path: str) -> list[str]:
    """Validate task YAML and return list of error messages."""
    errors: list[str] = []
    data = yaml.safe_load(Path(path).read_text())

    _check_required_fields(data, errors)
    _check_title_length(data, errors)
    _check_type_enum(data, errors)
    _check_status_enum(data, errors)
    _check_acceptance_criteria(data, errors)
    _check_definition_of_ready(data, errors)
    _check_dependencies(data, errors)

    return errors


def main() -> None:
    """Run validation on the given task YAML file."""
    if len(sys.argv) != 2:
        logger.error(f"Usage: {sys.argv[0]} <path/to/TASK_ID.yaml>")
        sys.exit(2)

    errors = validate(sys.argv[1])
    if errors:
        logger.error("Definition of Ready not met:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    else:
        logger.info("Definition of Ready met")
        sys.exit(0)


if __name__ == "__main__":
    main()
