# CI and test command detection

Read this file at Stage 0 if the project's test/CI commands are unknown.

## Detection order

Run these checks in order and stop at the first match.

### Test command

```bash
# 1. justfile
[ -f justfile ] && grep -q "^test:" justfile && echo "just test"

# 2. Makefile
[ -f Makefile ] && grep -q "^test:" Makefile && echo "make test"

# 3. tox
[ -f tox.ini ] && echo "tox"

# 4. nox
[ -f noxfile.py ] && echo "nox -s tests"

# 5. pyproject with uv / hatch
[ -f pyproject.toml ] && grep -q '\[tool\.hatch' pyproject.toml && echo "hatch run test"
[ -f pyproject.toml ] && grep -q '\[tool\.uv' pyproject.toml && echo "uv run pytest"

# 6. bare pytest (always available as final fallback)
echo "python -m pytest"
```

### CI command

```bash
# 1. justfile
[ -f justfile ] && grep -q "^ci:" justfile && echo "just ci"

# 2. Makefile
[ -f Makefile ] && grep -q "^ci:" Makefile && echo "make ci"

# 3. tox with multiple envs (lint + test)
[ -f tox.ini ] && echo "tox"

# 4. nox default
[ -f noxfile.py ] && echo "nox"

# 5. Compose: run lint + test manually
echo "ruff check . && python -m pytest"
```

## Reporting to the user

Once detected, state:
> "I'll use `<test-command>` to run tests and `<ci-command>` for full CI."

If neither `just` nor `make` exists and there's no tox/nox config, fall back to:
- Test: `python -m pytest -v`
- CI: `ruff check . && mypy . && python -m pytest`

Let the user confirm or override.
