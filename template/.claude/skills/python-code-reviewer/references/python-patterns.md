# Python patterns

> Load this file when you need concrete before/after code examples to include
> in a finding's Fix section. All examples target Python 3.11 unless noted.

---

## Table of Contents
1. Security Anti-Patterns
2. Common Bug Patterns
3. Pythonic Idioms (3.11)
4. Type Annotation Patterns (3.11)
5. Error Handling Patterns
6. Testing Patterns
7. Async Patterns
8. Python 3.11 New Patterns

---

## 1. Security Anti-Patterns

### SQL Injection
    # CRITICAL
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)

    # Fix — parameterised query
    cursor.execute("SELECT * FROM users WHERE name = %s", (username,))
    # ORM (Django) — always safe
    User.objects.filter(name=username)

### Unsafe YAML Loading
    # CRITICAL
    import yaml
    data = yaml.load(user_input)

    # Fix
    data = yaml.safe_load(user_input)

### eval on User Input
    # CRITICAL
    result = eval(user_expression)

    # Fix — safe literal parsing only
    import ast
    result = ast.literal_eval(user_expression)

### Path Traversal
    # HIGH
    def serve_file(filename):
        return open(f"/var/www/files/{filename}").read()  # ../../../etc/passwd works

    # Fix
    import os
    BASE_DIR = "/var/www/files"

    def serve_file(filename: str) -> str:
        path = os.path.normpath(os.path.join(BASE_DIR, filename))
        if not path.startswith(BASE_DIR + os.sep):
            raise PermissionError("Path traversal attempt blocked")
        return open(path).read()

### Hardcoded Secrets
    # CRITICAL
    API_KEY = "sk-abc123"  # pragma: allowlist secret
    DB_PASSWORD = "hunter2"  # pragma: allowlist secret

    # Fix
    import os
    API_KEY = os.environ["API_KEY"]          # crash-fast if missing
    DB_PASSWORD = os.environ["DB_PASSWORD"]

### Weak Crypto / Insecure Random
    # HIGH — MD5 for passwords, predictable token generation
    import hashlib, random
    token = random.randint(100000, 999999)
    pw_hash = hashlib.md5(password.encode()).hexdigest()

    # Fix
    import secrets, bcrypt
    token = secrets.token_urlsafe(32)
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

### Unsafe Pickle
    # CRITICAL — arbitrary code execution
    import pickle
    obj = pickle.loads(user_bytes)

    # Fix — use JSON for data exchange
    import json
    obj = json.loads(user_bytes)

---

## 2. Common Bug Patterns

### Mutable Default Argument
    # HIGH
    def add_item(item, container=[]):
        container.append(item)
        return container

    # Fix
    def add_item(item: object, container: list | None = None) -> list:
        if container is None:
            container = []
        container.append(item)
        return container

### Late-Binding Closure
    # HIGH — all lambdas return 4, not 0..4
    functions = [lambda: i for i in range(5)]

    # Fix — capture value at creation time
    functions = [lambda i=i: i for i in range(5)]

### Swallowing Exceptions
    # HIGH
    try:
        risky()
    except:           # catches KeyboardInterrupt, SystemExit
        pass

    # Fix
    import logging
    try:
        risky()
    except ValueError as e:
        logging.warning("Validation failed: %s", e)
        raise

### Missing Context Manager
    # MEDIUM
    f = open("data.txt")
    data = f.read()
    f.close()         # skipped if read() raises

    # Fix
    with open("data.txt") as f:
        data = f.read()

### String Concatenation in Loop
    # MEDIUM — O(n²)
    result = ""
    for chunk in chunks:
        result += chunk

    # Fix
    result = "".join(chunks)

### Iterating While Mutating
    # HIGH
    for key in my_dict:
        if condition(key):
            del my_dict[key]   # RuntimeError

    # Fix
    my_dict = {k: v for k, v in my_dict.items() if not condition(k)}

---

## 3. Pythonic Idioms (3.11)

