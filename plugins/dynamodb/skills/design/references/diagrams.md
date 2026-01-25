# DynamoDB Design Diagrams

Templates for generating schema visualizations.

> **Table Layout Options:** For detailed comparison of ASCII vs Mermaid Block formats, see [table-layout-options.md](table-layout-options.md)

## Entity-Relationship Diagram (ERD)

Use Mermaid ERD syntax to show entities and relationships before mapping to DynamoDB.

### Relationship Notation

| Symbol | Meaning |
|--------|---------|
| `\|\|` | Exactly one |
| `o\|` | Zero or one |
| `}o` | Zero or more |
| `}\|` | One or more |

### Template

```mermaid
erDiagram
    ENTITY_A ||--o{ ENTITY_B : "relationship"
    ENTITY_B ||--|{ ENTITY_C : "relationship"
    ENTITY_C }o--|| ENTITY_D : "relationship"
```

### E-Commerce Example

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER_ITEM }o--|| PRODUCT : references
    USER ||--o{ ADDRESS : has
    ORDER }o--|| ADDRESS : "ships to"
```

### Social Network Example

```mermaid
erDiagram
    USER ||--o{ POST : creates
    USER ||--o{ FOLLOW : follows
    FOLLOW }o--|| USER : "followed by"
    POST ||--o{ LIKE : receives
    LIKE }o--|| USER : "liked by"
```

### Gaming Example

```mermaid
erDiagram
    PLAYER ||--o{ CHARACTER : owns
    CHARACTER ||--|{ INVENTORY_ITEM : has
    INVENTORY_ITEM }o--|| ITEM_TEMPLATE : "instance of"
    PLAYER ||--o{ ACHIEVEMENT : earns
    PLAYER ||--o{ MATCH_HISTORY : "participates in"
```

---

## Table Layout Diagram

ASCII visualization showing item collections grouped by partition key.

### Template

```
┌─ Item Collection: <PK_VALUE> ───────────────────────────────┐
│                                                             │
│  PK          │ SK           │ Type    │ Attributes          │
│  ────────────┼──────────────┼─────────┼──────────────────── │
│  <pk>        │ <sk1>        │ <type>  │ <attrs>             │
│  <pk>        │ <sk2>        │ <type>  │ <attrs>             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### E-Commerce Example

```
┌─ Item Collection: USER#u123 ────────────────────────────────┐
│                                                             │
│  PK          │ SK              │ Type    │ Attributes       │
│  ────────────┼─────────────────┼─────────┼───────────────── │
│  USER#u123   │ PROFILE         │ User    │ name, email      │
│  USER#u123   │ ADDRESS#home    │ Address │ street, city     │
│  USER#u123   │ ADDRESS#work    │ Address │ street, city     │
│  USER#u123   │ ORDER#o001      │ Order   │ total, status    │
│  USER#u123   │ ORDER#o002      │ Order   │ total, status    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Item Collection: ORDER#o001 ───────────────────────────────┐
│                                                             │
│  PK          │ SK              │ Type      │ Attributes     │
│  ────────────┼─────────────────┼───────────┼─────────────── │
│  ORDER#o001  │ META            │ OrderMeta │ date, address  │
│  ORDER#o001  │ ITEM#sku-a      │ OrderItem │ qty, price     │
│  ORDER#o001  │ ITEM#sku-b      │ OrderItem │ qty, price     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Social Network Example

```
┌─ Item Collection: USER#u12345 ──────────────────────────────┐
│                                                             │
│  PK           │ SK             │ Type     │ Attributes      │
│  ─────────────┼────────────────┼──────────┼──────────────── │
│  USER#u12345  │ INFO           │ User     │ name, bio       │
│  USER#u12345  │ COUNT          │ Stats    │ posts, follows  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Item Collection: USER#u12345#follower ─────────────────────┐
│                                                             │
│  PK                   │ SK           │ Type    │ Attributes │
│  ─────────────────────┼──────────────┼─────────┼─────────── │
│  USER#u12345#follower │ USER#u999    │ Follow  │ since      │
│  USER#u12345#follower │ USER#u888    │ Follow  │ since      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Item Collection: POST#p001 ────────────────────────────────┐
│                                                             │
│  PK          │ SK             │ Type    │ Attributes        │
│  ────────────┼────────────────┼─────────┼────────────────── │
│  POST#p001   │ META           │ Post    │ content, author   │
│  POST#p001   │ LIKE#u999      │ Like    │ timestamp         │
│  POST#p001   │ LIKE#u888      │ Like    │ timestamp         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GSI Visualization

Show how GSI projects data for secondary access patterns.

### Template

```
Base Table                          GSI1 (by email)
┌────────────┬──────────┐           ┌────────────────┬──────────┐
│ PK         │ SK       │           │ GSI1PK         │ GSI1SK   │
├────────────┼──────────┤           ├────────────────┼──────────┤
│ USER#123   │ PROFILE  │ ───────── │ EMAIL#a@b.com  │ USER#123 │
│ USER#456   │ PROFILE  │ ───────── │ EMAIL#x@y.com  │ USER#456 │
└────────────┴──────────┘           └────────────────┴──────────┘
```

### Overloaded GSI Example

```
Base Table                          GSI1 (overloaded)
┌────────────┬──────────┐           ┌─────────────────┬──────────────┐
│ PK         │ SK       │           │ GSI1PK          │ GSI1SK       │
├────────────┼──────────┤           ├─────────────────┼──────────────┤
│ USER#123   │ PROFILE  │ ───────── │ EMAIL#a@b.com   │ USER#123     │
│ USER#123   │ ORDER#1  │ ───────── │ STATUS#pending  │ 2024-01-15   │
│ PROD#sku-a │ INFO     │ ───────── │ CAT#electronics │ PRICE#299    │
└────────────┴──────────┘           └─────────────────┴──────────────┘

GSI1 serves multiple access patterns:
• Find user by email:    GSI1PK = EMAIL#...
• Find pending orders:   GSI1PK = STATUS#pending
• Products by category:  GSI1PK = CAT#electronics
```

---

## Access Pattern Matrix

Combine with diagrams to show which queries use which keys.

```
┌─────────────────────────┬───────────┬─────────────────────────────────┐
│ Access Pattern          │ Index     │ Key Condition                   │
├─────────────────────────┼───────────┼─────────────────────────────────┤
│ Get user profile        │ Base      │ PK=USER#id, SK=PROFILE          │
│ User's orders           │ Base      │ PK=USER#id, SK begins_with ORDER│
│ Order items             │ Base      │ PK=ORDER#id, SK begins_with ITEM│
│ Find user by email      │ GSI1      │ GSI1PK=EMAIL#...                │
│ Orders by status        │ GSI1      │ GSI1PK=STATUS#..., sort by date │
└─────────────────────────┴───────────┴─────────────────────────────────┘
```

---

## Access Pattern Flow

Mermaid flowchart showing how queries route through table and GSIs.

### Template

```mermaid
flowchart LR
    subgraph Queries
        Q1[Query 1]
        Q2[Query 2]
        Q3[Query 3]
    end
    subgraph Indexes
        Base[(Base Table)]
        GSI1[(GSI1)]
    end
    Q1 --> Base
    Q2 --> Base
    Q3 --> GSI1
```

### E-Commerce Example

```mermaid
flowchart LR
    subgraph Access Patterns
        AP1[Get user profile]
        AP2[User's orders]
        AP3[Order items]
        AP4[Find by email]
        AP5[Orders by status]
    end
    subgraph Table & Indexes
        Base[(Base Table<br/>PK + SK)]
        GSI1[(GSI1<br/>email / status)]
    end
    AP1 --> Base
    AP2 --> Base
    AP3 --> Base
    AP4 --> GSI1
    AP5 --> GSI1
```

### Social Network Example

```mermaid
flowchart LR
    subgraph Access Patterns
        AP1[Get user info]
        AP2[User's followers]
        AP3[User's posts]
        AP4[Post likes]
        AP5[User timeline]
    end
    subgraph Table & Indexes
        Base[(Base Table)]
        GSI1[(GSI1<br/>timeline)]
    end
    AP1 --> Base
    AP2 --> Base
    AP3 --> Base
    AP4 --> Base
    AP5 --> GSI1
```

---

## Partition Distribution

ASCII visualization to identify hot partitions and sharding needs.

### Template

```
Partition Load Distribution
────────────────────────────────────────────────
<PK_VALUE>  <BAR>  <PERCENTAGE>  <STATUS>
```

### Healthy Distribution

```
Partition Load Distribution (Writes/sec)
────────────────────────────────────────────────
USER#001    ████████ 12%      ✅ OK
USER#002    ███████ 11%       ✅ OK
USER#003    ███████ 10%       ✅ OK
USER#004    ██████ 9%         ✅ OK
USER#005    ██████ 8%         ✅ OK
Others      ██████████████████████████████ 50%
────────────────────────────────────────────────
Distribution: EVEN - No sharding needed
```

### Hot Partition Warning

```
Partition Load Distribution (Writes/sec)
────────────────────────────────────────────────
COUNTER#global  ████████████████████████ 65%  ⚠️ HOT
USER#001        ████ 8%                       ✅ OK
USER#002        ███ 6%                        ✅ OK
USER#003        ███ 5%                        ✅ OK
Others          ████████ 16%
────────────────────────────────────────────────
⚠️  WARNING: COUNTER#global exceeds 20% threshold
    RECOMMENDATION: Apply write sharding (10 shards)

    Before: COUNTER#global
    After:  COUNTER#global#0, COUNTER#global#1, ... COUNTER#global#9
```

### Time-Series Hot Partition

```
Partition Load Distribution (Writes/sec)
────────────────────────────────────────────────
SENSOR#001#2024-01-25  ████████████████████ 45%  ⚠️ HOT
SENSOR#001#2024-01-24  ███ 5%                    ✅ OK
SENSOR#002#2024-01-25  ████████████ 25%          ⚠️ WARM
SENSOR#002#2024-01-24  ██ 3%                     ✅ OK
Others                 ██████████ 22%
────────────────────────────────────────────────
⚠️  WARNING: Current-day partitions are hot
    RECOMMENDATION: Consider table-per-period strategy

    Current: Single table with date in PK
    Better:  sensors-2024-01-25, sensors-2024-01-24, ...
```

---

## Architecture Diagram

Mermaid flowchart for DynamoDB event-driven architectures.

### OLTP + OLAP Pipeline

```mermaid
flowchart LR
    subgraph OLTP
        App[Application] --> DDB[(DynamoDB)]
    end
    subgraph Event Processing
        DDB --> Stream[DynamoDB Streams]
        Stream --> Lambda[Lambda]
    end
    subgraph OLAP
        Lambda --> Firehose[Kinesis Firehose]
        Firehose --> S3[(S3 Data Lake)]
        S3 --> Athena[Athena]
        S3 --> Redshift[Redshift]
    end
```

### Real-Time Aggregation

```mermaid
flowchart LR
    subgraph Writes
        App[Application] --> DDB[(DynamoDB<br/>Base Data)]
    end
    subgraph Stream Processing
        DDB --> Stream[Streams]
        Stream --> Lambda[Lambda<br/>Aggregator]
    end
    subgraph Aggregates
        Lambda --> Agg[(DynamoDB<br/>Aggregates)]
    end
    subgraph Reads
        Agg --> Dashboard[Dashboard]
    end
```

### Cross-Region Replication

```mermaid
flowchart TB
    subgraph Region A - Primary
        AppA[Application] --> DDBA[(DynamoDB)]
    end
    subgraph Global Tables
        DDBA <--> GT[Global Tables<br/>Replication]
        GT <--> DDBB
    end
    subgraph Region B - Secondary
        DDBB[(DynamoDB)] --> AppB[Application]
    end
```

### Event-Driven Microservices

```mermaid
flowchart LR
    subgraph Order Service
        OrderAPI[API] --> OrderDB[(Orders Table)]
    end
    subgraph Event Bus
        OrderDB --> Stream[Streams]
        Stream --> EB[EventBridge]
    end
    subgraph Downstream Services
        EB --> Inventory[Inventory<br/>Lambda]
        EB --> Notification[Notification<br/>Lambda]
        EB --> Analytics[Analytics<br/>Lambda]
    end
    subgraph Other Tables
        Inventory --> InvDB[(Inventory)]
        Analytics --> S3[(S3)]
    end
```
