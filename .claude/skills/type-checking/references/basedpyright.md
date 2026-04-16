# basedpyright

basedpyright is a community fork of pyright (Microsoft's static type checker for Python).
It adds stricter defaults, clearer error messages, and additional rules over vanilla pyright.

---

## What it does

- Performs static type analysis — no code is executed
- Checks annotations, inferred types, call signatures, narrowing, exhaustiveness, and more
- Reads `[tool.basedpyright]` from `pyproject.toml`

---

## Installation

```bash
pip install basedpyright     # or: uv add --dev basedpyright
```

Verify:
```bash
basedpyright --version
```

---

## pyproject.toml config (annotated)

```toml
[tool.basedpyright]
# Python version used for type checking (e.g. affects which stdlib types are available).
pythonVersion = "3.11"

# First-party source directories. Only these paths are type-checked.
include = ["src"]

# Paths excluded from analysis.
exclude = ["**/__pycache__", ".venv", "build", "dist"]

# Virtual environment resolution.
# venvPath = the DIRECTORY that contains your venv folder (usually the project root).
# venv      = the NAME of the venv folder inside venvPath.
# Together they tell basedpyright where to find installed third-party packages.
# Example: venvPath = "." and venv = ".venv" resolves to ./.venv
venvPath = "."
venv = ".venv"

# ── Strictness level ────────────────────────────────────────────────────────
# Options: "off" | "basic" | "standard" | "strict" | "all"
# Recommendation: start at "standard", move to "strict" once the codebase is annotated.
typeCheckingMode = "standard"

# ── Individual rule overrides ────────────────────────────────────────────────
# Each rule can be set to "none" | "information" | "warning" | "error"
# independently of typeCheckingMode. Uncomment to customise:

# reportUnknownVariableType = "error"           # flag x: Unknown
# reportUnknownMemberType = "error"             # flag unknown attribute types
# reportMissingTypeArgument = "warning"         # flag bare list, dict etc.
# reportUnusedImport = "warning"                # overlaps with ruff F401
# reportUninitializedInstanceVariable = "warning"
```

### Strictness levels explained

| Level | What it checks |
|---|---|
| `off` | Type checking disabled |
| `basic` | Only obvious errors: undefined names, wrong argument counts |
| `standard` | Full pyright checks — good default for most projects |
| `strict` | All checks; full annotation coverage required |
| `all` | basedpyright-specific extras on top of `strict` (may have false positives) |

**Recommended progression:** start at `standard`, fix all errors, then move to `strict`.
Use per-file overrides (below) to keep `strict` globally while granting exceptions for
tests or legacy modules.

---

## Per-file overrides

Relax or tighten type checking for specific directories:

```toml
[tool.basedpyright]
typeCheckingMode = "strict"

[[tool.basedpyright.executionEnvironments]]
root = "tests"
typeCheckingMode = "basic"    # test fixtures are often untyped; relax here

[[tool.basedpyright.executionEnvironments]]
root = "scripts"
typeCheckingMode = "standard"
```

For a single line, use an inline ignore (last resort — prefer fixing the root cause):

```python
result = some_untyped_library.call()  # type: ignore[no-untyped-call]
```

Always include the specific error code in `type: ignore`. Bare `# type: ignore` silences
all errors on the line and makes the intent invisible to reviewers.

---

## Common error codes and fixes

| Code | Meaning | Fix |
|---|---|---|
| `reportMissingImports` | Package not installed in the venv | Install the package; or check `venvPath`/`venv` config |
| `reportMissingTypeStubs` | Package has no type information | Install `types-<pkg>` stub; see below |
| `reportUnknownVariableType` | Type inferred as `Unknown` | Add an explicit annotation |
| `reportUnknownMemberType` | Attribute type is `Unknown` | Annotate the class attribute |
| `reportUnknownArgumentType` | Argument type cannot be inferred | Annotate the caller or the callee |
| `reportReturnType` | Return value doesn't match declared return type | Fix annotation or return value |
| `reportAttributeAccessIssue` | Attribute doesn't exist on the type | Check spelling; use `hasattr` guard |
| `reportOperatorIssue` | Operator not defined for these types | Narrow the type before the operation |
| `reportIndexIssue` | Index or key type is invalid | Ensure key type matches the container |
| `reportCallIssue` | Object is not callable | Check the type; unwrap Optional before calling |

### Handling third-party libraries without type stubs

**Option 1 — Install community stubs** (preferred when stubs exist):

```bash
pip install types-requests types-PyYAML types-python-dateutil
```

**Option 2 — Suppress missing-stubs warnings project-wide** (when no stubs exist):

```toml
[tool.basedpyright]
reportMissingTypeStubs = "none"    # or "warning" to see it without failing CI
```

**Option 3 — Suppress per import** (for one-off cases):

```python
import untyped_lib  # type: ignore[import-untyped]
```

**Option 4 — Generate a stub skeleton**:

```bash
basedpyright --createstub some_package   # writes a stub to typestubs/some_package/
```

Commit the generated stubs to the repo and add `stubPath = "typestubs"` to
`[tool.basedpyright]` so basedpyright picks them up automatically.

---

## Running basedpyright

```bash
# Check entire project (reads pyproject.toml automatically):
basedpyright

# Check a specific file:
basedpyright src/mymodule.py

# Verbose output — shows which config file was loaded, useful for debugging:
basedpyright --verbose

# JSON output — for tooling integration or counting errors:
basedpyright --outputjson | python -c "import sys,json; d=json.load(sys.stdin); print(d['summary'])"

# Count current errors (useful for tracking incremental adoption progress):
basedpyright 2>&1 | grep " error" | wc -l
```

Exit codes: `0` = no errors, `1` = type errors found, `2` = fatal configuration error.

---

## Incremental adoption strategy

For an existing codebase with many type errors, adopt in stages:

1. **`typeCheckingMode = "basic"`** — fix the small set of obvious errors first.
2. **`typeCheckingMode = "standard"`** — fix errors, use `executionEnvironments` to
   relax specific directories (tests, scripts, legacy modules) temporarily.
3. **`typeCheckingMode = "strict"`** — requires full annotation coverage across `src/`.
   Tackle module by module. Add `# type: ignore[<code>]` as a last resort.
4. **`typeCheckingMode = "all"`** — evaluate locally; some rules may be too aggressive
   for production CI. Keep at `"strict"` in CI unless all `"all"` rules are clean.

---

## CI step (GitHub Actions)

```yaml
- name: Install dependencies
  run: pip install -r requirements.txt   # basedpyright must be in here, or:
  # run: uv sync

- name: Type check with basedpyright
  run: basedpyright
```

basedpyright needs the project's dependencies installed so it can resolve third-party
imports. If it reports `reportMissingImports` on every import, the venv is not being
found — check that `venvPath` and `venv` in `pyproject.toml` match the actual venv path,
or that the CI runner has the packages on `PATH`.

---

## Pre-commit hook entry

Run as a `local` hook to use the project's installed venv:

```yaml
- repo: local
  hooks:
    - id: basedpyright
      name: basedpyright
      entry: basedpyright
      language: system         # uses basedpyright from the active venv
      types: [python]
      pass_filenames: false    # analyses the whole project, not individual files
```

Requires `basedpyright` to be installed in the active environment before committing.
In CI, install dependencies before running pre-commit (see `references/pre-commit.md`).

---

## Gotchas

- **`venvPath` vs `venv` — a common confusion.** `venvPath` is the *directory that
  contains* the venv, and `venv` is the *name of the venv folder*. For a project at
  `/my/project` with a venv at `/my/project/.venv`, set `venvPath = "."` and
  `venv = ".venv"`. Setting `venvPath = ".venv"` is wrong.
- **`reportMissingImports` on all third-party imports** usually means the venv isn't
  found. Double-check `venvPath`/`venv` config or confirm packages are installed.
- **basedpyright vs pyright.** A colleague using vanilla pyright will see nearly
  identical errors. basedpyright adds rules like `reportUnreachable`. Both tools read
  the same `[tool.basedpyright]` / `[tool.pyright]` config keys.
- **`pass_filenames: false` is required in pre-commit.** basedpyright resolves the full
  import graph across all files; giving it individual filenames breaks cross-module
  type inference.
- **`typeCheckingMode = "all"` may produce false positives.** Use `"strict"` in CI
  and evaluate `"all"` locally before committing to it.
