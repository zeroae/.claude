# ZeroAE Organization AI Assistant Instructions

This file provides organization-wide conventions and guidelines for AI assistants working on ZeroAE projects.

## Commit Message Format

All ZeroAE projects MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) format with [gitmoji](https://gitmoji.dev/) emojis.

See [commits.md](commits.md) for complete guidelines.

### Quick Reference

```
<emoji> <type>(<scope>): <description>
```

**Common types (see [gitmoji.dev](https://gitmoji.dev/) for full list):**
- ✨ `feat` - New feature
- 🐛 `fix` - Bug fix
- 📝 `docs` - Documentation
- 🎨 `style` - Code formatting
- ♻️ `refactor` - Code refactoring
- ⚡ `perf` - Performance improvement
- ✅ `test` - Tests
- 🔧 `chore` - Maintenance
- 🔨 `build` - Build system
- 👷 `ci` - CI/CD
- 🔒 `security` - Security fixes

## Automated Changelog Generation

All ZeroAE projects SHOULD use [git-cliff](https://git-cliff.org/) for automated changelog generation in GitHub Actions workflows.

### Why git-cliff?

- **Handles emoji-based commits**: Properly parses our `<emoji> <type>(<scope>): <description>` format
- **Highly customizable**: Flexible regex patterns and templates
- **Fast**: Written in Rust, faster than Node.js alternatives
- **Conventional commits native**: Built specifically for conventional commit workflows

### Standard Setup

1. **Add `cliff.toml` to project root:**

```toml
# git-cliff configuration
[changelog]
header = """
# Changelog\n
All notable changes to this project will be documented in this file.\n
"""
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
        - {% if commit.scope %}**{{commit.scope}}**: {% endif %}{{ commit.message | upper_first }} ([{{ commit.id | truncate(length=7, end="") }}]({{ commit.id }}))\
    {% endfor %}
{% endfor %}\n
"""
trim = true

[git]
conventional_commits = true
filter_unconventional = true
commit_preprocessors = [
  # Remove emoji and extract type, scope, and message
  { pattern = '^[^\w\s]+\s*(\w+)(\(([^\)]+)\))?:\s*(.*)$', replace = "${1}(${3}): ${4}" },
]
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^doc", group = "Documentation" },
  { message = "^perf", group = "Performance" },
  { message = "^refactor", group = "Refactoring" },
  { message = "^style", group = "Styling" },
  { message = "^test", group = "Testing" },
  { message = "^chore", group = "Miscellaneous Tasks" },
  { message = "^revert", group = "Revert" },
]
tag_pattern = "v[0-9].*"
sort_commits = "oldest"
```

2. **Add release job to `.github/workflows/release.yml`:**

```yaml
release:
  needs: build
  runs-on: ubuntu-latest
  permissions:
    contents: write
  steps:
    - uses: actions/checkout@v6
      with:
        fetch-depth: 0  # Required for full git history
    - uses: actions/download-artifact@v7
      with:
        name: dist
        path: dist/
    - name: Generate changelog
      uses: orhun/git-cliff-action@v4
      with:
        config: cliff.toml
        args: --latest --strip header
      env:
        OUTPUT: CHANGELOG.md
    - name: Create GitHub Release
      env:
        GH_TOKEN: ${{ github.token }}
      run: |
        gh release create ${{ github.ref_name }} \
          --title "Release ${{ github.ref_name }}" \
          --notes-file CHANGELOG.md \
          dist/*
```

### Key Points

- **Always use `fetch-depth: 0`** to get full git history for changelog generation
- **The commit preprocessor** strips emojis and normalizes our format to standard conventional commits
- **Release job runs in parallel** with publish job after build completes
- **No S3 or external storage needed** - everything happens in the GitHub Actions runner

### Resources

- [git-cliff documentation](https://git-cliff.org/)
- [git-cliff GitHub Action](https://github.com/orhun/git-cliff-action)
- [Example implementation](https://github.com/zeroae/zae-limiter)

## Code Style

- Follow project-specific linting and formatting tools
- Use type hints where applicable (Python, TypeScript)
- Write clear, self-documenting code
- Add docstrings/comments only where logic isn't self-evident

## General Principles

1. **Simplicity over cleverness** - Prefer straightforward solutions
2. **YAGNI** - Don't add features or abstractions until needed
3. **Security awareness** - Watch for OWASP top 10 vulnerabilities
4. **Backwards compatibility** - Consider migration paths for breaking changes
5. **Test coverage** - Write tests for new features and bug fixes

## Project Structure

Individual projects may extend these guidelines with project-specific instructions in their own `CLAUDE.md` files.
