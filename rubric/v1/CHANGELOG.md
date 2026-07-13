# Rubric changelog (v1 major line)

All changes to the measurement standard are recorded here. Version bump rules are in `docs/versioning.md`. One directory per MAJOR version, minor and patch changes are git history within it.

## 1.0.0

Initial curated rubric of 12 axes, grouped for a readable radar:

- Context: greenfield-vs-brownfield, small-scope-vs-large-scope, prototype-vs-production, solo-vs-team, generalist-vs-specialist
- Style: interrogative-vs-opinionated, autonomous-vs-human-in-loop
- Process: spec-light-vs-spec-driven, test-optional-vs-test-first
- Architecture: single-agent-vs-multi-agent, prescriptive-vs-composable
- Footprint: lightweight-vs-heavyweight

Curation notes. Implementation-first-vs-planning-first was dropped as a near-duplicate of spec-light-vs-spec-driven. Fresh-vs-mature is deferred until git and host-API evidence collectors exist, because a classified-only maturity axis would be weak. Magic-vs-mechanical, informal-vs-ceremonial, fast-start-vs-high-setup, and the audience axes are deferred as too correlated with existing axes to add signal yet. Model-agnostic-vs-model-specific, permissive-vs-guardrailed, stateless-vs-stateful, conversational-vs-command-driven, single-pass-vs-review-looped, and bare-vs-integration-heavy are backlog candidates.

Sign conventions, weights, and answer-to-value mappings are a first proposal and are expected to change before this rubric is treated as stable. Any change that can move a score for identical evidence bumps the MAJOR version.
