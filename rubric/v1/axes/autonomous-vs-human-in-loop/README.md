# Autonomous vs Human-in-loop

## Why this axis exists

How much an approach runs unattended determines how you spend your attention. An autonomous autopilot is a gift when you trust the task and want to step away, and a liability when you need to steer closely or the blast radius is large. Frequent checkpoints are the reverse. This axis helps a reader match a tool to how much oversight the work demands.

Negative (`human_in_loop`) means frequent approvals and checkpoints. Positive (`autonomous`) means end-to-end autopilot with little intervention. `ah1` detects an advertised autopilot mode, and `ah2` detects mandatory approvals between phases. This axis is classified-only: checkpoint vocabulary (approve, confirm, review) measured how often a project *mentions* oversight, not whether it *requires* it, so both indicators are answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Autonomous vs Human-in-loop)

Poles: `human_in_loop` (negative) to `autonomous` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| ah1 | Does it advertise an autonomous or autopilot end-to-end mode? | classified | 3 | yes +1, partial +0.3, no -1 |
| ah2 | Does it require explicit user approval between phases by default? | classified | 3 | every_phase -1, some_phases +0, none +1 |
<!-- END GENERATED -->
