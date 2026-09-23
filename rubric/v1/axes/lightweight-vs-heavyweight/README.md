# Lightweight vs Heavyweight

## Why this axis exists

How much a user must learn and install before getting value is a real adoption cost. Lightweight tools pay off immediately, heavyweight tools ask for concepts, roles, and setup first, which can be worth it for large efforts. Negative (`lightweight`) means small footprint and little ceremony, positive (`heavyweight`) means many concepts and steps. `learning-curve` weighs concepts and ceremony most, and `install-footprint` the install footprint. This axis is judged-only: ceremony vocabulary density detected how much a project *talks* about phases and roles, not how much a user must actually learn, and it saturated, so the judgment is answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Lightweight vs Heavyweight)

Poles: `lightweight` (negative) to `heavyweight` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| learning-curve | How many concepts and how much ceremony must a user learn before getting value? | judged | 3 | minimal -1, moderate +0, heavy +1 |
| install-footprint | How large is the install and setup footprint? | judged | 2 | tiny -1, moderate +0, large +1 |
<!-- END GENERATED -->
