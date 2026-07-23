# Rubric v2 plan: calibration remediation

Status: draft. Audience: rubric authors and engine maintainers. This is a planning
document, not a rubric. It records the decisions v2 commits to and the concrete changes
that follow from them.

## Why v2 exists

A corpus-wide audit of v1 (18 curated profiles, 13 axes) found that the rubric collapses
most targets onto one pole of several axes, and that the nominal ±10 scale is never
reachable. The defects are systemic, not isolated to one axis:

- **Vocabulary-band saturation.** Every `vocabulary` measured indicator tops out at a
  trivially small count, so any repo with documentation saturates to the top band. Raw
  counts span two to three orders of magnitude (`sd3`: 56 to 8628) and the three bands
  flatten all of it to a single value. Affects `sd3, sl3, gs3, io3, lw3, ah3, tf3, pp3,
  st3, ma2, gb3`.
- **Saturated indicators inject bias, they do not merely fail to discriminate.** A
  constant indicator contributes nothing to spread but shifts every score by
  `value * weight / axis_weight`. `sd2`, `sd3`, and `sl3` are fully constant across the
  corpus, each adding roughly +2.29 points to every target. Spec-driven is hit twice,
  which is why it is the most collapsed axis (observed range 2.4 of a possible 20).
- **The ±10 scale is a false promise.** No axis reaches ±10; the clamp in `scoring.py` is
  dead code. Per-axis reachable ceilings run from +6.0 (greenfield/brownfield) to +9.5
  (autonomous), set by whatever value magnitudes each indicator author happened to pick.
  Equal bar lengths across axes are therefore not equal extremity, which defeats the
  shared-scale premise, and some ranges are asymmetric so score 0 is not construct-neutral.
- **Weak construct validity in measured proxies.** `fresh-vs-mature` measures the checkout,
  not the project: 15 of 18 profiles report `commit_count = 1` and `age_days = 0` because
  the targets were shallow clones, so the git indicators resolve to the "fresh" floor as a
  fetch artifact, while `stars` (popularity, orthogonal to maturity) saturates to "mature"
  for everyone.
- **Keyword-context blindness.** Bag-of-words counts a term regardless of whether the
  sentence supports or negates the pole. "The ticket body is your spec" is a spec-light
  statement that scored as spec-driven; a doc saying "no approval needed" counts its words
  toward human-in-loop.
- **Middle answers tilt positive.** Intermediate classified answers are almost always
  mapped positive (+0.2 to +0.48), rarely 0, so "encouraged but not required" scores a
  quarter of the way to the positive pole instead of neutral.

v2 is a MAJOR rubric bump. It changes scores for identical evidence, so it lives under a
new `rubric/v2/` directory, ships a `rubric/CHANGELOG.md` entry with rationale, and does
not recompute v1 profiles. It does not touch the atlas premise: signed diverging axes, both
poles legitimate, no aggregate score.

## The invariant spine

These are the durable decisions. Everything under "Seed" is a specific way to satisfy them
and can change without reopening the spine. Each decision names what it binds and the
divergence it prevents.

### AD-1 Reproducibility forbids corpus-relative scoring `[ADOPTED]`

- **Binds:** all normalization, band calibration, and threshold selection.
- **Prevents:** a single profile's score depending on which other targets were profiled,
  which would break "every profile is reproducible" (core invariant 4).
