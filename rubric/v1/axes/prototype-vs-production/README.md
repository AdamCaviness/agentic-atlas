# Prototype vs Production

## Why this axis exists

This axis separates approaches that optimize for speed and disposability from those that optimize for shippable, maintainable code. It matters because a production-hardening approach wastes effort on a throwaway spike, and a prototype approach leaves gaps in production work. Negative (`prototype`) means fast, throwaway output, positive (`production`) means CI, security, and hardening. `pp1` weighs hardening emphasis most, and `pp2` captures tolerance for throwaway code. This axis is classified-only: a repository's own CI and deployment config measures whether the tool's own project is production-grade, not whether the methodology it teaches hardens the user's output, so the judgment is answered from the target with a cited quote rather than counted from the tool's files.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Prototype vs Production)

Poles: `prototype` (negative) to `production` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| pp1 | How much emphasis on production hardening (CI, deployment, security, observability)? | classified | 3 | none -1, some +0.3, strong +1 |
| pp2 | Is throwaway or vibe output acceptable, or does it insist on maintainable code? | classified | 2 | throwaway_ok -1, mixed +0, maintainable_only +1 |
<!-- END GENERATED -->
