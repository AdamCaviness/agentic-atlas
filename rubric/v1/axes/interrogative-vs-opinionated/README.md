# Interrogative vs Opinionated

## Why this axis exists

This axis captures how an approach reaches decisions, which is largely a matter of taste and team culture rather than quality. Some developers want a tool that interrogates them, drawing out requirements through questions before writing anything. Others want a tool that already has a strong opinion and just drives. Neither is better, they suit different people and moments.

Negative (`interrogative`) means the approach elicits and defers to the user. Positive (`opinionated`) means it prescribes a strong default path. `io1` detects an explicit questioning or brainstorming phase, and `io2` detects an enforced pipeline. This axis is classified-only: tone is not a countable artifact, and directive-word density (must, always, never) measured how forcefully a project *writes*, not whether it *defers* to the user, so both indicators are answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Interrogative vs Opinionated)

Poles: `interrogative` (negative) to `opinionated` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| io1 | Does it run a questioning or brainstorming phase before writing code, or proceed on its own default plan? | classified | 3 | yes -1, partial +0, no +1 |
| io2 | Does it enforce a fixed prescribed pipeline the user is expected to follow? | classified | 3 | strict +1, guided +0, loose -1 |
<!-- END GENERATED -->
