---
name: refactor
description: Guide incremental adoption of Cosmic Python patterns. Use when user says "adopt patterns", "improve architecture", "refactor to DDD", or needs migration guidance.
---

# Incremental Pattern Adoption Guide

Guide the incremental adoption of Cosmic Python architecture patterns in existing codebases.

## Philosophy

- **Incremental**: One pattern at a time
- **Safe**: Each step should be deployable
- **Testable**: Add tests before refactoring
- **Reversible**: Keep rollback possible

## Recommended Adoption Order

```
1. Service Layer  →  2. Repository  →  3. Unit of Work
       ↓                                       ↓
4. Aggregates    →  5. Domain Events  →  6. CQRS
```

Each pattern builds on the previous ones.

## Pattern Adoption Steps

### Step 1: Service Layer

**Goal**: Extract business logic from web handlers.

**Before**:
```python
# Everything in the route handler
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    customer = db.session.query(Customer).get(data["customer_id"])
    if not customer:
        return {"error": "Customer not found"}, 404

    order = Order(
        customer_id=data["customer_id"],
        status="pending",
    )
    for item in data["items"]:
        order.lines.append(OrderLine(
            sku=item["sku"],
            quantity=item["quantity"],
        ))
    db.session.add(order)
    db.session.commit()

    return {"order_id": order.id}, 201
```

**After**:
```python
# Route handler is thin
@app.route("/orders", methods=["POST"])
def create_order_endpoint():
    data = request.json
    try:
        order_id = services.create_order(
            customer_id=data["customer_id"],
            items=data["items"],
        )
        return {"order_id": order_id}, 201
    except CustomerNotFound:
        return {"error": "Customer not found"}, 404

# Business logic in service layer
def create_order(customer_id: str, items: list[dict]) -> str:
    customer = db.session.query(Customer).get(customer_id)
    if not customer:
        raise CustomerNotFound(customer_id)

    order = Order(customer_id=customer_id, status="pending")
    for item in items:
        order.lines.append(OrderLine(sku=item["sku"], quantity=item["quantity"]))

    db.session.add(order)
    db.session.commit()

    return order.id
```

**Refactoring Steps**:
1. Create `service_layer/` directory
2. Extract function for each route
3. Move business logic to function
4. Keep route as thin wrapper
5. Add tests for service functions

---

### Step 2: Repository Pattern

**Goal**: Abstract database access.

**Before**:
```python
def create_order(customer_id: str, items: list[dict]) -> str:
    customer = db.session.query(Customer).get(customer_id)  # Direct ORM
    if not customer:
        raise CustomerNotFound(customer_id)

    order = Order(customer_id=customer_id, status="pending")
    db.session.add(order)  # Direct session
    db.session.commit()

    return order.id
```

**After**:
```python
# Abstract interface
class AbstractOrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> None: ...

    @abstractmethod
    def get(self, order_id: str) -> Order | None: ...

# Concrete implementation
class SqlAlchemyOrderRepository(AbstractOrderRepository):
    def __init__(self, session):
        self.session = session

    def add(self, order: Order) -> None:
        self.session.add(order)

    def get(self, order_id: str) -> Order | None:
        return self.session.get(Order, order_id)

# Fake for testing
class FakeOrderRepository(AbstractOrderRepository):
    def __init__(self):
        self._orders = set()

    def add(self, order: Order) -> None:
        self._orders.add(order)

    def get(self, order_id: str) -> Order | None:
        return next((o for o in self._orders if o.id == order_id), None)

# Service uses repository
def create_order(
    customer_id: str,
    items: list[dict],
    customer_repo: AbstractCustomerRepository,
    order_repo: AbstractOrderRepository,
    session,  # Still need session for commit
) -> str:
    customer = customer_repo.get(customer_id)
    if not customer:
        raise CustomerNotFound(customer_id)

    order = Order(customer_id=customer_id, status="pending")
    order_repo.add(order)
    session.commit()

    return order.id
```

**Refactoring Steps**:
1. Create `adapters/repository.py`
2. Define abstract interface for each aggregate
3. Implement SqlAlchemy repository
4. Implement Fake repository for tests
5. Update services to accept repositories
6. Update tests to use fakes

---

### Step 3: Unit of Work

**Goal**: Manage transactions consistently.

**Before**:
```python
def create_order(
    customer_id: str,
    items: list[dict],
    customer_repo: AbstractCustomerRepository,
    order_repo: AbstractOrderRepository,
    session,  # Awkward session parameter
) -> str:
    customer = customer_repo.get(customer_id)
    order = Order(...)
    order_repo.add(order)
    session.commit()  # Manual commit
    return order.id
```

**After**:
```python
def create_order(
    customer_id: str,
    items: list[dict],
    uow: AbstractUnitOfWork,  # Clean dependency
) -> str:
    with uow:
        customer = uow.customers.get(customer_id)
        if not customer:
            raise CustomerNotFound(customer_id)

        order = Order(customer_id=customer_id, status="pending")
        uow.orders.add(order)
        uow.commit()  # Explicit commit

    return order.id  # After context manager exits
```

**Refactoring Steps**:
1. Create `service_layer/unit_of_work.py`
2. Define AbstractUnitOfWork with repositories
3. Implement SqlAlchemyUnitOfWork
4. Implement FakeUnitOfWork for tests
5. Update services to accept UoW
6. Remove session/repository parameters

---

### Step 4: Aggregate Design

**Goal**: Define consistency boundaries.

