# Integration Architecture

> How the three parts (engine, rubric, plugin) interface. Deep scan, 2026-07-22.

## Overview

The parts live in one repository and ship in one release, but they interface through two
narrow, stable seams rather than shared internals:

1. **Engine ⇄ Rubric** — the engine reads the rubric directory as validated data.
2. **Plugin ⇄ Engine** — the skill drives the engine through its CLI (via the launcher) and
   consumes its stdout JSON. No Python import crosses this boundary.

```
┌─────────────────────────────┐        reads (load_rubric, jsonschema-validated)
│  PLUGIN                      │        ┌───────────────────────────────┐
│  skills/run/SKILL.md         │        │  RUBRIC  rubric/v1/            │
│  skills/run/atlas.sh ────────┼──┐     │  rubric.yaml + axes/<id>/*.yaml│
└─────────────────────────────┘  │     └───────────────▲───────────────┘
        │  bash atlas.sh <args>   │                     │
        ▼                         │                     │ default --rubric rubric/v1
┌─────────────────────────────┐  │  exec agentic-atlas  │
│  ENGINE  agentic_atlas/      │◀─┘  (subprocess/CLI) ───┘
│  cli → profiler → scoring    │
│  stdout: JSON | text | md | html
└─────────────────────────────┘
        ▲   classified answers (JSON: source + answers{})
        │   host agent produces these; engine only validates
        └── the /agentic-atlas:run host model
```

## Integration points

| From | To | Mechanism | Contract / details |
|---|---|---|---|
| Plugin (`atlas.sh`) | Engine | Subprocess `exec`, args forwarded unchanged | Launcher bootstraps a cached `.venv`, then `exec "$ATLAS" "$@"` |
| Plugin (skill) | Engine | CLI commands + stdout parsing | `questions <target>` → worklist JSON; `profile <target> --answers - --format json/html/text` → profile; `atlas.sh --repo-root` → engine root for `--save` |
| Host agent (model) | Engine | `--answers` JSON (file or stdin `-`) | `{ "source": "agentic-atlas:<model>", "answers": { "<id>": {"answer","evidence"} } }`; engine validates value ∈ allowed set and quote verbatim in corpus |
| Engine | Rubric | `spec.load_rubric(dir)` | Reads `rubric.yaml` + `axes/<id>/axis.yaml`; validates against `rubric.schema.json` and `axis.schema.json`; scale + axis order from the manifest |
| Engine | Rubric READMEs | `docs.sync` | Regenerates each axis README's scoring block from its `axis.yaml`; `make docs-check` fails on drift |
| Engine | Filesystem/network | `evidence.Target` | Reads the target's text corpus, git history (`subprocess git`), and GitHub API (`urllib`) for measured indicators |

## Data flow: a full profile run

1. Host agent invokes `/agentic-atlas:run <target>`; the skill calls `atlas.sh` which ensures
   the engine venv and forwards to the `agentic-atlas` CLI.
2. `agentic-atlas questions <target>` → engine loads+validates `rubric/v1`, emits the
   classified worklist (id, axis, question, allowed answers) as JSON.
3. The host agent reads the target and answers each question with a value + a verbatim quote,
   assembling the answers JSON.
4. `agentic-atlas profile <target> --answers - --format json` → `profiler.profile_target`
   resolves measured indicators from the target and validates the supplied classified answers,
   scores each axis, and stamps the `Profile` (rubric version, engine version, target SHA,
   answer source).
5. `report.render_html` produces the self-contained profile; the skill writes it to a per-user
   cache and opens it, and prints a text fallback.
6. With `--save`, the skill writes `answers.json` + `profile.json` under
   `profiles/<TARGET_NAME>/` in this repo (path resolved via `atlas.sh --repo-root`).

## Why the boundaries are drawn here

- **Engine embeds no rubric.** All score-moving policy is in `rubric/`, so the rubric can
  version independently (measurement-standard semver) from the engine (software semver). A
  profile is only comparable to another under the same rubric MAJOR version.
- **Plugin embeds no scoring.** The skill only *supplies answers the engine validates*; it
  cannot change a result by editing logic. This keeps determinism entirely inside the engine
  and lets the skill run from any checkout against any target.
- **One code path.** Both the skill and any curated public profile call
  `profiler.profile_target`; they differ only in persistence. No second scoring path can drift.

## Shared dependencies

All three parts assume Python `>= 3.11` and the engine's two runtime deps (`pyyaml`,
`jsonschema`). The launcher provisions them into a cached venv; developers get them via
`make setup`. The rubric and plugin add no dependencies of their own.
