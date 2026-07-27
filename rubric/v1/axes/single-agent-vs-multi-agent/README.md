# Single-agent vs Multi-agent

## Why this axis exists

Internal structure, one conversation versus many specialized subagents or personas, affects context hygiene, cost, and how the approach reasons. Neither is better: multi-agent can decompose big problems but adds orchestration overhead. Negative (`single_agent`) means one agent, positive (`multi_agent`) means orchestrated specialists. `ma1` weighs orchestration most, and the measured `ma3` corroborates by counting agent-definition files a tool ships in the locations it installs them (0 or 1 reads single-agent, 2 or more reads multi-agent). `ma3` is deliberately low weight and its globs are anchored so template and source-tree copies do not leak in; a tool whose personas live inside skill definitions ships none in these locations and still lands multi-agent on `ma1`.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Single-agent vs Multi-agent)

Poles: `single_agent` (negative) to `multi_agent` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| ma1 | Does it orchestrate multiple specialized subagents or personas? | classified | 3 | single -1, some +0, many +1 |
| ma3 | How many agent-definition files does the tool ship? | measured | 1 |  |
<!-- END GENERATED -->
