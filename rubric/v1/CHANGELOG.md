# Rubric changelog

All changes to the measurement standard are recorded here, newest first. The authoritative version is `rubric_version` in `rubric/v1/rubric.yaml`; bump rules are in `docs/versioning.md`. A change that moves a score for identical evidence is a MAJOR bump, and profiles are comparable only within the same MAJOR.

## 2.0.0

Recalibrated **spec-light-vs-spec-driven** so that a ticket no longer counts as a specification. This is the first MAJOR bump: it moves scores for identical evidence, so profiles scored under 1.x are not comparable to 2.0.0.

Motivation: under 1.4.0 all 18 corpus targets landed spec-driven inside a band just 2.4 wide (every target at +5.6 or +8.0), and the ±10 scale was unreachable. Three defects on this one axis drove it:

- `sd1` asked whether "a written spec, PRD, or plan" was required, which a ticket satisfied, so agentic-toolkit, whose skills only file tickets ("The ticket body is your spec."), scored fully spec-driven.
- `sd2` ("are spec or plan artifacts produced and persisted") resolved "yes" for all 18, because persisting any file, including a ticket, counted. A constant indicator injects fixed bias, not signal (about +2.29 toward spec-driven).
- `sd3` counted specification *vocabulary* density, whose top band saturated for all 18 (counts 56 to 8628): talking about specs, not producing them.

Changes:

- **`sd1`** now asks whether a written *design specification* (a PRD, design doc, or written plan, not a ticket or work item) is required before implementation (AD-5, one construct per indicator). Its answers gain a true zero (AD-6): `{none: -1.0, encouraged: 0.0, required: +1.0}`, replacing `{none: -0.8, encouraged: +0.24, required: +0.8}`. "encouraged" is now a genuine neutral, so a balanced tool is expressible.
- **`sd2`** now requires the persisted artifact to be a *specification document* (a PRD, design, or requirements doc), so filing a ticket or writing a `tasks.json` is the negative pole. Answers `{no: -1.0, some: +0.3, yes: +1.0}` replace `{no: -0.8, some: +0.24, yes: +0.8}`; "some" is an argued lean, not a defaulted middle.
- **`sd3`** is now a structural `path_count` over the spec-producing machinery a tool ships (PRD/spec/requirements/design template documents and the Kiro `.kiro/specs`, OpenSpec `openspec/`, and PRP scaffold conventions), replacing the `vocabulary` signal (AD-2, measure structure not prose). Template globs require both a spec token and `template` (or a spec-token file under a `templates/` directory) and end in `.md`, so a command definition (`commands/design.md`), a test file (`spec-template-*.test.ts`), a consumed sample (`sample-prd.txt`), and a framework's own dated `*-design.md` dev docs are not counted. It is a heuristic weight-2 corroborator, not an exact inventory: `sd1` and `sd2` carry the construct, so a tool that produces specs at runtime without shipping templates still lands spec-driven on its classified answers. Bands are construct-natural (none, a few, many): `{0: -1.0, 1..2: +0.3, 3+: +1.0}`.
- Every bipolar indicator's extremes are now ±1.0 (AD-3, AD-4), so the axis reaches ±10 on both poles with no engine rescale, and the measured `sd3` (weight 2 of 7) corroborates rather than dominates.

Re-classification: `sd1` and `sd2` were re-answered from the target repositories under the sharpened definitions, each with a verbatim quote. Six targets moved: agentic-toolkit (ticket-only), plus agent-os, backlog-md, cursor-memory-bank, superclaude, and task-master on `sd1` or `sd2`. The other twelve carried their answers forward with no re-answer, since their design-spec answers were already correct.

Result: agentic-toolkit moves from +8.0 (fully spec-driven) to -10.0 (fully spec-light). The corpus now spans the full range from -10.0 to +10.0, with both poles populated: on the spec-light side agentic-toolkit (-10.0), backlog-md (-5.7), and cursor-memory-bank, superclaude, and task-master (-2.0); gstack near neutral (0.0); tools that require and produce specs but ship no committed templates around +4.3 (agent-os, ai-dev-tasks, ai-dlc, ccpm, superpowers); and the tools that ship spec templates or scaffolds at +10.0 (bmad-method, cc-sdd, context-engineering, gsd, openspec, prps-agentic-eng, spec-kit). In `tests/test_calibration.py` the strict xfails for `sd2`, `sd3`, this axis's neutral answer, and its pole reachability all flip to passing, and their registry entries are removed.

The other twelve axes still carry the v1 calibration defects (vocabulary saturation, no near-zero answer, unreachable scale) tracked as strict xfails in the calibration harness. They are the scope of the broader v2 pass, not this change.

## 1.4.0

Added a `path_count` measured signal and used it to fix two non-discriminating indicators found while profiling four frameworks under 1.3.0.

