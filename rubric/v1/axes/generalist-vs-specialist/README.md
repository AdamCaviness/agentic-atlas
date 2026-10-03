# Generalist vs Specialist

## Why this axis exists

Some approaches claim any domain (BMAD markets business and wellness uses), while most specialize in software. This matters if your work is not code, or if you specifically want software-aware machinery. Negative (`generalist`) means domain-agnostic, positive (`specialist`) means software delivery specifically. `domain-focus` weighs the framing most, and `non-code-claims` checks for explicit broad claims. This axis is judged-only: software-vocabulary density detected how much a project *talks* in code terms, not whether it is *built* for any domain, and it saturated (nearly every target is written in software language), so the judgment is answered from the target with a cited quote instead.

Two indicators are enough for this axis. The construct is the breadth of domains a tool claims, and a tool's claim about its domain is stated in one place and read the same way by every question you could ask about it: a third question (for example whether the steps assume software artifacts) re-reads the same claim and adds no separate facet. Most of the corpus sits at the specialist pole because the corpus is a population of software-delivery tools, not because the rubric cannot separate them: the five tools that claim some work beyond code (backlog-md, bmad-method, compound-engineering, gstack, superclaude) already land apart from the software-only ones. The pile at the specialist pole is a fact about which tools the corpus profiles.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Generalist vs Specialist)

Poles: `generalist` (negative) to `specialist` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| domain-focus | Is it framed for any domain, or specifically for software engineering? | judged | 3 | any_domain -1, mostly_software +0.5, software_only +1 |
| non-code-claims | Does it explicitly claim applicability beyond code (business, writing, wellness)? | judged | 2 | yes_broad -1, some +0, no +1 |
<!-- END GENERATED -->
