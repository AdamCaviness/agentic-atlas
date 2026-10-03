# Solo vs Team

## Why this axis exists

Whether an approach assumes one developer or many changes its coordination overhead entirely. A solo developer does not want claiming, assignment, and handoff ceremony, and a team is hampered without it. Negative (`solo`) means built for one, positive (`team`) means multi-contributor and team-safe. `team-coordination` weighs collaboration safety most, and `human-handoffs` captures handoffs between people. `shared-work-state` asks where the state of the work lives: on one developer's machine, in files committed to the repository, or in a tool the team shares such as an issue tracker. Committed files map to 0.0 because they reach collaborators through git but nothing in them is built for several people working at once. This is separate from `team-coordination`, which asks whether the tool prevents contributors from colliding, because a tool can publish its tasks to a shared tracker without any claiming or conflict rules. This axis is judged-only: a repository's own team infrastructure (CI workflows, code owners, PR templates) measures how that repository is governed, not whether the methodology it teaches is built for a team, so every indicator is answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Solo vs Team)

Poles: `solo` (negative) to `team` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| team-coordination | Does it provide team-safe collaboration (claiming or assigning work, avoiding conflicts between contributors)? | judged | 3 | none -1, partial +0, strong +1 |
| human-handoffs | Are there defined handoffs between people or human reviewers? | judged | 2 | none -1, some +0, many +1 |
| shared-work-state | By default, where does it keep the state of the work (plans, tasks, progress)? Answer "local" for one developer's machine (a session, a store outside the repository, or project files the docs keep out of version control), "repository" for files committed to the repository (including a tracker that stores its data in git), and "team_tool" for a hosted tool the team shares, such as an issue tracker or project board. When the tool syncs between stores by default, answer the most shared one. | judged | 2 | local -1, repository +0, team_tool +1 |
<!-- END GENERATED -->
