# hussam-skills

Skills that help engineers work like seniors when they **build, review, test, and ship products with AI**, and ship them **with confidence**.

Each skill is a plain `SKILL.md` folder. It works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and any other agent that reads skills.

## Skills

| Skill | Stage | What it does | Call it with |
|---|---|---|---|
| [senior-review](skills/senior-review) | Review · Test · Ship | Read-only review of a branch or PR before a production deploy. Maps what the change touches, checks the project's principles (SOLID, KISS, YAGNI, DRY), proves claims with evidence, and writes the exact change for every finding. | `/senior-review` |

## Install

### Any agent (recommended)

Uses the open [`skills`](https://github.com/vercel-labs/skills) CLI. Needs Node.js.

```sh
# all skills, pick your agents in a menu
npx skills add hussamkurd/hussam-skills -g

# one skill, straight into Claude Code and Codex
npx skills add hussamkurd/hussam-skills -g -a claude-code codex -s senior-review -y
```

Drop `-g` to install into the current project instead of your user folder. Other agent names: `cursor`, `gemini-cli`, `github-copilot`, `opencode`, `windsurf`; use `-a '*'` for all.

### Claude Code plugin

Inside Claude Code:

```
/plugin marketplace add hussamkurd/hussam-skills
/plugin install hussam-skills@hussam-skills
```

Skills from the plugin are called with the plugin prefix, for example `/hussam-skills:senior-review`.

### Manual

```sh
git clone https://github.com/hussamkurd/hussam-skills.git
cp -R hussam-skills/skills/senior-review ~/.claude/skills/   # Claude Code
cp -R hussam-skills/skills/senior-review ~/.agents/skills/   # Codex
```

## Update

```sh
npx skills update -g                                # skills CLI
/plugin marketplace update hussam-skills            # Claude Code plugin
git -C hussam-skills pull                           # manual (copy again)
```

## Uninstall

| Installed with | Remove with |
|---|---|
| skills CLI | `npx skills remove senior-review -g` (all agents), or add `-a codex` for one agent |
| Claude Code plugin | `/plugin uninstall hussam-skills@hussam-skills`, then `/plugin marketplace remove hussam-skills` |
| Manual copy | `rm -rf ~/.claude/skills/senior-review ~/.agents/skills/senior-review` |

Check what is installed with `npx skills list -g`.

## Safety

Skills run with your agent's permissions. Read a `SKILL.md` before you install it.
