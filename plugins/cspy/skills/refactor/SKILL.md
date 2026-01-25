---
name: refactor
description: Guide incremental adoption of Cosmic Python patterns. Use when user says "adopt patterns", "improve architecture", "refactor to DDD", "migrate to clean architecture", "legacy modernization", or needs migration guidance.
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

### Steps 2-6: Repository → Unit of Work → Aggregates → Events → CQRS

See `references/refactoring-steps.md` for detailed before/after code examples for each step.

**Summary**:
- **Step 2 (Repository)**: Abstract database access with interfaces
- **Step 3 (Unit of Work)**: Manage transactions consistently
- **Step 4 (Aggregates)**: Move business rules to domain model
- **Step 5 (Events)**: Decouple side effects with domain events
- **Step 6 (CQRS)**: Optimize reads separately from writes

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

- See `references/refactoring-steps.md` for detailed Steps 2-6 code examples
- See `../references/patterns-summary.md` for pattern overview
- See `../references/project-structure.md` for target structure
