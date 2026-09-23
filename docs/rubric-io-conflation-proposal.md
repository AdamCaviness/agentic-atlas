# Decision-ready proposal: the asks-before-coding conflation on Interrogative vs Opinionated

Status: closed. Maintainer decision: keep 3.0.0 `asks-before-coding` (Reading 1). Reopen only with new
evidence, not a new opinion. Audience: rubric authors. This documents a
construct-validity nuance found while validating rubric 3.0.0 by profiling five new tools. It is
NOT a defect that forces a change: the opinionated pole is reachable by real tools (see below),
the calibration harness is green, and the current axis is a defensible construct. It is a
judgment call about what "opinionated" should mean, presented with the exact change, the targets
that move, the version implications, and the accepted recommendation.

## The finding

On Interrogative vs Opinionated (negative `interrogative`, positive `opinionated`), the axis has
two judged indicators, each weight 3:

- `asks-before-coding` "Does it run a questioning or brainstorming phase before writing code, or proceed on its
  own default plan?" maps `{yes: -1.0, partial: 0.0, no: +1.0}`.
- `path-strictness` "Does it enforce a fixed prescribed pipeline the user is expected to follow?" maps
  `{strict: +1.0, guided: 0.0, loose: -1.0}`.

`axis = 5 * (io1_value + io2_value)`.

Across the 23-tool corpus (18 original plus the 5 profiled for this validation) the positions are:

| asks-before-coding \\ path-strictness | loose (−1) | guided (0) | strict (+1) |
|---|---|---|---|
| **yes (−1)** | *(none)* | **−5.0**: 13 tools (agent-os, ai-dev-tasks, ai-dlc, bmad-method, cc-sdd, compound-engineering, gsd, gstack, openspec, prps-agentic-eng, spec-kit, superclaude, vibe-coding) | **0.0**: ccpm, superpowers |
| **partial (0)** | *(none)* | **0.0**: agentic-toolkit, backlog-md, context-engineering, cursor-memory-bank | **+5.0**: claude-git-pr-skill, metaswarm |
| **no (+1)** | *(none)* | **+5.0**: task-master | **+10.0**: autonomous-dev |

The pattern the new tools exposed: **to score on the opinionated side, a tool must NOT elicit
(asks-before-coding = no or partial). A tool that elicits requirements (asks-before-coding = yes) is capped at 0.0 no matter
how strictly it prescribes its path (path-strictness = strict).** The clearest cases are `superpowers`
("Mandatory workflows, not suggestions", path-strictness = strict) and `ccpm` (path-strictness = strict): both are
maximally prescriptive about the path yet land at exactly 0.0 because they also run a
brainstorming phase (asks-before-coding = yes). `spec-kit`, whose constitution enforces a rigid
test-first / spec-plan-tasks pipeline, sits at −5.0 ("interrogative") purely because it "ask[s]
up to 5 highly targeted clarification questions".

The tool that reaches +10.0 (`autonomous-dev`) does so via asks-before-coding = no: `/implement "#72"` takes a
GitHub issue and drives it through a hard-gated 15-step pipeline without a requirements-questioning
phase (its one human touchpoint, plan approval, is booked on the autonomous axis as approval-gates, not asks-before-coding).
`metaswarm` lands +5.0 (asks-before-coding = partial): its default `/start-task` flow drives a provided spec
through unskippable gates but opens with a light complexity check-in ("ask the user to confirm your
assessment"), which is a check-in rather than a requirements-elicitation phase. So **the opinionated
pole IS reachable by a real, in-scope, whole-repo tool** (this refutes the pre-validation worry that
asks-before-coding/path-strictness made the pole anchor-only), and the opinionated side is populated by four tools
(autonomous-dev +10, and claude-git-pr-skill, metaswarm, task-master at +5). What the profiling shows is narrower: `asks-before-coding` measures *presence of a requirements-
elicitation phase*, which is near-universal among spec-driven methodologies and is orthogonal to
*how strongly the tool prescribes the approach*. A tool can ask you what to build (elicit) and
still prescribe, non-negotiably, how it will be built (`superpowers`). The axis currently scores
that tool "balanced".

## Is that wrong? Two defensible readings

- **Reading 1 (current, "whole decision posture"): keep as-is.** `interrogative` is defined as
  "elicits and defers to the user"; `opinionated` as "prescribes a strong default path and drives
  it." Under this reading a tool that both elicits requirements *and* enforces a pipeline is
  genuinely doing some of each, so 0.0 is a fair summary. A user who wants "drives hard with no
  collaboration" correctly reads `autonomous-dev` (+10) as more opinionated than `superpowers` (0.0,
  which collaborates on requirements). The axis is informative and the pole is reachable.

