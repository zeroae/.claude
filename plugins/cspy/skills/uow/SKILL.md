---
name: uow
description: Implement Unit of Work pattern for atomic transactions. Use when user says "add unit of work", "implement transactions", "manage database sessions", "atomic operations", or needs transaction boundaries.
---

# Unit of Work Implementer

Implement the Unit of Work pattern to manage atomic transactions across repositories.

## Workflow

### 1. Identify Requirements

Ask the user:
1. **Database/ORM**: SQLAlchemy, Django ORM, raw SQL?
2. **Repositories**: What repositories need to be accessible?
3. **Events**: Should it collect domain events?
4. **Async**: Synchronous or async operations?

### 2. Generate Abstract Unit of Work

```python
from abc import ABC, abstractmethod
from typing import Self


class AbstractUnitOfWork(ABC):
    """
    Abstract base class for Unit of Work pattern.

    Usage:
        with uow:
            entity = uow.repository.get(id)
            entity.do_something()
            uow.commit()

    If an exception occurs, rollback is called automatically on exit.
    """

    # Declare repositories as class attributes for type hints
    # Example: orders: AbstractOrderRepository

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        raise NotImplementedError
```

### 3. Generate SQLAlchemy Implementation

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from myproject.adapters.repository import SqlAlchemyRepository
from myproject.service_layer.unit_of_work import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work.

    Creates a new session for each context manager usage,
    ensuring isolation between transactions.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        # Initialize repositories with the session
        self.orders = SqlAlchemyOrderRepository(self.session)
        self.products = SqlAlchemyProductRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


# Session factory setup
DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine("postgresql://user:pass@localhost/db"),
    expire_on_commit=False,  # Allow accessing attributes after commit
)
```

### 4. Generate Fake for Testing

```python
from myproject.adapters.repository import FakeRepository
from myproject.service_layer.unit_of_work import AbstractUnitOfWork


class FakeUnitOfWork(AbstractUnitOfWork):
    """
    In-memory Unit of Work for testing.

    Uses fake repositories and tracks commit/rollback calls.
    """

    def __init__(self):
        self.orders = FakeOrderRepository()
        self.products = FakeProductRepository()
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> Self:
        self.committed = False
        self.rolled_back = False
        return super().__enter__()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True
```

### 5. Add Event Collection (Optional)

If using domain events:

```python
class AbstractUnitOfWork(ABC):
    """Unit of Work with event collection."""

    def collect_new_events(self) -> Generator[Event, None, None]:
        """
        Collect domain events from all tracked aggregates.

        Call this after commit to gather events for publishing.
        """
        for repository in self._get_repositories():
            for aggregate in repository.seen:
                while aggregate.events:
                    yield aggregate.events.pop(0)

    def _get_repositories(self) -> list[AbstractRepository]:
        """Return all repositories managed by this UoW."""
        # Override in concrete class to return actual repositories
        return []


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):

    def _get_repositories(self) -> list[AbstractRepository]:
        return [self.orders, self.products]
```

### 6. Generate Tests

```python
import pytest
from myproject.service_layer.unit_of_work import (
    SqlAlchemyUnitOfWork,
    FakeUnitOfWork,
)


class TestFakeUnitOfWork:
    """Tests for the fake UoW used in service layer tests."""

    def test_commit_sets_committed_flag(self):
        uow = FakeUnitOfWork()

        with uow:
            uow.commit()

        assert uow.committed

    def test_rollback_on_exception(self):
        uow = FakeUnitOfWork()

        with pytest.raises(ValueError):
            with uow:
                raise ValueError("something went wrong")

        assert uow.rolled_back

    def test_repositories_are_accessible(self):
        uow = FakeUnitOfWork()

        with uow:
            assert uow.orders is not None
            assert uow.products is not None


class TestSqlAlchemyUnitOfWork:
    """Integration tests for SQLAlchemy UoW."""

    @pytest.fixture
    def session_factory(self, test_database):
        """Create session factory connected to test database."""
        return sessionmaker(bind=test_database)

    def test_can_retrieve_entity(self, session_factory, seed_data):
        uow = SqlAlchemyUnitOfWork(session_factory)

        with uow:
            order = uow.orders.get("order-1")

        assert order is not None
        assert order.id == "order-1"

    def test_commit_persists_changes(self, session_factory):
        uow = SqlAlchemyUnitOfWork(session_factory)

        with uow:
            order = Order(id="new-order", customer_id="cust-1")
            uow.orders.add(order)
            uow.commit()

        # Verify in fresh session
        with uow:
            assert uow.orders.get("new-order") is not None

    def test_rollback_discards_changes(self, session_factory):
        uow = SqlAlchemyUnitOfWork(session_factory)

        with uow:
            order = Order(id="rolled-back", customer_id="cust-1")
            uow.orders.add(order)
            # Don't commit - let context manager rollback

        with uow:
            assert uow.orders.get("rolled-back") is None
```

## Common Issues

### Session Already Closed

If you access attributes after the `with` block exits:

```python
# Problem
with uow:
    order = uow.orders.get("order-1")
    uow.commit()

print(order.lines)  # Error: session closed

# Solution: Use expire_on_commit=False
session_factory = sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Detach objects after commit
)
```

### Nested Transactions

Avoid nesting UoW contexts:

```python
# BAD - nested transactions
with uow:
    with uow:  # This doesn't work as expected!
        ...

# GOOD - single transaction boundary
with uow:
    process_step_1(uow)
    process_step_2(uow)
    uow.commit()
```

## References

- See `references/async-uow.md` for async/await implementation and FastAPI integration
- See `../references/patterns-summary.md` for the full UoW pattern
- See `../references/project-structure.md` for file organization
