# Single-agent vs Multi-agent

## Why this axis exists

Internal structure, one conversation versus many specialized subagents or personas, affects context hygiene, cost, and how the approach reasons. Neither is better: multi-agent can decompose big problems but adds orchestration overhead. Negative (`single_agent`) means one agent, positive (`multi_agent`) means orchestrated specialists. `specialist-agents` weighs how many specialized roles the tool orchestrates. `separate-contexts` asks whether those roles run as subagents with their own context windows or as personas one conversation adopts in turn: a tool can define many personas and still run every one of them inside a single conversation, which gives none of the context isolation that makes multi-agent structure different. `parallel-agents` asks whether agents work at the same time on separate parts of the work, since subagents can also run strictly one after another. The two added facets carry weight 2 against 3 for `specialist-agents`, because the number of roles is the most direct evidence of the construct. A count of shipped agent-definition files was tried and removed in 4.0.0: tools define subagents as prompts inside skills, spawn them at runtime, or keep personas in reference folders, so a zero count wrongly pulled clearly multi-agent tools (bmad-method, superpowers, ccpm) toward single-agent.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Single-agent vs Multi-agent)

Poles: `single_agent` (negative) to `multi_agent` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| specialist-agents | Does it orchestrate multiple specialized subagents or personas? | judged | 3 | single -1, some +0, many +1 |
| separate-contexts | Does its work run in separate subagents, each with its own context window, or in one conversation (including personas that one conversation adopts in turn)? Answer "mixed" when the main work runs in one conversation and subagents handle specific steps, such as research or review. A tool with no roles that runs in one session answers "one_conversation". Grade the mechanism that runs: agent files the tool installs as host subagents run as subagents, whatever the docs call them. | judged | 2 | one_conversation -1, mixed +0, separate_subagents +1 |
| parallel-agents | Does it run several agents at the same time, in any step (research, implementation, or review)? Answer "default" when the default workflow runs agents concurrently, and "optional" when concurrency is offered but not on the default path. Several people or sessions working in parallel, or an external tool the docs recommend, do not count. | judged | 2 | no -1, optional +0, default +1 |
<!-- END GENERATED -->
