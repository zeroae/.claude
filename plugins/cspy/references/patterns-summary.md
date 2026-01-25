# Cosmic Python Patterns Quick Reference

> **Attribution**: This content is derived from "Architecture Patterns with Python" by Harry Percival and Bob Gregory, available at [cosmicpython.com](https://cosmicpython.com). Licensed under [CC BY-NC-ND 3.0](https://creativecommons.org/licenses/by-nc-nd/3.0/).

A summary of architecture patterns from the book.

## Pattern Overview

| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| **Repository** | Abstract data persistence | Always - isolates domain from storage |
| **Service Layer** | Orchestrate use cases | When business logic spans aggregates |
| **Unit of Work** | Atomic transactions | When multiple writes must succeed/fail together |
| **Aggregate** | Consistency boundary | Complex domains with invariants |
| **Domain Events** | Decouple side effects | Notifications, external systems |
| **Commands** | Express intent | User/system actions |
| **Message Bus** | Route messages | Event/command dispatch |
| **CQRS** | Separate reads/writes | Complex queries, read optimization |

## Layer Dependencies

```
┌─────────────────────────────────────────┐
│           Entrypoints                    │
│    (Flask, FastAPI, CLI, Message Bus)    │
└─────────────────┬───────────────────────┘
                  │ calls
┌─────────────────▼───────────────────────┐
│           Service Layer                  │
│    (Use cases, orchestration)            │
└─────────────────┬───────────────────────┘
                  │ uses
┌─────────────────▼───────────────────────┐
│           Domain Model                   │
│    (Entities, Value Objects, Aggregates) │
└─────────────────┬───────────────────────┘
                  │ defined by
┌─────────────────▼───────────────────────┐
│           Adapters                       │
│    (Repository impls, ORMs, APIs)        │
└─────────────────────────────────────────┘
```

**Rule**: Dependencies point inward. Domain knows nothing about infrastructure.

## Domain Model Building Blocks

### Value Object
- Identified by attributes, not identity
- Immutable
- Comparable by value

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
```

### Entity
- Has unique identity
- Identity persists across changes
- Mutable

```python
@dataclass
class Order:
    id: OrderId
    customer_id: CustomerId
    lines: list[OrderLine]
```

### Aggregate
- Cluster of entities/value objects
- Single entry point (root)
- Enforces invariants

```python
class Order:  # Aggregate root
    def add_line(self, product: Product, qty: int):
        if self.total_qty + qty > self.MAX_ITEMS:
            raise OrderTooLarge()
        self.lines.append(OrderLine(product, qty))
```

### Domain Service
- Business logic that doesn't belong to an entity
- Stateless operations

```python
def allocate(line: OrderLine, batches: list[Batch]) -> str:
    """Allocate order line to best available batch."""
    ...
```

## Repository Pattern

```python
# Abstract interface
class AbstractRepository(ABC):
    @abstractmethod
    def add(self, entity: T) -> None: ...

    @abstractmethod
    def get(self, id: ID) -> T | None: ...

# Concrete implementation
class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, entity: T) -> None:
        self.session.add(entity)

    def get(self, id: ID) -> T | None:
        return self.session.get(Entity, id)

# Fake for testing
class FakeRepository(AbstractRepository):
    def __init__(self):
        self._entities: set[T] = set()
```

## Service Layer Pattern

```python
def place_order(
    customer_id: str,
    items: list[dict],
    uow: AbstractUnitOfWork,
) -> str:
    with uow:
        customer = uow.customers.get(customer_id)
        if not customer:
            raise CustomerNotFound(customer_id)

        order = customer.place_order(items)
        uow.orders.add(order)
        uow.commit()

    return order.id
```

## Unit of Work Pattern

```python
class AbstractUnitOfWork(ABC):
    orders: AbstractOrderRepository

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def commit(self): ...

    @abstractmethod
    def rollback(self): ...

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.orders = SqlAlchemyOrderRepository(self.session)
        return self

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
```

## Events and Commands

### Command (imperative)
```python
@dataclass
class PlaceOrder:
    customer_id: str
    items: list[dict]
```

### Event (past tense)
```python
@dataclass
class OrderPlaced:
    order_id: str
    customer_id: str
    total: Decimal
```

### Message Bus
```python
HANDLERS: dict[type, list[Callable]] = {
    PlaceOrder: [handlers.place_order],
    OrderPlaced: [
        handlers.send_confirmation_email,
        handlers.update_inventory,
    ],
}

def handle(message: Message, uow: AbstractUnitOfWork):
    queue = [message]
    while queue:
        message = queue.pop(0)
        for handler in HANDLERS[type(message)]:
            handler(message, uow)
            queue.extend(uow.collect_new_events())
```

## CQRS

Separate read models from write models:

```python
# Write side - via domain model
def place_order(cmd: PlaceOrder, uow: AbstractUnitOfWork):
    with uow:
        order = Order.create(cmd.customer_id, cmd.items)
        uow.orders.add(order)
        uow.commit()

# Read side - direct queries
def get_order_summary(order_id: str) -> dict:
    return db.execute("""
        SELECT o.id, o.status, o.total,
               c.name as customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.id = :order_id
    """, {"order_id": order_id}).fetchone()
```

## Testing Strategy

### High Gear (Fast, Broad)
- Test through service layer
- Use fake repositories
- Good for incremental features

### Low Gear (Focused, Detailed)
- Test domain model directly
- No dependencies
- Good for complex business rules

```python
# High gear - service layer test
def test_place_order():
    uow = FakeUnitOfWork()
    uow.customers.add(Customer("cust-1"))

    order_id = place_order("cust-1", [{"sku": "ABC", "qty": 10}], uow)

    assert uow.orders.get(order_id) is not None

# Low gear - domain model test
def test_order_cannot_exceed_max_items():
    order = Order(id="order-1", customer_id="cust-1")
    order.add_line(Product("ABC"), 99)

    with pytest.raises(OrderTooLarge):
        order.add_line(Product("DEF"), 2)
```

## Incremental Adoption Path

1. **Service Layer** - Extract business logic from web handlers
2. **Repository** - Abstract database access
3. **Unit of Work** - Manage transactions
4. **Aggregates** - Define consistency boundaries
5. **Domain Events** - Decouple side effects
6. **CQRS** - Optimize reads separately

## Resources

- Book: [cosmicpython.com](https://cosmicpython.com)
- Code: [github.com/cosmicpython/code](https://github.com/cosmicpython/code)
