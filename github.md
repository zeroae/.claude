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

Note: Issue titles use **capitalized** descriptions for readability.

## Pull Request Titles

PR titles follow conventional commits format (lowercase, no emoji) for changelog generation:

| Type | Example |
|------|---------|
| Feature | `feat(limiter): add health_check method` |
| Bug | `fix(cli): handle missing config file` |
| Docs | `docs: update deployment guide` |
| Chore | `chore(ci): update workflow actions` |

The merge commit uses the PR title, and `git-cliff` parses it to generate changelogs.

## Creating Issues

Use `gh issue create` for labels and milestone, then set the type via API:

```bash
# 1. Create issue with labels and milestone
gh issue create \
  --title "✨ Add new feature" \
  --body "Description here" \
  --label "area/foo" \
  --label "area/bar" \
  --milestone "vX.Y.Z"

# 2. Set the issue type (gh issue create doesn't support --type)
gh api -X PATCH repos/{owner}/{repo}/issues/{number} -f type=Feature
```

Valid type values: `Epic`, `Feature`, `Bug`, `Task`, `Chore`

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

When creating a PR that closes an issue, inherit the issue's metadata (labels, milestone) at creation time.

### Creating a PR with Issue Metadata

```bash
# 1. Get the linked issue's metadata
gh issue view <issue-number> --json labels,milestone

# 2. Create PR with inherited metadata
gh pr create --title "feat(scope): description" \
  --body "Closes #<issue-number>" \
  --label "area/foo" \
  --milestone "vX.Y.Z"
```

### Updating an Existing PR

```bash
gh pr edit <pr-number> --add-label "area/foo" --milestone "vX.Y.Z"
```

This ensures PRs are tracked in the same milestone and have consistent labeling for filtering and reporting.

## Release Planning

Releases are tracked using GitHub milestones, narrative issues, and sub-issues:

- **Milestone**: Operational tracking - assign issues, view progress
- **Narrative issue**: Context - theme, goals, success criteria, breaking changes (type: Epic)
- **Sub-issues**: Link work tickets to narrative issues for progress tracking

### Querying Milestones

Query milestones dynamically rather than maintaining static lists in documentation:

```bash
# Open milestones
gh api repos/{owner}/{repo}/milestones --jq '.[] | "- \(.title): \(.description)"'

# Closed milestones
gh api repos/{owner}/{repo}/milestones?state=closed --jq '.[] | "- \(.title): \(.description)"'

# Issues in a milestone
gh issue list --milestone vX.Y.Z
gh issue list --milestone vX.Y.Z --state closed
```

### Creating a Release

1. **Create milestone** with a short description
2. **Create narrative issue** using the `Release Epic` template, assign to milestone
3. **Add sub-issues** to link work tickets to the narrative
4. **Assign work tickets** to the milestone
