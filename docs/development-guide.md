# Development Guide

> How to set up, run, test, and release Agentic Atlas. Deep scan, 2026-07-22. The Makefile
> is the primary entry point: `make` (or `make help`) lists all targets.

## Prerequisites

- **Python `>= 3.11`** on PATH (the engine requires it; `atlas.sh` probes
  `python3.13 → 3.12 → 3.11 → python3`).
- **GNU Make** (all workflows run through it).
- **git** — the Fresh↔Mature axis reads real git history, so measured runs assume a normal
  (non-shallow) clone.
- Network + optionally `GITHUB_TOKEN`/`GH_TOKEN` are only needed for the `github_api` measured
  signal; everything else works offline.

## Setup

```bash
make setup     # create .venv and editable-install the package with dev deps ([dev])
```

`make setup` builds `.venv` and installs `agentic-atlas` (editable) plus `pytest` and `ruff`.
The venv rebuilds automatically whenever `pyproject.toml` changes. `make install` is an alias.

The `agentic-atlas` console script is then available inside the venv
(`.venv/bin/agentic-atlas`).

## Everyday commands

```bash
make check                 # THE CI GATE: lint → docs-check → test
make test                  # pytest -q (69 tests)
make lint                  # ruff check .
make fmt                   # ruff format .   (alias: make format)
make validate              # validate rubric/v1 against its schemas (RUBRIC=... to override)
make docs                  # regenerate axis README scoring blocks from axis.yaml
make docs-check            # fail if any axis README block is stale (part of make check)
make profile TARGET=/path/to/approach [ANSWERS=answers.json FORMAT=text|md|json|html]
make clean                 # remove venv, caches, build artifacts
```

Ruff is configured in `pyproject.toml`: line length 100, target `py311`. Pytest's
`testpaths = ["tests"]`.

## Using the CLI directly

```bash
agentic-atlas validate rubric/v1                                # schema check
agentic-atlas docs rubric/v1 [--check]                          # regenerate / verify README blocks
agentic-atlas profile /path/to/approach                         # measured indicators only (no key)
agentic-atlas questions /path/to/approach                       # emit classified worklist (JSON)
agentic-atlas profile /path/to/approach --answers answers.json  # unlock classified indicators
agentic-atlas profile /path/to/approach --answers - --format json  # answers from stdin
```

A bare `profile` resolves only the measured indicators and reports the rest as needing
interpretation. Supply `--answers` (a `{ "source": ..., "answers": {...} }` JSON, file or
stdin `-`) to score the classified indicators. See [skill-integration.md](./skill-integration.md).

## Running through the skill

Inside a coding harness with the plugin installed:

```
/agentic-atlas:run                          # profile the current directory (announced)
/agentic-atlas:run ~/code/some-framework    # local checkout, print only
/agentic-atlas:run https://github.com/org/repo   # full clone to temp, profile, clean up
/agentic-atlas:run ~/code/some-framework --save   # also write artifacts under profiles/
```

The launcher `skills/run/atlas.sh` bootstraps its own cached engine venv on first run
(independent of `make setup`), so the skill works from an arbitrary checkout. Override engine
discovery with `AGENTIC_ATLAS_ENGINE=/path/to/repo` when testing.

## Testing approach

`pytest`, deterministic core first. Files: `test_scoring.py` (the arithmetic — must never
drift), `test_spec.py` (loading + validation), `test_evidence.py` (measured signals + honest
coverage guards), `test_classify.py` (answer + verbatim-quote validation),
`test_profiler.py` (full pipeline), `test_report.py` (renderers), `test_docs.py` (README
sync). Run `make test`, or the full gate with `make check`.

When adding a **measured signal type**, extend both `evidence.resolve_measured` and
`axis.schema.json`, and cover it in `test_evidence.py`.

## Contribution conventions

From [AGENTS.md](../AGENTS.md) (the canonical agent guidance; `CLAUDE.md` is a symlink):

- **Python 3.11+.** Keep the deterministic core (`models.py`, `spec.py`, `scoring.py`)
  dependency-light and fully tested.
- **No `TODO` comments.** Implement it, or record the plan in `docs/`.
- **Document what the code *is*, not what it was** — git history covers the past.
- **Prose in docs uses commas rather than dashes** for punctuation.
- **Never hand-edit generated axis README scoring blocks** — edit `axis.yaml`, run `make docs`.
- **Changing the rubric** in a way that can move scores requires a version bump, a
  `rubric/CHANGELOG.md` entry, and a PR rationale. Do not silently recalibrate. See
  [versioning.md](./versioning.md).

## Release process

Automated with **release-please** (`.github/workflows/release-please.yml`,
`release-please-config.json`, `.release-please-manifest.json`). Conventional-commit messages
drive version bumps and the `CHANGELOG.md`; merging the release PR tags a new engine version.
The package builds with Hatchling (`make`/`pip` build the wheel from `pyproject.toml`, which
packages the `agentic_atlas` module). The engine version is stamped onto every profile via
`agentic_atlas.__version__`.

## Two version lines (don't conflate)

- **Engine version** — `pyproject.toml` (`0.4.0`), standard software semver.
- **Rubric version** — `rubric/v1/rubric.yaml` (`rubric_version: 1.4.0`), measurement-standard
  semver where any change that can move a score for identical evidence is MAJOR.

Every profile stamps both, plus the target commit SHA and (for classified indicators) the
answer source, so any profile is reproducible.
