---
name: cqrs
description: Analyze and design CQRS read models. Use when user says "optimize reads", "separate queries", "create read model", "read vs write", "denormalized views", or needs to split reads from writes.
---

# CQRS Analyzer

Analyze codebase for CQRS opportunities and design optimized read models.

## What is CQRS?

Command Query Responsibility Segregation:
- **Commands**: Write operations through domain model (enforce business rules)
- **Queries**: Read operations directly from database (optimized for display)

## When to Use CQRS

Use CQRS when:
- Read and write patterns differ significantly
- Complex queries slow down the application
- Different data shapes needed for display vs. storage
- Read scaling requirements differ from write

Don't use CQRS when:
- Simple CRUD application
- Reads and writes have similar patterns
- Team unfamiliar with the complexity

## Workflow

### 1. Analyze Current Queries

Identify slow or complex queries:

```python
# Signs you need CQRS:

# 1. Multiple JOINs for display
SELECT o.*, c.name, c.email,
       COUNT(ol.id) as line_count,
       SUM(ol.quantity * ol.price) as total
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_lines ol ON ol.order_id = o.id
GROUP BY o.id, c.name, c.email

# 2. Aggregations computed repeatedly
SELECT product_id, SUM(quantity) as total_sold
FROM order_lines
GROUP BY product_id

# 3. Data transformation in application code
orders = repository.list_all()
for order in orders:
    order.customer_name = customer_repo.get(order.customer_id).name
    order.total = sum(line.price * line.qty for line in order.lines)
```

### 2. Design Read Models

Create denormalized views optimized for specific use cases:

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


# Read models are simple data structures
# No business logic, just display data

@dataclass
class OrderSummary:
    """Read model for order list view."""
    order_id: str
    customer_name: str
    status: str
    total: Decimal
    line_count: int
    created_at: datetime


@dataclass
class OrderDetail:
    """Read model for order detail view."""
    order_id: str
    customer_name: str
    customer_email: str
    status: str
    shipping_address: str
    lines: list["OrderLineView"]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass
class OrderLineView:
    """Read model for order line display."""
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


@dataclass
class ProductInventory:
    """Read model for inventory dashboard."""
    sku: str
    product_name: str
    total_stock: int
    allocated: int
    available: int
    reorder_point: int
    needs_reorder: bool
```

### 3. Implement Read Side

#### Option A: Direct SQL Queries (Recommended)

Simple and effective for most cases. Start here:

```python
from typing import Optional
from myproject.views import OrderSummary, OrderDetail


def get_order_summary(order_id: str) -> Optional[OrderSummary]:
    """
    Get order summary for display.

    Read side: bypasses domain model, queries directly.
    """
    row = db.execute("""
        SELECT
            o.id as order_id,
            c.name as customer_name,
            o.status,
            SUM(ol.quantity * ol.unit_price) as total,
            COUNT(ol.id) as line_count,
            o.created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_lines ol ON ol.order_id = o.id
        WHERE o.id = :order_id
        GROUP BY o.id, c.name, o.status, o.created_at
    """, {"order_id": order_id}).fetchone()

    if not row:
        return None

    return OrderSummary(**row._mapping)


def list_orders(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OrderSummary]:
    """List orders with optional filtering."""
    query = """
        SELECT
            o.id as order_id,
            c.name as customer_name,
            o.status,
            SUM(ol.quantity * ol.unit_price) as total,
            COUNT(ol.id) as line_count,
            o.created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_lines ol ON ol.order_id = o.id
    """
    params = {"limit": limit, "offset": offset}

    if status:
        query += " WHERE o.status = :status"
        params["status"] = status

    query += """
        GROUP BY o.id, c.name, o.status, o.created_at
        ORDER BY o.created_at DESC
        LIMIT :limit OFFSET :offset
    """

    rows = db.execute(query, params).fetchall()
    return [OrderSummary(**row._mapping) for row in rows]
```

#### Option B: Materialized Views

For complex aggregations:

```sql
-- Create materialized view for product inventory
CREATE MATERIALIZED VIEW product_inventory_view AS
SELECT
    p.sku,
    p.name as product_name,
    COALESCE(SUM(b.quantity), 0) as total_stock,
    COALESCE(SUM(a.allocated), 0) as allocated,
    COALESCE(SUM(b.quantity), 0) - COALESCE(SUM(a.allocated), 0) as available,
    p.reorder_point,
    (COALESCE(SUM(b.quantity), 0) - COALESCE(SUM(a.allocated), 0)) < p.reorder_point as needs_reorder
