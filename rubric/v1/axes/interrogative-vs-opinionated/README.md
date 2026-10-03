# Interrogative vs Opinionated

## Why this axis exists

This axis captures how an approach reaches decisions, which is largely a matter of taste and team culture rather than quality. Some developers want a tool that interrogates them, drawing out requirements through questions before writing anything. Others want a tool that already has a strong opinion and just drives. Neither is better, they suit different people and moments.

Negative (`interrogative`) means the approach elicits and defers to the user. Positive (`opinionated`) means it prescribes a strong default path. `asks-before-coding` detects an explicit questioning or brainstorming phase, and `path-strictness` detects an enforced pipeline. This axis is judged-only: tone is not a countable artifact, and directive-word density (must, always, never) detected how forcefully a project *writes*, not whether it *defers* to the user, so every indicator is answered from the target with a cited quote.

Two tools with the same questioning phase and the same guided pipeline can still sit far apart, so two more facets each measure a distinct kind of opinion. `decision-ownership` asks who makes the technical choices: a tool can interview the user about goals and then pick the library, architecture, and data model itself, which is opinionated where it counts even after a questioning phase. Approving a finished plan does not count as the user choosing, because autonomous-vs-human-in-loop measures approval points. `mandated-conventions` asks whether the tool imposes conventions on the user's code (coding standards, naming rules, a project structure), a separate question from whether it imposes the order of the steps, which `path-strictness` measures. Testing practice is left out of it because test-optional-vs-test-first measures it, and the layout of the tool's own files is left out because that is the tool's process, not an opinion about the user's code. The two added indicators carry weight 2 against 3 for the original pair, because the questioning phase and the pipeline are the parts of the construct a user meets first.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Interrogative vs Opinionated)

Poles: `interrogative` (negative) to `opinionated` (positive). Scale ±10.

Position is a weighted mean of 4 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| asks-before-coding | Does it run a questioning or brainstorming phase before writing code, or proceed on its own default plan? | judged | 3 | yes -1, partial +0, no +1 |
| path-strictness | Does it enforce a fixed prescribed pipeline the user is expected to follow? | judged | 3 | strict +1, guided +0, loose -1 |
| decision-ownership | When a technical choice has several valid options (a library, an architecture, a data model), does it present the options for the user to pick, or pick one itself? A recommendation the user then confirms or overrides is "mixed". Approving a finished plan is not picking an option, so a tool that writes the plan with its own choices and asks only for plan approval answers "tool_chooses". | judged | 2 | user_chooses -1, mixed +0, tool_chooses +1 |
| mandated-conventions | Does it require the user's code to follow conventions it ships (coding standards, naming rules, a project structure, a forbidden pattern), or leave those to each project? Answer "mandated" if at least one such convention is required by default, even when an escape hatch exists, and "overridable_defaults" if it ships conventions but tells the user to replace or choose them. Testing practice does not count (it is measured on test-optional-vs-test-first), and neither does the layout of the tool's own files (its spec folder or state files). | judged | 2 | project_defined -1, overridable_defaults +0, mandated +1 |
<!-- END GENERATED -->
