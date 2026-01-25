---
name: help
description: DynamoDB plugin help and usage guide. Use when users ask about the DynamoDB plugin, want to know what skills are available, ask "how do I use the DynamoDB plugin", or say "/dynamodb:help".
context: fork
---

# DynamoDB Plugin Help

## Skills

| Skill | Command | When to Use |
|-------|---------|-------------|
| **schema** | `/dynamodb:schema` | Design new or audit existing DynamoDB schema |
| **patterns** | `/dynamodb:patterns` | Learn design patterns, ask DynamoDB modeling questions |

## Agent

| Agent | Triggers When |
|-------|---------------|
| **auditor** | Share DynamoDB code (CDK/CFN/Terraform) + ask for feedback |

## Quick Start

| Goal | Action |
|------|--------|
| New schema | `/dynamodb:schema` → select "new" |
| Audit existing schema | `/dynamodb:schema` → select "existing" |
| Questions about patterns | Ask directly or `/dynamodb:patterns` |
| Deep autonomous analysis | Share code + ask for review (triggers agent) |
