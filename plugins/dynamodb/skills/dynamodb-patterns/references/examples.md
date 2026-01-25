# Real-World DynamoDB Examples

Case studies from Rick Houlihan's AWS re:Invent talks demonstrating pattern application.

## Table of Contents
- [Audible WhisperSync](#audible)
- [Delivery Service](#delivery-service)

---

## Audible WhisperSync {#audible}

Syncs reading/listening position across Kindle and Audible apps.

### Access Patterns

1. Get user's library (all books)
2. Get reading position for a specific book
3. Update reading position
4. Get book metadata
5. Find all users reading a specific book (analytics)

### Entity Analysis

- **User**: Has library of books
- **Book**: Has metadata, owned by many users
- **UserBook**: Junction - reading position per user per book

### Single-Table Design

```
PK              | SK              | GSI1PK        | Attributes
----------------|-----------------|---------------|------------------
USER#12345      | BOOK#asin-001   | ASIN#asin-001 | position, lastRead, ...
USER#12345      | BOOK#asin-002   | ASIN#asin-002 | position, lastRead, ...
USER#67890      | BOOK#asin-001   | ASIN#asin-001 | position, lastRead, ...
BOOK#asin-001   | META            | -             | title, author, duration, ...
BOOK#asin-002   | META            | -             | title, author, duration, ...
```

### Query Implementation

| Access Pattern | Implementation |
|---------------|----------------|
| User's library | `PK=USER#12345, SK begins_with BOOK#` |
| Reading position | `PK=USER#12345, SK=BOOK#asin-001` |
| Update position | `UpdateItem PK=USER#12345, SK=BOOK#asin-001` |
| Book metadata | `PK=BOOK#asin-001, SK=META` |
| Users reading book | GSI1: `GSI1PK=ASIN#asin-001` |

### Key Insights

- **User-centric primary key**: Most queries are "for this user, get X"
- **GSI for inverse query**: Find users by book (analytics use case)
- **Metadata separate**: Book info stored once, not duplicated per user
- **Position updates are single-item**: Fast, no transactions needed

---

## Delivery Service {#delivery-service}

Complex logistics app with customers, orders, drivers, deliveries.

### Access Patterns

1. Get customer profile
2. Get customer's orders
3. Get order details with items
4. Get driver's current deliveries
5. Get delivery status
6. Update delivery location
7. Find orders by status (for dispatch)

### Entity Analysis

- **Customer**: Places orders
- **Order**: Contains items, assigned to delivery
- **OrderItem**: Product in an order
- **Driver**: Handles deliveries
- **Delivery**: Links order to driver with status/location

### Relational Model (What NOT to Do)

```
Customers    Orders       OrderItems    Drivers    Deliveries
---------    ------       ----------    -------    ----------
id           id           id            id         id
name         customer_id  order_id      name       order_id
email        status       product_id    vehicle    driver_id
             total        quantity                 status
                          price                    location
```

This requires JOINs and multiple queries. Don't do this in DynamoDB.

### Single-Table Design

```
PK              | SK                    | GSI1PK          | GSI1SK           | Attributes
----------------|----------------------|-----------------|------------------|------------
CUST#c001       | PROFILE              | -               | -                | name, email, ...
CUST#c001       | ORDER#o001           | STATUS#pending  | DATE#2024-01-15  | total, ...
CUST#c001       | ORDER#o002           | STATUS#delivered| DATE#2024-01-14  | total, ...
ORDER#o001      | ITEM#prod-a          | -               | -                | qty, price, ...
ORDER#o001      | ITEM#prod-b          | -               | -                | qty, price, ...
ORDER#o001      | DELIVERY             | DRIVER#d001     | STATUS#in_transit| location, ...
DRIVER#d001     | PROFILE              | -               | -                | name, vehicle, ...
DRIVER#d001     | DELIVERY#ORDER#o001  | -               | -                | (reference)
```

### Query Implementation

| Access Pattern | Implementation |
|---------------|----------------|
| Customer profile | `PK=CUST#c001, SK=PROFILE` |
| Customer orders | `PK=CUST#c001, SK begins_with ORDER#` |
| Order with items | `PK=ORDER#o001` (returns items + delivery) |
| Driver's deliveries | `PK=DRIVER#d001, SK begins_with DELIVERY#` |
| Delivery status | `PK=ORDER#o001, SK=DELIVERY` |
| Update location | `UpdateItem PK=ORDER#o001, SK=DELIVERY` |
| Orders by status | GSI1: `GSI1PK=STATUS#pending` |

### Key Insights

- **Multiple entry points**: Same data accessible via customer, order, or driver
- **Denormalization**: Delivery info stored under both ORDER# and DRIVER#
- **GSI for status queries**: Dispatch needs to find pending orders quickly
- **Composite SK**: `DELIVERY#ORDER#o001` under driver enables range queries

### Design Trade-offs

| Decision | Rationale |
|----------|-----------|
| Duplicate delivery under driver | Enables "driver's deliveries" without GSI |
| Status in GSI | Dispatch queries are frequent, need efficiency |
| Items under ORDER# PK | Always fetched with order, natural grouping |
| Customer as PK prefix | Most queries are customer-initiated |

---

## Pattern Application Summary

Both examples demonstrate:

1. **Access patterns first**: Schema designed around queries, not entities
2. **Single table**: All entities in one table with key prefixes
3. **GSI for secondary access**: When primary key doesn't serve a pattern
4. **Strategic denormalization**: Duplicate data to avoid joins
5. **Composite keys**: Enable range queries and hierarchical access
