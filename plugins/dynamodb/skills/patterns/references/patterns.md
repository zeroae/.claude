# DynamoDB Design Patterns

Detailed reference for each pattern. Load only the sections needed.

## Table of Contents
- [Single-Table Design](#single-table)
- [Multi-Table Design](#multi-table)
- [Composite Keys](#composite-keys)
- [Local Secondary Index (LSI)](#lsi)
- [GSI Overloading](#gsi-overloading)
- [Adjacency List](#adjacency-list)
- [Write Sharding](#write-sharding)
- [Sparse GSI](#sparse-gsi)
- [Version Control](#version-control)
- [Time-Series Tables](#time-series-tables)
- [Transactions](#transactions)
- [DynamoDB Streams](#streams)

## Visualization Templates

| Pattern | Layout Template |
|---------|-----------------|
| Single-Table, Adjacency List | Item Collection |
| GSI Overloading, LSI, Sparse GSI | Side-by-Side |
| Composite Keys, Version Control | Simple Table |
| Full schema overview | Full Schema |

---

## Single-Table Design {#single-table}

Store multiple entity types in ONE table.

**Why:**
- Retrieve related data in one Query (no round trips)
- Enable transactions across entity types
- Simplify operations (one table to manage)

**How:**
- Use generic attribute names: `PK`, `SK`
- Encode entity type in key values: `PK=USER#123`, `SK=PROFILE`
- Use composite sort keys for hierarchical queries

**Example - E-commerce:**
```
PK              | SK                  | Data
----------------|---------------------|------------------
USER#123        | PROFILE             | {name, email, ...}
USER#123        | ORDER#2024-001      | {total, status, ...}
USER#123        | ORDER#2024-002      | {total, status, ...}
ORDER#2024-001  | ITEM#SKU-A          | {qty, price, ...}
ORDER#2024-001  | ITEM#SKU-B          | {qty, price, ...}
```

**Queries:**
- User profile: `PK=USER#123, SK=PROFILE`
- User's orders: `PK=USER#123, SK begins_with ORDER#`
- Order items: `PK=ORDER#2024-001, SK begins_with ITEM#`

---

## Multi-Table Design {#multi-table}

When to use **multiple tables** instead of single-table design.

**Single-table is NOT always best.** Consider multi-table when:

### When to Use Multi-Table

| Scenario | Why Multi-Table Wins |
|----------|---------------------|
| **GraphQL APIs** | One resolver per table is simpler |
| **Multi-tenant encryption** | Each tenant can have separate KMS keys |
| **Different backup policies** | Hot data vs. cold data retention |
| **Separate access patterns** | Entities never queried together |
| **Infrequent Access storage** | Only apply IA class to archival tables |
| **Independent scaling** | Different capacity needs per entity |
| **Dedicated streams** | Separate Lambda processors per entity |

### Trade-off Comparison

| Aspect | Single Table | Multi-Table |
|--------|--------------|-------------|
| **RCU cost** | Lower (one query) | Higher (multiple queries) |
| **Latency** | Lower | Higher |
| **Design complexity** | High (learning curve) | Low (intuitive) |
| **Ops overhead** | Low (one table) | High (many alarms, IAM) |
| **Data flexibility** | Limited (shared policies) | High (per-table policies) |
| **SDK support** | Harder (mixed types) | Easier (typed mappers) |

### Decision Guide

```
Do you query multiple entity types together?
├── YES → Single-table (data locality wins)
└── NO → Do entities have different:
         ├── Backup requirements? → Multi-table
         ├── Encryption keys? → Multi-table
         ├── Access patterns? → Multi-table
         └── None of the above? → Either works, prefer simpler
```

**Key insight:** Start with single-table for OLTP apps. Switch to multi-table when you have specific operational requirements that demand it.

---

## Composite Keys {#composite-keys}

Encode hierarchy or time in sort key for range queries.

### Hierarchical Data

Use `#` delimiter to encode hierarchy levels. Query with `begins_with()` at any level.

**Example - Store Locations (from DynamoDB Guide):**

```
PK (StoreNumber) | Country | StateCityZip
-----------------|---------|------------------
STORE#001        | USA     | NE#OMAHA#68144
STORE#002        | USA     | NE#OMAHA#68102
STORE#003        | USA     | CA#SF#94102
STORE#004        | USA     | CA#LA#90001
```

**GSI (StoreLocationIndex):**
- PK: Country
- SK: StateCityZip (composite: `STATE#CITY#ZIP`)

**Queries using `begins_with()`:**
- All US stores: `Country=USA`
- Stores in Nebraska: `Country=USA, SK begins_with NE#`
- Stores in Omaha: `Country=USA, SK begins_with NE#OMAHA#`
- Stores in zip 68144: `Country=USA, SK begins_with NE#OMAHA#68144`

**Key insight:** One GSI supports 4+ access patterns via hierarchical sort key.

### Time-Series Data

```
PK = DEVICE#sensor-1
SK = READING#2024-01-15T10:30:00Z
```

**Query last 24 hours:**
```
SK between READING#2024-01-14T10:30:00Z and READING#2024-01-15T10:30:00Z
```

---

## Local Secondary Index (LSI) {#lsi}

Alternate sort key on the same partition key. Enables different sort orders without duplicating data.

### LSI vs GSI

| Aspect | LSI | GSI |
|--------|-----|-----|
| Partition key | Same as base table | Different from base table |
| Creation | Table creation only | Anytime |
| Consistency | Strongly consistent available | Eventually consistent only |
| Throughput | Shares with base table | Separate provisioned capacity |
| Size limit | 10GB per partition key | No limit |
| Max per table | 5 | 20 |

### When to Use LSI

- **Strongly consistent reads** on alternate sort orders
- **Same partition, different sorts** (e.g., orders by date OR by status)
- **Avoid GSI write costs** (LSI shares base table WCU)
- **Data fits 10GB per partition** (critical constraint)

### Example - Orders with Multiple Sort Orders

```
Base Table:
PK            | SK (by date)      | LSI1SK (by status) | LSI2SK (by total)
--------------|-------------------|--------------------|-----------------
USER#alice    | ORDER#2024-01-15  | pending            | 150.00
USER#alice    | ORDER#2024-01-20  | shipped            | 89.99
USER#alice    | ORDER#2024-02-01  | pending            | 299.00
```

**Access patterns:**
- Orders by date (base table): `PK=USER#alice, SK begins_with ORDER#`
- Orders by status (LSI1): `PK=USER#alice, LSI1SK=pending`
- Orders by total descending (LSI2): `PK=USER#alice`, ScanIndexForward=false

### Projections

Choose what attributes to copy into the LSI:

| Projection | Use Case | Storage Cost |
|------------|----------|--------------|
| `KEYS_ONLY` | Just need to find items, fetch full item separately | Lowest |
| `INCLUDE` | Specific attributes needed for query | Medium |
| `ALL` | Full item access without fetching base | Highest |

**Best practice:** Start with `KEYS_ONLY` or `INCLUDE`, use `ALL` only when you always need the full item.

### Constraints

- **Must define at table creation** - Cannot add LSI to existing table
- **10GB limit per partition key** - All items + LSI entries under same PK
- **Max 5 LSIs** - Plan carefully, can't change later
- **Consumes base table RCU** - Reads count against table capacity

### Anti-Pattern: LSI When GSI is Better

Don't use LSI when:
- You need to query across different partition keys
- Partition size might exceed 10GB
- You might need to add indexes later
- You need independent scaling

**Rule of thumb:** If unsure, use GSI. LSI is an optimization for specific use cases.

---

## GSI Overloading {#gsi-overloading}

Use generic GSI attribute names to support multiple access patterns from one index.

**Base table with overloaded GSI:**
```
PK      | SK          | GSI1PK          | GSI1SK
--------|-------------|-----------------|----------------
USER#1  | PROFILE     | EMAIL#a@b.com   | USER#1
USER#1  | ORDER#001   | STATUS#pending  | DATE#2024-01-15
PROD#A  | INFO        | CAT#electronics | PRICE#299
```

**GSI1 supports:**
- Find user by email: `GSI1PK=EMAIL#a@b.com`
- Find pending orders: `GSI1PK=STATUS#pending`
- Products by category sorted by price: `GSI1PK=CAT#electronics`

**Key insight:** Different entity types use the same GSI with different key prefixes.

---

## Adjacency List {#adjacency-list}

Model many-to-many relationships by storing edges as items.

**Pattern:** Store both the node and its edges under the same partition key.

```
PK          | SK          | Data
------------|-------------|------------------
USER#alice  | USER#alice  | {type: "user", name: "Alice"}
USER#alice  | GROUP#devs  | {type: "membership", role: "admin"}
USER#alice  | GROUP#ops   | {type: "membership", role: "member"}
GROUP#devs  | GROUP#devs  | {type: "group", name: "Developers"}
GROUP#devs  | USER#alice  | {type: "membership", role: "admin"}
GROUP#devs  | USER#bob    | {type: "membership", role: "member"}
```

**Access patterns:**
- User and all their groups: `PK=USER#alice`
- Group and all its members: `PK=GROUP#devs`
- Bidirectional traversal in single table

**Note:** Edges are duplicated (stored under both nodes) for bidirectional queries.

---

## Write Sharding {#write-sharding}

Distribute writes across partitions for hot keys.

**Problem:** Single partition key limited to ~1000 writes/second.

**Solution:** Add random suffix to partition key.

```python
NUM_SHARDS = 10
shard = random.randint(0, NUM_SHARDS - 1)
pk = f"COUNTER#{shard}"
```

### Scatter-Gather Pattern

To read sharded data, query all shards and aggregate in application:

```python
# SCATTER: Query each shard
results = []
for shard in range(NUM_SHARDS):
    response = table.query(
        KeyConditionExpression=Key('PK').eq(f'LEADERBOARD#{shard}'),
        ScanIndexForward=False,  # Descending
        Limit=10  # Top 10 per shard
    )
    results.extend(response['Items'])

# GATHER: Sort and take top N
top_10 = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
```

**Trade-offs:**
- More shards = better write distribution, but more read overhead
- Only use when write traffic genuinely exceeds single-partition capacity
- Consider caching aggregated results

**Use for:** Vote counters, view counts, leaderboards, any high-write single logical key.

---

## Sparse GSI {#sparse-gsi}

Only items with the GSI attribute appear in the index.

```
PK      | SK      | GSI_PK (sparse)
--------|---------|----------------
USER#1  | PROFILE | (not set)
USER#2  | PROFILE | ADMIN
USER#3  | PROFILE | (not set)
USER#4  | PROFILE | ADMIN
```

**Result:** GSI contains ONLY admin users (2 items, not 4).

**Use for:**
- Featured/promoted items
- Flagged content requiring review
- Items in specific workflow states
- Any rare attribute that needs efficient filtering

**Benefit:** Small, focused index with low storage and write costs.

---

## Version Control {#version-control}

Track item history while enabling easy access to the latest version.

**Pattern:** Use sort key prefixes `v0_` (latest) and `v1_`, `v2_`, etc. (history).

### How It Works

1. **Create dual copies** for each item:
   - `v0_` prefix → always contains the latest version
   - `v1_` prefix → first version (immutable)

2. **On update:**
   - Create new item with next version prefix (`v2_`, `v3_`, etc.)
   - Replace contents of `v0_` item with the new data

### Example - Equipment Audits

```
PK              | SK              | Data
----------------|-----------------|------------------
EQUIPMENT#001   | v0_Audit        | {latest audit data}
EQUIPMENT#001   | v1_Audit        | {first audit - 2024-01}
EQUIPMENT#001   | v2_Audit        | {second audit - 2024-06}
EQUIPMENT#001   | v3_Audit        | {third audit - 2024-12}
```

### Query Patterns

| Access Pattern | Implementation |
|---------------|----------------|
| Latest version | `PK=EQUIPMENT#001, SK=v0_Audit` |
| Full history | `PK=EQUIPMENT#001, SK begins_with v`, filter out `v0_` |
| Specific version | `PK=EQUIPMENT#001, SK=v2_Audit` |

### Multi-Part Documents

For documents with multiple sections:

```
PK              | SK                  | Data
----------------|---------------------|------------------
DOC#report-123  | v0_Section#intro    | {latest intro}
DOC#report-123  | v0_Section#body     | {latest body}
DOC#report-123  | v1_Section#intro    | {v1 intro}
DOC#report-123  | v1_Section#body     | {v1 body}
```

**Use for:** Audit trails, compliance requirements, document versioning, configuration history.

---

## Time-Series Tables {#time-series-tables}

For high-volume time-series data, use **one table per time period** instead of a single table.

**Why:** The composite sort key approach (`SK=READING#timestamp`) works for moderate scale, but high-volume time-series (IoT, logs, metrics) needs table-per-period.

### Problems with Single Table

| Issue | Impact |
|-------|--------|
| **TTL deletes consume WCU** | Expensive at scale (millions of expirations) |
| **Hot partitions** | Recent timestamps concentrate all writes |
| **Capacity waste** | Old data rarely accessed but shares capacity |
| **No lifecycle management** | Can't easily archive or delete old data |

### Table-Per-Period Pattern

**Structure:**
```
events-2024-01  (archived, 1 WCU, minimal RCU)
events-2024-02  (archived, 1 WCU, minimal RCU)
events-2024-03  (current month, high capacity)
events-2024-04  (pre-created, ready for next period)
```

### Lifecycle Management

```
Period starts → Create new table with high capacity
              → Redirect writes to new table
              → Scale down previous table to 1 WCU
              → Reduce RCU as access declines
              → Delete/archive when retention expires
```

### Capacity Strategy

| Table Age | Write Capacity | Read Capacity |
|-----------|---------------|---------------|
| Current | High (match traffic) | High |
| Previous month | 1 WCU (minimum) | Medium |
| Older | 1 WCU | Low or on-demand |
| Past retention | Delete table | - |

### Implementation

```python
from datetime import datetime

def get_table_name(base_name: str) -> str:
    """Get current period's table name."""
    period = datetime.utcnow().strftime('%Y-%m')
    return f"{base_name}-{period}"

def write_event(event: dict):
    table_name = get_table_name('events')
    dynamodb.Table(table_name).put_item(Item=event)
```

### Partition Key Design

Include date in partition key to align with table boundaries:

```
PK = DEVICE#sensor-1#2024-03-15
SK = 10:30:00Z
```

### Comparison

| Aspect | Sort Key Approach | Table-Per-Period |
|--------|-------------------|------------------|
| Scale | Moderate | High (millions/day) |
| Cost for old data | Same forever | Scale to minimum |
| TTL cleanup | Consumes WCU | Just drop table |
| Complexity | Lower | Higher (table management) |
| Best for | Mixed workloads | Pure time-series |

**Use for:** IoT sensor data, application logs, metrics, clickstream, any write-heavy time-series that ages out.

---

## Transactions {#transactions}

ACID transactions across up to 100 items in same region.

**TransactWriteItems example:**
```python
client.transact_write_items(
    TransactItems=[
        {
            'Update': {
                'TableName': 'MyTable',
                'Key': {'PK': {'S': 'ACCT#A'}},
                'UpdateExpression': 'SET balance = balance - :amt',
                'ExpressionAttributeValues': {':amt': {'N': '100'}}
            }
        },
        {
            'Update': {
                'TableName': 'MyTable',
                'Key': {'PK': {'S': 'ACCT#B'}},
                'UpdateExpression': 'SET balance = balance + :amt',
                'ExpressionAttributeValues': {':amt': {'N': '100'}}
            }
        },
        {
            'Put': {
                'TableName': 'MyTable',
                'Item': {
                    'PK': {'S': 'TXN#123'},
                    'SK': {'S': 'LOG'},
                    'amount': {'N': '100'},
                    'from': {'S': 'ACCT#A'},
                    'to': {'S': 'ACCT#B'}
                }
            }
        }
    ]
)
```

**Use for:**
- Financial transfers
- Inventory reservations
- Any operation requiring all-or-nothing semantics

**Limits:**
- 100 items max per transaction
- 4MB total size
- Items must be in same region
- 2x capacity consumption

---

## DynamoDB Streams {#streams}

Capture item-level changes for event-driven architectures.

**Use cases:**
- **OLAP offloading**: Replicate to Redshift/Athena for analytics
- **Aggregations**: Maintain counters, leaderboards without hot partitions
- **Cross-region replication**: Global Tables use streams internally
- **Audit trails**: Capture all changes for compliance
- **Event triggers**: Lambda functions on data changes

**Architecture for OLAP:**
```
DynamoDB (OLTP) → Stream → Lambda → Kinesis Firehose → S3 → Athena (OLAP)
```

**Key insight:** Keep DynamoDB for real-time OLTP. Use streams to feed analytics systems for reporting and ad-hoc queries.

**Stream record types:**
- `KEYS_ONLY`: Just the key attributes
- `NEW_IMAGE`: Item after modification
- `OLD_IMAGE`: Item before modification
- `NEW_AND_OLD_IMAGES`: Both (for change detection)

**Best practice:** Use `NEW_AND_OLD_IMAGES` when you need to compute deltas (e.g., increment aggregates by the difference).
