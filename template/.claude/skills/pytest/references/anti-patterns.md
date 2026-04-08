# Anti-patterns and fixes

This document catalogues common pytest anti-patterns, explains why they cause problems,
and shows the fix. Use it as a checklist when reviewing test code.

## Table of contents

- [Interdependent tests](#interdependent-tests)
- [Shared mutable state](#shared-mutable-state)
- [Over-mocking](#over-mocking)
- [Testing implementation details](#testing-implementation-details)
- [Flaky tests](#flaky-tests)
- [Giant test functions](#giant-test-functions)
- [Ignoring test output](#ignoring-test-output)
- [Hardcoded paths and values](#hardcoded-paths-and-values)
- [Catch-all exception handling in tests](#catch-all-exception-handling-in-tests)

---

## Interdependent tests

**Problem:** Test B relies on Test A running first to create data.

```python
# Bad: test_delete depends on test_create running first
def test_create_user():
    create_user("Bob")
    assert "Bob" in get_all_users()

def test_delete_user():
    delete_user("Bob")        # fails if test_create didn't run first
    assert "Bob" not in get_all_users()
```

**Why it breaks:** Tests may run in any order (especially under `pytest-xdist`). The
dependency is invisible — nothing in `test_delete_user` says it needs `test_create_user`.

**Fix:** Use fixtures for setup. Each test manages its own preconditions.

```python
@pytest.fixture()
def existing_user(db_session):
    user = create_user("Bob")
    yield user
    delete_user("Bob")  # cleanup

def test_delete_user(existing_user):
    delete_user(existing_user.name)
    assert existing_user.name not in get_all_users()
```

## Shared mutable state

**Problem:** Tests modify a module-level variable, dict, or object.

```python
# Bad: tests share a mutable list
_events = []

def test_emits_event():
    emit("click")
    assert "click" in _events

def test_starts_empty():
    assert len(_events) == 0  # fails if test_emits_event ran first
```

**Fix:** Use a fixture that provides fresh state.

```python
@pytest.fixture()
def events():
    return []

def test_emits_event(events, monkeypatch):
    monkeypatch.setattr("myapp.events._events", events)
    emit("click")
    assert "click" in events
```

Or use `autouse` to reset the state:

```python
@pytest.fixture(autouse=True)
def reset_events():
    _events.clear()
    yield
    _events.clear()
```

## Over-mocking

**Problem:** So many things are mocked that the test proves nothing about real behaviour.

```python
# Bad: mocking the thing being tested
def test_process_order(mocker):
    mocker.patch("myapp.orders.validate_order", return_value=True)
    mocker.patch("myapp.orders.calculate_total", return_value=100)
    mocker.patch("myapp.orders.charge_payment", return_value=True)
    mocker.patch("myapp.orders.send_confirmation")

    result = process_order(order_id=1)
    assert result is True  # of course it is — everything is mocked!
```

**Fix:** Only mock external boundaries. Let internal logic run for real.

```python
def test_process_order(mocker, sample_order):
    # Mock only the external payment gateway
    mocker.patch("myapp.payments.gateway.charge", return_value=ChargeResult(ok=True))
    mocker.patch("myapp.email.send")

    result = process_order(sample_order)

    assert result.status == "confirmed"
    assert result.total == sample_order.expected_total  # real calculation
```

## Testing implementation details

**Problem:** The test asserts on private attributes, internal method calls, or
intermediate state rather than observable output.

```python
# Bad: testing how, not what
def test_caching(mocker):
    spy = mocker.spy(myapp.cache, "_write_to_disk")
    get_data(key="x")
    get_data(key="x")  # should hit cache
    assert spy.call_count == 1  # fragile — tied to caching mechanism
```

**Fix:** Assert on the observable effect of caching.

```python
def test_caching_returns_same_result():
    first = get_data(key="x")
    second = get_data(key="x")
    assert first == second

def test_caching_is_faster_on_second_call():
    get_data(key="x")  # warm the cache
    start = time.monotonic()
    get_data(key="x")
    elapsed = time.monotonic() - start
    assert elapsed < 0.01  # should be near-instant from cache
```

## Flaky tests

**Problem:** A test sometimes passes and sometimes fails without any code change.

**Common causes and fixes:**

| Cause                          | Fix                                                |
|--------------------------------|----------------------------------------------------|
| Shared state between tests     | Use fixtures for isolation                         |
| Time-dependent logic           | Use `freezegun` or mock `datetime.now()`           |
| Random ordering                | Ensure tests are order-independent                 |
| Network calls                  | Mock HTTP calls or use `responses`/`httpx_mock`    |
| Race conditions                | Avoid `time.sleep()` — use events or polling       |
| Floating-point comparisons     | Use `pytest.approx()`                              |
| File system timing             | Use `tmp_path`, not shared directories             |

**Temporary mitigation** while investigating:

```python
@pytest.mark.xfail(strict=False, reason="Flaky — investigating #456")
def test_sometimes_fails():
    ...
```

Do not leave `xfail` markers indefinitely. Track them as issues and fix the root cause.

**Using pytest-rerunfailures** as a last resort:

```bash
pytest --reruns 3 --reruns-delay 1
```

This retries failed tests up to 3 times. It masks the problem — use it only in CI while
the root cause is being investigated.

## Giant test functions

**Problem:** A single test is 50+ lines with multiple actions and assertions.

```python
# Bad: doing too much in one test
def test_entire_checkout_flow():
    user = create_user()
    cart = create_cart(user)
    cart.add_item(product_a)
    cart.add_item(product_b)
    assert len(cart.items) == 2
    total = cart.calculate_total()
    assert total == 250
    payment = charge(user, total)
    assert payment.success
    order = create_order(cart, payment)
    assert order.status == "confirmed"
    email = get_last_email(user)
    assert "confirmed" in email.subject
```

**Fix:** Split into focused tests. Each tests one behaviour.

```python
def test_cart_tracks_added_items(empty_cart, product_a, product_b):
    empty_cart.add_item(product_a)
    empty_cart.add_item(product_b)
    assert len(empty_cart.items) == 2

def test_cart_calculates_correct_total(cart_with_items):
    assert cart_with_items.calculate_total() == 250

def test_successful_payment_creates_confirmed_order(paid_cart):
    order = create_order(paid_cart)
    assert order.status == "confirmed"
```

## Hardcoded paths and values

**Problem:** Tests use hardcoded file paths or magic numbers.

```python
# Bad: hardcoded path, breaks on other machines
def test_reads_config():
    config = load("/Users/alice/project/test_config.json")
    assert config["debug"] is True
```

**Fix:** Use `tmp_path` and create test data within the test.

```python
def test_reads_config(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"debug": true}')

    config = load(config_file)
    assert config["debug"] is True
```

## Catch-all exception handling in tests

**Problem:** Using try/except in tests to "handle" expected errors.

```python
# Bad: hides the actual error
def test_processes_data():
    try:
        result = process(bad_input)
        assert False, "should have raised"
    except Exception:
        pass  # "it raised, so it works" — but which exception?
```

**Fix:** Use `pytest.raises` to assert on the specific exception.

```python
def test_rejects_bad_input():
    with pytest.raises(ValueError, match="invalid format"):
        process(bad_input)
```

This is both more precise (asserts the *right* exception) and more readable.
