# Greenfield vs Brownfield

## Why this axis exists

The single biggest predictor of whether an approach will help or frustrate is whether your work is greenfield or brownfield. Greenfield methods front-load spec and product generation and assume they own the whole tree. Brownfield methods assume a large existing codebase they must read, respect, and change surgically. A tool tuned for one is often actively painful for the other, so this axis is usually the first one a reader should consult.

Negative (`greenfield`) means the approach shines starting from an idea with no product yet. Positive (`brownfield`) means it shines inside an existing codebase. The two heaviest indicators capture the defining choices: `gb1` weighs the starting assumption (a blank slate versus an existing codebase), and `gb2` whether the tool ships real machinery for ingesting existing code. `gb4` adds the default unit of work (whole-project generation versus a targeted small diff). This axis is classified-only: on a corpus that mixes prompt methodologies with full software projects, a structural count of greenfield or brownfield artifacts would measure the target's own repository rather than the methodology it teaches, so the judgment lives in questions the skill answers with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Greenfield vs Brownfield)

Poles: `greenfield` (negative) to `brownfield` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| gb1 | Does the workflow assume it starts from a blank slate (an idea or empty project, with no existing code) or from an existing codebase it must work within? | classified | 3 | blank_slate -1, either +0, existing_codebase +1 |
| gb2 | Does it ship explicit steps or agents for ingesting and mapping an existing codebase? | classified | 3 | yes +1, partial +0.4, no -1 |
| gb4 | Is the default unit of work whole-project generation or a targeted small diff? | classified | 2 | whole_project -1, mixed +0, small_diff +1 |
<!-- END GENERATED -->
