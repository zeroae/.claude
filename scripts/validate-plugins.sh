#!/usr/bin/env bash
# Quick validation for Claude Code plugins
# Used by: pre-commit hook, GitHub Actions
set -euo pipefail

PLUGINS_DIR="${1:-plugins}"
ERRORS=0
WARNINGS=0

# Colors (disabled in CI)
if [[ -t 1 ]] && [[ -z "${CI:-}" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' NC=''
fi

log_error() { echo -e "${RED}❌ $1${NC}"; ERRORS=$((ERRORS + 1)); }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; WARNINGS=$((WARNINGS + 1)); }
log_ok() { echo -e "${GREEN}✓ $1${NC}"; }

echo "=== Claude Code Plugin Validation ==="
echo ""

# Find all plugins
for plugin_dir in "$PLUGINS_DIR"/*/; do
    [[ -d "$plugin_dir" ]] || continue
    plugin_name=$(basename "$plugin_dir")

    echo "--- Plugin: $plugin_name ---"

    # Check 1: plugin.json exists
    manifest="$plugin_dir/.claude-plugin/plugin.json"
    if [[ ! -f "$manifest" ]]; then
        log_error "Missing .claude-plugin/plugin.json"
        continue
    fi

    # Check 2: Validate manifest with claude CLI (if available)
    if command -v claude &>/dev/null; then
        if claude plugin validate "$plugin_dir" &>/dev/null; then
            log_ok "Manifest valid"
        else
            log_error "Manifest validation failed"
            claude plugin validate "$plugin_dir" 2>&1 | sed 's/^/    /'
        fi
    else
        # Fallback: basic JSON validation
        if python3 -c "import json; json.load(open('$manifest'))" 2>/dev/null; then
            log_ok "Manifest JSON valid (claude CLI not available for full validation)"
        else
            log_error "Invalid JSON in plugin.json"
        fi
    fi

    # Check 3: Validate each skill
    skills_dir="$plugin_dir/skills"
    if [[ -d "$skills_dir" ]]; then
        skill_count=0
        while IFS= read -r -d '' skill_file; do
            skill_count=$((skill_count + 1))
            skill_name=$(basename "$(dirname "$skill_file")")

            # Check frontmatter exists
            if ! head -1 "$skill_file" | grep -q "^---"; then
                log_error "Skill '$skill_name': Missing YAML frontmatter"
                continue
            fi

            # Extract frontmatter (between first two ---)
            # Use awk for portability (head -n -1 not available on macOS)
            frontmatter=$(awk '/^---$/{if(++c==2)exit}c==1' "$skill_file")

            # Check required fields
            if ! echo "$frontmatter" | grep -q "^name:"; then
                log_error "Skill '$skill_name': Missing 'name' in frontmatter"
            fi

            if ! echo "$frontmatter" | grep -q "^description:"; then
                log_error "Skill '$skill_name': Missing 'description' in frontmatter"
            else
                # Check description quality (length)
                desc=$(echo "$frontmatter" | grep "^description:" | cut -d: -f2- | xargs)
                if [[ ${#desc} -lt 20 ]]; then
                    log_warn "Skill '$skill_name': Description too short (<20 chars)"
                fi
            fi

            # Check if skill-local references/ mentioned but directory missing
            # (Plugin-level references/ is fine and doesn't need a local copy)
            skill_dir=$(dirname "$skill_file")
            if grep -qE "\./references/|skill.*references/" "$skill_file" 2>/dev/null; then
                if [[ ! -d "$skill_dir/references" ]]; then
                    log_warn "Skill '$skill_name': Local references mentioned but references/ directory missing"
                fi
            fi

        done < <(find "$skills_dir" -name "SKILL.md" -print0 2>/dev/null)

        if [[ $skill_count -gt 0 ]]; then
            log_ok "Found $skill_count skill(s)"
        else
            log_warn "No skills found in skills/ directory"
        fi
    fi

    echo ""
done

# Summary
echo "=== Summary ==="
if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    log_ok "All plugins validated successfully"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}Completed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi
