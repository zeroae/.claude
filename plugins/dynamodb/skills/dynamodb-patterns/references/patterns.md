# DynamoDB Design Patterns

Detailed reference for each pattern. Load only the sections needed.

## Table of Contents
- [Single-Table Design](#single-table)
- [Composite Keys](#composite-keys)
- [GSI Overloading](#gsi-overloading)
- [Adjacency List](#adjacency-list)
- [Write Sharding](#write-sharding)
- [Sparse GSI](#sparse-gsi)
- [Transactions](#transactions)
- [DynamoDB Streams](#streams)

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
