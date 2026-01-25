# Async Unit of Work Implementation

Reference for async/await Unit of Work pattern with SQLAlchemy and FastAPI integration.

## Async Unit of Work Base Class

```python
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AbstractAsyncUnitOfWork(ABC):
    """Async Unit of Work base class."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
```

## SQLAlchemy Async Implementation

```python
class SqlAlchemyAsyncUnitOfWork(AbstractAsyncUnitOfWork):
    """Async SQLAlchemy Unit of Work."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()
        self.orders = SqlAlchemyAsyncOrderRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
```

## Async Service Layer Usage

```python
async def create_order(
    customer_id: str,
    items: list[dict],
    uow: AbstractAsyncUnitOfWork,
) -> str:
    async with uow:
        customer = await uow.customers.get(customer_id)
        if not customer:
            raise CustomerNotFound(customer_id)

        order = Order.create(customer_id, items)
        await uow.orders.add(order)
        await uow.commit()

    return order.id
```

## FastAPI Dependency Injection

```python
from fastapi import Depends

async def get_async_uow() -> AsyncGenerator[AbstractAsyncUnitOfWork, None]:
    """Dependency that provides an async Unit of Work."""
    uow = SqlAlchemyAsyncUnitOfWork(async_session_factory)
    try:
        yield uow
    finally:
        await uow.session.close()


@app.post("/orders")
async def create_order_endpoint(
    request: CreateOrderRequest,
    uow: AbstractAsyncUnitOfWork = Depends(get_async_uow),
):
    order_id = await create_order(
        customer_id=request.customer_id,
        items=request.items,
        uow=uow,
    )
    return {"order_id": order_id}
```

## Sync FastAPI Dependency (Alternative)

For synchronous UoW with FastAPI:

```python
from fastapi import Depends

def get_uow() -> Generator[AbstractUnitOfWork, None, None]:
    """Dependency that provides a Unit of Work."""
    uow = SqlAlchemyUnitOfWork(session_factory)
    yield uow


@app.post("/orders")
def create_order_endpoint(
    request: CreateOrderRequest,
    uow: AbstractUnitOfWork = Depends(get_uow),
):
    order_id = create_order(
        customer_id=request.customer_id,
        items=request.items,
        uow=uow,
    )
    return {"order_id": order_id}
```

## Testing Async Services

```python
import pytest

class FakeAsyncUnitOfWork(AbstractAsyncUnitOfWork):
    def __init__(self):
        self.orders = FakeAsyncRepository()
        self.customers = FakeAsyncRepository()
        self.committed = False

    async def __aenter__(self):
        self.committed = False
        return await super().__aenter__()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


@pytest.mark.asyncio
async def test_create_order_async():
    uow = FakeAsyncUnitOfWork()
    await uow.customers.add(Customer(id="cust-1"))

    order_id = await create_order(
        customer_id="cust-1",
        items=[{"sku": "LAMP", "qty": 2}],
        uow=uow,
    )

    assert order_id is not None
    assert uow.committed
```
