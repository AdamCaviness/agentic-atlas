# Fresh vs Mature

## Why this axis exists

Maturity reads like a magnitude (more commits, more age, more contributors), but the rubric models it as a signed axis so it stays in the same family as every other slider and so both ends are framed as legitimate. Negative (`fresh`) means new, fast-moving, and cutting-edge: you get the newest ideas at the cost of churn and a thin track record. Positive (`mature`) means established, stable, and battle-tested: you get fewer surprises at the cost of inertia. A reader choosing an approach for a conservative production team and a reader chasing the latest technique want opposite ends of this axis, and both are making a sound choice.

This axis is the reason the `git_stats` collector exists. Its weight sits deliberately on deterministic git-history facts (`repo-age` through `release-tags` measure age, commits, distinct people, and release tags up to the profiled commit), so it produces a meaningful position with no model in the loop, which is exactly why a judged-only maturity axis was rejected during v1 curation. The single judged indicator (`stated-stability`) only nudges the position by reading how the project describes its own stability. Star count is deliberately absent: popularity is adoption, not maturity, and a widely-starred week-old project is still fresh. Contributors are counted as people, not email addresses: identities sharing a name, email, or GitHub login merge, and automation and AI authors listed in the axis file are dropped, so a solo project driven by bots does not read as a team. A shallow clone truncates history, so on one the git indicators resolve to unresolved (counted against coverage) rather than a false fresh floor, and a partial run is never mistaken for a complete one.

Bands are a first proposal calibrated to open-source norms (roughly: under 6 months / 100 commits / 2 contributors reads as fresh, multi-year with a thousand-plus commits and a real release history reads as mature) and are expected to be contested and refined.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Fresh vs Mature)

Poles: `fresh` (negative) to `mature` (positive). Scale ±10.

Position is a weighted mean of 5 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| repo-age | How old is the repository, from its first commit to HEAD? | detected | 2 | git age_days: <= 180: -1, <= 730: +0, more: +1 |
| commit-count | How many commits has the repository accumulated? | detected | 2 | git commit_count: <= 100: -1, <= 1000: +0, more: +1 |
| contributor-count | How many distinct people have committed? | detected | 1 | git contributor_count: <= 2: -1, <= 10: +0, more: +1 |
| release-tags | How many release tags are in the history up to the profiled commit, as a proxy for an established release cadence? | detected | 1 | git tag_count: <= 0: -1, <= 5: +0, more: +1 |
| stated-stability | How does the project describe its own stability in its docs? | judged | 2 | experimental -1, evolving +0, stable +1 |
<!-- END GENERATED -->
