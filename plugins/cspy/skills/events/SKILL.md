---
name: events
description: Design domain events, commands, and message bus. Use when user says "add domain events", "design commands", "implement message bus", or needs event-driven patterns.
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

### 5. Generate Event Handlers

```python
from myproject.domain import events
from myproject.service_layer.unit_of_work import AbstractUnitOfWork


def send_order_confirmation(event: events.OrderCreated, uow: AbstractUnitOfWork) -> None:
    """
    Send confirmation email when order is created.

    Event handler: fire-and-forget, doesn't affect the command.
    """
    with uow:
        customer = uow.customers.get(event.customer_id)
        email_service.send(
            to=customer.email,
            subject="Order Confirmation",
            body=f"Your order {event.order_id} has been received.",
        )


def update_read_model(event: events.OrderConfirmed, uow: AbstractUnitOfWork) -> None:
    """Update denormalized read model when order is confirmed."""
    with uow:
        uow.order_views.upsert(
            order_id=event.order_id,
            status="confirmed",
            total=event.total,
        )
        uow.commit()


def notify_warehouse(event: events.OrderConfirmed, uow: AbstractUnitOfWork) -> None:
    """Notify warehouse system to prepare order."""
    warehouse_api.queue_order(event.order_id)


def log_out_of_stock(event: events.OutOfStock, uow: AbstractUnitOfWork) -> None:
    """Log out of stock events for inventory alerts."""
    logger.warning(f"Out of stock: {event.sku} for order {event.order_id}")
    metrics.increment("inventory.out_of_stock", tags={"sku": event.sku})
```

### 6. Generate Message Bus

```python
from typing import Callable, Type, Union
from myproject.domain import commands, events
from myproject.service_layer import handlers
from myproject.service_layer.unit_of_work import AbstractUnitOfWork

Message = Union[commands.Command, events.Event]

# Command handlers: exactly one per command
COMMAND_HANDLERS: dict[Type[commands.Command], Callable] = {
    commands.CreateOrder: handlers.create_order,
    commands.ConfirmOrder: handlers.confirm_order,
    commands.CancelOrder: handlers.cancel_order,
    commands.AllocateStock: handlers.allocate_stock,
}

# Event handlers: zero or more per event
EVENT_HANDLERS: dict[Type[events.Event], list[Callable]] = {
    events.OrderCreated: [
        handlers.send_order_confirmation,
    ],
    events.OrderConfirmed: [
        handlers.update_read_model,
        handlers.notify_warehouse,
    ],
    events.OutOfStock: [
        handlers.log_out_of_stock,
    ],
}


def handle(message: Message, uow: AbstractUnitOfWork) -> list:
    """
    Handle a message (command or event) and all resulting events.

    Returns list of results from command handlers.
    """
    results = []
    queue: list[Message] = [message]

    while queue:
        message = queue.pop(0)

        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            result = handle_command(message, queue, uow)
            results.append(result)
        else:
            raise TypeError(f"Unknown message type: {type(message)}")

    return results


def handle_command(
    command: commands.Command,
    queue: list[Message],
    uow: AbstractUnitOfWork,
) -> any:
    """Handle a single command."""
    handler = COMMAND_HANDLERS[type(command)]
    result = handler(command, uow)
    queue.extend(uow.collect_new_events())
    return result


def handle_event(
    event: events.Event,
    queue: list[Message],
    uow: AbstractUnitOfWork,
) -> None:
    """Handle a single event (may have multiple handlers)."""
    for handler in EVENT_HANDLERS.get(type(event), []):
        try:
            handler(event, uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            # Log but don't fail - events are fire-and-forget
            logger.exception(f"Error handling {type(event).__name__}")
            continue
```

### 7. Generate Tests

```python
import pytest
from myproject.domain import commands, events
from myproject.service_layer import messagebus


class TestMessageBus:
    """Test message bus dispatching."""

    def test_command_returns_result(self):
        uow = FakeUnitOfWork()
        uow.customers.add(Customer(id="cust-1"))

        cmd = commands.CreateOrder(
            customer_id="cust-1",
            items=({"sku": "LAMP", "qty": 2},),
        )

        results = messagebus.handle(cmd, uow)

        assert len(results) == 1
        assert results[0] is not None  # Order ID

    def test_events_are_collected_and_processed(self):
        uow = FakeUnitOfWork()
        uow.customers.add(Customer(id="cust-1", email="test@example.com"))

        cmd = commands.CreateOrder(
            customer_id="cust-1",
            items=({"sku": "LAMP", "qty": 2},),
        )

        messagebus.handle(cmd, uow)

        # Verify event handler was called
        assert email_service.sent_count == 1

    def test_command_failure_raises_exception(self):
        uow = FakeUnitOfWork()
        # No customer exists

        cmd = commands.CreateOrder(
            customer_id="nonexistent",
            items=({"sku": "LAMP", "qty": 2},),
        )

        with pytest.raises(CustomerNotFound):
            messagebus.handle(cmd, uow)


class TestEventHandlers:
    """Test individual event handlers."""

    def test_order_confirmation_sends_email(self):
        uow = FakeUnitOfWork()
        uow.customers.add(Customer(id="cust-1", email="test@example.com"))

        event = events.OrderCreated(
            order_id="order-1",
            customer_id="cust-1",
        )

        handlers.send_order_confirmation(event, uow)

        assert email_service.last_recipient == "test@example.com"
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

### External Event Consumer

```python
import redis
import json
from myproject.domain import events
from myproject.service_layer import messagebus, unit_of_work

def main():
    r = redis.Redis()
    pubsub = r.pubsub()
    pubsub.subscribe("orders")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        data = json.loads(message["data"])
        event = deserialize_event(data)

        uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
        messagebus.handle(event, uow)
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

- See `references/patterns-summary.md` for message bus details
- See `references/project-structure.md` for file organization
