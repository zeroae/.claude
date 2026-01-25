# Common Service Layer Use Case Patterns

Reference file for common service layer patterns following Cosmic Python.

## Create Entity Pattern

```python
def create_order(
    customer_id: str,
    items: list[dict],
    uow: AbstractUnitOfWork,
) -> str:
    """Create a new order for a customer."""
    with uow:
        customer = uow.customers.get(customer_id)
        if not customer:
            raise CustomerNotFound(customer_id)

        order = Order.create(
            customer_id=customer_id,
            items=[OrderLine(**item) for item in items],
        )
        uow.orders.add(order)
        uow.commit()

    return order.id
```

## Update Entity Pattern

```python
def update_order_status(
    order_id: str,
    new_status: str,
    uow: AbstractUnitOfWork,
) -> None:
    """Update an order's status."""
    with uow:
        order = uow.orders.get(order_id)
        if not order:
            raise OrderNotFound(order_id)

        order.update_status(new_status)  # Domain validates status transition
        uow.commit()
```

## Cross-Aggregate Operation Pattern

```python
def allocate_stock(
    order_id: str,
    sku: str,
    qty: int,
    uow: AbstractUnitOfWork,
) -> str:
    """Allocate stock to an order line."""
    with uow:
        order = uow.orders.get(order_id)
        if not order:
            raise OrderNotFound(order_id)

        batches = uow.batches.list_by_sku(sku)
        if not batches:
            raise OutOfStock(sku)

        # Domain logic determines which batch to allocate from
        batch_ref = allocate(order.get_line(sku), batches)
        uow.commit()

    return batch_ref
```

## Query Operation Pattern (CQRS Read Side)

For read-only operations, you may bypass the domain model:

```python
def get_order_summary(order_id: str) -> dict | None:
    """Get order summary for display (read model)."""
    # Direct query - no UoW needed for reads
    return db.execute("""
        SELECT o.id, o.status, o.total,
               c.name as customer_name,
               COUNT(ol.id) as line_count
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_lines ol ON ol.order_id = o.id
        WHERE o.id = :order_id
        GROUP BY o.id, c.name
    """, {"order_id": order_id}).fetchone()
```

## Delete/Cancel Pattern

```python
def cancel_order(
    order_id: str,
    reason: str,
    uow: AbstractUnitOfWork,
) -> None:
    """Cancel an order."""
    with uow:
        order = uow.orders.get(order_id)
        if not order:
            raise OrderNotFound(order_id)

        order.cancel(reason)  # Domain validates cancelability
        uow.commit()
```

## Batch Processing Pattern

```python
def process_pending_orders(
    batch_size: int,
    uow: AbstractUnitOfWork,
) -> int:
    """Process pending orders in batch."""
    with uow:
        pending = uow.orders.list_by_status("pending", limit=batch_size)

        processed = 0
        for order in pending:
            try:
                order.process()
                processed += 1
            except DomainException:
                continue  # Skip failed orders

        uow.commit()

    return processed
```
