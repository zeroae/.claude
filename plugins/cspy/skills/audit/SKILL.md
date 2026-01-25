---
name: audit
description: Analyze codebase architecture against Cosmic Python patterns. Use when user says "analyze architecture", "check patterns", "audit code", or wants to understand pattern coverage.
---

# Architecture Pattern Audit

Analyze the current Python codebase for adherence to Cosmic Python architecture patterns.

## Workflow

### 1. Discover Project Structure

First, understand the project layout:

```
- Find Python source directories (src/, app/, or project name)
- Identify test directories (tests/, test/)
- Locate configuration files (pyproject.toml, setup.py)
- Check for existing domain/service/adapter directories
```

### 2. Pattern Detection Checklist

For each pattern, search for indicators:

#### Repository Pattern
- [ ] Abstract repository interface exists (`AbstractRepository`, `Repository` protocol)
- [ ] Concrete implementations (SQLAlchemy, in-memory, file-based)
- [ ] Fake/mock repository for testing
- [ ] Repository methods: `add()`, `get()`, `list()`

Search patterns:
```python
# Look for
class.*Repository
def add\(self.*\)
def get\(self.*\)
AbstractRepository
```

#### Service Layer
- [ ] Service functions/handlers exist
- [ ] Services accept dependencies (UoW, repositories)
- [ ] Services orchestrate domain operations
- [ ] Clear separation from web handlers

Search patterns:
```python
# Look for
def.*uow.*AbstractUnitOfWork
with uow:
uow.commit()
```

#### Unit of Work
- [ ] Abstract UoW interface
- [ ] Context manager implementation (`__enter__`, `__exit__`)
- [ ] `commit()` and `rollback()` methods
- [ ] Repository access via UoW

Search patterns:
```python
# Look for
class.*UnitOfWork
def __enter__
def commit
def rollback
```

#### Domain Model
- [ ] Entities with identity
- [ ] Value objects (frozen dataclasses)
- [ ] Domain logic in model classes (not services)
- [ ] No infrastructure imports in domain

Search patterns:
```python
# Look for
@dataclass
@dataclass(frozen=True)
class.*:.*\n.*id:
```

#### Aggregates
- [ ] Clear aggregate roots
- [ ] Invariant enforcement in aggregate methods
- [ ] Single entry point to aggregate cluster

#### Domain Events
- [ ] Event classes defined
- [ ] Events named in past tense
- [ ] Events collected and dispatched

Search patterns:
```python
# Look for
class.*Event
class.*Created
class.*Updated
class.*Deleted
events.append
```

#### Commands
- [ ] Command classes defined
- [ ] Commands named imperatively
- [ ] Command handlers exist

Search patterns:
```python
# Look for
class.*Command
class Create.*
class Update.*
class Delete.*
```

#### Message Bus
- [ ] Central message dispatcher
- [ ] Handler registration
- [ ] Event collection after command handling

Search patterns:
```python
# Look for
HANDLERS.*=
def handle.*message
messagebus
```

#### CQRS
- [ ] Separate read models/queries
- [ ] Write operations through domain model
- [ ] Direct database queries for reads

### 3. Dependency Direction Check

Verify dependencies point inward:

```
Entrypoints → Service Layer → Domain Model
                    ↓
               Adapters

Domain should NOT import from:
- flask, fastapi, django (web frameworks)
- sqlalchemy, databases (ORMs)
- requests, httpx (external services)
```

### 4. Generate Report

Output a structured report:

```markdown
# Architecture Audit Report

## Summary
- **Patterns Detected**: X/8
- **Dependency Violations**: Y
- **Recommendations**: Z

## Pattern Coverage

### Repository Pattern: [FULL | PARTIAL | MISSING]
**Status**: What was found
**Location**: File paths
**Issues**: What's missing
**Recommendation**: Next steps

### Service Layer: [FULL | PARTIAL | MISSING]
...

### Unit of Work: [FULL | PARTIAL | MISSING]
...

### Domain Model: [FULL | PARTIAL | MISSING]
...

### Aggregates: [FULL | PARTIAL | MISSING]
...

### Domain Events: [FULL | PARTIAL | MISSING]
...

### Commands: [FULL | PARTIAL | MISSING]
...

### Message Bus: [FULL | PARTIAL | MISSING]
...

### CQRS: [FULL | PARTIAL | MISSING]
...

## Dependency Analysis
- Domain imports: [CLEAN | VIOLATIONS FOUND]
- Violation details...

## Recommended Adoption Path
1. First priority...
2. Second priority...
3. ...

## Quick Wins
- Immediate improvements that require minimal effort
```

## Example Output

```
# Architecture Audit Report

## Summary
- **Patterns Detected**: 3/8 (Repository, Service Layer partial, Domain Model partial)
- **Dependency Violations**: 2
- **Recommendations**: 5

## Pattern Coverage

### Repository Pattern: PARTIAL
**Status**: Repository class exists but lacks abstraction
**Location**: `src/db/repository.py`
**Issues**:
- No abstract interface (can't swap implementations)
- No fake repository for testing
**Recommendation**: Extract `AbstractRepository` protocol, create `FakeRepository`

### Service Layer: PARTIAL
**Status**: Some business logic in service functions
**Location**: `src/services/orders.py`
**Issues**:
- Services don't accept UoW dependency
- Direct database access in services
**Recommendation**: Inject UoW, move DB calls to repository

### Unit of Work: MISSING
**Status**: No UoW pattern detected
**Issues**:
- Transactions managed inconsistently
- No atomic operations guarantee
**Recommendation**: Implement AbstractUnitOfWork with SqlAlchemy session

### Domain Model: PARTIAL
**Status**: Some domain classes exist
**Location**: `src/models/`
**Issues**:
- Models are ORM classes (SQLAlchemy models)
- Business logic in services, not domain
**Recommendation**: Separate domain model from ORM, move logic to entities

## Dependency Analysis
**Violations Found**:
1. `src/domain/order.py` imports `sqlalchemy` (line 3)
2. `src/domain/user.py` imports `flask` (line 5)

## Recommended Adoption Path
1. Extract domain model from ORM classes
2. Create abstract repository interface
3. Implement Unit of Work
4. Move business logic to domain model
5. Add domain events for side effects

## Quick Wins
- Add type hints to service functions
- Create FakeRepository for faster tests
- Remove framework imports from domain/
```

## References

See `references/patterns-summary.md` for pattern details and code examples.
