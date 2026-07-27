# Small-scope vs Large-scope

## Why this axis exists

How much of the delivery lifecycle an approach spans is a practical fit question. A single-task helper is perfect for a quick change and obstructive when driving a whole project, and the reverse is true for a full-lifecycle framework. Negative (`small_scope`) means one focused task, positive (`large_scope`) means idea-to-release coverage. `sl1` (phase coverage) carries the most weight because it measures span directly, and `sl2` separates a one-shot command from a multi-stage pipeline. This axis is classified-only: lifecycle span is a property of the methodology, not of any file a repository ships, so both indicators are answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Small-scope vs Large-scope)

Poles: `small_scope` (negative) to `large_scope` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| sl1 | How many lifecycle phases does it cover (idea, spec, plan, implement, test, review, release)? | classified | 3 | one -1, few -0.4, most +0.5, full_lifecycle +1 |
| sl2 | Is it invoked as a single command or skill, or as a multi-stage pipeline? | classified | 2 | single -1, mixed +0, multi_stage +1 |
<!-- END GENERATED -->
