# DynamoDB Plugin

Advanced DynamoDB design patterns and data modeling expertise for Claude Code, based on Rick Houlihan's AWS re:Invent talks.

## Overview

Expert guidance on DynamoDB schema design using NoSQL-native patterns:

- Design efficient single-table schemas
- Optimize access patterns
- Review and audit existing schemas
- Apply advanced patterns (GSI overloading, adjacency lists, write sharding)
- Generate visual diagrams (ERD, table layouts, GSI mappings)

## Skills

| Skill | Triggers When |
|-------|---------------|
| `help` | "How do I use the DynamoDB plugin?", `/dynamodb:help` |
| `patterns` | Asking about DynamoDB design, access patterns, single-table design, GSIs |
| `design` | "Help me design a DynamoDB schema for X", "Model my data for DynamoDB" |
| `audit` | "Audit my DynamoDB schema", "Review this table design", "Check for issues" |

## Agents

| Agent | Triggers When |
|-------|---------------|
| `schema-auditor` | User shares DynamoDB code (CDK/CloudFormation/Terraform) and asks for feedback |

## Usage Examples

### Design a new schema
```
"Help me design a DynamoDB schema for a task management app with users, projects, and tasks"
```

### Audit existing schema
```
"Can you audit my DynamoDB schema? Here's my CDK code..."
```

### Quick review (agent triggers automatically)
```
"Here's my DynamoDB table definition, what do you think?"
[paste code]
```

### Ask questions (patterns skill triggers)
```
"How do I model many-to-many relationships in DynamoDB?"
"What's the best partition key for time-series data?"
"Should I use single-table design?"
```

## Diagram Outputs

The `design` skill generates visual diagrams to help understand schema structure:

| Diagram Type | Format | Purpose |
|--------------|--------|---------|
| **ERD** | Mermaid | Entity relationships before DynamoDB mapping |
| **Table Layout** | ASCII / Mermaid Block | Item collections grouped by partition key |
| **GSI Visualization** | ASCII / Mermaid Block | How GSIs project data for secondary access |
| **Access Pattern Matrix** | ASCII | Which queries use which keys |
| **Access Pattern Flow** | Mermaid | How queries route through table + GSIs |
| **Partition Distribution** | ASCII | Visualize hot spots and sharding needs |
| **Architecture** | Mermaid | DynamoDB + Streams + Lambda pipelines |

**Format choice:** ASCII for terminal/universal compatibility, Mermaid Block for docs/presentations with color-coded entity types.

## Patterns Covered

- **Single-Table Design** - Multiple entities in one table
- **Multi-Table Design** - When separate tables are better (GraphQL, multi-tenant)
- **Composite Keys** - Hierarchical data with sort key prefixes
- **GSI Overloading** - Multiple access patterns from one GSI
- **Adjacency Lists** - M:N relationships
- **Write Sharding** - Distribute hot partition writes
- **Sparse GSIs** - Efficient rare attribute filtering
- **Version Control** - Item history with `v0_`/`v1_` sort key pattern
- **Time-Series Tables** - Table-per-period for high-volume time-series

## References

### AWS Documentation

- [DynamoDB Data Modeling](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling.html)
- [Data Modeling Foundations](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling-foundations.html) - Single vs multi-table design
- [Partition Key Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)
- [Sort Key Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html) - Version control pattern
- [GSI Overloading](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-overloading.html)
- [Time-Series Data](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html) - Table-per-period strategy
- [Relational Data Modeling](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-relational-modeling.html)

### Rick Houlihan's AWS re:Invent Talks

- [2017: DAT403-R](https://www.youtube.com/watch?v=jzeKPKpucS0)
- [2018: DAT401](https://www.youtube.com/watch?v=HaEPXoXVf2k)
- [2019: DAT403-R1](https://www.youtube.com/watch?v=6yqfmXiZTlM)

### Community Resources

- [DynamoDBGuide.com](https://www.dynamodbguide.com) - Alex DeBrie's comprehensive guide
- [20 Steps to Switch from RDBMS](https://www.jeremydaly.com/how-to-switch-from-rdbms-to-dynamodb-in-20-easy-steps/) - Jeremy Daly

## License

MIT
