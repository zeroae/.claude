---
name: domain
description: Design domain models with entities, value objects, and aggregates. Use when user says "design domain model", "identify entities", "create value object", "DDD", "aggregate design", or needs domain-driven design help.
---

# Domain Model Designer

Design domain models following Domain-Driven Design principles from Cosmic Python.

## Workflow

### 1. Discover Ubiquitous Language

Talk with the user to understand their domain:

1. **What problem are you solving?**
   - e-commerce, healthcare, logistics, finance, etc.
2. **What are the key business concepts?**
   - List nouns (potential entities/values)
3. **What actions can be performed?**
   - List verbs (potential methods/services)
4. **What rules must always be true?**
   - Invariants that aggregates enforce

### 2. Classify Concepts

For each concept, determine:

| Concept | Entity? | Value Object? | Aggregate Root? |
|---------|---------|---------------|-----------------|
| Has identity? | Yes | No | Yes |
| Mutable? | Usually | No (frozen) | Yes |
| Lifecycle? | Created/updated/deleted | Replaced entirely | Owns child entities |

### 3. Generate Domain Model

#### Value Objects

Use for concepts without identity:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """
    Represents a monetary amount with currency.

    Value object: identified by amount and currency, not by identity.
    Immutable: changing amount creates a new Money instance.
    """
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, multiplier: int | Decimal) -> "Money":
        return Money(self.amount * Decimal(multiplier), self.currency)


@dataclass(frozen=True)
class Address:
    """Postal address value object."""
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"


@dataclass(frozen=True)
class DateRange:
    """Date range value object."""
    start: date
    end: date

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End date must be after start date")

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    @property
    def days(self) -> int:
        return (self.end - self.start).days
```

#### Entities

Use for concepts with identity:

```python
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class Customer:
    """
    Customer entity.

    Entity: identified by id, not by attributes.
    Two customers with same name are different entities.
    """
    id: str
    name: str
    email: str
    address: Address  # Value object
    created_at: datetime = field(default_factory=datetime.utcnow)

    def update_address(self, new_address: Address) -> None:
        """Update customer's shipping address."""
        self.address = new_address

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Product:
    """Product entity."""
    sku: str  # Stock Keeping Unit - the identity
    name: str
    price: Money
    description: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.sku == other.sku

    def __hash__(self) -> int:
        return hash(self.sku)
```

#### Aggregates

Use for consistency boundaries:

```python
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myproject.domain.events import Event


