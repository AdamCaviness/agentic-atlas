# Installing Agentic Atlas for Codex

Install from [agentic-marketplace](https://github.com/adamcaviness/agentic-marketplace). Codex loads the plugin (`run`, `open-explorer`, `explain`) from `.codex-plugin/plugin.json`. Use **exactly one** path, or skills appear twice.

## 1. ChatGPT desktop (recommended)

1. Open **Plugins** → **Add plugin marketplace**.
2. Source: `adamcaviness/agentic-marketplace` (not `github.com/...`).
3. Git ref: `main`.
4. Sparse paths: leave empty.
5. Add the marketplace, then install **agentic-atlas**.
6. Restart ChatGPT / Codex if the plugin does not appear, then start a new chat.

If you previously cloned this repo and symlinked `skills/` into `~/.agents/skills/agentic-atlas`, remove that link before installing from the marketplace:

```bash
rm ~/.agents/skills/agentic-atlas
```

## 2. Codex CLI (optional)

```bash
codex plugin marketplace add adamcaviness/agentic-marketplace --ref main
codex plugin add agentic-atlas@agentic-marketplace
```

List with `codex plugin list --marketplace agentic-marketplace`. Remove with `codex plugin remove agentic-atlas@agentic-marketplace`.

## 3. Manual fallback (clone and symlink)

Use this only if you cannot add a marketplace. Do **not** combine it with path 1 or 2.

```bash
git clone https://github.com/adamcaviness/agentic-atlas.git ~/.codex/agentic-atlas
mkdir -p ~/.agents/skills
ln -s ~/.codex/agentic-atlas/skills ~/.agents/skills/agentic-atlas
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\agentic-atlas" "$env:USERPROFILE\.codex\agentic-atlas\skills"
```

Restart Codex. Update with `git -C ~/.codex/agentic-atlas pull`. Uninstall with `rm ~/.agents/skills/agentic-atlas`.
