# Review checklist

> Load this file for Deep mode reviews, thorough audits, or when uncertain about
> specific sub-checks in any category. All checklist items assume Python 3.11
> unless marked with a version note.

---

## Table of Contents
1.  Security
2.  Correctness & Bugs
3.  Type Safety
4.  Pythonic Style & PEP 8
5.  Design & Architecture
6.  Error Handling
7.  Testing
8.  Performance
9.  Concurrency & Async
10. Dependencies
11. Documentation
12. Framework Specifics (Django / Flask / FastAPI)
13. Data Science (Pandas / NumPy / PyTorch)

---

## 1. Security

### Injection
- [ ] SQL built with string formatting or concatenation instead of parameterised queries?
- [ ] `subprocess` called with `shell=True` and user-controlled input?
- [ ] Template injection: `render_template_string` or `jinja2.Template(user_input)`?
- [ ] `eval()`, `exec()`, or `compile()` called on user-controlled strings?

### Deserialization
- [ ] `pickle.loads()` on untrusted data? (Use JSON or sign the payload)
- [ ] `yaml.load()` without `Loader=yaml.SafeLoader`?
- [ ] `marshal`, `shelve`, or `__reduce__` used with untrusted data?

### Path Traversal
- [ ] User-controlled path not validated with `os.path.normpath()` + prefix check?
- [ ] `open(user_input)` without sanitisation?
- [ ] `send_file(user_input)` in Flask/FastAPI without `safe_join`?

### Secrets & Auth
- [ ] API keys, passwords, or tokens hardcoded in source?
- [ ] Secrets in committed config files instead of `.env` or a secrets manager?
- [ ] `MD5` or `SHA1` used for security (passwords, tokens) — not just checksums?
- [ ] `random` module used for security tokens? (Use `secrets` module)
- [ ] JWT decoded with `algorithm=None` or `options={"verify_signature": False}`?
- [ ] `hashlib.pbkdf2_hmac` with too few iterations (< 600 000 for PBKDF2-SHA256)?

### Web Security
- [ ] CSRF protection missing on state-changing endpoints?
- [ ] Cookies missing `HttpOnly` / `Secure` / `SameSite` flags?
- [ ] User input rendered in HTML without escaping?
- [ ] CORS configured as `allow_origins=["*"]` with `allow_credentials=True`?
- [ ] Rate limiting absent on authentication endpoints?

---

## 2. Correctness & Bugs

### Python-Specific Traps
- [ ] Mutable default argument: `def f(items=[])` — use `None` + guard
- [ ] Late-binding closure: `lambda: x` inside a loop captures loop variable by reference
- [ ] Integer vs float: `5 / 2 == 2.5`; use `//` if integer result intended
- [ ] `is` vs `==`: `is` for identity (None, True, False only); `==` for value equality
- [ ] String concatenation in a loop (`s += chunk`) — O(n²); use `"".join()`
- [ ] `dict.keys()` iterated while the dict is mutated
- [ ] `datetime.datetime.utcnow()` deprecated in 3.12 — prefer `datetime.now(UTC)` now

### Logic
- [ ] Off-by-one errors in slices (`[:n]` vs `[:n+1]`) or `range()`
- [ ] Incorrect boolean short-circuit assumptions
- [ ] Function that should return a value has a path that falls through to implicit `None`
- [ ] Unreachable code after `return` / `raise` / `continue` / `break`

### Data Structures
- [ ] List used for O(n) membership tests that should be a `set` (O(1))
- [ ] Modifying a list or dict while iterating it
- [ ] Shallow copy (`list.copy()`, `dict.copy()`) where deep copy is needed
- [ ] `collections.defaultdict` or `Counter` would simplify the pattern

---

## 3. Type Safety (Python 3.11)

- [ ] Use `X | Y` union syntax (3.10+) — not `Union[X, Y]` or `Optional[X]`
- [ ] Use `Self` (from `typing`) for methods that return the instance type
- [ ] Use `Never` for functions that always raise or never return
- [ ] Use `TypeVarTuple` / `Unpack` for variadic generics
- [ ] `LiteralString` used for SQL/shell strings built from user input (3.11)
- [ ] Public functions missing parameter and return type annotations
- [ ] `Any` used where a more specific type is knowable
- [ ] `Optional` result used at callsite without a `None` check
- [ ] `cast()` used to silence mypy rather than fix a real type inconsistency
- [ ] `# type: ignore` without an explanatory comment — is it justified?
- [ ] `isinstance()` used for runtime checks (correct); `type(x) ==` avoided
- [ ] `dataclass`, `TypedDict`, or Pydantic `BaseModel` used for structured data
- [ ] `@overload` used where the return type depends on argument type

---

