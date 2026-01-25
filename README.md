# ZeroAE Claude Code Plugins

A collection of Claude Code plugins for ZeroAE development standards and workflows.

## Structure

- **`/plugins`** - Plugins developed and maintained by ZeroAE

## Installation

To install, run `/plugin install {plugin-name}@zeroae.com`

## Available Plugins

| Plugin | Description |
|--------|-------------|
| `zstd` | Organization-wide development standards and conventions |

## Plugin Structure

```
plugins/
└── zstd/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    │   └── conventions/
    └── references/
```

## Documentation

For more information on developing Claude Code plugins, see the [official documentation](https://docs.anthropic.com/en/docs/claude-code/plugins).