### None Comparisons
    # Wrong
    if x == None: ...
    if x != None: ...

    # Right
    if x is None: ...
    if x is not None: ...

### Empty Container Check
    # Verbose
    if len(items) == 0: ...

    # Pythonic
    if not items: ...

### Enumerate / Zip
    # Old style
    for i in range(len(items)):
        print(i, items[i])

    # Pythonic
    for i, item in enumerate(items):
        print(i, item)

    # Zip with length safety check (3.10+)
    for a, b in zip(list_a, list_b, strict=True):
        ...

### Dict Merge (3.9+)
    # Old
    merged = {**defaults, **overrides}

    # Modern
    merged = defaults | overrides

### Structural Pattern Matching (3.10+)
    # Verbose if/elif chain
    if command == "quit":
        quit_game()
    elif command == "go" and direction in ("north", "south"):
        go(direction)
    elif command == "pick" and item:
        pick(item)

    # match/case — clearer intent, exhaustiveness checkable
    match command.split():
        case ["quit"]:
            quit_game()
        case ["go", ("north" | "south") as direction]:
            go(direction)
        case ["pick", item]:
            pick(item)
        case _:
            print(f"Unknown command: {command}")

### tomllib for TOML (3.11 stdlib)
    # Old — required third-party package
    import toml
    config = toml.load("config.toml")

    # Modern — stdlib, no dependency needed
    import tomllib
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

### StrEnum (3.11)
    # Old verbose pattern
    from enum import Enum
    class Color(str, Enum):
        RED = "red"
        GREEN = "green"

    # Modern
    from enum import StrEnum
    class Color(StrEnum):
        RED = "red"
        GREEN = "green"

### Datetime UTC (deprecation in 3.12)
    # Deprecated
    from datetime import datetime
    now = datetime.utcnow()

    # Correct — timezone-aware
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

### Pathlib
    # String-based — fragile
    import os
    path = os.path.join(base, "subdir", "file.txt")
    if os.path.exists(path):
        with open(path) as f:
            data = f.read()

    # Pathlib — composable and readable
    from pathlib import Path
    path = Path(base) / "subdir" / "file.txt"
    if path.exists():
        data = path.read_text()

---

## 4. Type Annotation Patterns (3.11)

### Union Syntax
    # Old (still valid, but verbose)
    from typing import Optional, Union
    def find(user_id: int) -> Optional[User]: ...
    def process(value: Union[int, str]) -> None: ...

    # Modern (3.10+)
    def find(user_id: int) -> User | None: ...
    def process(value: int | str) -> None: ...

### Self Return Type
    # Old — fragile with subclassing
    from typing import TypeVar
    T = TypeVar("T", bound="Builder")
    class Builder:
        def set_name(self: T, name: str) -> T: ...

    # Modern (3.11)
    from typing import Self
    class Builder:
        def set_name(self, name: str) -> Self: ...

### Never for Unreachable Code
    from typing import Never
    def assert_never(x: Never) -> Never:
        raise AssertionError(f"Unhandled value: {x}")

    # Use in exhaustive match
    match status:
        case "ok": handle_ok()
        case "error": handle_error()
        case _ as unreachable:
            assert_never(unreachable)   # mypy confirms exhaustiveness

### LiteralString for SQL Safety (3.11)
    from typing import LiteralString

    def execute(query: LiteralString) -> None:
        cursor.execute(query)

    # mypy now rejects: execute(f"SELECT * FROM {user_input}")
    # mypy accepts:     execute("SELECT * FROM users WHERE id = %s")

### TypedDict
    # Untyped
    def create_response(status: int, body: str) -> dict: ...

    # Typed
    from typing import TypedDict
    class Response(TypedDict):
        status: int
        body: str
        headers: dict[str, str]

    def create_response(status: int, body: str) -> Response: ...

---

## 5. Error Handling Patterns

### Exception Chaining
    # MEDIUM — original traceback lost
    try:
        db.connect()
    except ConnectionError:
        raise RuntimeError("Database unavailable")

    # Fix
    try:
        db.connect()
    except ConnectionError as e:
        raise RuntimeError("Database unavailable") from e

