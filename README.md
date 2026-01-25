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

### Git Submodule (Legacy)

Add as a submodule for CLAUDE.md instructions:

```bash
git submodule add https://github.com/zeroae/.claude.git .claude/rules/zeroae
```

To update to latest conventions:

```bash
git submodule update --remote .claude/rules/zeroae
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

- [Commit Conventions](commits.md)
- [GitHub Project Management](github.md)
- [Development Principles](principles.md)
- [Changelog Generation](changelog.md)

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
├── commits.md                 # Root docs (backwards compat)
├── github.md
├── principles.md
├── changelog.md
└── README.md
```

## Contributing

1. Fork this repository
2. Create a feature branch
3. Make your changes following the conventions
4. Submit a pull request

## License

MIT
