# Design

## Thesis

Comparisons of agentic workflows are currently subjective blog posts. Atlas replaces the subjective take with a **transparent, versioned function**. It profiles a tool by locating it on signed bipolar axes, and each axis position is computed from many small, named, evidence-backed indicators.

Atlas is not perfect and does not claim objective truth. It claims something better than a vibe: a spec anyone can inspect, contest at the level of a single indicator, and improve through a versioned pull request.

## Not a ranking

Atlas produces a **profile**, a vector of signed axis positions, not a score. There is no aggregate number and no leaderboard. The output supports a fit decision ("this tool leans hard greenfield and opinionated, which matches my project") rather than a verdict ("this tool is best").

Overlaying two or three profiles on the same axes is the primary intended use.

## Spec plus interpreter

The repository holds two independently versioned things.

### The rubric (data)

`rubric/vX.Y.Z.yaml` defines axes, their poles, and the indicators and weights that compute each axis. `rubric/schema.json` validates any rubric file. The rubric carries all scoring policy, the engine embeds none.

### The engine (code)

`atlas/` reads a rubric, gathers evidence from a target, resolves each indicator to a value, computes axis scores with a fixed formula, and renders a profile. Pipeline:

```
target ─▶ evidence ─▶ indicator resolution ─▶ scoring ─▶ report
             │              │      │
        measured       measured  classified
      (engine only)   (engine)   (model or human, cited)
```

## The two indicator kinds

The tension in the project is "subjective axis, deterministic result." It resolves by decomposing each axis into indicators of two kinds.

- **`measured`** indicators are computed by the engine directly from the repository, with no model. Current signal types: `vocabulary` (term density across docs and commands, bucketed into bands) and `path_presence` (glob matches to a yes/no value). These are fully deterministic.
- **`classified`** indicators require reading and selecting from a small, defined answer set (for example `yes` / `partial` / `no`). A model or a human picks the answer, and the engine records the answer **plus a cited quote** as evidence. The answer set is bounded and anchored so independent resolvers converge.

The scoring step treats both kinds identically: each resolved indicator yields a value in `[-1, 1]` and a weight. The axis score is:

```
axis_score = scale * sum(weight_i * value_i) / sum(weight_i)
```

clamped to `[-scale, +scale]` and rounded. Indicators that cannot be resolved (for example classified indicators with no judge configured) are excluded, and the profile reports coverage so a partial profile is never mistaken for a complete one.

## Where judgment lives, and how it is constrained

Judgment does not vanish, it moves. It is no longer "score this axis from -10 to 10." It is "answer indicator gb1 with yes, partial, or no, and cite the line that proves it." Constraints that keep this reproducible:

- Bounded answer sets with anchored definitions in the rubric.
- A required evidence citation per classified answer.
- Low or zero temperature when a model resolves classified indicators.
- The model id is stamped on the profile, so a resolution is attributable.

## Reproducibility

Every profile stamps rubric version, engine version, target commit SHA, and model id. A local run by the `/atlas` skill and a curated public profile in `profiles/` use the exact same engine, the skill simply does not persist output. There is no second code path.

## Fairness

See `docs/conflict-of-interest.md`. The short version: self-evaluate publicly, version every rubric change with rationale, and let profiled projects contest individual indicators.
