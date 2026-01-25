# ZeroAE Claude Code Plugins

A collection of Claude Code plugins for ZeroAE development standards and workflows.

## Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| `zstd` | Organization-wide development standards and conventions | 1 |
| `cspy` | Architecture patterns from [Cosmic Python](https://cosmicpython.com) for domain-driven design | 8 |

## Installation

```bash
/plugin install {plugin-name}@zeroae.com
```

## cspy Plugin

Architecture patterns from "Architecture Patterns with Python" by Harry Percival and Bob Gregory.

**Skills:**
- `cspy:audit` - Analyze codebase architecture against Cosmic Python patterns
- `cspy:service-layer` - Generate service layer functions
- `cspy:uow` - Implement Unit of Work pattern
- `cspy:domain` - Design domain models (entities, value objects, aggregates)
- `cspy:events` - Design domain events, commands, and message bus
- `cspy:cqrs` - Analyze and design CQRS read models
- `cspy:test-strategy` - Recommend test levels based on TDD approach
- `cspy:refactor` - Guide incremental pattern adoption

**Agent:**
- `cspy:architecture-auditor` - Proactively analyze Python code architecture

## Development

### Structure

```
.
├── plugins/
│   ├── cspy/           # Cosmic Python patterns
│   └── zstd/           # ZeroAE standards
├── scripts/
│   └── validate-plugins.sh
├── .githooks/
│   └── pre-commit
└── .github/
    └── workflows/
        └── validate-plugins.yml
```

### Validation

Plugins are validated automatically on commit and in CI:

```bash
./scripts/validate-plugins.sh
```

## Documentation

For more information on developing Claude Code plugins, see the [official documentation](https://docs.anthropic.com/en/docs/claude-code/plugins).
