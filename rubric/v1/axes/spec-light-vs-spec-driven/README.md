# Spec-light vs Spec-driven

## Why this axis exists

How much written design specification precedes code is a core methodology divide. Spec-driven front-loads a PRD or plan, powerful for complex or shared work and heavy for quick changes, while spec-light gets to code fast, sometimes from a ticket alone. Negative (`spec_light`) means jump to implementation, positive (`spec_driven`) means write and follow a specification first. The distinction that separates them is a design specification versus a work item: a PRD, design, or requirements document is a specification, but a ticket, issue, or task list is not, so a ticket-driven tool that never writes a spec sits on the spec-light pole. `spec-required` weighs whether a design spec is required, and `spec-documents` whether specification documents are produced and persisted (not tickets or tasks). The axis is judged-only. A count of shipped spec-template files was tried and removed in 4.0.0: many spec-driven tools write their specs at runtime from prompts and ship no template file, so a zero count wrongly pulled them toward spec-light, and a nonzero count often read the tool's own project folders rather than machinery it ships. This is distinct from interrogative-vs-opinionated: a tool can ask many questions to build a spec, making it both interrogative and spec-driven.

Many tools require and persist a specification, so two more facets measure how much the specification governs the work after it is written. `spec-verification` asks whether the finished result is checked against the specification, by tracing tasks to requirements or by a step that compares the code to the spec: a tool can write a PRD and never read it again. `spec-lifecycle` asks whether the specification stays current as the code changes (a living source of truth) or is written once for the initial build. A spec written once maps to 0.0 because it sits halfway between no specification and a maintained one. Both carry weight 2 against 3 for `spec-required`, and a tool with no specification answers the negative pole on both, so neither question can pull a spec-light tool toward the center.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Spec-light vs Spec-driven)

Poles: `spec_light` (negative) to `spec_driven` (positive). Scale ±10.

Position is a weighted mean of 4 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| spec-required | Is a written design specification (a PRD, design doc, or written plan, not merely a ticket or work item) required before implementation begins? | judged | 3 | none -1, encouraged +0, required +1 |
| spec-documents | Does the workflow produce and persist specification documents (a PRD, design, or requirements doc), as opposed to only tickets, task lists, or code? | judged | 2 | no -1, some +0.3, yes +1 |
| spec-verification | After implementation, is the result checked against the written specification (tasks traced to requirements, or a review or verification step that compares the code to the spec)? Answer "partial" when the check covers only the task list or some requirements, or runs only when a spec file exists. A tool with no specification answers "no". | judged | 2 | no -1, partial +0, yes +1 |
| spec-lifecycle | When a later change alters behavior a specification describes, does the workflow require updating that specification so it stays the source of truth ("living"), or is each specification written for one piece of work and then left, closed, or archived ("written_once")? A specification that may be edited but is not required to be is "written_once". When the docs offer several models with no default, grade the one the main workflow follows. A tool with no specification answers "none". | judged | 2 | none -1, written_once +0, living +1 |
<!-- END GENERATED -->
