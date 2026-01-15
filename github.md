# GitHub Project Management

Conventions for managing GitHub issues, labels, and releases in ZeroAE projects.

## Issue Types

Types classify the fundamental nature of work. They map to conventional commit types:

| Type | Commit Types | Purpose |
|------|--------------|---------|
| Epic | N/A | Release narratives, multi-issue initiatives |
| Feature | `feat`, `perf` | New functionality, enhancements |
| Bug | `fix`, `security` | Defects, unexpected behavior |
| Task | `docs`, `test` | Specific deliverables |
| Chore | `refactor`, `chore`, `ci`, `build`, `deps` | Maintenance, internal work |

## Issue Titles

Use emoji-only prefix (not full conventional commit format):

| Type | Emoji | Example |
|------|-------|---------|
| Feature | ✨ | `✨ Add health_check method` |
| Bug | 🐛 | `🐛 Fix asyncio deprecation warning` |
| Task | 📋 | `📋 Update migration docs` |
| Epic | 🎯 | `🎯 v0.9.0: API Polish` |
| Chore | 🔧 | `🔧 Update CI workflow` |

Note: Issue/PR titles use **capitalized** descriptions for readability. Commit messages use lowercase (`✨ feat(scope): add feature`) per conventional commits.

## Labels

### Area Labels

Use `area/` prefix for component labels. Define project-specific areas in each project's `CLAUDE.md`.

Example: `area/api`, `area/cli`, `area/infra`

### Attribute Labels

Common attributes across projects:

- `performance` - Performance optimization
- `api-design` - API surface changes
- `documentation` - Docs improvements
- `testing` - Test coverage
- `security` - Security improvements
- `breaking` - Breaking change
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed

## Pull Requests

When creating a PR that closes an issue, inherit the issue's metadata:

1. **Copy labels** from the linked issue to the PR
2. **Copy milestone** from the linked issue to the PR

```bash
# Get issue metadata
gh issue view <issue-number> --json labels,milestone

# Apply to PR
gh pr edit <pr-number> --add-label "area/foo" --milestone "vX.Y.Z"
```

This ensures PRs are tracked in the same milestone and have consistent labeling for filtering and reporting.

## Release Planning

Releases are tracked using GitHub milestones, narrative issues, and sub-issues:

- **Milestone**: Operational tracking - assign issues, view progress
- **Narrative issue**: Context - theme, goals, success criteria, breaking changes (type: Epic)
- **Sub-issues**: Link work tickets to narrative issues for progress tracking

### Creating a Release

1. **Create milestone** with a short description
2. **Create narrative issue** using the `Release Epic` template, assign to milestone
3. **Add sub-issues** to link work tickets to the narrative
4. **Assign work tickets** to the milestone

### Viewing Progress

```bash
gh issue list --milestone vX.Y.Z
gh issue list --milestone vX.Y.Z --state closed
```
