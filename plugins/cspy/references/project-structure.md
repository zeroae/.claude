# Cosmic Python Project Structure

> **Attribution**: This content is derived from "Architecture Patterns with Python" by Harry Percival and Bob Gregory, available at [cosmicpython.com](https://cosmicpython.com). Licensed under [CC BY-NC-ND 3.0](https://creativecommons.org/licenses/by-nc-nd/3.0/).

Recommended project layout from the book's Appendix B.

## Standard Layout

```
myproject/
├── pyproject.toml
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── domain/              # Domain model
│       │   ├── __init__.py
│       │   ├── model.py         # Entities, Value Objects, Aggregates
│       │   ├── events.py        # Domain events
│       │   └── commands.py      # Command definitions
│       │
│       ├── service_layer/       # Application services
│       │   ├── __init__.py
│       │   ├── handlers.py      # Command/Event handlers
│       │   ├── unit_of_work.py  # UoW abstract + implementations
│       │   └── messagebus.py    # Message bus
│       │
│       ├── adapters/            # Infrastructure
│       │   ├── __init__.py
│       │   ├── repository.py    # Repository implementations
│       │   ├── orm.py           # SQLAlchemy mappings
│       │   └── notifications.py # External service adapters
│       │
│       └── entrypoints/         # Application entry points
│           ├── __init__.py
│           ├── api.py           # FastAPI/Flask app
│           ├── cli.py           # Command-line interface
│           └── redis_eventconsumer.py
│
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Domain model tests
│   │   └── test_model.py
│   ├── integration/             # Service layer tests
│   │   └── test_handlers.py
│   └── e2e/                     # End-to-end tests
│       └── test_api.py
│
└── docker-compose.yml
```

## File Responsibilities

### `domain/model.py`
Contains business logic with no infrastructure dependencies.

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

@dataclass(frozen=True)
class OrderLine:
    """Value object for order line items."""
    sku: str
    qty: int

@dataclass
class Batch:
    """Entity representing inventory batch."""
    reference: str
    sku: str
    qty: int
    eta: Optional[date]
    allocations: set[OrderLine] = field(default_factory=set)

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self.allocations.add(line)
        else:
            raise OutOfStock(f"Cannot allocate {line.sku}")

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    @property
    def available_quantity(self) -> int:
        return self.qty - sum(line.qty for line in self.allocations)
```

### `domain/events.py`
Domain events as immutable dataclasses.

```python
from dataclasses import dataclass
from datetime import datetime

class Event:
    """Base class for domain events."""
    pass

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class StockAllocated(Event):
    order_id: str
    sku: str
    qty: int
    batch_ref: str
```

### `domain/commands.py`
Commands as immutable dataclasses.

```python
from dataclasses import dataclass

class Command:
    """Base class for commands."""
    pass

@dataclass(frozen=True)
class CreateOrder:
    customer_id: str
    items: tuple[dict, ...]

@dataclass(frozen=True)
class AllocateStock:
    order_id: str
    sku: str
    qty: int
```

### `service_layer/unit_of_work.py`
Unit of Work pattern implementation.

```python
from abc import ABC, abstractmethod
from typing import Self

class AbstractUnitOfWork(ABC):
    batches: AbstractRepository

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.rollback()

    def collect_new_events(self):
        for batch in self.batches.seen:
            while batch.events:
                yield batch.events.pop(0)

    @abstractmethod
    def commit(self): ...

    @abstractmethod
    def rollback(self): ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = SqlAlchemyRepository(self.session)
        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
```

### `service_layer/handlers.py`
Command and event handlers.

```python
from myproject.domain import model, events, commands
from myproject.service_layer.unit_of_work import AbstractUnitOfWork

def allocate(cmd: commands.AllocateStock, uow: AbstractUnitOfWork) -> str:
    with uow:
        batches = uow.batches.list()
        batch = model.allocate(cmd.sku, cmd.qty, batches)
        uow.commit()
    return batch.reference

def send_out_of_stock_notification(event: events.OutOfStock, uow: AbstractUnitOfWork):
    # Send notification via external adapter
    pass
```

### `service_layer/messagebus.py`
Message bus for dispatching commands and events.

```python
from typing import Callable, Type, Union
from myproject.domain import commands, events
from myproject.service_layer import handlers, unit_of_work

Message = Union[commands.Command, events.Event]

COMMAND_HANDLERS: dict[Type[commands.Command], Callable] = {
    commands.AllocateStock: handlers.allocate,
    commands.CreateOrder: handlers.create_order,
}

EVENT_HANDLERS: dict[Type[events.Event], list[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.StockAllocated: [handlers.publish_allocated_event],
}

def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            result = handle_command(message, queue, uow)
            results.append(result)
    return results
```

### `adapters/repository.py`
Repository implementations.

```python
from abc import ABC, abstractmethod
from typing import Set
from myproject.domain import model

class AbstractRepository(ABC):
    def __init__(self):
        self.seen: Set[model.Batch] = set()

    def add(self, batch: model.Batch):
        self._add(batch)
        self.seen.add(batch)

    def get(self, reference: str) -> model.Batch:
        batch = self._get(reference)
        if batch:
            self.seen.add(batch)
        return batch

    @abstractmethod
    def _add(self, batch: model.Batch): ...

    @abstractmethod
    def _get(self, reference: str) -> model.Batch: ...


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, batch):
        self.session.add(batch)

    def _get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).first()


