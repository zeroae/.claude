---
name: help
description: DynamoDB plugin help and usage guide. Use when users ask about the DynamoDB plugin, want to know what skills are available, ask "how do I use the DynamoDB plugin", or say "/dynamodb:help".
---

# DynamoDB Plugin Help

## Skills

| Skill | Command | When to Use |
|-------|---------|-------------|
| **patterns** | `/dynamodb:patterns` | Learn design patterns, ask DynamoDB modeling questions |
| **design** | `/dynamodb:design` | Design a new schema from scratch |
| **audit** | `/dynamodb:audit` | Audit an existing schema interactively |

## Agent

| Agent | Triggers When |
|-------|---------------|
| **schema-auditor** | Share DynamoDB code (CDK/CFN/Terraform) + ask for feedback |

## Quick Start

| Goal | Action |
|------|--------|
| New schema | `/dynamodb:design` |
| Questions about patterns | Ask directly (auto-triggers patterns) |
| Review existing schema | `/dynamodb:audit` or share code |
| Deep autonomous analysis | Share code + ask for review (auto-triggers agent) |
