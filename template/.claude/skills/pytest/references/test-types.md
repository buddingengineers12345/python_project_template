# Test types

Different tests serve different purposes and have different constraints. Understanding
the testing pyramid helps you decide what kind of test to write and how to structure it.

## Table of contents

- [The testing pyramid](#the-testing-pyramid)
- [Unit tests](#unit-tests)
- [Integration tests](#integration-tests)
- [Functional and API tests](#functional-and-api-tests)
- [End-to-end tests](#end-to-end-tests)
- [Choosing the right test type](#choosing-the-right-test-type)

---

## The testing pyramid

The pyramid is a guideline for the ratio of test types in a healthy suite:

```
        /  E2E  \          Few — slow, expensive, high confidence
       /----------\
      / Functional \       Some — moderate speed, real interactions
     /--------------\
    /  Integration   \     More — exercise component boundaries
   /------------------\
  /      Unit          \   Most — fast, isolated, focused
 /______________________\
```

Most tests should be unit tests (fast, cheap, isolated). Integration and functional
tests add confidence that components work together. E2E tests are the most expensive
and should be few.

## Unit tests

Unit tests verify a single function, method, or class in isolation. They should not
touch the filesystem, network, database, or any external system.

**Characteristics:**

- Fast — milliseconds per test.
- Deterministic — same result every time, regardless of environment.
- Isolated — mock or stub all external dependencies.
- Focused — one behaviour per test.

```python
# Unit test: pure logic, no I/O
def test_calculate_discount_for_premium_tier():
    discount = calculate_discount(price=100.0, tier="premium")
    assert discount == 10.0

def test_calculate_discount_for_standard_tier():
    discount = calculate_discount(price=100.0, tier="standard")
    assert discount == 0.0

def test_calculate_discount_rejects_negative_price():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_discount(price=-50.0, tier="premium")
```

**When the unit touches I/O**, mock the boundary:

```python
def test_fetches_user_profile(mocker):
    mocker.patch("myapp.api.http_get", return_value={"name": "Alice"})
    profile = fetch_user_profile(user_id=42)
    assert profile.name == "Alice"
```

**Organise** unit tests to mirror the source layout:

```
src/myapp/orders.py     →  tests/test_orders.py
src/myapp/auth/login.py →  tests/auth/test_login.py
```

## Integration tests

Integration tests verify that two or more components work together correctly. They
exercise real boundaries: database queries, file I/O, inter-module communication.

**Characteristics:**

- Slower than unit tests (seconds per test).
- May require setup (databases, temp files, services).
- Fewer mocks — the point is to test real interactions.
- Still isolated from the external world where possible (test DB, temp dirs).

```python
# Integration test: real database interaction
@pytest.fixture()
def db_session(test_database):
    session = test_database.create_session()
    yield session
    session.rollback()

def test_creates_and_retrieves_user(db_session):
    repo = UserRepository(db_session)
    repo.create(User(name="Alice", email="alice@example.com"))

    found = repo.find_by_email("alice@example.com")
    assert found is not None
    assert found.name == "Alice"
```

```python
# Integration test: filesystem interaction
def test_exports_report_to_csv(tmp_path):
    output = tmp_path / "report.csv"
    data = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 87}]

    export_csv(data, output)

    lines = output.read_text().splitlines()
    assert lines[0] == "name,score"
    assert len(lines) == 3  # header + 2 data rows
```

**Separating from unit tests:** either use directory structure (`tests/unit/`,
`tests/integration/`) or markers (`@pytest.mark.integration`) so you can run them
separately.

## Functional and API tests

Functional tests verify higher-level features or API contracts. They test from the
perspective of a consumer (API caller, CLI user) rather than internal implementation.

```python
# API/functional test: test the HTTP endpoint
def test_create_user_endpoint(test_client):
    response = test_client.post("/api/users", json={
        "name": "Alice",
        "email": "alice@example.com",
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"
    assert "id" in response.json()

def test_create_user_rejects_duplicate_email(test_client, existing_user):
    response = test_client.post("/api/users", json={
        "name": "Bob",
        "email": existing_user.email,
    })
    assert response.status_code == 409
```

```python
# CLI functional test
def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])
    assert "1.0.0" in capsys.readouterr().out
```

These tests are valuable because they catch integration issues that unit tests miss
(routing, serialisation, middleware, error handling).

## End-to-end tests

E2E tests simulate a complete user workflow from start to finish. They exercise the
entire stack — application, database, external services (or realistic fakes).

**Characteristics:**

- Slowest test type (seconds to minutes per test).
- Most realistic — closest to actual user experience.
- Most brittle — sensitive to environment, timing, UI changes.
- Require the most infrastructure setup.

```python
@pytest.mark.e2e
@pytest.mark.slow
def test_user_signup_to_first_order(live_app, browser):
    # Sign up
    browser.get(f"{live_app.url}/signup")
    browser.fill("name", "Alice")
    browser.fill("email", "alice@example.com")
    browser.click("Create Account")
    assert browser.text_contains("Welcome, Alice")

    # Place an order
    browser.get(f"{live_app.url}/products")
    browser.click("Add to Cart")
    browser.click("Checkout")
    assert browser.text_contains("Order confirmed")
```

Mark E2E tests with `@pytest.mark.slow` or `@pytest.mark.e2e` so they can be excluded
from fast CI runs.

## Choosing the right test type

| Question                                         | Test type       |
|--------------------------------------------------|-----------------|
| Does it test pure logic with no I/O?             | Unit            |
| Does it verify two modules talking to each other?| Integration     |
| Does it test an API contract or CLI interface?   | Functional      |
| Does it simulate a full user workflow?           | E2E             |
| Is the dependency easy to mock?                  | Unit (with mock) |
| Is the dependency the thing being tested?        | Integration     |

When in doubt, write a unit test first. Add an integration test when the boundary
behaviour is complex or has failed before. Add E2E tests only for critical user paths.
