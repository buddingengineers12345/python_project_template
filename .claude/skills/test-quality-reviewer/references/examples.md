# Test quality examples

Before/after code for all common issues. Use as inspiration when writing fix snippets in a review.

## Table of Contents

1. [Asserting Nothing](#1-asserting-nothing)
2. [Testing the Mock Instead of the Behavior](#2-testing-the-mock-instead-of-the-behavior)
3. [Silent Exception Swallowing](#3-silent-exception-swallowing)
4. [Magic Numbers](#4-magic-numbers)
5. [Duplicate Tests → Parametrize](#5-duplicate-tests--parametrize)
6. [Test Interdependence](#6-test-interdependence)
7. [Repeated Setup → Fixture](#7-repeated-setup--fixture)
8. [Missing Error-Path Tests](#8-missing-error-path-tests)
9. [Overly Broad `except`](#9-overly-broad-except)
10. [Assertion with `== True` / `== False` / `!= None`](#10-assertion-with--true---false---none)
11. [Floating-Point Exact Equality](#11-floating-point-exact-equality)
12. [Imports Inside Test Functions](#12-imports-inside-test-functions)
13. [assert len(x) > 0](#13-assert-lenx--0)
14. [Test Doing Too Many Things](#14-test-doing-too-many-things)
15. [Fixture Missing Teardown](#15-fixture-missing-teardown)
16. [Expensive Fixture Wrong Scope](#16-expensive-fixture-wrong-scope)
17. [`@pytest.mark.skip` Without Reason](#17-pytestmarkskip-without-reason)
18. [Asserting repr/str of Object](#18-asserting-reprstr-of-object)
19. [`assert mock.called` Instead of `assert_called_once_with`](#19-assert-mockcalled-instead-of-assert_called_once_with)
20. [Hard-coded Paths and Credentials](#20-hard-coded-paths-and-credentials)

---

## 1. Asserting Nothing

```python
# ❌ Before — test always passes regardless of behavior
def test_process_order():
    order = Order(items=["apple"])
    process(order)  # no assertion — green even if process() does nothing

# ✅ After — assert the observable result
def test_process_order_marks_as_processed():
    order = Order(items=["apple"])
    process(order)
    assert order.status == "processed"
```

---

## 2. Testing the Mock Instead of the Behavior

```python
# ❌ Before — only proves the mock was wired up
def test_send_welcome_email(mocker):
    mock_send = mocker.patch("myapp.email.send")
    register_user("alice@example.com")
    assert mock_send.called  # true even if called with wrong args

# ✅ After — verify the right arguments were used AND the state changed
def test_register_user_sends_welcome_email(mocker):
    mock_send = mocker.patch("myapp.email.send")
    register_user("alice@example.com")
    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject="Welcome to the platform!",
    )
    assert User.objects.filter(email="alice@example.com").exists()
```

---

## 3. Silent Exception Swallowing

```python
# ❌ Before — can never fail; catches the assertion too
def test_invalid_input_handled():
    try:
        parse_date("not-a-date")
    except Exception:
        pass  # swallows everything, including assert errors in the try block

# ✅ After — use pytest.raises
def test_invalid_date_raises_value_error():
    with pytest.raises(ValueError, match="invalid date format"):
        parse_date("not-a-date")

# ✅ Or, if it should return None rather than raise:
def test_invalid_date_returns_none():
    result = parse_date("not-a-date")
    assert result is None
```

---

## 4. Magic Numbers

```python
# ❌ Before — why 27.0? what does 10 and 3 represent?
def test_price_calculation():
    assert calculate_price(10, 3) == 27.0

# ✅ After — make the intent clear
def test_price_applies_10_percent_bulk_discount():
    unit_price = 10
    quantity = 3
    bulk_discount = 0.9  # 10% off for orders of 3+
    expected = unit_price * quantity * bulk_discount
    assert calculate_price(unit_price, quantity) == expected
```

---

## 5. Duplicate Tests → Parametrize

```python
# ❌ Before — three tests with identical structure
def test_is_palindrome_racecar():
    assert is_palindrome("racecar")

def test_is_palindrome_level():
    assert is_palindrome("level")

def test_is_palindrome_hello_is_false():
    assert not is_palindrome("hello")

# ✅ After
@pytest.mark.parametrize("word,expected", [
    ("racecar", True),
    ("level",   True),
    ("hello",   False),
    ("",        True),   # edge case: empty string
])
def test_is_palindrome(word, expected):
    assert is_palindrome(word) == expected
```

---

## 6. Test Interdependence

```python
# ❌ Before — test_b silently depends on test_a having run first
_shared_user = None

def test_a_create_user():
    global _shared_user
    _shared_user = create_user("alice")
    assert _shared_user.id is not None

def test_b_update_user():
    _shared_user.name = "Alice Smith"  # NoneType error if run alone
    assert _shared_user.name == "Alice Smith"

# ✅ After — each test owns its setup
@pytest.fixture
def user():
    return create_user("alice")

def test_create_user_assigns_id():
    u = create_user("alice")
    assert u.id is not None

def test_update_user_changes_name(user):
    user.name = "Alice Smith"
    assert user.name == "Alice Smith"
```

---

## 7. Repeated Setup → Fixture

```python
# ❌ Before — identical 5-line setup copy-pasted into every test
def test_checkout_empty_cart():
    db = FakeDatabase()
    cart = Cart(db=db)
    user = User(id=1, balance=100)
    assert cart.checkout(user) == {"total": 0, "items": []}

def test_checkout_applies_coupon():
    db = FakeDatabase()
    cart = Cart(db=db)
    user = User(id=1, balance=100)
    cart.add(Item(price=50))
    assert cart.checkout(user, coupon="HALF") == {"total": 25, "items": [...]}

# ✅ After
@pytest.fixture
def fake_db():
    return FakeDatabase()

@pytest.fixture
def cart(fake_db):
    return Cart(db=fake_db)

@pytest.fixture
def funded_user():
    return User(id=1, balance=100)

def test_checkout_empty_cart(cart, funded_user):
    assert cart.checkout(funded_user) == {"total": 0, "items": []}

def test_checkout_applies_coupon(cart, funded_user):
    cart.add(Item(price=50))
    assert cart.checkout(funded_user, coupon="HALF") == {"total": 25}
```

---

## 8. Missing Error-Path Tests

```python
# Source
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("cannot divide by zero")
    return a / b

# ❌ Before — only tests the happy path
def test_divide():
    assert divide(10, 2) == 5.0

# ✅ After — add the error path
def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError, match="cannot divide by zero"):
        divide(10, 0)
```

---

## 9. Overly Broad `except`

```python
# ❌ Before — catches typos and logic errors in the test itself
def test_save_user_rejects_none():
    try:
        save_user(None)
        assert False, "should have raised"
    except Exception:
        pass

# ✅ After — only catches the specific expected exception
def test_save_user_raises_for_none():
    with pytest.raises(ValueError, match="user cannot be None"):
        save_user(None)
```

---

## 10. Assertion with `== True` / `== False` / `!= None`

```python
# ❌ Before
assert is_active(user) == True
assert is_banned(user) == False
assert get_token(user) != None

# ✅ After
assert is_active(user)          # or: assert is_active(user) is True (if None-safety matters)
assert not is_banned(user)
assert get_token(user) is not None
```

---

## 11. Floating-Point Exact Equality

```python
# ❌ Before — will fail on some environments
def test_tax_calculation():
    assert calculate_tax(100, rate=0.07) == 7.0

# The problem:
>>> 0.1 + 0.2 == 0.3
False  # IEEE 754 floating point

# ✅ After — use pytest.approx (default tolerance: 1e-6 relative)
def test_tax_calculation():
    assert calculate_tax(100, rate=0.07) == pytest.approx(7.0)

# For tighter or looser tolerance:
assert result == pytest.approx(expected, rel=1e-3)   # 0.1% tolerance
assert result == pytest.approx(expected, abs=0.01)   # absolute tolerance
```

---

## 12. Imports Inside Test Functions

```python
# ❌ Before — imports scattered inside functions (common in copy-pasted tests)
def test_parse_date():
    from myapp.utils import parse_date   # re-imported every test run
    assert parse_date("2024-01-01") is not None

def test_format_date():
    from myapp.utils import format_date  # again
    assert format_date(date(2024, 1, 1)) == "January 1, 2024"

# ✅ After — imports at the top of the file
from myapp.utils import parse_date, format_date

def test_parse_date():
    assert parse_date("2024-01-01") is not None

def test_format_date():
    assert format_date(date(2024, 1, 1)) == "January 1, 2024"
```

---

## 13. `assert len(x) > 0`

```python
# ❌ Before — verbose and gives a bad failure message
assert len(results) > 0
assert len(errors) == 0

# ✅ After — cleaner and pytest's diff output is more helpful
assert results          # empty list/dict/str is falsy
assert not errors

# If you want an explicit message:
assert results, f"Expected results but got empty {type(results).__name__}"
```

---

## 14. Test Doing Too Many Things

```python
# ❌ Before — tests create AND update AND delete in one test
def test_user_lifecycle():
    user = create_user("alice")
    assert user.id is not None          # creation
    user.name = "Alice Smith"
    update_user(user)
    assert user.name == "Alice Smith"   # update
    delete_user(user.id)
    assert not User.exists(user.id)     # deletion

# ✅ After — one behavior per test (share setup via fixture)
@pytest.fixture
def alice():
    return create_user("alice")

def test_create_user_assigns_id(alice):
    assert alice.id is not None

def test_update_user_persists_name_change(alice):
    alice.name = "Alice Smith"
    update_user(alice)
    assert alice.name == "Alice Smith"

def test_delete_user_removes_from_store(alice):
    delete_user(alice.id)
    assert not User.exists(alice.id)
```

---

## 15. Fixture Missing Teardown

```python
# ❌ Before — creates a test DB but never cleans it up
@pytest.fixture
def db():
    conn = create_test_database()
    return conn  # tables and data leak into the next test

# ✅ After — use yield to guarantee cleanup
@pytest.fixture
def db():
    conn = create_test_database()
    yield conn
    conn.execute("DROP TABLE IF EXISTS users")
    conn.close()

# ✅ Alternative — use a transaction that rolls back
@pytest.fixture
def db():
    conn = create_test_database()
    conn.begin()
    yield conn
    conn.rollback()
    conn.close()
```

---

## 16. Expensive Fixture Wrong Scope

```python
# ❌ Before — starts the server once per test function (100 tests = 100 server starts)
@pytest.fixture
def app_server():  # scope defaults to "function"
    server = start_test_server()
    yield server
    server.stop()

# ✅ After — start once per session, reset state between tests
@pytest.fixture(scope="session")
def app_server():
    server = start_test_server()
    yield server
    server.stop()

@pytest.fixture(autouse=True)
def reset_server_state(app_server):
    """Reset mutable state before each test, not the server itself."""
    app_server.reset()
    yield
```

---

## 17. `@pytest.mark.skip` Without Reason

```python
# ❌ Before — silent skip; becomes permanent tech debt
@pytest.mark.skip
def test_payment_refund():
    ...

# ✅ After — document why and when to revisit
@pytest.mark.skip(reason="Stripe sandbox is down until 2024-Q2; see ticket #1234")
def test_payment_refund():
    ...

# ✅ Or use xfail for known failures you plan to fix
@pytest.mark.xfail(reason="Bug #1234: refund calculation off by 1 cent", strict=True)
def test_payment_refund():
    ...
```

---

## 18. Asserting repr/str of Object

```python
# ❌ Before — breaks whenever __repr__ changes
def test_user_display():
    user = User(name="Alice", role="admin")
    assert str(user) == "Alice (admin)"  # tightly coupled to __repr__ format

# ✅ After — assert the actual data attributes
def test_user_has_correct_name_and_role():
    user = User(name="Alice", role="admin")
    assert user.name == "Alice"
    assert user.role == "admin"

# If __repr__ behavior itself is what you're testing, that's fine — make it explicit:
def test_user_repr_includes_name_and_role():
    user = User(name="Alice", role="admin")
    user_repr = repr(user)
    assert "Alice" in user_repr
    assert "admin" in user_repr
```

---

## 19. `assert mock.called` Instead of `assert_called_once_with`

```python
# ❌ Before — passes even if called with wrong arguments or called 10 times
def test_sends_password_reset_email(mocker):
    mock_send = mocker.patch("myapp.email.send")
    request_password_reset("alice@example.com")
    assert mock_send.called  # no argument checking

# ✅ After — verify exactly what was sent
def test_sends_password_reset_email(mocker):
    mock_send = mocker.patch("myapp.email.send")
    request_password_reset("alice@example.com")
    mock_send.assert_called_once_with(
        to="alice@example.com",
        template="password_reset",
    )
```

---

## 20. Hard-coded Paths and Credentials

```python
# ❌ Before — only works on one machine, leaks credentials
def test_load_config():
    config = load_config("/home/devuser/project/config.yml")
    assert config["debug"] is True

def test_db_connection():
    conn = connect(host="localhost", password="devpassword123")
    assert conn.ping()

# ✅ After — use tmp_path, env vars, or test fixtures
def test_load_config(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text("debug: true\n")
    config = load_config(str(config_file))
    assert config["debug"] is True

def test_db_connection(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "testpassword")
    conn = connect_from_env()
    assert conn.ping()
```
