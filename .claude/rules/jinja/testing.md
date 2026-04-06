# Jinja2 Template Testing

# applies-to: **/*.jinja

> This file extends [common/testing.md](../common/testing.md) with Jinja2-specific content.

## What to test

Every Jinja2 template change requires a corresponding test in `tests/test_template.py`.
Tests render the template with `copier copy` and assert on the output.

Scenarios to cover for each template file:

1. **Default values** — render with `--defaults` and assert the file exists with
   expected content.
2. **Boolean feature flags** — render with each combination of `include_*` flags that
   affects the template and assert the relevant sections are present or absent.
3. **Variable substitution** — render with non-default values (e.g. a custom
   `project_name`) and assert the value appears correctly in the output.
4. **Whitespace correctness** — spot-check that blank lines are not spuriously added or
   removed by whitespace-control tags.

## Test utilities

Tests use the `copier` Python API directly (not the CLI) for reliability:

```python
from copier import run_copy

def test_renders_with_pandas(tmp_path):
    run_copy(
        src_path=str(ROOT),
        dst_path=str(tmp_path),
        data={"include_pandas_support": True},
        defaults=True,
        overwrite=True,
        unsafe=True,
        vcs_ref="HEAD",
    )
    pyproject = (tmp_path / "pyproject.toml").read_text()
    assert "pandas" in pyproject
```

The `ROOT` constant points to the repository root. Use the `tmp_path` fixture for the
destination directory so pytest cleans it up automatically.

## Syntax validation

The `post-edit-jinja.sh` PostToolUse hook validates Jinja2 syntax automatically after
every `.jinja` file edit in a Claude Code session:

```
┌─ Jinja2 syntax check: template/pyproject.toml.jinja
│  ✓ Jinja2 syntax OK
└─ Done
```

If the hook reports a syntax error, fix it before running tests — `copier copy` will
fail with a less helpful error message if template syntax is broken.

## Manual rendering for inspection

Render the full template to inspect a complex template change:

```bash
copier copy . /tmp/test-output --trust --defaults --vcs-ref HEAD
```

Inspect specific files:

```bash
cat /tmp/test-output/pyproject.toml
cat /tmp/test-output/src/my_library/__init__.py
```

Clean up:

```bash
rm -rf /tmp/test-output
```

## Update testing

Test `copier update` scenarios when changing `_skip_if_exists` or the `.copier-answers.yml`
template. The `tests/test_template.py` file includes update scenario tests; add new ones
when you add new `_skip_if_exists` entries.

## Coverage for template branches

Aim to cover every `{% if %}` branch in every template file with at least one test.
Untested branches can produce invalid code in generated projects.
