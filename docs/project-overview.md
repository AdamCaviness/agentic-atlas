# Project Overview: Agentic Atlas

> Generated for AI context on 2026-07-22 (deep scan). See [index.md](./index.md) for full navigation.

## Purpose

Agentic Atlas is an open, versioned methodology and toolset for **profiling agentic
development approaches** (the plugins, frameworks, and skill collections you run inside a
coding harness such as Claude Code or Codex, for example Superpowers, BMAD-METHOD, GSD, LFG).
It locates each target on **13 signed, diverging axes** on a shared `-10..+10` scale, where
`0` is neutral and both poles are legitimate.

It is deliberately **not a ranking tool**. There is **no aggregate score**. A profile is a
vector of independent signed positions that tells a reader where a tool sits so they can
judge fit for their own project and working style, never which tool "wins".

## What makes it distinctive

- **Subjective axis, deterministic result.** Each axis decomposes into small, named,
  evidence-backed *indicators*. The scoring formula is pure arithmetic, so identical evidence
  always yields an identical position.
- **Rubric is data, engine is code.** All scoring policy (poles, indicators, weights,
  formulas) lives in versioned YAML under `rubric/`. The Python engine interprets a rubric,
  it embeds none.
- **No API key.** The engine computes *measured* indicators directly from the repository and
  only *validates* *classified* answers supplied from outside. The intended answerer is the
  host coding agent driving the `run` skill, so the full profile is produced with no key.
- **Every profile is reproducible and arguable.** Each stamps the rubric version, engine
  version, target commit SHA, and (for classified indicators) the answer source.

## Repository shape

This is a **single Git repository** organized into three cohesive parts that version and
evolve on their own cadences:

| Part | Path | What it is | Type |
|---|---|---|---|
| **Engine** | `agentic_atlas/`, `tests/` | The deterministic Python CLI + importable library that reads a rubric, gathers evidence, resolves indicators, scores axes, and renders reports | CLI / library |
| **Rubric** | `rubric/v1/` | The versioned measurement standard: a manifest plus one YAML file per axis (13 axes), each defining poles, indicators, and weights | Data (YAML) |
| **Plugin & skill** | `.claude-plugin/`, `skills/run/`, `gemini-extension.json`, `.codex/` | The distribution surface: the `/agentic-atlas:run` skill and its launcher that drive the engine from a coding harness | Extension / skill |

The parts are separated because they answer to different authorities: the **engine** follows
standard software semver, the **rubric** follows a measurement-standard semver (any change
that can move a score for identical evidence is MAJOR), and the **plugin** is the packaging
that ships the skill to marketplaces.

## Technology stack

| Category | Technology | Version | Role |
|---|---|---|---|
| Language | Python | >= 3.11 | Whole engine |
| Build backend | Hatchling | (build-system) | Wheel packaging |
| Runtime dep | PyYAML | >= 6.0 | Parse rubric/axis YAML |
| Runtime dep | jsonschema | >= 4.0 | Validate rubric + axis files (imported lazily) |
| Dev dep | pytest | >= 8.0 | Test suite (69 tests across 7 files) |
| Dev dep | ruff | >= 0.6 | Lint + format (line length 100) |
| Task runner | GNU Make | n/a | `make setup/check/validate/docs/profile` |
| CI / release | release-please (GitHub Actions) | n/a | Automated versioning and changelog |
| Skill launcher | Bash | n/a | `skills/run/atlas.sh` bootstraps the engine venv |

The deterministic core (`models.py`, `spec.py`, `scoring.py`) is intentionally
dependency-light. `jsonschema` is imported lazily inside `spec.py` so the scoring path stays
minimal; `evidence.py` uses only the standard library (`subprocess`, `urllib`, `re`).

## Architecture at a glance

The engine is a straight pipeline with no framework:

```
target ─▶ evidence ─▶ indicator resolution ─▶ scoring ─▶ report
             │              │        │
        measured        measured   classified
      (engine only)     (engine)   (validated from supplied answers)
```

- **measured** indicators: computed from the repo (vocabulary density, path presence, path
  count, git stats, GitHub API), fully deterministic.
- **classified** indicators: a bounded answer plus a verbatim quote, produced by an external
  agent and *validated* (never generated) by the engine.

See [architecture-engine.md](./architecture-engine.md) for the module-level design,
[architecture-rubric.md](./architecture-rubric.md) for the data model, and
[architecture-plugin.md](./architecture-plugin.md) for the skill contract.

## Current status

Early scaffold, actively developed (43 commits, 4 tags, ~8 days of history at scan time).
Engine version `0.4.0`; rubric version `1.4.0` (still MAJOR v1, pre-settled per
[versioning.md](./versioning.md)). Working today: schema-validated per-axis rubric, the
deterministic scoring core, all five measured evidence collectors, the classified-answer
validation seam, text/markdown/JSON/HTML reports (including an interactive 3D profile
crystal), the `agentic-atlas docs` generator kept in sync by `make docs-check`, and the
`/agentic-atlas:run` skill. Planned: a `compare` overlay command, committed answer sets for
reproducible published profiles, and more public profiles.