@dataclass
class Order:
    """
    Order aggregate root.

    Aggregate: cluster of entities (Order, OrderLine) with Order as root.
    All modifications go through the root to enforce invariants.
    Raises domain events for side effects.
    """
    id: str
    customer_id: str
    lines: list["OrderLine"] = field(default_factory=list)
    status: str = "pending"
    events: list["Event"] = field(default_factory=list, repr=False)

    MAX_LINES = 20
    VALID_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

    def add_line(self, product: Product, quantity: int) -> None:
        """
        Add a product line to the order.

        Enforces invariant: orders cannot exceed MAX_LINES items.
        """
        if len(self.lines) >= self.MAX_LINES:
            raise OrderTooLarge(f"Cannot exceed {self.MAX_LINES} line items")

        if quantity <= 0:
            raise InvalidQuantity("Quantity must be positive")

        # Check if product already in order
        existing = next((l for l in self.lines if l.sku == product.sku), None)
        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(OrderLine(
                sku=product.sku,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
            ))

    def remove_line(self, sku: str) -> None:
        """Remove a product line from the order."""
        self.lines = [l for l in self.lines if l.sku != sku]

    def confirm(self) -> None:
        """
        Confirm the order.

        Enforces invariant: only pending orders can be confirmed.
        Raises OrderConfirmed event for downstream processing.
        """
        if self.status != "pending":
            raise InvalidStatusTransition(f"Cannot confirm {self.status} order")

        if not self.lines:
            raise EmptyOrder("Cannot confirm order with no items")

        self.status = "confirmed"
        self.events.append(OrderConfirmed(
            order_id=self.id,
            customer_id=self.customer_id,
            total=self.total,
        ))

    def cancel(self) -> None:
        """Cancel the order if allowed."""
        if self.status in ["shipped", "delivered"]:
            raise InvalidStatusTransition(f"Cannot cancel {self.status} order")

        self.status = "cancelled"
        self.events.append(OrderCancelled(order_id=self.id))

    @property
    def total(self) -> Money:
        """Calculate order total."""
        if not self.lines:
            return Money(Decimal("0"))
        return sum((l.subtotal for l in self.lines), Money(Decimal("0")))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class OrderLine:
    """
    Order line item (child entity within Order aggregate).

    Cannot exist outside of an Order.
    No direct repository access - always accessed through Order.
    """
    sku: str
    name: str
    unit_price: Money
    quantity: int

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity
```

#### Domain Services

Use for operations that don't belong to one entity:

```python
def allocate(line: OrderLine, batches: list[Batch]) -> str:
    """
    Allocate an order line to the best available batch.

    Domain service: doesn't belong to OrderLine or Batch alone.
    Returns the batch reference that was allocated.
    Raises OutOfStock if no suitable batch found.
    """
    # Sort batches by ETA (prefer in-stock over shipments)
    sorted_batches = sorted(batches, key=lambda b: (b.eta is not None, b.eta))

    for batch in sorted_batches:
        if batch.can_allocate(line):
            batch.allocate(line)
            return batch.reference

    raise OutOfStock(f"Out of stock for SKU: {line.sku}")
```

### 4. Generate Tests

Test domain models at the unit level (low gear):

```python
import pytest
from decimal import Decimal
from myproject.domain.model import Order, Product, Money


class TestMoney:
    """Value object: test equality and operations."""

    def test_money_equality(self):
        assert Money(Decimal("10.00")) == Money(Decimal("10.00"))

    def test_cannot_add_different_currencies(self):
        with pytest.raises(ValueError):
            Money(Decimal("10"), "USD") + Money(Decimal("5"), "EUR")


class TestOrder:
    """Aggregate: test invariants and events."""

    def test_cannot_exceed_max_lines(self):
        order = Order(id="order-1", customer_id="cust-1")
        for i in range(Order.MAX_LINES):
            order.add_line(Product(sku=f"SKU-{i}", name=f"P{i}", price=Money(Decimal("10"))), 1)

        with pytest.raises(OrderTooLarge):
            order.add_line(Product(sku="EXTRA", name="Extra", price=Money(Decimal("10"))), 1)

    def test_confirm_raises_event(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 1)
        order.confirm()

        assert order.status == "confirmed"
        assert isinstance(order.events[0], OrderConfirmed)
```

See `references/domain-tests.md` for comprehensive test examples.

## Design Guidelines

### When to Use Value Objects

- Money, currency, quantities
- Addresses, coordinates, ranges
- Measurements (weight, dimensions)
- Identifiers (SKU, ISBN, email)
- Status values (if immutable)

### When to Use Entities

- Users, customers, employees
- Products, inventory items
- Anything with a lifecycle
- Things you need to track changes to

### When to Create an Aggregate

- Group of entities that must be consistent together
- Clear boundary for transactions
- Single entry point enforces invariants

### Aggregate Design Rules

1. **Reference by ID**: Aggregates reference other aggregates by ID, not object
2. **One repository per aggregate**: Only aggregate roots have repositories
3. **Small aggregates**: Prefer smaller aggregates for concurrency
4. **Eventual consistency**: Accept eventual consistency between aggregates

## References

- See `references/domain-tests.md` for comprehensive test examples
- See `../references/patterns-summary.md` for pattern overview
- See `../references/project-structure.md` for file organization
