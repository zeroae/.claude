# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a Claude Code plugin repository containing plugins for ZeroAE development workflows. Plugins extend Claude Code with skills (guided workflows) and agents (autonomous specialists).

## Commands

```bash
# Validate all plugins
./scripts/validate-plugins.sh

# Validate specific plugin
claude plugin validate plugins/cspy

# Test a skill invocation (in Claude Code)
/cspy:audit
```

## Plugin Architecture

Each plugin follows this structure:
```
plugins/{name}/
├── .claude-plugin/
│   └── plugin.json      # Manifest (name, version, skills path)
├── skills/
│   └── {skill-name}/
│       ├── SKILL.md     # Skill definition with YAML frontmatter
│       └── references/  # Optional: supporting docs for the skill
├── agents/              # Optional: autonomous agent definitions
├── references/          # Optional: shared references across skills
└── README.md            # Plugin documentation (required)
```

**SKILL.md frontmatter requirements:**
- `name`: lowercase, hyphenated identifier
- `description`: clear trigger conditions for skill discovery (>20 chars)

**plugin.json requirements:**
- Do not use `agents` or `attribution` fields (not in schema)
- Use `"skills": "./skills/"` to point to skills directory

**Plugin README.md should include:**
- Plugin name and description
- Table of skills with descriptions
- Table of agents (if any)
- License information

## Conventions

Follow the official Claude plugins marketplace for conventions:
- Repository: `anthropics/claude-plugins-official`
- Docs: https://code.claude.com/docs/en/plugins

When updating documentation, compare against the official marketplace for alignment.

## Validation

Plugins are validated:
1. **Pre-commit**: `.githooks/pre-commit` runs on modified plugins
2. **CI**: `.github/workflows/validate-plugins.yml` on push/PR
3. **SessionStart**: Git hooks path auto-configured via `.claude/settings.json`

## Enabled Plugins

This repo uses these official plugins (see `.claude/settings.json`):
- `plugin-dev` - For developing new plugins
- `example-skills` - Reference implementations
- `hookify` - Custom hook creation
