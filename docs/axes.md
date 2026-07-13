# Axis authoring

## What an axis is

An axis is a signed spectrum between two named poles, with `0.0` as neutral balance. The sign indicates lean, the magnitude indicates strength of lean. The scale is symmetric (default `10`, so scores run `-10` to `+10`).

An axis is never "good vs bad." Both poles are legitimate design choices. The profile locates a tool so a reader can judge fit for their own context.

## How an axis is built

Do not score the axis directly. An axis is a **weighted scoring system over N measurements**. Decompose it into indicators, each a narrow question (one measurement) with a bounded answer that maps to a value in `[-1, 1]` signed toward one pole. Give each indicator a weight expressing its importance to the axis. The engine then folds those N measurements into the single signed position on the continuum:

```
axis_position = scale * sum(weight_i * measurement_i) / sum(weight_i)
```

The crafting of the axis is choosing the indicators and their weights. That craft lives entirely in the rubric, the engine only executes the arithmetic. A well built axis has enough indicators that no single one dominates, and enough `measured` indicators that a meaningful position exists even before any classification.

## Worked example: Greenfield vs Brownfield

Sign convention: negative pole = greenfield, positive pole = brownfield. A method that shines when starting from an idea and weakens on existing code lands strongly negative.

| id  | question                                                        | kind       | weight | maps to |
|-----|-----------------------------------------------------------------|------------|--------|---------|
| gb1 | First mandatory step generates a spec/PRD from an idea?         | classified | 3      | yes -1.0, partial -0.5, no 0.0 |
| gb2 | Ships explicit steps/agents for ingesting an existing codebase? | classified | 3      | yes +1.0, partial +0.5, no -0.5 |
| gb3 | Density of brownfield vocabulary in docs/commands               | measured   | 2      | none -1.0, some +0.3, heavy +1.0 |
| gb4 | Default unit of work: whole-project generation vs small diff    | classified | 2      | whole -1.0, mixed 0.0, small_diff +1.0 |
| gb5 | Onboarding assumes a new repo vs pointing at an existing one    | measured   | 1      | new_repo -1.0, either 0.0, existing +1.0 |

The full machine-readable form of this axis is in `rubric/v1/axes/greenfield-vs-brownfield/axis.yaml`, and its generated scoring block is in the sibling `README.md`.

## The axis catalog

The full working catalog of candidate axes lives in `README.md`, grouped by the decision each helps a reader make. Three axes ship in `v1.0.0` (Greenfield↔Brownfield, Interrogative↔Opinionated, Autonomous↔Human-in-loop), the rest are backlog. Keep the README catalog and `rubric/*.yaml` as the two sources of truth, this file covers method, not the list.

Some backlog axes need evidence collectors the engine does not have yet. Fresh↔Mature, for example, needs git statistics (age, commit count) and host API facts (stars, forks, release cadence). Adding a collector is an engine change, and it only affects scores once a rubric actually uses it.

## Authoring checklist

- Both poles are legitimate, neither is framed as the failure mode.
- At least one `measured` indicator, so the axis is not fully dependent on classification.
- Every `classified` indicator has a small, mutually exclusive, defined answer set.
- Weights are integers and their intent is documented in the rubric `description`.
- Adding or reweighting an indicator triggers a MAJOR rubric bump. See `docs/versioning.md`.