**Before**:
```python
# ORM models with no encapsulation
class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"))
    status = Column(String)
    lines = relationship("OrderLine")

# Logic scattered in services
def add_line_to_order(order_id, sku, qty, uow):
    with uow:
        order = uow.orders.get(order_id)
        if len(order.lines) >= 20:  # Business rule in service!
            raise OrderTooLarge()
        order.lines.append(OrderLine(sku=sku, quantity=qty))
        uow.commit()
```

**After**:
```python
# Rich domain model
@dataclass
class Order:
    id: str
    customer_id: str
    lines: list[OrderLine] = field(default_factory=list)
    status: str = "pending"
    events: list[Event] = field(default_factory=list)

    MAX_LINES = 20

    def add_line(self, product: Product, quantity: int) -> None:
        """Add line with invariant enforcement."""
        if len(self.lines) >= self.MAX_LINES:
            raise OrderTooLarge(f"Cannot exceed {self.MAX_LINES} lines")
        self.lines.append(OrderLine(
            sku=product.sku,
            name=product.name,
            unit_price=product.price,
            quantity=quantity,
        ))

# Thin service
def add_line_to_order(order_id, sku, qty, uow):
    with uow:
        order = uow.orders.get(order_id)
        product = uow.products.get(sku)
        order.add_line(product, qty)  # Delegate to aggregate
        uow.commit()
```

**Refactoring Steps**:
1. Identify aggregate boundaries
2. Move business rules to aggregate methods
3. Separate domain model from ORM
4. Use classical mapping or separate tables
5. Update services to call aggregate methods
6. Add domain model tests

---

### Step 5: Domain Events

**Goal**: Decouple side effects.

**Before**:
```python
def confirm_order(order_id: str, uow: AbstractUnitOfWork) -> None:
    with uow:
        order = uow.orders.get(order_id)
        order.status = "confirmed"

        # Side effects mixed with main logic
        email_service.send_confirmation(order)
        inventory_service.reserve_stock(order)
        analytics.track_order_confirmed(order)

        uow.commit()
```

**After**:
```python
# Domain raises events
class Order:
    def confirm(self) -> None:
        if self.status != "pending":
            raise InvalidStatusTransition()
        self.status = "confirmed"
        self.events.append(OrderConfirmed(
            order_id=self.id,
            customer_id=self.customer_id,
        ))

# Service is simple
def confirm_order(order_id: str, uow: AbstractUnitOfWork) -> None:
    with uow:
        order = uow.orders.get(order_id)
        order.confirm()
        uow.commit()

# Side effects handled separately
def send_confirmation_email(event: OrderConfirmed, uow):
    customer = uow.customers.get(event.customer_id)
    email_service.send(customer.email, "Order Confirmed", ...)

def reserve_inventory(event: OrderConfirmed, uow):
    inventory_service.reserve(event.order_id)

# Register handlers
EVENT_HANDLERS[OrderConfirmed] = [
    send_confirmation_email,
    reserve_inventory,
    track_analytics,
]
```

**Refactoring Steps**:
1. Create `domain/events.py`
2. Add events list to aggregates
3. Move side effects to event handlers
4. Create message bus for dispatch
5. Collect events after commit
6. Register handlers

---

### Step 6: CQRS

**Goal**: Optimize reads separately from writes.

**Before**:
```python
# Reads go through domain model
def get_order_summary(order_id: str, uow: AbstractUnitOfWork) -> dict:
    with uow:
        order = uow.orders.get(order_id)
        customer = uow.customers.get(order.customer_id)
        return {
            "order_id": order.id,
            "customer_name": customer.name,  # Extra fetch
            "total": sum(l.price * l.qty for l in order.lines),  # Computed
            "line_count": len(order.lines),
        }
```

**After**:
```python
# Reads bypass domain model
def get_order_summary(order_id: str) -> OrderSummary | None:
    row = db.execute("""
        SELECT o.id, c.name, SUM(ol.price * ol.qty), COUNT(ol.id)
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN order_lines ol ON ol.order_id = o.id
        WHERE o.id = :order_id
        GROUP BY o.id, c.name
    """, {"order_id": order_id}).fetchone()

    if not row:
        return None
    return OrderSummary(*row)

# Writes still through domain
def create_order(cmd: CreateOrder, uow: AbstractUnitOfWork) -> str:
    with uow:
        order = Order.create(cmd.customer_id, cmd.items)
        uow.orders.add(order)
        uow.commit()
    return order.id
```

**Refactoring Steps**:
1. Create `views.py` or `queries.py`
2. Identify read-heavy endpoints
3. Write optimized SQL queries
4. Create read model dataclasses
5. Update read endpoints to use views
6. Keep write endpoints unchanged

---

## Migration Checklist

For each pattern:

- [ ] Understand current state
- [ ] Write characterization tests
- [ ] Create new structure
- [ ] Migrate incrementally
- [ ] Verify tests pass
- [ ] Deploy and monitor
- [ ] Remove old code

## Common Pitfalls

### Big Bang Refactoring
- **Problem**: Trying to adopt all patterns at once
- **Solution**: One pattern at a time, deploy between each

### Skipping Tests
- **Problem**: Refactoring without test coverage
- **Solution**: Write characterization tests before changing anything

### Over-Engineering
- **Problem**: Adding patterns that aren't needed
- **Solution**: Only add patterns when you feel the pain they solve

### Ignoring Team
- **Problem**: Patterns unfamiliar to team
- **Solution**: Train team, pair program, document decisions

## References

- See `references/patterns-summary.md` for pattern overview
- See `references/project-structure.md` for target structure
