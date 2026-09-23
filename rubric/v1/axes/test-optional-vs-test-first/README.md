# Test-optional vs Test-first

## Why this axis exists

Whether testing is enforced up front (TDD) or left to the user is both a quality and a taste decision. Test-first suits teams and production code and can feel heavy during exploration. Negative (`test_optional`) means incidental testing, positive (`test_first`) means enforced TDD. `tests-first` weighs enforcement most, and `testing-phase` whether testing is a first-class phase. This axis is judged-only: a repository's own test directories measure whether the tool's own code is tested, not whether the methodology it teaches enforces test-first for the user (a heavily-tested CLI whose methodology is task management would otherwise read as test-first), so both indicators are answered from the target with a cited quote.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Test-optional vs Test-first)

Poles: `test_optional` (negative) to `test_first` (positive). Scale ±10.

Position is a weighted mean of 2 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| tests-first | Does it enforce writing tests before implementation (TDD)? | judged | 3 | no -1, encouraged +0, enforced +1 |
| testing-phase | Is testing a first-class phase, or incidental? | judged | 2 | incidental -1, present +0, first_class +1 |
<!-- END GENERATED -->
