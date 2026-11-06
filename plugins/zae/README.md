# zae

Hand-picked pieces of other people's plugins, one skill (or agent, command,
output style) at a time, next to ones we write ourselves. Call them as
`/zae:<name>`.

## Install

```
/plugin marketplace add zeroae/claude-plugins
/plugin install zae@zeroae.com
```

On Claude Code 2.1.275 or later, one step does both:

```
/plugin install zae --marketplace zeroae/claude-plugins
```

## Skills

| Skill | Description | From |
|-------|-------------|------|
| `unslop` | Cut AI tells from any writing | [pstack-claude](https://github.com/michael-denyer/pstack-claude/tree/main/plugins/pstack/skills/unslop) (poteto's pstack), MIT |

## Output styles

| Style | Description | From |
|-------|-------------|------|
| `zae:plain` | Plain, direct prose with no AI tells, leading with the answer. Keeps Claude Code's coding instructions | Our own: `unslop`'s chat rules, in the shape of Claude Code's built-in styles |

An output style applies to every reply in a session, so it is opt-in: pick it
with `/output-style zae:plain`, or set `"outputStyle": "zae:plain"` in
`~/.claude/settings.json`. Claude Code adds the `zae:` prefix itself, so the
file's `name` is just `plain`. It does not set `force-for-plugin`, so
enabling `zae` does not turn it on.

## Picked vs. our own

A picked component is a copy of an upstream file or folder at a pinned
commit. [`vendored.json`](vendored.json) records, for each one, the upstream
repo and path, the commit, the git object id, the license and a hash of the
copied files. Do not edit a picked component by hand: `check` fails on it.
To change one, make it our own (below).

Anything under `skills/`, `agents/`, `commands/` or `output-styles/` that
`vendored.json` does not list is our own. Write it here like in any other
plugin.

## Managing picks

From the repo root:

```bash
# Pick a skill: a GitHub tree URL gives repo, ref and path in one go
scripts/zae-vendor.py add https://github.com/<owner>/<repo>/tree/main/skills/<name>

# Or owner/repo and a path; --as renames it or says what kind it is
scripts/zae-vendor.py add <owner>/<repo> plugins/x/agents/reviewer.md --as agents/reviewer.md

scripts/zae-vendor.py status                 # which picks are behind upstream HEAD (exit 2 = some are)
scripts/zae-vendor.py update skills/unslop   # re-copy at upstream HEAD (or --ref <commit>)
scripts/zae-vendor.py update --all
scripts/zae-vendor.py check                  # copies match vendored.json
scripts/zae-vendor.py remove skills/unslop
```

`add` and `update` refuse upstreams with no LICENSE near the component, and
symlinks. They copy that license to `licenses/`. They print a REVIEW block
when what the component can run or widen changes: frontmatter `hooks`,
`allowed-tools`, `tools`, `mcpServers`, `permissionMode` or `model`, and
executable files. Read the diff before you commit, like any third-party code.

To make a picked component our own, so you can edit it: copy it aside,
`remove` it, put the copy back and edit away. Keep its license file in
`licenses/` and say where it came from in the table above.

## License

Our own content: MIT. Each picked component keeps its upstream license, copied
to [`licenses/`](licenses/) and named in `vendored.json`.
