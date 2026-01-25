---
name: service-layer
description: Generate service layer functions following Cosmic Python patterns. Use when user says "create service function", "add use case", "implement handler", "orchestration code", or needs to wire up domain operations.
---

# Service Layer Generator

Generate service layer functions that orchestrate domain operations following Cosmic Python patterns.

## Workflow

### 1. Gather Requirements

Ask the user:
1. **Use case name**: What operation? (e.g., "place order", "allocate stock")
2. **Input parameters**: What data does it need?
3. **Domain operations**: What domain objects are involved?
4. **Output**: What should it return?
5. **Error cases**: What can go wrong?

### 2. Generate Service Function

Follow this template:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myproject.service_layer.unit_of_work import AbstractUnitOfWork

def use_case_name(
    param1: str,
    param2: int,
    uow: "AbstractUnitOfWork",
) -> ReturnType:
    """
    Brief description of what this use case does.

    Args:
        param1: Description
        param2: Description
        uow: Unit of Work for transaction management

    Returns:
        Description of return value

    Raises:
        DomainException: When validation fails
        NotFoundError: When entity doesn't exist
    """
    with uow:
        # 1. Fetch required aggregates
        aggregate = uow.repository.get(id)

        # 2. Validate preconditions
        if not aggregate:
            raise NotFoundError(f"Entity {id} not found")

        # 3. Execute domain logic
        result = aggregate.do_operation(param1, param2)

        # 4. Persist changes (if any new entities)
        # uow.repository.add(new_entity)

        # 5. Commit transaction
        uow.commit()

    # 6. Return result
    return result
```

### 3. Key Principles

1. **Accept UoW as parameter** - Don't create it inside the function
2. **Use context manager** - `with uow:` ensures cleanup
3. **Fetch first, then act** - Get aggregates before operating
4. **Let domain raise exceptions** - Don't catch domain errors here
5. **Commit explicitly** - Call `uow.commit()` to persist
6. **Keep it thin** - Logic belongs in domain model

### 4. Generate Corresponding Test

```python
import pytest
from myproject.domain.model import Aggregate
from myproject.service_layer.handlers import use_case_name

class FakeUnitOfWork:
    def __init__(self):
        self.repository = FakeRepository()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_use_case_happy_path():
    # Arrange
    uow = FakeUnitOfWork()
    uow.repository.add(Aggregate(id="agg-1", ...))

    # Act
    result = use_case_name(param1="value", param2=10, uow=uow)

    # Assert
    assert result == expected_value
    assert uow.committed


def test_use_case_raises_when_not_found():
    uow = FakeUnitOfWork()

    with pytest.raises(NotFoundError):
        use_case_name(param1="value", param2=10, uow=uow)


def test_use_case_raises_on_validation_error():
    uow = FakeUnitOfWork()
    uow.repository.add(Aggregate(id="agg-1", ...))

    with pytest.raises(DomainException):
        use_case_name(param1="invalid", param2=-1, uow=uow)
```

## Anti-Patterns to Avoid

### Don't Create UoW Inside Function

```python
# BAD - hard to test
def create_order(customer_id: str, items: list[dict]) -> str:
    uow = SqlAlchemyUnitOfWork()  # Can't inject fake for testing
    with uow:
        ...

# GOOD - UoW injected
def create_order(customer_id: str, items: list[dict], uow: AbstractUnitOfWork) -> str:
    with uow:
        ...
```

### Don't Put Business Logic Here

```python
# BAD - logic in service layer
def apply_discount(order_id: str, discount_code: str, uow: AbstractUnitOfWork):
    with uow:
        order = uow.orders.get(order_id)
        discount = uow.discounts.get(discount_code)

        # Business logic doesn't belong here!
        if discount.type == "percent":
            order.total = order.total * (1 - discount.amount / 100)
        elif discount.type == "fixed":
            order.total = order.total - discount.amount

        uow.commit()

# GOOD - delegate to domain
def apply_discount(order_id: str, discount_code: str, uow: AbstractUnitOfWork):
    with uow:
        order = uow.orders.get(order_id)
        discount = uow.discounts.get(discount_code)

        order.apply_discount(discount)  # Domain handles the logic
        uow.commit()
```

### Don't Catch Domain Exceptions

```python
# BAD - swallowing domain errors
def create_order(customer_id: str, items: list[dict], uow: AbstractUnitOfWork):
    with uow:
        try:
            order = Order.create(customer_id, items)
        except InvalidOrder:
            return None  # Caller doesn't know what went wrong
        uow.orders.add(order)
        uow.commit()
    return order.id

# GOOD - let exceptions propagate
def create_order(customer_id: str, items: list[dict], uow: AbstractUnitOfWork):
    with uow:
        order = Order.create(customer_id, items)  # May raise InvalidOrder
        uow.orders.add(order)
        uow.commit()
    return order.id
```

## References

- See `references/use-case-patterns.md` for common patterns (create, update, query, cross-aggregate)
- See `../references/patterns-summary.md` for the full service layer pattern
- See `../references/project-structure.md` for where to place service functions
