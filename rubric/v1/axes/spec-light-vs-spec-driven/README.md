# Spec-light vs Spec-driven

## Why this axis exists

How much written design specification precedes code is a core methodology divide. Spec-driven front-loads a PRD or plan, powerful for complex or shared work and heavy for quick changes, while spec-light gets to code fast, sometimes from a ticket alone. Negative (`spec_light`) means jump to implementation, positive (`spec_driven`) means write and follow a specification first. The distinction that separates them is a design specification versus a work item: a PRD, design, or requirements document is a specification, but a ticket, issue, or task list is not, so a ticket-driven tool that never writes a spec sits on the spec-light pole. `sd1` weighs whether a design spec is required, `sd2` whether specification documents are produced and persisted (not tickets or tasks), and the measured `sd3` corroborates by counting the spec-producing machinery a tool ships (spec templates and spec-scaffold conventions), never specification vocabulary. This is distinct from interrogative-vs-opinionated: a tool can ask many questions to build a spec, making it both interrogative and spec-driven.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Spec-light vs Spec-driven)

Poles: `spec_light` (negative) to `spec_driven` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| sd1 | Is a written design specification (a PRD, design doc, or written plan, not merely a ticket or work item) required before implementation begins? | classified | 3 | none -1, encouraged +0, required +1 |
| sd2 | Does the workflow produce and persist specification documents (a PRD, design, or requirements doc), as opposed to only tickets, task lists, or code? | classified | 2 | no -1, some +0.3, yes +1 |
| sd3 | How many spec-producing artifacts does the tool ship (spec templates and spec-scaffold conventions)? | measured | 2 |  |
<!-- END GENERATED -->