## 4. Pythonic Style & PEP 8

### Naming
- [ ] `snake_case` for functions and variables
- [ ] `PascalCase` for classes
- [ ] `UPPER_CASE` for module-level constants
- [ ] No single-letter names outside comprehensions, lambdas, or mathematical code
- [ ] No `l`, `O`, or `I` as variable names (ambiguous with `1`, `0`, `1`)

### Modern Python 3.11 Idioms
- [ ] `match`/`case` used for structural dispatch instead of long `if`/`elif` chains (3.10+)
- [ ] `tomllib` (stdlib 3.11) instead of third-party `toml` / `tomli` packages
- [ ] `datetime.now(timezone.utc)` instead of deprecated `utcnow()`
- [ ] `StrEnum` (3.11) for string-valued enums instead of `(str, Enum)`
- [ ] `ExceptionGroup` and `except*` for concurrent/multi-error handling (3.11)
- [ ] `typing.assert_never()` in exhaustive `match` branches to catch missing cases

### General Idioms
- [ ] `if x is None:` not `if x == None:`
- [ ] `if not items:` not `if len(items) == 0:`
- [ ] f-strings for interpolation (not `.format()` or `%`)
- [ ] `with open(...) as f:` — not manual `f.open()` / `f.close()`
- [ ] `enumerate()` instead of `range(len(...))`
- [ ] `zip()` to iterate parallel sequences; `zip(..., strict=True)` (3.10+) to catch length mismatches
- [ ] `pathlib.Path` over `os.path` string manipulation
- [ ] `_` for unused loop variables: `for _ in range(n):`
- [ ] `dict | other` for merging dicts (3.9+) over `{**a, **b}`

### Code Style
- [ ] 2 blank lines around top-level definitions; 1 blank line between methods
- [ ] Imports: stdlib → third-party → local; one import per line
- [ ] No wildcard imports (`from module import *`) except deliberate `__init__.py` re-exports
- [ ] No semicolons combining multiple statements on one line

---

## 5. Design & Architecture

### Functions
- [ ] Single responsibility — does each function do exactly one thing?
- [ ] Functions > 30 lines — consider splitting
- [ ] > 3–4 parameters without a dataclass/config object grouping them
- [ ] Boolean flag parameter that switches behaviour — consider two separate functions
- [ ] Deep nesting (> 3 levels) — can guard clauses / early returns flatten this?
- [ ] Side effects (I/O, mutation) mixed with pure computation in the same function

### Classes
- [ ] Is a class actually needed, or would module-level functions suffice?
- [ ] `__init__` doing expensive work (I/O, network) — consider a factory `@classmethod`
- [ ] Missing `__repr__` on data-holding classes
- [ ] Inheritance used where composition would be simpler and more explicit
- [ ] `@dataclass` / `NamedTuple` / Pydantic model for data-only classes
- [ ] `__slots__` considered for high-volume small objects

### Modules
- [ ] Circular imports (A imports B imports A)?
- [ ] Magic numbers that should be named constants
- [ ] Configuration logic mixed with business logic — separate them
- [ ] God module (> 500 lines doing several unrelated things)?
- [ ] Missing `__all__` on a public module (controls what `import *` exposes)

---

## 6. Error Handling

- [ ] Bare `except:` catches `KeyboardInterrupt`, `SystemExit` — always name the exception
- [ ] `except Exception: pass` silently swallowing errors
- [ ] Original exception lost: `raise RuntimeError(...)` inside except — use `raise X from e`
- [ ] `try` block too wide — wrapping code that cannot realistically raise the caught exception
- [ ] Resource leak: `open()`, DB connection, socket not in a `with` block
- [ ] Custom exceptions inheriting from a semantically appropriate base
  (`ValueError`, `RuntimeError`, `OSError`, etc.)
- [ ] `logger.exception()` used (not `logger.error()`) to preserve traceback in except blocks
- [ ] `ExceptionGroup` used where multiple concurrent errors can occur together (3.11)
- [ ] `except*` used to handle specific exception types within an `ExceptionGroup` (3.11)

---

## 7. Testing

- [ ] New public functions / classes covered by at least one test?
- [ ] Edge cases: empty input, `None`, zero, negative, max/min values, empty collections
- [ ] Tests assert behaviour (not just "no exception raised")
- [ ] Mock / patch targets the right import path:
      `mymodule.requests.get`, not `requests.get`
- [ ] No real I/O (filesystem, network, DB) in unit tests — mock or use fixtures
- [ ] Tests are isolated: no shared mutable state, no execution-order dependency
- [ ] `@pytest.mark.parametrize` used for repeated cases instead of copy-paste tests
- [ ] Fixtures reused via `conftest.py` instead of duplicated `setUp`-style code
- [ ] Line coverage ≠ branch coverage ≠ behaviour coverage — check what is actually asserted
- [ ] `pytest-asyncio` used correctly for async tests

