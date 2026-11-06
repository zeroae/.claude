# ZeroAE Claude Code Plugins

A collection of Claude Code plugins for ZeroAE development standards and workflows.

> **⚠️ Important:** Make sure you trust a plugin before installing, updating, or using it. Review each plugin's source code and documentation before use.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [`zstd`](plugins/zstd/) | Organization-wide development standards and conventions |
| [`cspy`](plugins/cspy/) | Architecture patterns from [Cosmic Python](https://cosmicpython.com) for domain-driven design |
| [`zae`](plugins/zae/) | Hand-picked skills from other plugins, pinned to an upstream commit, plus our own |

## Installation

```
/plugin install {plugin-name}@zeroae.com
```

Or browse in `/plugin > Discover`

## Plugin Structure

Each plugin follows a standard structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── skills/              # Skill definitions (optional)
├── agents/              # Agent definitions (optional)
├── commands/            # Slash commands (optional)
├── references/          # Shared documentation (optional)
├── .mcp.json            # MCP server configuration (optional)
└── README.md            # Documentation
```

## Contributing

To add a new plugin:

1. Create plugin directory under `plugins/`
2. Add `.claude-plugin/plugin.json` manifest
3. Run `./scripts/validate-plugins.sh` to validate
4. Submit a pull request

## Development

Plugins are validated automatically on commit and in CI:

```bash
./scripts/validate-plugins.sh
```

## Documentation

For more information on developing Claude Code plugins, see the [official documentation](https://code.claude.com/docs/en/plugins).
