# Commit Conventions

All ZeroAE projects follow the [Conventional Commits](https://www.conventionalcommits.org/) format with [gitmoji](https://gitmoji.dev/) emojis for better visual scanning in git logs.

## Format

```
<emoji> <type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Emojis

Use [gitmoji.dev](https://gitmoji.dev/) as the canonical reference for emoji meanings.

**Common mappings to conventional commit types:**

| Emoji | Type | Gitmoji Description |
|-------|------|---------------------|
| :sparkles: | `feat` | Introduce new features |
| :bug: | `fix` | Fix a bug |
| :memo: | `docs` | Add or update documentation |
| :art: | `style` | Improve structure/format of code |
| :recycle: | `refactor` | Refactor code |
| :zap: | `perf` | Improve performance |
| :white_check_mark: | `test` | Add or update tests |
| :wrench: | `chore` | Add or update configuration files |
| :hammer: | `build` | Add or update development scripts |
| :construction_worker: | `ci` | Add or update CI build system |
| :lock: | `security` | Fix security issues |
| :arrow_up: | `deps` | Upgrade dependencies |
| :arrow_down: | `downgrade` | Downgrade dependencies |
| :fire: | `remove` | Remove code or files |
| :rewind: | `revert` | Revert changes |
| :boom: | `breaking` | Introduce breaking changes |

**Additional useful gitmojis:**

| Emoji | When to Use |
|-------|-------------|
| :ambulance: | Critical hotfix |
| :construction: | Work in progress |
| :green_heart: | Fix CI build |
| :adhesive_bandage: | Simple fix for non-critical issue |
| :building_construction: | Architectural changes |
| :bricks: | Infrastructure changes |
| :pencil2: | Fix typos |
| :twisted_rightwards_arrows: | Merge branches |

See [gitmoji.dev](https://gitmoji.dev/) for the complete list with descriptions.

## Guidelines

### 1. Type (Required)

Always specify a type. The type communicates the intent of the change.

```bash
# Good
:sparkles: feat(auth): add OAuth2 support
:bug: fix: handle null pointer exception

# Bad
add OAuth2 support  # Missing type and emoji
update code  # Too vague
```

### 2. Scope (Optional)

Use scope to indicate the affected component. Project-specific scopes should be documented in each project's `CLAUDE.md`.

```bash
# With scope
:sparkles: feat(api): add pagination support
:bug: fix(database): prevent connection leak

# Without scope (when change is global)
:art: style: format all files with prettier
```

### 3. Description (Required)

- Use **imperative mood**: "add feature" not "added feature"
- Keep first line **<=72 characters**
- Be specific and descriptive
- Start with lowercase (after the type)

### 4. Body (Optional)

Use the body to explain **why** the change was made and provide context.

### 5. Footer (Optional)

Use footers for:
- **Breaking changes**: `BREAKING CHANGE: description`
- **Issue references**: `Fixes #123`, `Closes #456`
- **Co-authors**: `Co-Authored-By: Name <email>`

### 6. Breaking Changes

Indicate breaking changes with `!` after the type/scope:

```bash
:sparkles: feat(api)!: remove deprecated v1 endpoints

BREAKING CHANGE: All v1 endpoints removed. Use v2 API instead.
```

## Best Practices

1. **Commit often**: Make small, focused commits
2. **One concern per commit**: Don't mix refactoring with features
3. **Test before committing**: Ensure tests pass
4. **Reference issues**: Link commits to issues/PRs when relevant

## References

- [gitmoji.dev](https://gitmoji.dev/) - Emoji reference
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
