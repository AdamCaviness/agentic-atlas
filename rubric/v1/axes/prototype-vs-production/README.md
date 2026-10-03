# Prototype vs Production

## Why this axis exists

This axis separates approaches that optimize for speed and disposability from those that optimize for shippable, maintainable code. It matters because a production-hardening approach wastes effort on a throwaway spike, and a prototype approach leaves gaps in production work. Negative (`prototype`) means fast, throwaway output, positive (`production`) means CI, security, and hardening. `production-hardening` weighs hardening emphasis most, and `throwaway-tolerance` captures tolerance for throwaway code. This axis is judged-only: a repository's own CI and deployment config measures whether the tool's own project is production-grade, not whether the methodology it teaches hardens the user's output, so the judgment is answered from the target with a cited quote rather than counted from the tool's files.

Most tools insist on maintainable code while treating operations lightly, so two more facets separate them. `non-functional-requirements` asks whether the tool has the user or agent state performance, security, reliability, or scalability requirements for what is being built, which is how production intent is written down before any code exists. `review-before-done` asks whether a change must pass a review against quality criteria before it counts as done. The reviewer may be an agent or a person: solo-vs-team measures handoffs between people, and this indicator measures only whether the quality check happens. A test run alone is not a review, because testing is measured on test-optional-vs-test-first. Both added indicators carry weight 2 against 3 for `production-hardening`.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Prototype vs Production)

Poles: `prototype` (negative) to `production` (positive). Scale ±10.

Position is a weighted mean of 4 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| production-hardening | How much emphasis on production hardening (CI, deployment, security, observability)? | judged | 3 | none -1, some +0, strong +1 |
| throwaway-tolerance | Is throwaway or vibe output acceptable, or does it insist on maintainable code? | judged | 2 | throwaway_ok -1, mixed +0, maintainable_only +1 |
| non-functional-requirements | Does its default workflow require a written statement of non-functional requirements (performance, security, reliability, or scalability; any one counts) for the work being built, filled in by the user or the agent? Answer "prompted" when such a section or question is optional, conditional on task size, or skippable, and "no" when the workflow names none of them (a generic "any constraints?" question is "no"). | judged | 2 | no -1, prompted +0, required +1 |
| review-before-done | Before a change counts as done, must it pass a review of its quality (correctness, security, maintainability) by a reviewer other than the implementing agent: a separate agent or a person? Answer "required" when the review runs and gates by default, even if a flag can skip it. Answer "optional" when the review is offered, advisory (it runs but cannot block), or is a checklist the implementing agent applies to its own work. A test or lint run alone is not a review. | judged | 2 | none -1, optional +0, required +1 |
<!-- END GENERATED -->
