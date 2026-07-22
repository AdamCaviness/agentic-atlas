# Agentic Atlas — Documentation Index

> **Primary entry point for AI-assisted development.** Generated 2026-07-22 by a deep scan.
> Point brownfield planning workflows here.

Agentic Atlas profiles agentic development approaches by locating each on 13 signed, diverging
axes on a shared `-10..+10` scale. It is not a ranking tool and there is **no aggregate
score** — a profile is a vector of independent signed positions.

## Project Overview

- **Type:** multi-part repository with 3 parts (engine, rubric, plugin)
- **Primary language:** Python `>= 3.11` (engine); YAML (rubric); Bash + JSON (plugin)
- **Architecture:** spec + interpreter — a versioned data rubric read by a deterministic
  Python engine, driven from a coding harness by a skill
- **Engine version:** `0.4.0` · **Rubric version:** `1.4.0` (still MAJOR v1)
- **Scale of code:** ~1,970 LOC engine, 69 tests, 13 axes

## Parts

### Engine (`agentic_atlas/`, `tests/`)
- **Type:** Python CLI + importable library
- **Entry point:** `agentic_atlas/cli.py:main` (console script `agentic-atlas`)
- **Deps:** `pyyaml`, `jsonschema` (runtime); `pytest`, `ruff` (dev)
- Reads a rubric, gathers evidence, resolves measured + classified indicators, scores axes,
  renders text/md/json/html.

### Rubric (`rubric/v1/`)
- **Type:** versioned YAML data + JSON Schema
- **Source of truth:** `axes/<id>/axis.yaml` (poles, indicators, weights, signals)
- All scoring policy lives here; the engine embeds none. Measurement-standard semver.

### Plugin & skill (`.claude-plugin/`, `skills/run/`, `gemini-extension.json`, `.codex/`)
- **Type:** Claude Code / Gemini / Codex plugin
- **Entry point:** `/agentic-atlas:run` (`skills/run/SKILL.md`); launcher `skills/run/atlas.sh`
- Drives the engine via its CLI; the host agent answers the classified questions. No scoring
  logic of its own.

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Architecture — Engine](./architecture-engine.md)
- [Architecture — Rubric](./architecture-rubric.md)
- [Architecture — Plugin & Skill](./architecture-plugin.md)
- [Integration Architecture](./integration-architecture.md)
- [Development Guide](./development-guide.md)
- [Project Parts metadata](./project-parts.json)

## Existing Documentation (authored, not generated)

- [README.md](../README.md) — human-facing overview and usage
- [AGENTS.md](../AGENTS.md) — canonical agent instructions (`CLAUDE.md` symlinks to it)
- [docs/design.md](./design.md) — the architecture thesis (spec + interpreter)
- [docs/axes.md](./axes.md) — axis authoring method and the full candidate catalog
- [docs/versioning.md](./versioning.md) — the two independent version lines
- [docs/skill-integration.md](./skill-integration.md) — the stable engine surface the skill targets
- [CHANGELOG.md](../CHANGELOG.md) — engine changelog (release-please)
- [rubric/v1/CHANGELOG.md](../rubric/v1/CHANGELOG.md) — rubric (score-moving) changelog
- [specs/handoff.md](../specs/handoff.md), [specs/personas-correlation-ordering.md](../specs/personas-correlation-ordering.md) — working specs

## Getting Started

```bash
make setup     # create .venv, editable-install with dev deps
make check     # the CI gate: lint → docs-check → test
make validate  # validate the rubric against its schemas
make profile TARGET=/path/to/approach FORMAT=md   # profile a target (measured only)
```

Then read [development-guide.md](./development-guide.md) for the full workflow and
[architecture-engine.md](./architecture-engine.md) for the module-level map.

## Core invariants (do not violate without a versioned rubric change)

1. **No aggregate score** — never collapse axes into one number.
2. **Rubric is data, engine is code** — scoring policy lives in `rubric/*.yaml`.
3. **The axis score is a deterministic function of indicators** — `scoring.py` is pure arithmetic.
4. **Every profile is reproducible** — stamps rubric version, engine version, target SHA, answer source.
5. **`measured` vs `classified` stay separate** — the engine computes measured, validates classified.