### ExceptionGroup (3.11) — Concurrent Errors
    # Multiple errors from concurrent tasks
    errors = []
    for task in tasks:
        try:
            task.run()
        except ValueError as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup("task failures", errors)

    # Handle specific types in the group
    try:
        run_all_tasks()
    except* ValueError as eg:
        for exc in eg.exceptions:
            log.warning("Validation error: %s", exc)
    except* IOError as eg:
        for exc in eg.exceptions:
            log.error("I/O error: %s", exc)

### Custom Exception Hierarchy
    # Too generic
    raise Exception("User not found")

    # Better — specific, catchable by callers
    class AppError(Exception):
        """Base for all application errors."""

    class NotFoundError(AppError):
        """Resource does not exist."""

    class ConfigError(AppError):
        """Invalid or missing configuration."""

    raise NotFoundError(f"User {user_id} not found")

---

## 6. Testing Patterns

### Correct Mock Target
    # Wrong — mocking where requests is defined
    from unittest.mock import patch
    @patch("requests.get")
    def test_fetch(mock_get): ...

    # Right — mock where it is used
    @patch("mymodule.requests.get")
    def test_fetch(mock_get): ...

### Parametrize
    # Repetitive
    def test_valid_1(): assert validate("a@b.com")
    def test_valid_2(): assert validate("x@y.org")
    def test_invalid(): assert not validate("bad")

    # Concise
    import pytest
    @pytest.mark.parametrize("email,expected", [
        ("a@b.com", True),
        ("x@y.org", True),
        ("bad",     False),
    ])
    def test_validate(email, expected):
        assert validate(email) == expected

### Async Tests
    import pytest, pytest_asyncio

    @pytest.mark.asyncio
    async def test_fetch():
        result = await fetch_data()
        assert result["status"] == "ok"

---

## 7. Async Patterns

### Blocking I/O in Async
    # HIGH — blocks the event loop
    async def fetch():
        response = requests.get(url)   # sync, blocking

    # Fix
    import httpx
    async def fetch():
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.json()

### Fire-and-Forget Bug
    # HIGH — exception from background_job() is silently discarded
    async def handler():
        asyncio.create_task(background_job())

    # Fix — store the task reference
    _background_tasks: set[asyncio.Task] = set()

    async def handler():
        task = asyncio.create_task(background_job())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

### TaskGroup (3.11) — Structured Concurrency
    # Old — gather swallows some exceptions
    results = await asyncio.gather(task1(), task2(), task3())

    # Modern — all tasks cancelled if any fails, errors surface cleanly
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(task1())
        t2 = tg.create_task(task2())
        t3 = tg.create_task(task3())
    results = [t1.result(), t2.result(), t3.result()]

### Run Blocking Sync Code in Async
    # MEDIUM — CPU-bound work blocks the event loop
    async def process():
        result = heavy_computation(data)

    # Fix
    import asyncio
    async def process():
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, heavy_computation, data)

---

## 8. Python 3.11 New Patterns

### Fine-Grained Error Locations
    # Python 3.11 tracebacks now show the exact expression that raised.
    # This means multi-expression lines like:
    result = obj.method().attr["key"]
    # will point to the specific sub-expression (e.g. .attr) not just the line.
    # Implication for review: split complex chains for better production debugging.

### tomllib (No External Dependency)
    # 3.11 ships tomllib in stdlib — remove tomli / toml from dependencies
    import tomllib
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

### StrEnum
    from enum import StrEnum, auto
    class Direction(StrEnum):
        NORTH = auto()   # value becomes "north" (lowercased name)
        SOUTH = auto()

    assert Direction.NORTH == "north"   # True — no .value needed

### TaskGroup (see Async section above)

### exception.__notes__ (3.11)
    # Attach context notes to an exception without subclassing
    try:
        process(record)
    except ValueError as e:
        e.add_note(f"Occurred while processing record id={record.id}")
        raise
