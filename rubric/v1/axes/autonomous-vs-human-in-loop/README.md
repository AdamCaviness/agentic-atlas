# Autonomous vs Human-in-loop

## Why this axis exists

How much an approach runs unattended determines how you spend your attention. An autonomous autopilot is a gift when you trust the task and want to step away, and a liability when you need to steer closely or the blast radius is large. Frequent checkpoints are the reverse. This axis helps a reader match a tool to how much oversight the work demands.

Negative (`human_in_loop`) means frequent approvals and checkpoints. Positive (`autonomous`) means end-to-end autopilot with little intervention. `autopilot-mode` detects an advertised autopilot mode, and `approval-gates` detects mandatory approvals between phases. This axis is judged-only: checkpoint vocabulary (approve, confirm, review) detected how often a project *mentions* oversight, not whether it *requires* it, so every indicator is answered from the target with a cited quote.

`failure-recovery` adds what happens when a step fails: a tool that diagnoses and retries a failing test or build on its own needs less attention than one that stops and hands every failure to the user, even when both pause at the same planned approval points. This is a separate facet from `approval-gates`, which counts planned pauses, and from `autopilot-mode`, which reads what the tool advertises. It carries weight 2 against 3 for the original pair, because planned pauses and the advertised mode decide most of the attention a run needs.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Autonomous vs Human-in-loop)

Poles: `human_in_loop` (negative) to `autonomous` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| autopilot-mode | Does it advertise an autonomous or autopilot end-to-end mode? | judged | 3 | yes +1, partial +0, no -1 |
| approval-gates | Does it require explicit user approval between phases by default? | judged | 3 | every_phase -1, some_phases +0, none +1 |
| failure-recovery | In its main implementation flow, when a step fails (a test fails, a build breaks, a check rejects the work), does the agent diagnose and retry until it passes, retry a bounded number of times and then stop, or stop and hand the failure to the user? A tool that ships no failure handling, or where a person does the implementing, answers "stops_for_user". | judged | 2 | stops_for_user -1, retries_then_stops +0, self_recovers +1 |
<!-- END GENERATED -->