class FakeRepository(AbstractRepository):
    def __init__(self, batches=None):
        super().__init__()
        self._batches = set(batches or [])

    def _add(self, batch):
        self._batches.add(batch)

    def _get(self, reference):
        return next((b for b in self._batches if b.reference == reference), None)

    def list(self):
        return list(self._batches)
```

### `adapters/orm.py`
SQLAlchemy ORM mappings (classical mapping style).

```python
from sqlalchemy import Table, Column, Integer, String, Date, ForeignKey, MetaData
from sqlalchemy.orm import registry, relationship
from myproject.domain import model

mapper_registry = registry()
metadata = mapper_registry.metadata

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("qty", Integer),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", Integer, ForeignKey("order_lines.id")),
    Column("batch_id", Integer, ForeignKey("batches.id")),
)

def start_mappers():
    mapper_registry.map_imperatively(model.Batch, batches)
```

### `entrypoints/api.py`
FastAPI application entry point.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from myproject.domain import commands
from myproject.service_layer import messagebus, unit_of_work

app = FastAPI()

class AllocateRequest(BaseModel):
    order_id: str
    sku: str
    qty: int

@app.post("/allocate")
def allocate_endpoint(request: AllocateRequest):
    try:
        uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
        cmd = commands.AllocateStock(
            order_id=request.order_id,
            sku=request.sku,
            qty=request.qty,
        )
        results = messagebus.handle(cmd, uow)
        return {"batch_ref": results[0]}
    except model.OutOfStock as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Test Organization

### `tests/unit/test_model.py`
Pure domain logic tests, no infrastructure.

```python
import pytest
from myproject.domain.model import Batch, OrderLine

def test_allocating_reduces_available_quantity():
    batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=None)
    line = OrderLine("order-001", "SMALL-TABLE", 2)

    batch.allocate(line)

    assert batch.available_quantity == 18
```

### `tests/integration/test_handlers.py`
Service layer tests with fake repositories.

```python
from myproject.service_layer import handlers
from myproject.adapters.repository import FakeRepository

class FakeUnitOfWork:
    def __init__(self):
        self.batches = FakeRepository()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

def test_allocate_returns_batch_ref():
    uow = FakeUnitOfWork()
    uow.batches.add(Batch("batch-001", "LAMP", 100, None))

    result = handlers.allocate(commands.AllocateStock("order-1", "LAMP", 10), uow)

    assert result == "batch-001"
```

### `tests/e2e/test_api.py`
End-to-end tests against real API.

```python
import pytest
from fastapi.testclient import TestClient
from myproject.entrypoints.api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_returns_allocation(client, add_stock):
    add_stock([("batch-001", "LAMP", 100, None)])

    response = client.post("/allocate", json={
        "order_id": "order-001",
        "sku": "LAMP",
        "qty": 3,
    })

    assert response.status_code == 200
    assert response.json()["batch_ref"] == "batch-001"
```

## Configuration

### `pyproject.toml`

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.100",
    "sqlalchemy>=2.0",
    "uvicorn>=0.23",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "httpx>=0.24",  # For TestClient
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myproject
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myproject
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```
