# Installing Agentic Atlas for Cursor

Cursor discovers skills from several places. Use **exactly one** of the paths below for this plugin, or skills appear twice in **Customize → Skills** and under `/` in Agents.

| Your setup | What to do |
|---|---|
| You already use **Claude Code** with this plugin | Install once in Claude Code (path 1). Cursor picks it up automatically. Do **not** also install path 2. |
| **Cursor only** (Pro / Hobby / individual) | Clone or link into `~/.cursor/plugins/local` (path 2). |
| **Cursor Teams / Enterprise** admin | Import the marketplace from the web dashboard (path 3). Teammates install from **Customize**. |

Leave **Settings → Rules, Skills, Subagents → Include third-party Plugins, Skills, and other configs** enabled (the default) if you rely on path 1.

## 1. Via Claude Code (best if you use both)

In Claude Code:

```bash
/plugin marketplace add adamcaviness/agentic-marketplace
/plugin install agentic-atlas@agentic-marketplace
```

Reload Cursor (**Developer: Reload Window**). Use `/agentic-atlas:run` (and the other atlas skills) in Agents.

Stop here. Do not also clone or symlink into `~/.cursor/plugins/local`, `~/.cursor/skills/`, or `~/.agents/skills/`.

## 2. Cursor only (Pro / individual, no Claude Code install)

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-atlas.git ~/.cursor/plugins/local/agentic-atlas
```

Or link an existing clone:

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn /absolute/path/to/agentic-atlas ~/.cursor/plugins/local/agentic-atlas
```

Reload the window. Confirm in **Customize → Skills**.

Update: `git -C ~/.cursor/plugins/local/agentic-atlas pull`, then reload.

Uninstall: `rm -rf ~/.cursor/plugins/local/agentic-atlas`.

## 3. Cursor Teams / Enterprise

**Dashboard** is [cursor.com/dashboard](https://cursor.com/dashboard) (web admin), not the desktop app.

1. Admin: **Dashboard → Plugins → Team Marketplaces** → import `https://github.com/adamcaviness/agentic-marketplace`.
2. Teammates: install **agentic-atlas** from **Customize**.

## Why skills show up twice

Cursor scans `~/.cursor/plugins/local/`, Claude Code’s `~/.claude/plugins/` (when third-party includes are on), `~/.agents/skills/`, `~/.cursor/skills/`, and Codex roots. One install root only.
