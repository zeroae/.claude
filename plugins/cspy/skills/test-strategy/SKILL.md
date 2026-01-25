---
name: test-strategy
description: Recommend test levels and strategies based on Cosmic Python TDD approach. Use when user says "where should I test", "test strategy", "high gear low gear", "TDD", "unit tests", "integration tests", or needs testing guidance.
---

# Test Level Advisor

Recommend appropriate test levels using the "High Gear / Low Gear" TDD approach from Cosmic Python.

## Test Pyramid

From bottom to top:
1. **Domain Model Tests (Unit)** - Low gear, complex logic only
2. **Service Layer Tests (Integration)** - High gear, most tests here
3. **E2E Tests** - Few, slow, brittle - only for critical paths

## High Gear vs. Low Gear

### High Gear (Service Layer Tests)
- **Speed**: Fast (use fakes, no I/O)
- **Scope**: Broad (test full use cases)
- **When**: Most development, incremental features
- **Trade-off**: Less precise failure messages

### Low Gear (Domain Model Tests)
- **Speed**: Fastest (pure Python, no dependencies)
- **Scope**: Narrow (single behavior)
- **When**: Complex business rules, new algorithms
- **Trade-off**: More tests to maintain

## Decision Framework

### When to Use Low Gear (Domain Tests)

Test the domain model directly when:

1. **Complex Business Rules**
   - Multi-step validation logic
   - State machines with many transitions
   - Calculations with edge cases

2. **New Domain Behavior**
   - Implementing a new aggregate method
   - Adding invariant enforcement
   - Creating value object operations

3. **Algorithm Development**
   - Sorting, matching, allocation logic
   - Financial calculations
   - Date/time manipulation

4. **Debugging Domain Issues**
   - Narrowing down business logic bugs
   - Understanding edge case behavior

```python
# Low gear example: Testing complex allocation algorithm
def test_prefers_earlier_batches():
    earliest = Batch("batch-001", "LAMP", 10, eta=today)
    medium = Batch("batch-002", "LAMP", 10, eta=tomorrow)
    latest = Batch("batch-003", "LAMP", 10, eta=next_week)

    line = OrderLine("order-1", "LAMP", 5)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_quantity == 5
    assert medium.available_quantity == 10
    assert latest.available_quantity == 10


def test_prefers_warehouse_stock_to_shipments():
    in_stock = Batch("batch-001", "LAMP", 10, eta=None)  # No ETA = in stock
    shipment = Batch("batch-002", "LAMP", 10, eta=tomorrow)

    line = OrderLine("order-1", "LAMP", 5)

    allocate(line, [shipment, in_stock])

    assert in_stock.available_quantity == 5
    assert shipment.available_quantity == 10
```

### When to Use High Gear (Service Layer Tests)

Test through the service layer when:

1. **Incremental Features**
   - Adding a field to an existing flow
   - Extending an existing use case
   - Minor business rule additions

2. **Integration Behavior**
   - Verifying repository interactions
   - Testing transaction boundaries
   - Checking event publication

3. **Refactoring**
   - Moving code between layers
   - Extracting patterns
   - Changing implementations

4. **Full Use Case Flows**
   - Happy path scenarios
   - Error handling
   - Multi-aggregate operations

```python
# High gear example: Testing full use case
def test_returns_allocation():
    uow = FakeUnitOfWork()
    uow.batches.add(Batch("batch-001", "LAMP", 100, eta=None))

    result = allocate(
        cmd=AllocateStock(order_id="order-1", sku="LAMP", qty=10),
        uow=uow,
    )

    assert result == "batch-001"


def test_error_for_out_of_stock():
    uow = FakeUnitOfWork()
    # No batches added

    with pytest.raises(OutOfStock):
        allocate(
            cmd=AllocateStock(order_id="order-1", sku="LAMP", qty=10),
            uow=uow,
        )


def test_commits_on_success():
    uow = FakeUnitOfWork()
    uow.batches.add(Batch("batch-001", "LAMP", 100, eta=None))

    allocate(
        cmd=AllocateStock(order_id="order-1", sku="LAMP", qty=10),
        uow=uow,
    )

    assert uow.committed
```

### When to Use E2E Tests

Sparingly, for critical paths:

1. **Smoke Tests**
   - API endpoint returns 200
   - Basic authentication works
   - Database connection established

2. **Critical User Journeys**
   - Checkout flow completes
   - Payment processing succeeds
   - Critical workflows

3. **Infrastructure Verification**
   - Database migrations work
   - External service integration