- **New `path_count` signal.** Bands the number of files matching a set of globs, so a large modular collection reads differently from a small one, the resolution binary `path_presence` lacks. Additive: `path_presence` stays for genuinely binary cases. It reuses the shared band shape and glob matcher and unresolves on an empty target, like the other measured signals.
- **prescriptive-vs-composable `pc3`** moved from binary `path_presence` to `path_count` over the same globs. Under 1.3.0, BMAD-METHOD and gsd-plugin tied at +1.7 because the binary signal was present for both; by module count they now separate (BMAD +0.9 from 11 matching files, gsd +2.3 from 106).
- **solo-vs-team** gained a measured `path_count` indicator (`st4`) for team and CI infrastructure (workflows, code owners, PR templates), breaking the exact four-way tie at +4.0. Its classified indicators still answer alike across the sampled tools, which are all individual skill libraries with light review workflow, so the axis stays clustered; a classified redesign and a strongly team-oriented sample tool are the next step.

Measured-only change, so committed answer sets re-score without re-answering. Saturation stays at 0%. Bumps rubric_version to 1.4.0.

## 1.3.0

Recalibrated indicator values across all 13 axes to stop pole saturation. A four-way profile (agentic-toolkit, superpowers, BMAD-METHOD, gsd-plugin) clamped 28% of axis positions to ±10; measured indicators resolved to exactly ±1.0 89% of the time, and axes carry only 2-3 indicators, so a single maxed measured signal plus one strong classified answer pinned an axis. This is a value-only recalibration: indicator ids, questions, kinds, weights, terms, globs, metrics, and band thresholds (`max_count`) are unchanged.

- Measured `vocabulary`, `git_stats`, and `github_api` band values scaled by 0.8, so a maxed measured proxy contributes at most ±0.8 and can no longer alone pin an axis.
- Measured `path_presence` softened to present +0.6 / absent -0.6: a single glob hit is suggestive, not a full pole vote.
- Classified answer values on the three chronic saturators (small-scope-vs-large-scope, generalist-vs-specialist, spec-light-vs-spec-driven) scaled by 0.8, so their strongest option stops being a guaranteed +1.

Result: saturation drops from 28% to 0% across the four profiled frameworks while axis direction and cross-tool spread are preserved. This moves scores for identical evidence.

Known non-discriminating indicators remain for a follow-up: `path_presence` globs that match the whole category (for example prescriptive-vs-composable `pc3`, present for every skills-based tool) act as a constant bias rather than a signal, and solo-vs-team's indicators do not separate the profiled tools. The fix is a count-based path signal and redesigned indicators, not a value change.

## 1.2.0

Two changes to how axes are scored and displayed.

- **Scale is now a rubric-wide constant.** Moved `scale` from a per-axis field to a single value in `rubric.yaml` (`scale: 10`), removed from `axis.schema.json`, added to `rubric.schema.json`. No score moves: scale is only a display multiplier on the normalized weighted mean and every axis already used `10`. A shared scale is what keeps positions comparable across axes, so a per-axis knob was an unused degree of freedom that could only break comparability. The engine still carries `scale` per axis internally, populated from the manifest at load time.
- **Vocabulary signals match whole tokens, not substrings.** A term like `spec` no longer matches inside `specification`, nor `ci` inside `decision`. This is a correctness fix, but it does move measured scores for identical evidence: counts drop for short or inflectable terms, so banded values and axis positions can shift.

## 1.1.0

Added the **fresh-vs-mature** axis (context group, after generalist-vs-specialist). MINOR because it introduces a whole new axis and leaves every existing axis score untouched for identical evidence.

Its indicators lean on two new measured signal types, `git_stats` (repository age, commit count, contributor count, tag count) and `github_api` (stars), both banded to a value the same way `vocabulary` counts are. Five of its six indicators are measured, so the axis scores meaningfully with no model in the loop; this is what made it worth shipping now, since the reason it was deferred from 1.0.0 was that a classified-only maturity axis would be weak. The single classified indicator reads how the project describes its own stability. Host facts that vary over time (stars) record the fetched value verbatim as evidence and resolve to unresolved (counted against coverage) when there is no network or origin remote.

Bands are a first proposal calibrated to open-source norms and, like all weights, are expected to be contested and refined.

## 1.0.0

Initial curated rubric of 12 axes, grouped for a readable radar:

- Context: greenfield-vs-brownfield, small-scope-vs-large-scope, prototype-vs-production, solo-vs-team, generalist-vs-specialist
- Style: interrogative-vs-opinionated, autonomous-vs-human-in-loop
- Process: spec-light-vs-spec-driven, test-optional-vs-test-first
- Architecture: single-agent-vs-multi-agent, prescriptive-vs-composable
- Footprint: lightweight-vs-heavyweight

Curation notes. Implementation-first-vs-planning-first was dropped as a near-duplicate of spec-light-vs-spec-driven. Fresh-vs-mature is deferred until git and host-API evidence collectors exist, because a classified-only maturity axis would be weak. Magic-vs-mechanical, informal-vs-ceremonial, fast-start-vs-high-setup, and the audience axes are deferred as too correlated with existing axes to add signal yet. Model-agnostic-vs-model-specific, permissive-vs-guardrailed, stateless-vs-stateful, conversational-vs-command-driven, single-pass-vs-review-looped, and bare-vs-integration-heavy are backlog candidates.

Sign conventions, weights, and answer-to-value mappings are a first proposal and are expected to be contested and refined. Any change that can move a score for identical evidence bumps the MAJOR version.