---

## 8. Performance

> Flag only for hot paths, loops over large data, or when explicitly requested.

- [ ] N+1 query: related objects fetched inside a loop — use `select_related` / `prefetch_related`
- [ ] Expensive value re-computed inside a loop that could be hoisted before the loop
- [ ] String concatenation in a loop — use `"".join()`
- [ ] Reading an entire large file into memory — consider streaming / chunking
- [ ] `for i in range(len(items)):` — use `enumerate` or iterate directly
- [ ] Unnecessary object creation in a tight inner loop

---

## 9. Concurrency & Async

- [ ] Blocking I/O (`requests.get`, `time.sleep`) inside `async def` — use async alternatives
- [ ] `asyncio.create_task()` result not stored — uncaught exceptions silently discarded
- [ ] `asyncio.sleep(0)` missing to yield control in CPU-bound `async` loops
- [ ] Shared mutable state accessed from multiple threads without a lock
- [ ] `threading.Thread` missing `daemon=True` or `join()` — may hang on exit
- [ ] Race condition in `if not exists: create` — use atomic DB operations or a lock
- [ ] `asyncio.TaskGroup` (3.11) preferred over `asyncio.gather()` for structured concurrency
- [ ] `timeout` parameter on `asyncio.wait_for()` to prevent hung tasks

---

## 10. Dependencies

- [ ] New dependency not added to `pyproject.toml` / `requirements.txt`?
- [ ] Production deps pinned to an exact version or a narrow range?
- [ ] Known vulnerability in the pinned version (check PyPI Security Advisories)?
- [ ] Heavy library imported for a trivial use that stdlib could handle?
- [ ] `tomllib` (stdlib 3.11) replaces the need for `tomli` or `toml` packages

---

## 11. Documentation

- [ ] Public functions and classes have docstrings?
- [ ] Docstring style consistent with the project (Google / NumPy / reStructuredText)?
- [ ] Non-obvious logic has a comment explaining *why*, not just *what*
- [ ] Module-level docstring states the module's purpose?
- [ ] TODOs tracked in an issue, not left indefinitely in code
- [ ] `CHANGELOG.md` / `README.md` updated for user-visible interface changes?
- [ ] Deprecation warnings (`warnings.warn(..., DeprecationWarning)`) added for removed APIs?

---

## 12. Framework Specifics

### Django
- [ ] Raw SQL in `cursor.execute()` using string formatting?
- [ ] `request.POST` / `request.GET` used without form or serializer validation?
- [ ] Views missing `@login_required` or `permission_classes`?
- [ ] Queryset accesses related object in a loop without `select_related`/`prefetch_related`?
- [ ] `null=True` on a `CharField` — use `blank=True`; empty string is the Django convention
- [ ] `SECRET_KEY` or `DEBUG=True` committed to source?
- [ ] Django signals used where an explicit service-layer call would be clearer?

### Flask
- [ ] `app.secret_key` hardcoded in source?
- [ ] `render_template_string` called with unsanitised user input?
- [ ] `DEBUG=True` in a production config file?
- [ ] Missing `abort(403)` / `abort(404)` where appropriate?

### FastAPI
- [ ] Request/response bodies use Pydantic `BaseModel`, not raw `dict`?
- [ ] `response_model` specified on all endpoints?
- [ ] Blocking code inside `async def` endpoints?
  (Use `def` route handlers or `run_in_executor` for sync I/O)
- [ ] Dependencies injected via `Depends()`, not via global state?
- [ ] `Annotated[X, Depends(...)]` pattern (modern FastAPI style) used?

---

## 13. Data Science (Pandas / NumPy / PyTorch)

### Pandas
- [ ] Chained indexing `df[col][row]` — use `df.loc[row, col]`
- [ ] `.iterrows()` for something that can be vectorised?
- [ ] `inplace=True` — prefer explicit reassignment (`df = df.dropna()`)
- [ ] Reading a large CSV fully into memory — consider chunking or Polars

### NumPy
- [ ] Python loop where vectorised NumPy operations would work?
- [ ] Unnecessary copy (`np.copy()`) where a view suffices?
- [ ] Broadcasting assumptions not documented with a comment?

### PyTorch
- [ ] `model.eval()` and `torch.no_grad()` missing during inference?
- [ ] Tensors not moved to the same device before operations?
- [ ] No random seed set for reproducibility (`torch.manual_seed`, `numpy.random.seed`)?
- [ ] `print()` debugging statements left in notebook or training script?
- [ ] Data loading/preprocessing logic mixed with model logic — consider a `Dataset` class?
