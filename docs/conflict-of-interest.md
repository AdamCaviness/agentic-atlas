# Conflict of interest and fairness

## The problem

The author of Atlas also maintains [agentic-toolkit](https://github.com/adamcaviness/agentic-toolkit), which is itself a valid profiling target. A rubric that grades competitors while its author ships a competing tool invites the obvious criticism, and that criticism should be met structurally, not with a promise of good intentions.

## The defenses, built into the process

1. **Public self-evaluation, no special path.** agentic-toolkit is profiled with the same rubric, the same engine, and the same commit-pinned method as every other target, and its profile is published in `profiles/` alongside the others. It receives no manual adjustment.
2. **Rubric changes are versioned pull requests with rationale.** Every change that can move a score bumps the rubric MAJOR version and records why. Recalibration is visible in git and in `rubric/CHANGELOG.md`, never silent.
3. **Indicator-level contestability.** A profiled project that disagrees does not argue with a vibe, it opens an issue against a specific indicator with specific evidence. The dispute is narrow and resolvable.
4. **No aggregate score.** There is no single number to game or to tilt. A profile is a position, not a grade, which removes most of the incentive to bias it.

## The honest framing

Atlas is opinionated by design. The value is not neutrality, it is that the opinion is fully exposed, versioned, and open to surgical correction. A reader who distrusts a position can trace it to the exact indicators and evidence that produced it, and can propose a change.
