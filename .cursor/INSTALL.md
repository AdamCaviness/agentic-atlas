# Installing Agentic Atlas for Cursor

User-level install for Cursor desktop and CLI (Pro, Hobby, and other non-Teams plans).

Use **one** install path only. Cursor also discovers `~/.agents/skills/` and `~/.cursor/skills/`, so linking there *and* under `~/.cursor/plugins/local/` lists skills twice.

## Install (copy-paste)

Requires Git. Paste into Terminal:

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-atlas.git ~/.cursor/plugins/local/agentic-atlas
```

Then in Cursor: Command Palette → **Developer: Reload Window** (or quit and reopen Cursor).

Confirm in **Customize → Skills**, or type `/agentic-atlas:run` in Agents.

## Update

```bash
git -C ~/.cursor/plugins/local/agentic-atlas pull
```

Reload the window again.

## Uninstall

```bash
rm -rf ~/.cursor/plugins/local/agentic-atlas
rm -f ~/.agents/skills/agentic-atlas
rm -f ~/.cursor/skills/agentic-atlas
```

Reload the window.

## Already have a clone?

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn /absolute/path/to/agentic-atlas ~/.cursor/plugins/local/agentic-atlas
```

Do **not** also symlink `skills/` into `~/.agents/skills/` or `~/.cursor/skills/` while this plugin link exists.

## Teams / Enterprise

Team Marketplace import is a web admin flow at [cursor.com/dashboard](https://cursor.com/dashboard) → **Plugins**, not a screen in the desktop app. Individuals on Pro should use the install block above.
