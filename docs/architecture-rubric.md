# Architecture: Rubric (`rubric/`)

> Part `rubric` — the versioned measurement standard, expressed as data. Deep scan,
> 2026-07-22. Complements [axes.md](./axes.md) (authoring method + candidate catalog) and
> [versioning.md](./versioning.md) (the semver policy).

## Executive summary

The rubric is **data, not code**. It carries all scoring policy (poles, indicators, weights,
answer-to-value mappings, measured signal specs) so the engine can interpret it without
embedding any of it. It is a directory per MAJOR version (`rubric/v1`), schema-validated, and
its human documentation's scoring block is machine-generated from the same source of truth the
engine reads. This is the "spec" half of the spec-plus-interpreter design.

Current version: **`rubric_version: 1.4.0`**, scale `10`, **13 active axes**.

## Layout

```
rubric/v1/
├── rubric.yaml          Manifest: rubric_version, title, description, scale, ordered axis ids
├── rubric.schema.json   JSON Schema validating the manifest
├── axis.schema.json     JSON Schema validating one axis file
├── CHANGELOG.md         Every score-moving change, per rubric semver
└── axes/<id>/
    ├── axis.yaml        Source of truth: poles, explain, indicators (weights, signals, answers)
    └── README.md        Hand-written rationale + a GENERATED scoring block (do not hand-edit)
```

Each axis is its own directory: a dispute over an indicator is a change to exactly one folder,
and its generated README block cannot drift from the weights the engine uses.

## The manifest (`rubric.yaml`)

Holds `rubric_version`, `title`, `description`, a rubric-wide `scale` (default 10 — a single
shared range is what makes axes comparable, so it is a constant, never a per-axis knob), and
`axes`, the ordered list of axis ids in display order. Axes are grouped for display as
context / style / process / architecture / footprint. Every id maps to `axes/<id>/axis.yaml`;
the engine errors if the file is missing or its internal `id` disagrees with the directory.

## The 13 active axes

| Axis (negative ↔ positive) | Meaning |
|---|---|
| greenfield-vs-brownfield | Excels from an idea vs inside an existing codebase |
| small-scope-vs-large-scope | One task vs the whole delivery lifecycle |
| prototype-vs-production | Fast throwaway output vs production hardening |
| solo-vs-team | Single developer vs multi-contributor / team-safe |
| generalist-vs-specialist | Any domain vs software delivery specifically |
| fresh-vs-mature | New and fast-moving vs established and battle-tested |
| interrogative-vs-opinionated | Elicits and asks vs prescribes a strong default |
| autonomous-vs-human-in-loop | Unattended autopilot vs frequent checkpoints |
| spec-light-vs-spec-driven | Jumps to code vs plans and specs first |
| test-optional-vs-test-first | Testing incidental vs TDD enforced |
| single-agent-vs-multi-agent | One conversation vs subagents / personas |
| prescriptive-vs-composable | Fixed pipeline vs pick-and-choose parts |
| lightweight-vs-heavyweight | Small footprint vs large and elaborate |

The shipped set is a curated subset of a larger candidate catalog; heavily correlated axes
dilute a profile rather than sharpen it, so the rest are backlog (see [axes.md](./axes.md)).

## The axis data model (`axis.yaml`)

Worked example, `greenfield-vs-brownfield`:

```yaml
id: greenfield-vs-brownfield
title: Greenfield vs Brownfield
poles:
  negative: greenfield          # the -scale end
  positive: brownfield          # the +scale end
explain:                        # plain-language meaning shown in the report
  negative: excels starting from an idea, with no code yet
  positive: excels working inside an existing, established codebase
indicators:
  - id: gb1
    question: "Is the first mandatory step generating a spec or PRD from an idea...?"
    kind: classified
    weight: 3
    answers: { "yes": -1.0, partial: -0.5, "no": 0.0 }   # answer → value in [-1, 1]
  - id: gb3
    question: "Density of brownfield vocabulary across docs and commands."
    kind: measured
    weight: 2
    signal:
      type: vocabulary
      terms: ["legacy", "migration", "migrate", "refactor", "existing codebase", "brownfield"]
      bands:
        - { max_count: 0, value: -0.8 }
        - { max_count: 5, value: 0.24 }
        - { max_count: null, value: 0.8 }    # null = catch-all top band
```

Field rules the engine relies on:

- **`kind: classified`** carries an `answers` map from each allowed value to a float in
  `[-1, 1]` signed toward a pole. The keys are the *only* accepted answers; boolean-looking
  keys (`yes`/`no`) must be quoted (YAML 1.1 would coerce them, and `spec.py` rejects the
  coerced form).
- **`kind: measured`** carries a `signal` dict interpreted by `evidence.resolve_measured`. The
  supported types are `vocabulary`, `path_presence`, `path_count`, `git_stats`, `github_api`.
  `vocabulary`/`path_count`/`git_stats`/`github_api` map a raw count to a value via ordered
  `bands` (first band whose `max_count` is `>=` the count wins; a `null` `max_count` is the
  catch-all). `path_presence` maps to explicit `present`/`absent` values.
- **`weight`** scales the indicator's contribution to the axis's weighted mean.

Both kinds resolve to a value + weight and are scored identically by `scoring.py`; the sign
lives entirely in the data, not the engine.

## Schemas

- `rubric.schema.json` validates the manifest (required version/title/axes, scale).
- `axis.schema.json` validates a single axis: required `id`, `title`, `poles`, `indicators`;
  per-indicator `kind`, `weight`, and the shape of `answers` (classified) or `signal`
  (measured).

`agentic-atlas validate rubric/v1` (or `make validate`) runs both. Adding a new measured
signal type means extending both `evidence.resolve_measured` and this schema.

## Generated README scoring blocks

Each `axes/<id>/README.md` has hand-written rationale above a delimited, machine-generated
block (poles, formula, and the indicator table). `agentic-atlas docs` (`make docs`)
regenerates the block from `axis.yaml`; `make docs-check` fails the CI gate on any drift.
Never hand-edit between the `<!-- BEGIN GENERATED -->` / `<!-- END GENERATED -->` markers.

## Versioning (measurement-standard semver)

Distinct from the engine's software semver. Guiding question: *would this change move a score
for identical evidence?*

- **MAJOR** — anything that can move an existing score: add/remove an indicator, change a
  weight or formula, change an answer→value mapping, redefine a pole. New MAJOR ⇒ new
  `rubric/vN` directory; profiles across MAJOR versions are not comparable.
- **MINOR** — add a whole new axis or optional metadata, leaving every existing score identical.
- **PATCH** — wording that cannot change any indicator value.

**Pre-settled status:** v1 is an initial work in progress. Until the standard stabilizes and
public profiles exist, score-moving changes are logged honestly in `rubric/CHANGELOG.md` but
do not each mint a new MAJOR directory (which is why the manifest reads `1.4.0` while still
living under `v1`). Every rubric change requires a CHANGELOG entry and a PR rationale — do not
silently recalibrate. See [versioning.md](./versioning.md).
