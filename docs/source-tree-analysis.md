# Source Tree Analysis

> Generated for AI context on 2026-07-22 (deep scan). Annotates the critical directories
> of each part and marks entry points and integration seams.

## Annotated tree

```
agentic-atlas/
├── agentic_atlas/            # PART: engine — the deterministic Python engine (CLI + library)
│   ├── __init__.py           #   package version (__version__), stamped onto every profile
│   ├── models.py             #   ★ frozen dataclasses: Rubric/Axis/Indicator, *Result, Profile
│   ├── spec.py               #   load + jsonschema-validate a rubric dir into typed models
│   ├── scoring.py            #   ★ pure-arithmetic scoring core (no I/O, no model)
│   ├── evidence.py           #   Target + resolve_measured: the 5 measured signal types
│   ├── classify.py           #   resolve_classified: validate supplied answers + verbatim quote
│   ├── profiler.py           #   profile_target: the single orchestration path
│   ├── report.py             #   render_text / render_markdown / render_html (3D crystal)
│   ├── docs.py               #   generate axis README scoring blocks (make docs / --check)
│   └── cli.py                #   ← ENTRY POINT: agentic-atlas console script (argparse)
│
├── rubric/                   # PART: rubric — the versioned measurement standard (data)
│   └── v1/                   #   one directory per MAJOR version
│       ├── rubric.yaml       #   manifest: rubric_version, title, scale, ordered axis ids
│       ├── rubric.schema.json    #   JSON Schema for the manifest
│       ├── axis.schema.json      #   JSON Schema for a single axis file
│       ├── CHANGELOG.md          #   score-moving change log (rubric semver)
│       └── axes/<id>/            #   13 axes, each a self-contained, contestable unit
│           ├── axis.yaml         #   ★ source of truth: poles, indicators, weights, signals
│           └── README.md         #   hand-written rationale + GENERATED scoring block
│
├── skills/                   # PART: plugin — the distribution surface
│   └── run/
│       ├── SKILL.md          #   the /agentic-atlas:run workflow the host agent follows
│       └── atlas.sh          #   ← LAUNCHER: bootstraps the engine venv, forwards args
├── .claude-plugin/
│   └── plugin.json           #   Claude Code plugin manifest (name, version, keywords)
├── gemini-extension.json     #   Gemini CLI extension manifest (contextFileName: AGENTS.md)
├── .codex/INSTALL.md         #   Codex install notes
│
├── docs/                     # design/method/versioning docs + this generated doc set
│   ├── design.md             #   architecture thesis (spec + interpreter)
│   ├── axes.md               #   axis authoring method + full candidate catalog
│   ├── versioning.md         #   the two independent version lines
│   └── skill-integration.md  #   the stable engine surface the skill targets
├── specs/                    # working specs (handoff notes, correlation ordering)
├── profiles/                 # curated public profiles (.gitkeep only today)
│
├── tests/                    # pytest suite, deterministic core covered first (69 tests)
│   ├── test_scoring.py       #   the arithmetic core (must never drift)
│   ├── test_spec.py          #   rubric loading + validation
│   ├── test_evidence.py      #   measured signal resolution (23 tests)
│   ├── test_classify.py      #   classified answer validation
│   ├── test_profiler.py      #   full-pipeline orchestration
│   ├── test_report.py        #   renderers (23 tests)
│   └── test_docs.py          #   README scoring-block sync
│
├── pyproject.toml            # package metadata, deps, console script, ruff + pytest config
├── Makefile                  # ← primary developer entry point (make help lists targets)
├── AGENTS.md                 # canonical agent instructions (CLAUDE.md is a symlink to it)
├── README.md                 # human-facing overview and usage
├── CHANGELOG.md              # engine changelog (release-please generated)
├── release-please-config.json / .release-please-manifest.json  # release automation
└── LICENSE                   # MIT
```

★ = deterministic core that must stay pure and fully tested.

## Critical directories explained

- **`agentic_atlas/`** — the engine package. The three files that carry the core invariants
  are `models.py` (data only, no score-moving behaviour), `scoring.py` (pure arithmetic), and
  `spec.py` (loads and validates the rubric). `evidence.py` and `classify.py` are the two
  symmetric indicator resolvers; `profiler.py` is the single code path that wires them
  together; `report.py` and `docs.py` are output surfaces; `cli.py` is the only entry point.
- **`rubric/v1/axes/<id>/`** — each axis lives in its own directory so a dispute over an
  indicator is a change to one folder. `axis.yaml` is authoritative; the `README.md` scoring
  block between the generated markers is machine-written from it and must never be hand-edited.
- **`skills/run/`** — the plugin's only skill. `SKILL.md` is the workflow the host agent
  executes; `atlas.sh` is the launcher that finds the engine repo, bootstraps a cached venv,
  and forwards arguments to the `agentic-atlas` console script unchanged.

## Entry points

| Entry point | File | Invoked by |
|---|---|---|
| `agentic-atlas` console script | `agentic_atlas/cli.py:main` | Shell, `make` targets, `atlas.sh` |
| `/agentic-atlas:run` skill | `skills/run/SKILL.md` | Host coding agent (Claude Code) |
| Engine launcher | `skills/run/atlas.sh` | The skill; also `--repo-root` helper |
| `make` (default help) | `Makefile` | Developers |

## Multi-part structure

The three parts share one repo and one release, but interface through narrow, stable seams:
the engine's `questions`/`profile --answers` CLI contract, and the rubric directory the
engine reads. See [integration-architecture.md](./integration-architecture.md) for the data
flow between parts.