- **Rule:** any quantity derived from the corpus (band edges, thresholds, reachable-range
  constants) is calibrated once and frozen into the rubric as data. Scoring a target reads
  only that target plus frozen rubric constants. Per-target self-relative measures (for
  example, a count normalized by the target's own corpus size) are allowed because they
  depend on the target alone. Corpus-relative math at scoring time (z-scores, demeaning,
  live quantile bands) is not.

### AD-2 The measured layer scores behavior-bearing structure, not prose

- **Binds:** every `measured` indicator.
- **Prevents:** vocabulary saturation, keyword-context blindness, and "talks about X"
  masquerading as "does X".
- **Rule:** measured indicators read structural or behavioral evidence (command, skill, and
  template definitions; the artifacts a workflow produces; git and host-API facts), not
  free-text word density. A lexical signal, if one survives, is corroborating only under
  AD-4 and is never the sole measured indicator that can move an axis.

### AD-3 The nominal scale is the reachable scale

- **Binds:** indicator value ranges and the axis scoring step.
- **Prevents:** unreachable poles, and (under the ±1.0 convention) incommensurable bars
  across axes.
- **Rule:** every axis can reach both `+scale` and `-scale`. The preferred mechanism is the
  ±1.0 value convention (AD-4): when every bipolar indicator's extremes are ±1.0, the axis
  reaches the bound with no rescale and bars are directly comparable across axes. Where an
  indicator is honestly one-directional (it can only evidence one pole, for example `gb1`),
  an engine rescale maps the axis's rubric-derived reachable range onto ±scale piecewise
  about zero, so raw 0 stays 0 and each pole is reachable. A rescaled axis buys reachability
  but not evidence-strength comparability, a bar then means "fraction of reachable range"
  (see Risks), so the rescale is a fallback for genuinely one-directional axes, not the
  default.

### AD-4 Uncertainty is expressed through weight, not shrunk extremes

- **Binds:** how indicator values and weights are assigned.
- **Prevents:** a noisy indicator injecting constant bias while appearing humble (the v1
  ±0.8 habit shrank extremes on saturated signals, which added bias rather than caution).
- **Rule:** a low-confidence indicator carries low weight; its extreme values remain ±1.0.
  Measured indicators should not dominate an axis; prefer classified indicators to carry the
  construct, so a future saturated measured signal has bounded influence. (A fixed weight cap
  is deferred: on a three-indicator axis a single weight-2 measured indicator is already 29%,
  so a hard 20% would force indicator inflation. The principle is "measured does not
  dominate", not a specific percentage.)

### AD-5 One construct per axis, one construct per indicator

- **Binds:** axis and indicator authoring.
- **Prevents:** conflation, such as scoring "a written work item exists" (a ticket) as if
  it were "a design specification exists" (a PRD).
- **Rule:** each indicator names the single construct it measures. The conflation test: name
  a target that has property A but not property B; if the indicator cannot distinguish them,
  it conflates and must be split.

### AD-6 Classified scales have a true zero

- **Binds:** every `classified` answer map.
- **Prevents:** the middle-answer positive tilt.
- **Rule:** extremes map to ±1.0, and intermediate answers are placed by justified construct
  distance rather than defaulted to a positive value. That distance may be 0.0, and a
  genuinely asymmetric construct may justify a nonzero middle, but the placement is argued,
  not incidental. An axis must offer at least one answer that can land near zero, so a
  balanced target is expressible.

### AD-7 Guarantees live in the engine, calibration lives in a standing harness

- **Binds:** where each protection is enforced.
- **Prevents:** a known failure mode recurring through prose an agent can skip. The v1 run
  skill already warned against shallow clones, yet the committed corpus is still corrupt,
  because a warning is not a guarantee.
- **Rule:** deterministic invariants are enforced in code or schema (a shallow clone makes
  git indicators resolve to unresolved, not to a pole; the schema validates the AD-4 and
  AD-6 value conventions). Corpus-level health (indicator variance, axis spread,
  reachability, anchor placement) is a CI test over a frozen fixture.

## Seed: the concrete v2 changes

Replaceable specifics that satisfy the spine. True at v2 cold-start, owned by the rubric and
engine once built.

**New engine signal type `command_artifact`** (satisfies AD-2). Parses command and skill
definitions (`skills/*/SKILL.md` frontmatter, `.claude/commands/*.md`) and detects artifacts
a step *structurally* declares it produces: an explicit output field, or a file path the step
is defined to write. The detection contract is the whole point, and its failure mode is real
(see Risks): if it falls back to scanning the skill body prose for output words, it is
vocabulary matching again. So it keys only off structural declarations and resolves
*unresolved* when a target's commands carry none, rather than guessing from prose. Within that
contract it measures behavior ("this tool has a step that emits a PRD") rather than vocabulary
("this tool says PRD a lot"), has no polarity problem, and is reproducible from the target
alone.

**Spec-light vs spec-driven** (AD-2, AD-5, AD-6):
- Split `sd1` into "is a design specification required before code?" and "is a work item
  required before code?" Decide whether the second belongs here or on
  prescriptive-vs-composable (a ticket-before-code is a process decision, not a spec).
- `sd2` requires the persisted artifact to be a specification, not any file, so filing a
  ticket no longer counts as producing a spec.
- Replace `sd3` (vocabulary) with a `command_artifact` or multi-band `path_count` signal
  over spec-producing steps (`**/templates/*prd*`, `.kiro/specs/**`, `openspec/**`,
  commands that emit `design.md`/`requirements.md`).
- Re-map `sd1` answers with a true zero: `{none: -1.0, encouraged: 0.0, required: +1.0}`,
  adjusting only with a written justification.

**Fresh vs mature** (AD-2, AD-7):
- The engine detects a shallow clone (`git rev-parse --is-shallow-repository`) and resolves
  git indicators to unresolved rather than the "fresh" floor.
- Drop `stars` from this axis; it measures popularity. Prefer reproducible git-history facts
  (`age_days`, `commit_count` from a full clone) with host-API `created_at`/`pushed_at` and
  release count as fallback.
- Re-profile the corpus with full clones.

**The other nine vocabulary indicators** (AD-2): convert to a structural signal where one
genuinely reflects the practice (for example test-first to test directories plus CI config),
otherwise move the judgment into a `classified` indicator the skill answers with a cited
quote. This continues the plan already sketched in `docs/axes.md`, corrected to prefer
multi-band `path_count` over binary `path_presence` (presence under-discriminates) and to
target produced-artifact structure rather than the framework's own files.

**Scale** (AD-3, AD-4): set bipolar indicator extremes to ±1.0; add the piecewise rescale in
`scoring.py` for one-directional axes; keep the clamp as a safety net.

**Schema** (AD-7): validate that bipolar indicator extremes are ±1.0 and that each axis offers
a near-zero answer. The "measured does not dominate" principle (AD-4) is a review-time check
rather than a schema rule, since it has no single defensible threshold.

## Calibration harness

`tests/test_calibration.py` runs the rubric over a frozen fixture (the committed corpus plus
the anchors above) and asserts, per indicator and per axis: no indicator is constant across
the corpus; multi-band measured indicators actually exercise their bands (at least three
distinct values *and* at least a fifth of the corpus off the single top band, so a 16/1/1
near-constant does not slip through); each axis's reachable range equals ±scale, checked by
running the real `score_axis` on pinned indicator results rather than a parallel formula; the
maturity axis is not a shallow-clone artifact; each axis offers a near-zero answer; and each
anchor lands on its expected pole (running today against the built fixtures).

The harness enforces AD-2, AD-3, and AD-6 mechanically and detects the AD-7 maturity
artifact; AD-1 (reproducibility), AD-4 (measured does not dominate), and AD-5 (no conflation)
are authoring constraints checked at review and, where possible, by schema, not by the corpus
harness. Spread is not validity, so the anchors are what keep the harness from rewarding
mere discrimination (see Risks). Today's known-broken cases ship as strict `xfail` entries
keyed to the solution that removes them, so the suite stays green while the live defect list
is explicit, and a fix flips the xfail to a failure that prompts removing the marker.

## Anchors

Deliberate calibration targets so a collapsed axis can be told apart from a homogeneous
corpus (AD-7), and the only check on *validity* rather than mere spread, so their design is
load-bearing, not an afterthought.

A real "no framework" project has almost no repository, so it would leave the measured
indicators unresolved and the classified questions with nothing to read (see Risks).
Anchors are therefore **purpose-built fixture repositories** under `tests/fixtures/anchors/`,
each a minimal but real tree crafted to sit at a known pole, committed with pinned classified
answers so the anchor is reproducible without a live agent. Planned anchors:

- **`spec-light-minimal/`**: a README plus one skill that jumps straight to implementation,
  no spec templates, no CI, one contributor. Expected negative on spec-driven, lightweight,
  test-optional, single-agent, composable.
- **`spec-heavy-maximal/`**: PRD, design, and requirements templates, a mandatory ordered
  pipeline, multi-agent roles, CI and coverage gates. Expected positive on the same axes.
- **`generalist/`**: a domain-agnostic assistant config with no software-only vocabulary.
  Expected negative on generalist-vs-specialist.

Two anchors per axis (one per pole) is the target where a pole is reachable at all. If an
axis cannot place its known-extreme anchor near the expected pole, the axis is broken, not
the corpus. These three anchors are built and their nine pole assertions pass against the
shipped rubric today, so the validity backstop is live, not implied. Redesigned axes gain
their pole-anchors as v2 progresses.

## Sequencing

1. Build the calibration harness and anchor fixture. It fails loudly on v1; that is the
   baseline.
2. Re-profile with full clones and add the engine shallow-clone guard (cheapest real win,
   and the fixture needs clean maturity data).
3. Redesign indicators (structural signals, true-zero scales, ±1.0 extremes), re-running the
   harness until variance, spread, and anchor checks pass.
4. Add the engine rescale last (for the one-directional axes only), once indicators are honest.

## Risks and how v2 answers them

An adversarial pass surfaced these. Each has a concrete resolution; the residual, where any
remains, is stated plainly rather than deferred.

- **Harness rewards spread, not validity (Goodhart).** *Resolution:* the anchor fixtures are
  built and the validity check runs today (`tests/fixtures/anchors/`, `test_anchor_placement`),
  profiling crafted spec-light, spec-heavy, and generalist targets and asserting each lands on
  the expected pole against the shipped rubric. Validity is checked directly, not inferred from
  spread. *Residual:* the anchors cover the axes they exercise; extend the set so every
  redesigned axis gains a pole-anchor.
- **`command_artifact` could reintroduce the disease.** *Resolution:* the detection contract is
  fixed in Seed, structural declarations only (an explicit output field or a defined written
  file), resolving unresolved when absent, never prose scanning. *Residual:* the parser's
  supported formats are a deferred question; until it exists, `sd3` uses multi-band
  `path_count` over produced-artifact paths, which shares the no-polarity property.
- **Rescale gives reachability, not evidence-strength comparability.** *Resolution:* AD-3 now
  prefers the ±1.0 convention (no rescale, bars directly comparable) and confines the rescale
  to genuinely one-directional axes with the reachable range documented. *Residual:* those few
  axes carry a "fraction of reachable range" reading; that is inherent to one-directional
  evidence and is labeled, not hidden.
- **Anchors hard to construct.** *Resolution:* done. Anchors are purpose-built fixture repos
  with pinned sibling answer files, working end to end today (all nine pole assertions pass).
  No residual for the built anchors.
- **Freezing corpus-fit bands overfits to these 18 tools.** *Resolution:* v2 abandons
  vocabulary for structural signals whose bands are construct-natural (0 / 1 / few / many of a
  countable behavior), so edges come from meaning, not corpus-fit, and there is nothing to
  overfit. Rule: a measured band edge must have a stated construct meaning; corpus calibration
  is allowed only for a signal with no natural threshold, and then frozen with a two-target
  holdout check. *Residual:* none for structural signals.
- **Re-classification cost.** *Resolution:* bounded and explicit. Most v2 changes are to
  measured indicators, which the engine recomputes with zero re-answering. Only changed
  classified indicators need new answers (roughly `sd1`'s reshape, a new `sd1b`, and `sd2`,
  about three questions times 18 targets). Carry-forward rule: an answer whose question text
  and answer set are unchanged between v1 and v2 carries over; a diff of the two rubrics'
  classified questions emits the exact re-answer worklist. *Residual:* that scoped
  re-classification, now visible rather than hidden in "re-run until green".
- **Consumer coexistence.** *Resolution:* the design and its single enforcement point are fixed
  here. Profiles already stamp `rubric_version`; the compare guard is "same rubric MAJOR only"
  (a mixed pair is refused with a reason); the site defaults to the latest MAJOR with a version
  switcher, and v1 profiles stay viewable, labeled by version. *Residual:* the implementation
  touches site and report code that the release line owns, so it is cross-session coordination,
  not a rubric change; this branch carries only the guard rule and the version stamp it needs.

## Deferred and open questions

- Exact construct-natural band edges for each new `path_count`/`command_artifact` signal (from
  the meaning of the counts, per the Risks resolution, not corpus-fit).
- Whether "work item before code" becomes its own axis or folds into
  prescriptive-vs-composable.
- The exact command and skill formats `command_artifact` parses.
- Whether any purely lexical signal is worth keeping as a low-weight corroborator, or whether
  the type is retired entirely.