FROM products p
LEFT JOIN batches b ON b.sku = p.sku
LEFT JOIN (
    SELECT batch_id, COUNT(*) as allocated
    FROM allocations
    GROUP BY batch_id
) a ON a.batch_id = b.id
GROUP BY p.sku, p.name, p.reorder_point;

-- Refresh periodically or on triggers
REFRESH MATERIALIZED VIEW product_inventory_view;
```

```python
def get_inventory_dashboard() -> list[ProductInventory]:
    """Get inventory status from materialized view."""
    rows = db.execute("""
        SELECT * FROM product_inventory_view
        WHERE needs_reorder = true
        ORDER BY available ASC
    """).fetchall()

    return [ProductInventory(**row._mapping) for row in rows]
```

#### Option C: Event-Sourced Read Models

Update read models in response to domain events:

```python
from myproject.domain import events
from myproject.service_layer.unit_of_work import AbstractUnitOfWork


def update_order_summary_on_created(
    event: events.OrderCreated,
    uow: AbstractUnitOfWork,
) -> None:
    """Update read model when order is created."""
    with uow:
        uow.order_summaries.upsert(
            order_id=event.order_id,
            customer_name=get_customer_name(event.customer_id),
            status="pending",
            total=Decimal("0"),
            line_count=0,
            created_at=event.occurred_at,
        )
        uow.commit()


def update_order_summary_on_line_added(
    event: events.OrderLineAdded,
    uow: AbstractUnitOfWork,
) -> None:
    """Update read model when line is added."""
    with uow:
        summary = uow.order_summaries.get(event.order_id)
        summary.line_count += 1
        summary.total += event.line_total
        uow.commit()


def update_order_summary_on_confirmed(
    event: events.OrderConfirmed,
    uow: AbstractUnitOfWork,
) -> None:
    """Update read model when order is confirmed."""
    with uow:
        summary = uow.order_summaries.get(event.order_id)
        summary.status = "confirmed"
        uow.commit()


# Register handlers
EVENT_HANDLERS[events.OrderCreated].append(update_order_summary_on_created)
EVENT_HANDLERS[events.OrderLineAdded].append(update_order_summary_on_line_added)
EVENT_HANDLERS[events.OrderConfirmed].append(update_order_summary_on_confirmed)
```

### 4. Keep Write Side Clean

Write operations still go through domain model:

```python
# Write side: through domain model and service layer
def create_order(cmd: CreateOrder, uow: AbstractUnitOfWork) -> str:
    with uow:
        order = Order.create(cmd.customer_id, cmd.items)
        uow.orders.add(order)
        uow.commit()
    return order.id

# Read side: direct query (no domain model)
def get_order_for_display(order_id: str) -> OrderDetail:
    return views.get_order_detail(order_id)
```

### 5. API Layer Separation

```python
from fastapi import FastAPI, Depends
from myproject.domain import commands
from myproject.service_layer import messagebus, views

app = FastAPI()

# Commands (write)
@app.post("/orders")
def create_order(request: CreateOrderRequest, uow=Depends(get_uow)):
    cmd = commands.CreateOrder(...)
    results = messagebus.handle(cmd, uow)
    return {"order_id": results[0]}

@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str, uow=Depends(get_uow)):
    cmd = commands.ConfirmOrder(order_id=order_id)
    messagebus.handle(cmd, uow)
    return {"status": "confirmed"}

# Queries (read)
@app.get("/orders")
def list_orders(status: str = None, limit: int = 50, offset: int = 0):
    # Direct to views module, no UoW needed
    return views.list_orders(status=status, limit=limit, offset=offset)

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = views.get_order_detail(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order
```

## Analysis Report Template

When auditing for CQRS opportunities:

```markdown
# CQRS Analysis Report

## Current State
- Read queries found: X
- Complex queries (3+ joins): Y
- Aggregations computed in app: Z

## Recommendations

### High Priority
| Query | Location | Issue | Recommendation |
|-------|----------|-------|----------------|
| Order list | `api.py:45` | 4 JOINs, computed totals | Create OrderSummary view |
| Dashboard | `dashboard.py:20` | Real-time aggregation | Materialized view |

### Medium Priority
...

### Suggested Read Models
1. `OrderSummary` - for list views
2. `OrderDetail` - for detail views
3. `ProductInventory` - for dashboard

### Implementation Plan
1. Create views module with direct queries
2. Add event handlers to update denormalized data
3. Migrate API endpoints to use views
```

## References

- See `references/patterns-summary.md` for CQRS overview
- See `references/project-structure.md` for views module organization
