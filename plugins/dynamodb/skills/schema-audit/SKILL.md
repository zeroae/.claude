---
name: schema-audit
description: DynamoDB schema audit workflow. Use when users ask to audit their DynamoDB schema, review their table design, check for issues, or optimize their existing DynamoDB setup. Triggers on "audit my DynamoDB", "review this schema", "check my table design".
---

# DynamoDB Schema Audit

Structured workflow to audit an existing DynamoDB schema.

## Step 1: Locate Schema

Search for DynamoDB definitions or ask user:

```
Glob: **/*dynamodb*.ts, **/cdk*.ts, **/*.tf, **/template.yaml
Grep: "dynamodb.Table" or "AWS::DynamoDB" or "aws_dynamodb_table"
```

If not found, ask user to provide or describe their schema.

## Step 2: Parse Schema

Extract and confirm:
- Table name
- Primary key (PK + SK)
- GSI definitions
- Billing mode

"I found table X with PK=Y, SK=Z, and N GSIs. Correct?"

## Step 3: Gather Access Patterns

Ask user:
"What queries does your application perform? List each:
- Get/List/Find [what] by/for [condition]"

## Step 4: Map Patterns to Schema

For each access pattern, identify:
1. Which table/index serves it
2. Query or Scan operation
3. Filter expressions needed

Present mapping for review.

## Step 5: Analyze Against Best Practices

**Key Design**
- [ ] High-cardinality partition key?
- [ ] Effective sort key for ranges?
- [ ] Single-table design where appropriate?

**Access Efficiency**
- [ ] All patterns use Query?
- [ ] Filters doing key's work?

**GSI Health**
- [ ] Overloading used?
- [ ] Sparse GSI opportunities?

**Scalability**
- [ ] Hot partition risks?
- [ ] Write sharding needed?

## Step 6: Present Findings

```
## Audit Results

### Summary
Critical: X | Warnings: Y | Suggestions: Z

### Access Pattern Analysis
| Pattern | Method | Status |
|---------|--------|--------|

### Issues (prioritized)
1. [Critical] ...
2. [Warning] ...

### Recommended Actions
1. ...
```

## Step 7: Offer Next Steps

"Would you like me to:
1. Generate the improved schema?
2. Explain a specific recommendation?
3. Show migration approach?"
