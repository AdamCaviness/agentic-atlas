# Installing Agentic Atlas for Cursor

User-level install for Cursor desktop and CLI (Pro, Hobby, and other non-Teams plans).

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
```

Reload the window.

## Already have a clone?

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn /absolute/path/to/agentic-atlas ~/.cursor/plugins/local/agentic-atlas
```

## Teams / Enterprise

Team Marketplace import is a web admin flow at [cursor.com/dashboard](https://cursor.com/dashboard) → **Plugins**, not a screen in the desktop app. Individuals on Pro should use the install block above.
