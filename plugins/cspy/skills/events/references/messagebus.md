# Message Bus Implementation

Reference file for complete message bus implementation following Cosmic Python patterns.

## Message Bus Core

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

## Event Handler Examples

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

## Message Bus Tests

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

## External Event Consumer

For consuming events from external sources (Redis, RabbitMQ, etc.):

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


def deserialize_event(data: dict) -> events.Event:
    """Deserialize event from external source."""
    event_type = data.pop("type")
    event_class = getattr(events, event_type)
    return event_class(**data)
```

## Async Message Bus (Alternative)

For fully async applications:

```python
async def handle_async(message: Message, uow: AbstractAsyncUnitOfWork) -> list:
    """Async version of message handler."""
    results = []
    queue: list[Message] = [message]

    while queue:
        message = queue.pop(0)

        if isinstance(message, events.Event):
            await handle_event_async(message, queue, uow)
        elif isinstance(message, commands.Command):
            result = await handle_command_async(message, queue, uow)
            results.append(result)

    return results
```
