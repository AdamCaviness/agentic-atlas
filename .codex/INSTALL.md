# Installing Agentic Atlas for Codex

Enable the `run` skill in Codex via native skill discovery. Clone the repo once, then symlink the `skills/` directory into `~/.agents/skills/`.

## Prerequisites

- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adamcaviness/agentic-atlas.git ~/.codex/agentic-atlas
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/agentic-atlas/skills ~/.agents/skills/agentic-atlas
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\agentic-atlas" "$env:USERPROFILE\.codex\agentic-atlas\skills"
   ```

3. **Restart Codex** (quit and relaunch the CLI) to discover the skill.

## Verify

```bash
ls -la ~/.agents/skills/agentic-atlas
```

You should see a symlink (or junction on Windows) pointing to the cloned skills directory.

## Updating

```bash
cd ~/.codex/agentic-atlas && git pull
```

The skill updates instantly through the symlink.

## Uninstalling

```bash
rm ~/.agents/skills/agentic-atlas
```

Optionally delete the clone: `rm -rf ~/.codex/agentic-atlas`.