```python
# E2E example: Verify API contract
def test_api_returns_allocation(client, add_stock):
    add_stock([("batch-001", "LAMP", 100, None)])

    response = client.post("/allocate", json={
        "order_id": "order-1",
        "sku": "LAMP",
        "qty": 10,
    })

    assert response.status_code == 200
    assert response.json()["batch_ref"] == "batch-001"
```

## Workflow

### 1. Identify the Change Type

Ask:
- What kind of change is this?
- How complex is the business logic?
- Is this new behavior or extending existing?

### 2. Apply Decision Matrix

| Scenario | Gear | Test Location |
|----------|------|---------------|
| New complex algorithm | Low | `tests/unit/test_model.py` |
| New aggregate invariant | Low | `tests/unit/test_model.py` |
| Value object operations | Low | `tests/unit/test_model.py` |
| New use case (simple) | High | `tests/integration/test_handlers.py` |
| Extending existing flow | High | `tests/integration/test_handlers.py` |
| Refactoring internals | High | `tests/integration/test_handlers.py` |
| API contract change | E2E | `tests/e2e/test_api.py` |
| Critical user journey | E2E | `tests/e2e/test_api.py` |

### 3. Generate Test Scaffolding

```python
# For low gear (domain tests)
class TestOrderAggregate:
    """Low gear tests for Order business rules."""

    def test_can_add_line_to_order(self):
        order = Order(id="order-1", customer_id="cust-1")
        product = Product(sku="LAMP", name="Lamp", price=Money(Decimal("25")))

        order.add_line(product, quantity=2)

        assert len(order.lines) == 1

    def test_cannot_exceed_max_lines(self):
        # Test invariant
        ...

    def test_confirm_raises_event(self):
        # Test domain event
        ...


# For high gear (service layer tests)
class TestCreateOrderHandler:
    """High gear tests for create order use case."""

    def test_creates_order_for_valid_customer(self):
        uow = FakeUnitOfWork()
        uow.customers.add(Customer(id="cust-1"))

        order_id = create_order(
            CreateOrder(customer_id="cust-1", items=(...)),
            uow,
        )

        assert uow.orders.get(order_id) is not None

    def test_raises_for_invalid_customer(self):
        uow = FakeUnitOfWork()

        with pytest.raises(CustomerNotFound):
            create_order(
                CreateOrder(customer_id="nonexistent", items=(...)),
                uow,
            )
```

## Testing Patterns

### Fake Repository

```python
class FakeRepository:
    def __init__(self, items=None):
        self._items = set(items or [])
        self.seen = set()

    def add(self, item):
        self._items.add(item)
        self.seen.add(item)

    def get(self, id):
        item = next((i for i in self._items if i.id == id), None)
        if item:
            self.seen.add(item)
        return item

    def list(self):
        return list(self._items)
```

### Fake Unit of Work

```python
class FakeUnitOfWork:
    def __init__(self):
        self.orders = FakeRepository()
        self.customers = FakeRepository()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def collect_new_events(self):
        for repo in [self.orders, self.customers]:
            for item in repo.seen:
                while item.events:
                    yield item.events.pop(0)
```

### Test Data Builders

```python
def make_order(
    id="order-1",
    customer_id="cust-1",
    lines=None,
    status="pending",
):
    """Builder for test orders."""
    order = Order(id=id, customer_id=customer_id, status=status)
    for line in (lines or []):
        order.add_line(line["product"], line["quantity"])
    return order


def make_batch(
    reference="batch-001",
    sku="LAMP",
    qty=100,
    eta=None,
):
    """Builder for test batches."""
    return Batch(reference=reference, sku=sku, qty=qty, eta=eta)
```

## Anti-Patterns to Avoid

### Testing Implementation Details

```python
# BAD - tests internal state
def test_order_lines_stored_as_list():
    order = Order(...)
    assert isinstance(order._lines, list)  # Implementation detail!

# GOOD - tests behavior
def test_can_retrieve_added_lines():
    order = Order(...)
    order.add_line(product, 2)
    assert order.lines[0].quantity == 2
```

### Over-mocking

```python
# BAD - mocking everything
def test_create_order(mock_repo, mock_customer, mock_order):
    mock_repo.get.return_value = mock_customer
    mock_order.create.return_value = Order(...)
    # What are we even testing?

# GOOD - use fakes, test real behavior
def test_create_order():
    uow = FakeUnitOfWork()
    uow.customers.add(Customer(id="cust-1"))

    order_id = create_order(...)

    assert uow.orders.get(order_id) is not None
```

## References

- See `references/patterns-summary.md` for test strategy overview
- See `references/project-structure.md` for test file organization
