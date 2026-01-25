---
name: conventions
description: Apply ZeroAE development conventions for commits, PRs, issues, and code style
---

# ZeroAE Development Conventions

Apply these conventions when working on ZeroAE projects. Reference the detailed documentation in `references/` for complete guidelines.

## Commit Format

All commits follow Conventional Commits with gitmoji:

```
<emoji> <type>(<scope>): <description>
```

### Common Types

| Emoji | Type | Purpose |
|-------|------|---------|
| :sparkles: | `feat` | New features |
| :bug: | `fix` | Bug fixes |
| :memo: | `docs` | Documentation |
| :recycle: | `refactor` | Refactoring |
| :white_check_mark: | `test` | Tests |
| :wrench: | `chore` | Configuration |
| :construction_worker: | `ci` | CI/CD changes |

Use [gitmoji.dev](https://gitmoji.dev/) as the canonical emoji reference.

## Issue Titles

Use emoji-only prefix with capitalized descriptions:

- Feature: `:sparkles: Add new capability`
- Bug: `:bug: Fix error handling`
- Task: `:clipboard: Update documentation`
- Epic: `:dart: v1.0.0: Major Release`
- Chore: `:wrench: Update dependencies`

## Pull Request Titles

PRs follow conventional commits format (lowercase, no emoji) for changelog generation:

```
feat(scope): add new capability
fix(api): handle missing parameters
docs: update installation guide
```

## Creating Issues

```bash
# 1. Create issue with labels and milestone
gh issue create \
  --title ":sparkles: Add new feature" \
  --body "Description" \
  --label "area/component" \
  --milestone "vX.Y.Z"

# 2. Set issue type (gh doesn't support --type)
gh api -X PATCH repos/{owner}/{repo}/issues/{number} -f type=Feature
```

Valid types: `Epic`, `Feature`, `Bug`, `Task`, `Chore`

## Creating PRs

Inherit issue metadata when creating PRs:

```bash
# Get issue metadata
gh issue view <number> --json labels,milestone

# Create PR with inherited metadata
gh pr create --title "feat(scope): description" \
  --body "Closes #<number>" \
  --label "area/component" \
  --milestone "vX.Y.Z"
```

## Development Principles

1. **Simplicity over cleverness** - Prefer straightforward solutions
2. **YAGNI** - Don't add features until needed
3. **Security awareness** - Watch for OWASP top 10
4. **Test coverage** - Write tests for new features and fixes

## Changelog Generation

Use git-cliff with the standard `cliff.toml` configuration. See `references/changelog.md` for setup.

## References

Detailed documentation available in the references directory:

- `commits.md` - Complete commit conventions
- `github.md` - GitHub project management
- `principles.md` - Development principles
- `changelog.md` - Changelog automation setup