- **Reading 2 ("path-prescription"): asks-before-coding conflates two constructs (AD-5).** If "opinionated" is
  meant to capture *how strongly the tool prescribes the approach* regardless of whether it
  gathers requirements, then `asks-before-coding` folds in an orthogonal near-universal behavior (elicitation)
  and mis-reads `superpowers`/`spec-kit` as non-opinionated. This is the AD-5 conflation test
  from `docs/rubric-v2-plan.md`: name a target with property A (prescribes a strong path) but not
  B (defers decisions), `superpowers` is exactly that, and `asks-before-coding` cannot distinguish it from a
  genuinely deferential tool.

## The proposed change (if Reading 2 is the intent)

Redefine `asks-before-coding` to measure decision-deference on the *approach*, not the presence of an
elicitation phase:

> `asks-before-coding` (reworded): "When it decides HOW to proceed (the approach, structure, and next step),
> does it defer to the user or commit to its own strong default?"
> `{defers: -1.0, mixed: 0.0, decides: +1.0}`

Re-answer `asks-before-coding` for all 23 targets under the new wording. A tool that asks clarifying questions
about *what* to build but prescribes *how* (e.g. `spec-kit`, `superpowers`) becomes
`decides`/`mixed` rather than `yes`. `path-strictness` and its weight are unchanged. Extremes stay ±1.0, so
the axis still reaches ±scale (AD-3) and still offers a neutral middle (AD-6); the calibration
harness stays green by construction.

Targets that move most (illustrative, exact values set at re-answer time):

- `superpowers`, `ccpm`: 0.0 -> about +5 to +10 (strict path prescription, minimal path-deference).
- `spec-kit`: −5.0 -> about 0 to +5 (rigid prescribed pipeline, elicits only requirements).
- the 13 tools now at −5.0: spread according to how much each defers on the approach; the pure
  "brainstorm then let you drive" tools stay negative, the strong-default methodologies move up.
- `autonomous-dev`, `task-master`: unchanged (already asks-before-coding = no -> `decides`). `metaswarm`
  (asks-before-coding = partial today) moves up insofar as its complexity check-in is a routing confirmation
  rather than genuine deference on the approach.

Rejected alternatives:
- **Reweight path-strictness > asks-before-coding** (e.g. asks-before-coding weight 2, path-strictness weight 4): mechanically lifts `superpowers`/`ccpm`
  to +3.3 with no re-answering, but it does not fix the conflation, it just down-weights it, and
  it silently changes every io position. Cleaner to fix the indicator than to hide it behind weights.
- **Shrink asks-before-coding's negative value** (e.g. yes -> −0.5): breaks the ±1.0 convention (AD-3); the
  interrogative pole would no longer reach −scale. Rejected.

## Version implications

Either reading is internally consistent; moving between them is a MAJOR rubric bump (it moves
scores for identical evidence), requiring: `rubric_version` 3.0.0 -> 4.0.0, a `rubric/CHANGELOG.md`
entry, re-answering `asks-before-coding` for all 23 corpus targets with fresh cited quotes, regenerating the axis
README (`make docs`) and the profile corpus (`make profiles`), and a green harness plus adversarial
review, exactly the bar 3.0.0 met.

## Recommendation (accepted)

**Keep the axis as-is (Reading 1).** This is the maintainer decision. Rationale: (1) the opinionated
pole is reachable by real tools, so nothing is broken; (2) the current construct ("elicits and
defers" vs "prescribes and drives") is defensible and the 0.0 placements are fair summaries of
tools that do both; (3) a MAJOR bump and a full re-answer for a construct-definition preference is
not warranted without new evidence that "opinionated" should mean path-prescription
specifically. If that evidence appears, the change above is ready to implement to
the 3.0.0 bar. Do not adopt the reweight or value-shrink shortcuts.

One related honest population fact (not a defect): the interrogative extreme (−10) is currently
unreached because it needs `path-strictness = loose` (no prescribed pipeline at all), and every profiled
agentic-development tool ships at least a guided flow. The axis still reaches −10 by construction
and the `spec-heavy-maximal` anchor exercises the opinionated pole; a purely elicitation-only
tool with no methodology would sit at −10 but is out of the corpus's populated range, the same
way the prototype pole is (see the validation verdict).
