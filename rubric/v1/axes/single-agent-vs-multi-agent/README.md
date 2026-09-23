# Single-agent vs Multi-agent

## Why this axis exists

Internal structure, one conversation versus many specialized subagents or personas, affects context hygiene, cost, and how the approach reasons. Neither is better: multi-agent can decompose big problems but adds orchestration overhead. Negative (`single_agent`) means one agent, positive (`multi_agent`) means orchestrated specialists. `specialist-agents` carries the axis. A count of shipped agent-definition files was tried and removed in 4.0.0: tools define subagents as prompts inside skills, spawn them at runtime, or keep personas in reference folders, so a zero count wrongly pulled clearly multi-agent tools (bmad-method, superpowers, ccpm) toward single-agent.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Single-agent vs Multi-agent)

Poles: `single_agent` (negative) to `multi_agent` (positive). Scale ±10.

Position is a weighted mean of 1 indicator measurement:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| specialist-agents | Does it orchestrate multiple specialized subagents or personas? | judged | 3 | single -1, some +0, many +1 |
<!-- END GENERATED -->
