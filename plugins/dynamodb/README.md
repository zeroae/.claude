# DynamoDB Plugin

Advanced DynamoDB design patterns and data modeling expertise for Claude Code, based on Rick Houlihan's AWS re:Invent talks.

## Overview

Expert guidance on DynamoDB schema design using NoSQL-native patterns:

- Design efficient single-table schemas
- Optimize access patterns
- Review and audit existing schemas
- Apply advanced patterns (GSI overloading, adjacency lists, write sharding)

## Skills

| Skill | Triggers When |
|-------|---------------|
| `dynamodb-patterns` | Asking about DynamoDB design, access patterns, single-table design, GSIs |
| `schema-designer` | "Help me design a DynamoDB schema for X", "Model my data for DynamoDB" |
| `schema-audit` | "Audit my DynamoDB schema", "Review this table design", "Check for issues" |

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

## Patterns Covered

- **Single-Table Design** - Multiple entities in one table
- **Composite Keys** - Hierarchical data with sort key prefixes
- **GSI Overloading** - Multiple access patterns from one GSI
- **Adjacency Lists** - M:N relationships
- **Write Sharding** - Distribute hot partition writes
- **Sparse GSIs** - Efficient rare attribute filtering

## References

Based on Rick Houlihan's AWS re:Invent talks:

- [2017: DAT403-R](https://www.youtube.com/watch?v=jzeKPKpucS0)
- [2018: DAT401](https://www.youtube.com/watch?v=HaEPXoXVf2k)
- [2019: DAT403-R1](https://www.youtube.com/watch?v=6yqfmXiZTlM)

## License

MIT
