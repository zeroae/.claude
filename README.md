# ZeroAE Claude Code Extensions

Organization-wide Claude Code extensions, development standards, and conventions.

## Installation

### Plugin Marketplace (Recommended)

Install via the Claude Code plugin marketplace:

```bash
# Add ZeroAE marketplace
/plugin marketplace add zeroae/.claude

# Install development standards plugin
/plugin install zstd@zeroae.com
```

## Available Plugins

### zstd (ZeroAE Standards)

Organization-wide development standards including:

- **Commit conventions** - Conventional Commits with gitmoji
- **GitHub workflows** - Issues, PRs, labels, and releases
- **Development principles** - Code style and best practices
- **Changelog automation** - git-cliff configuration

#### Using the Conventions Skill

```bash
/zstd:conventions
```

This loads ZeroAE development conventions into your session.

## Documentation

Reference documentation is available at:

- [Commit Conventions](plugins/zstd/references/commits.md)
- [GitHub Project Management](plugins/zstd/references/github.md)
- [Development Principles](plugins/zstd/references/principles.md)
- [Changelog Generation](plugins/zstd/references/changelog.md)

## Marketplace Structure

```
.claude/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace registry
├── plugins/
│   └── zstd/                  # Standards plugin
│       ├── .claude-plugin/
│       │   └── plugin.json    # Plugin manifest
│       ├── skills/
│       │   └── conventions/   # Conventions skill
│       └── references/        # Documentation
└── README.md
```

## Contributing

1. Fork this repository
2. Create a feature branch
3. Make your changes following the conventions
4. Submit a pull request

## License

MIT
