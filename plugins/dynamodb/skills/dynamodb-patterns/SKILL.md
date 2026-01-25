---
name: dynamodb-patterns
description: DynamoDB advanced design patterns and data modeling expertise. Use when users ask about DynamoDB schema design, single-table design, access patterns, partition keys, sort keys, GSIs, adjacency lists, NoSQL data modeling, or migrating from relational to DynamoDB.
---

# DynamoDB Advanced Design Patterns

Apply NoSQL-native thinking. **Unlearn relational normalization** - it's the hardest but most important step when switching to DynamoDB.

## Core Principles

1. **Access patterns drive schema design** - Identify ALL patterns upfront, design keys to serve them with Query (never Scan)
2. **DynamoDB is for OLTP, not OLAP** - Real-time transactional queries only. Analytics/reporting belong in a data warehouse.
3. **Denormalization is correct** - Duplicate data to avoid joins. Storage is cheap, latency is expensive.

## Modeling Workflow

1. **List ALL access patterns** - Every query the app will make
2. **Filter to OLTP only** - Remove analytics, reporting, ad-hoc queries (use Athena/Redshift for those)
3. **Identify entities** - Users, Orders, Products, etc.
4. **Identify relationships** - 1:1, 1:N, M:N
5. **Design keys for primary patterns** - PK/SK combinations
6. **Add GSIs for secondary patterns** - Overload when possible
7. **Validate with sample data** - Write out example items
8. **Iterate until 95% confident** - Don't go to production until design is solid

## Pattern Index

| Pattern | When to Use | Reference |
|---------|-------------|-----------|
| Single-Table Design | Most apps - multiple entities in one table | [patterns.md#single-table](references/patterns.md) |
| Composite Keys | Hierarchical data, time-series | [patterns.md#composite-keys](references/patterns.md) |
| GSI Overloading | Multiple secondary access patterns | [patterns.md#gsi-overloading](references/patterns.md) |
| Adjacency List | Many-to-many relationships | [patterns.md#adjacency-list](references/patterns.md) |
| Write Sharding | Hot keys (counters, leaderboards) | [patterns.md#write-sharding](references/patterns.md) |
| Sparse GSI | Filter rare attributes efficiently | [patterns.md#sparse-gsi](references/patterns.md) |

## Quick Reference

**Single-table key pattern:**
```
PK: ENTITY#<id>    SK: TYPE#<qualifier>
```

**Hierarchical sort key (for `begins_with` queries):**
```
SK: STATE#<state>#CITY#<city>#ZIP#<zip>
```

**GSI overloading:**
```
GSI1PK: <access-pattern-key>    GSI1SK: <sort-attribute>
```

## Anti-Patterns

- **Normalized tables** - Don't create separate tables and join in app
- **Scan operations** - If you need Scan, redesign your keys
- **Hot partitions** - Use write sharding for high-traffic keys
- **OLAP in DynamoDB** - Use streams to replicate to analytics systems
- **Ad-hoc queries** - DynamoDB requires known access patterns

## Resources

- **Detailed patterns**: See [references/patterns.md](references/patterns.md)
- **Real-world examples**: See [references/examples.md](references/examples.md)
- **Rick Houlihan talks**: [2017](https://youtube.com/watch?v=jzeKPKpucS0) | [2018](https://youtube.com/watch?v=HaEPXoXVf2k) | [2019](https://youtube.com/watch?v=6yqfmXiZTlM)
- **Alex DeBrie's guide**: [DynamoDBGuide.com](https://www.dynamodbguide.com)
- **Jeremy Daly's migration guide**: [20 Steps to Switch from RDBMS](https://www.jeremydaly.com/how-to-switch-from-rdbms-to-dynamodb-in-20-easy-steps/)
