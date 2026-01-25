---
name: audit
description: Analyze codebase architecture against Cosmic Python patterns. Use when user says "analyze architecture", "check patterns", "audit code", "pattern coverage", or wants to assess DDD adoption.
---

# Architecture Pattern Audit

Analyze the current Python codebase for adherence to Cosmic Python architecture patterns.

## Workflow

### 1. Discover Project Structure

Find Python source directories (`src/`, `app/`, or project name), test directories (`tests/`), and check for existing `domain/`, `service_layer/`, `adapters/` directories.

### 2. Pattern Detection Checklist

For each pattern, search for key indicators:

#### Repository Pattern
- [ ] Abstract repository interface (`AbstractRepository`, `Protocol`)
- [ ] Concrete implementations (SQLAlchemy, in-memory)
- [ ] Fake repository for testing
- [ ] Standard methods: `add()`, `get()`, `list()`

Search: `class.*Repository`, `AbstractRepository`, `def add\(self`

#### Service Layer
- [ ] Service functions accept UoW dependency
- [ ] Orchestration logic separate from web handlers
- [ ] Explicit transaction management

Search: `def.*uow.*AbstractUnitOfWork`, `with uow:`, `uow.commit()`

#### Unit of Work
- [ ] Abstract UoW interface
- [ ] Context manager (`__enter__`, `__exit__`)
- [ ] `commit()` and `rollback()` methods

Search: `class.*UnitOfWork`, `def __enter__`, `def commit`

#### Domain Model
- [ ] Entities with identity (`id` field)
- [ ] Value objects (`@dataclass(frozen=True)`)
- [ ] Business logic in model classes
- [ ] No infrastructure imports in domain

Search: `@dataclass`, `@dataclass(frozen=True)`

#### Aggregates
- [ ] Clear aggregate roots with invariant enforcement
- [ ] Child entities accessed only through root

#### Domain Events
- [ ] Event classes (past tense naming)
- [ ] Events collected on aggregates

Search: `class.*Event`, `class.*Created`, `events.append`

#### Commands
- [ ] Command classes (imperative naming)
- [ ] One handler per command

Search: `class.*Command`, `class Create.*`

#### Message Bus
- [ ] Central dispatcher with handler registration

Search: `HANDLERS.*=`, `messagebus`

#### CQRS
- [ ] Separate read models/queries
- [ ] Direct SQL for reads, domain model for writes

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
