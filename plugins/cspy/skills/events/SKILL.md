---
name: events
description: Design domain events, commands, and message bus. Use when user says "add domain events", "design commands", "implement message bus", "event-driven", "CQRS events", or needs side-effect decoupling.
---

# Event/Command Designer

Design domain events, commands, and message bus infrastructure for event-driven architecture.

## Concepts

### Commands
- **Intent**: "I want something to happen"
- **Naming**: Imperative verb (`CreateOrder`, `AllocateStock`)
- **Handler**: Exactly one handler per command
- **Failure**: Commands can fail (raise exceptions)

### Events
- **Meaning**: "Something happened"
- **Naming**: Past tense (`OrderCreated`, `StockAllocated`)
- **Handlers**: Zero or more handlers per event
- **Failure**: Event handlers shouldn't fail the original operation

### Message Bus
- Dispatches commands and events to handlers
- Collects new events raised during handling
- Processes all events until queue is empty

## Workflow

### 1. Identify Messages

Ask the user:
1. **What actions can users perform?** → Commands
2. **What are the outcomes of those actions?** → Events
3. **What side effects should happen?** → Event handlers

### 2. Generate Command Definitions

```python
from dataclasses import dataclass
from typing import Sequence


class Command:
    """Base class for commands."""
    pass


@dataclass(frozen=True)
class CreateOrder(Command):
    """
    Create a new order for a customer.

    Command: imperative, represents user intent.
    Handled by: handlers.create_order
    """
    customer_id: str
    items: tuple[dict, ...]  # Use tuple for immutability


@dataclass(frozen=True)
class AddOrderLine(Command):
    """Add a line item to an existing order."""
    order_id: str
    sku: str
    quantity: int


@dataclass(frozen=True)
class ConfirmOrder(Command):
    """Confirm an order for processing."""
    order_id: str


@dataclass(frozen=True)
class CancelOrder(Command):
    """Cancel an order."""
    order_id: str
    reason: str = ""


@dataclass(frozen=True)
class AllocateStock(Command):
    """Allocate inventory to an order line."""
    order_id: str
    sku: str
    quantity: int
```

### 3. Generate Event Definitions

```python
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


class Event:
    """Base class for domain events."""
    pass


@dataclass(frozen=True)
class OrderCreated(Event):
    """
    An order was created.

    Event: past tense, records what happened.
    Handlers: send confirmation email, update analytics
    """
    order_id: str
    customer_id: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class OrderConfirmed(Event):
    """An order was confirmed and is ready for processing."""
    order_id: str
    customer_id: str
    total: Decimal


@dataclass(frozen=True)
class OrderCancelled(Event):
    """An order was cancelled."""
    order_id: str
    reason: str = ""


@dataclass(frozen=True)
class StockAllocated(Event):
    """Inventory was allocated to an order line."""
    order_id: str
    sku: str
    quantity: int
    batch_ref: str


@dataclass(frozen=True)
class OutOfStock(Event):
    """An allocation failed due to insufficient stock."""
    sku: str
    order_id: str
```

### 4. Generate Command Handlers

```python
from myproject.domain import commands
from myproject.service_layer.unit_of_work import AbstractUnitOfWork


def create_order(cmd: commands.CreateOrder, uow: AbstractUnitOfWork) -> str:
    """
    Handle CreateOrder command.

    Returns the created order ID.
    """
    with uow:
        customer = uow.customers.get(cmd.customer_id)
        if not customer:
            raise CustomerNotFound(cmd.customer_id)

        order = Order.create(
            customer_id=cmd.customer_id,
            items=cmd.items,
        )
        uow.orders.add(order)
        uow.commit()

    return order.id


def confirm_order(cmd: commands.ConfirmOrder, uow: AbstractUnitOfWork) -> None:
    """Handle ConfirmOrder command."""
    with uow:
        order = uow.orders.get(cmd.order_id)
        if not order:
            raise OrderNotFound(cmd.order_id)

        order.confirm()  # Raises OrderConfirmed event
        uow.commit()


def allocate_stock(cmd: commands.AllocateStock, uow: AbstractUnitOfWork) -> str:
    """
    Handle AllocateStock command.

    Returns the batch reference that was allocated.
    """
    with uow:
        batches = uow.batches.list_by_sku(cmd.sku)
        if not batches:
            uow.events.append(OutOfStock(sku=cmd.sku, order_id=cmd.order_id))
            uow.commit()
            return None

        batch_ref = allocate(
            OrderLine(sku=cmd.sku, quantity=cmd.quantity),
            batches,
        )
        uow.commit()

    return batch_ref
```

### 5. Generate Message Bus

See `references/messagebus.md` for full implementation. Key concepts:

```python
# Handler registration
COMMAND_HANDLERS = {commands.CreateOrder: handlers.create_order}
EVENT_HANDLERS = {events.OrderCreated: [handlers.send_confirmation]}

# Dispatch loop processes commands and collects events
def handle(message: Message, uow: AbstractUnitOfWork) -> list:
    queue = [message]
    while queue:
        msg = queue.pop(0)
        if isinstance(msg, events.Event):
            for handler in EVENT_HANDLERS.get(type(msg), []):
                handler(msg, uow)
                queue.extend(uow.collect_new_events())
        else:
            result = COMMAND_HANDLERS[type(msg)](msg, uow)
            queue.extend(uow.collect_new_events())
    return results
```

### 6. Test Message Bus

```python
def test_command_returns_result():
    uow = FakeUnitOfWork()
    uow.customers.add(Customer(id="cust-1"))

    results = messagebus.handle(
        commands.CreateOrder(customer_id="cust-1", items=(...)),
        uow,
    )

    assert results[0] is not None  # Order ID
```

## Integration with Entrypoints

### FastAPI

```python
from fastapi import FastAPI, Depends
from myproject.domain import commands
from myproject.service_layer import messagebus, unit_of_work

app = FastAPI()

@app.post("/orders")
def create_order(
    request: CreateOrderRequest,
    uow: AbstractUnitOfWork = Depends(get_uow),
):
    cmd = commands.CreateOrder(
        customer_id=request.customer_id,
        items=tuple(request.items),
    )
    results = messagebus.handle(cmd, uow)
    return {"order_id": results[0]}
```

## Event Naming Conventions

| Action | Command (Imperative) | Event (Past Tense) |
|--------|---------------------|-------------------|
| Create order | `CreateOrder` | `OrderCreated` |
| Update status | `UpdateOrderStatus` | `OrderStatusUpdated` |
| Cancel | `CancelOrder` | `OrderCancelled` |
| Allocate | `AllocateStock` | `StockAllocated` |
| Ship | `ShipOrder` | `OrderShipped` |
| Fail | `FailOrder` | `OrderFailed` |

## References

- See `references/messagebus.md` for full message bus implementation and tests
- See `../references/patterns-summary.md` for message bus details
- See `../references/project-structure.md` for file organization
