# Rubric 3.0.0 validity verdict: profiling five off-distribution tools

Status: validation record. This documents an independent check of whether rubric 3.0.0 places
real, varied tools where a careful reader would. The 18-tool corpus is homogeneous (all
software-delivery frameworks), so several poles were validated at 3.0.0 only by synthetic anchors,
never by a profiled tool. Five new tools were profiled to test those poles. Every classified
answer is backed by a verbatim quote the engine verified against the target at the stamped SHA.

## What was profiled and why

Candidates were chosen to reach specific under-populated poles, each with a written hypothesis
that the profiling would test:

| tool | url | why chosen (hypothesis) |
|---|---|---|
| claude-git-pr-skill | github.com/aidankinzett/claude-git-pr-skill | a single-purpose PR-review skill: test the **small-scope** and **lightweight** poles |
| vibe-coding-prompt-template | github.com/KhazP/vibe-coding-prompt-template | a "vibe coding / ship MVPs" template: test the **prototype** pole |
| metaswarm | github.com/dsifry/metaswarm | 18-agent, 9-phase, mandatory-gate framework with external CLI deps: test the **heavyweight** and **opinionated** poles |
| autonomous-dev | github.com/akaszubski/autonomous-dev | a hard-gated deterministic harness: test the **opinionated** pole (saturation) |
| compound-engineering | github.com/EveryInc/compound-engineering-plugin | a mature 32-skill plugin shipping both brainstorm and an autonomous `lfg`: test **mature**, **composable**, and the io1/io2 conflation |

## Before/after per-pole population

n = 18 (3.0.0 corpus) -> n = 23 (with the five new tools).

| axis (neg pole) | before min..max (#neg/#0/#pos) | after min..max (#neg/#0/#pos) | change |
|---|---|---|---|
| greenfield-vs-brownfield | −5.0..10.0 (5/0/13) | −10.0..10.0 (6/0/17) | greenfield extreme now reached (vibe-coding −10) |
| small-scope-vs-large-scope | −2.4..10.0 (2/0/16) | −10.0..10.0 (3/0/20) | small-scope extreme now reached (claude-git-pr-skill −10) |
| prototype-vs-production | −2.0..10.0 (1/0/17) | −2.0..10.0 (1/0/22) | **unchanged** (see finding P) |
| solo-vs-team | −10.0..10.0 (2/1/14) | −10.0..10.0 (3/1/18) | solo extreme re-populated (vibe-coding −10) |
| generalist-vs-specialist | 3.0..10.0 (0/0/18) | 3.0..10.0 (0/0/23) | **unchanged** (see finding G) |
| fresh-vs-mature | −5.0..7.5 (5/1/12) | −6.2..7.5 (7/1/15) | freshest extended (claude-git-pr-skill −6.2) |
| interrogative-vs-opinionated | −5.0..5.0 (11/6/1) | −5.0..**10.0** (13/6/4) | **opinionated pole now reached** (autonomous-dev +10; metaswarm, claude-git-pr-skill, task-master +5) |
| autonomous-vs-human-in-loop | −10.0..5.0 (8/1/9) | −10.0..5.0 (10/1/12) | autonomous side populated (3 tools +5) |
| spec-light-vs-spec-driven | −10.0..10.0 (5/1/12) | −10.0..10.0 (7/1/15) | both poles stay spanned |
| test-optional-vs-test-first | −10.0..10.0 (9/0/9) | −10.0..10.0 (12/0/11) | both poles stay spanned |
| single-agent-vs-multi-agent | −10.0..10.0 (9/0/9) | −10.0..10.0 (12/0/11) | both poles stay spanned |
| prescriptive-vs-composable | −10.0..10.0 (5/10/3) | −10.0..10.0 (9/10/4) | both poles stay spanned |
| lightweight-vs-heavyweight | −10.0..**6.0** (10/6/2) | −10.0..**10.0** (12/7/4) | **heavyweight pole now reached** (metaswarm, autonomous-dev +10) |

Headline: two poles the entire 3.0.0 corpus could not reach, opinionated (was capped at +5.0) and
heavyweight (was capped at +6.0), are now reached at +10.0 by real, in-scope, whole-repo tools.
That is the strongest possible validity result: the scale is not just reachable by construction,
it is reachable by tools that exist.

## Per-tool verdict (position on every axis, with the deciding indicator)

Peers named for comparison are from the studied answer key (spec-kit, bmad-method, task-master,
ai-dev-tasks) and the wider corpus.

### claude-git-pr-skill — a single-purpose PR-review skill
- small-scope-vs-large-scope **−10.0** (sl1=one "Use when reviewing GitHub pull requests with gh CLI", sl2=single). Reaches the small-scope extreme; the prior most-small-scope real tool was agent-os at −2.4. A pure review-phase skill genuinely covers one phase.
- lightweight-vs-heavyweight **−10.0** (lw1=minimal, lw2=tiny "Copy the skill directly to your skills directory"). One SKILL.md, install by copy. Ties ai-dev-tasks (−10).
- interrogative-vs-opinionated **+5.0** (io1=partial "Always get explicit user approval before posting any review comments", io2=strict "The skill enforces this workflow"). Opinionated via a different route than task-master (+5, io1=no): a mandatory workflow with a light approval check-in.
- autonomous-vs-human-in-loop **−10.0**, spec-light **−10.0**, test-optional **−10.0**, single-agent **−10.0**, prescriptive **−10.0**: a narrow, mandatory, human-gated, spec-free, single-skill tool legitimately maxes negative on these.
- greenfield-vs-brownfield +2.5 (gb1=existing_codebase, reviews changes to existing code; gb2=no, reads the diff not the whole codebase). generalist +10.0. prototype +1.8, solo +1.2 (code review is mildly team, no work-claiming), fresh −6.2 (a one-day commit burst, Dec 2025).

### vibe-coding-prompt-template — a structured idea->MVP pipeline
- greenfield-vs-brownfield **−10.0** (gb1=blank_slate "Turn an idea into an MVP", gb2=no, gb4=whole_project). Reaches the greenfield extreme; the prior most-greenfield real tool was ai-dev-tasks/spec-kit at −5.0.
- solo-vs-team **−10.0** (st1=none, st2=none). A solo-developer MVP workflow.
- small-scope-vs-large-scope +7.0, spec-light-vs-spec-driven +4.3 (sd1=required, produces a PRD and tech-design before build), single-agent −10.0, interrogative −5.0, human-in-loop −5.0, lightweight −4.0.
- prototype-vs-production **+1.8** (pp1=some "Once the MVP works, do a final pass on secrets, auth, and basic abuse protections before you deploy", pp2=mixed "Prioritize MVP scope. Offer the simplest working implementation."). It does NOT reach the prototype pole (see finding P): despite "vibe coding / ship MVPs" framing, it ships a REVIEW-CHECKLIST and a security pass, so it lands mild-production, alongside spec-kit (+1.8).

### metaswarm — 18-agent, 9-phase, mandatory-gate orchestration
- lightweight-vs-heavyweight **+10.0** (lw1=heavy "Coordinate 18 specialized AI agents and 13 orchestration skills", lw2=large "Node.js 18+ (for automation scripts)", requiring external BEADS and gh CLIs). First tool to reach the heavyweight pole; bmad-method and superclaude were capped at +6.0 because their footprint is lw2=moderate.
- interrogative-vs-opinionated **+5.0** (io1=partial "ask the user to confirm your assessment", io2=strict "Gates are blocking state transitions, not advisory."). Strongly opinionated: it drives a provided spec ("Start with a working spec, not a vague idea.") through unskippable gates, but its default flow opens with a light complexity check-in, so io1=partial rather than no. That check-in is the honest, conservative call flagged by the adversarial review; the +10 opinionated pole is anchored by autonomous-dev, which has no such check-in.
- multi-agent **+10.0** (ma1=many "18 specialized agent personas"; measured ma3=+1 from 19 anchored agent files), test-first **+10.0**, large-scope **+10.0**, production **+10.0**, prescriptive **−10.0**.
- autonomous +5.0 (ah1=yes "coordinates a swarm of specialized AI agents to autonomously handle GitHub Issues from creation to merged PR", ah2=some_phases: planned human checkpoints). spec-driven +4.3, mature +1.2 (young repo, but "proven in the field"), brownfield +3.8, solo +1.2.

### autonomous-dev — a hard-gated deterministic harness
- interrogative-vs-opinionated **+10.0** (io1=no "Claude executes a full development pipeline", io2=strict "if the model tries to skip a step, it's physically blocked"). The anchor for the opinionated pole: `/implement "#72"` takes an issue and runs the whole pipeline on its own plan with no requirements-questioning phase (its plan-approval touchpoint is booked on the autonomous axis as ah2, not io1). The adversarial review called this a clean, bulletproof +10.
- lightweight-vs-heavyweight **+10.0** (lw1=heavy "autonomous-dev implements all 12 elements of this framework", lw2=large "26 hooks with JSON"). The lw2=large call is the most contestable of the five (a one-line installer that deploys a large harness); even downgraded to moderate (+6.0) it stays a strong heavyweight, and metaswarm independently establishes the pole.
- test-first +10.0, multi-agent +10.0 (16 anchored agent files), large-scope +10.0, production +10.0, prescriptive −10.0, autonomous +5.0 (ah1=yes "runs the same loop unattended", ah2=some_phases: plan approval gate), mature +5.0, brownfield +6.2, spec-driven +2.3.

### compound-engineering — a mature 32-skill composable plugin
- prescriptive-vs-composable **+10.0** (pc1=composable "AI skills that make each unit of engineering work easier than the last.", pc2=optional_reorderable). A pick-and-choose menu of 32 skills.
- fresh-vs-mature **+5.0** (1084 commits, 86 contributors, 194 tags; fm6=evolving). A genuinely mature project, near the top of the mature range.
- single-agent-vs-multi-agent **−2.5** (ma1=some "Specialist review, research, and workflow behavior lives inside the owning skills as skill-local prompt assets"; measured ma3=−1). This is a live validation of the 3.0.0 ma3 design: the plugin's own README says it "ships 32 skills and 0 standalone agents", so ma3's anchored globs correctly read 0 (personas embedded in skills) and ma1 carries the construct, exactly as intended.
- autonomous +5.0 (ships the hands-off `lfg`), interrogative −5.0 (io1=yes, ships ce-brainstorm), spec-light −2.0, test-optional −4.8, large-scope +6.0, production +5.8, generalist-side +3.0 (ce-plan handles "software and non-software tasks", the least-specialist of the new tools, still specialist).

## Findings and resolutions

**Finding O (io1/io2 conflation) — RESOLVED as a decision-ready proposal.** The pre-validation
worry was that the opinionated pole might be unreachable by design because io1 ("runs a questioning
phase") is near-universal. Profiling REFUTES the reachability worry: autonomous-dev reaches +10
opinionated (and metaswarm, claude-git-pr-skill, task-master reach +5). It CONFIRMS a narrower
construct nuance: a tool that elicits requirements (io1=yes) is capped at 0.0 no matter how strictly
it prescribes the path (superpowers and ccpm, both io2=strict, sit at exactly 0.0). Whether that is correct depends on what "opinionated" should
mean, a construct-definition judgment call, so it is written up as a decision-ready proposal with
the exact reword, the targets that move, and a recommendation (keep as-is; the pole is reachable
and the current construct is defensible) in `docs/rubric-io-conflation-proposal.md`. Not forced,
because nothing is broken.

**Finding P (prototype pole under-populated) — RESOLVED as thinly-reachable, with reason.** The
prototype pole (pp1=none + pp2=throwaway_ok) is reachable in principle (the spec-light-minimal
anchor sits at −10) but stays under-populated among whole-repo methodologies. vibe-coding, the
strongest whole-repo "vibe/MVP" candidate, lands +1.8 (mild production) because even it ships a
security/review pass before deploy. The genuine throwaway-spike tools that reach the pole
(mattpocock/skills' `prototype` skill: "throwaway code ... no tests ... Throwaway from day one";
LibreUIUX's rapid-prototyping: "Speed > Quality, Throwaway code, Fail cheap") ship as
sub-components of broad collections, not as clean standalone repos, so they are not honest
whole-repo corpus targets. Reason: production-hardening is near-universal in whole-repo
agentic-development methodologies, so they sit at pp >= 0; the prototype pole belongs to narrow
disposable-spike skills and is validated by the anchor. agent-os (−2.0) remains the most-prototype
real whole-repo tool. No rubric change needed.

**Finding G (generalist pole empty) — RESOLVED as unreachable by in-scope tools, with reason.**
Any tool in scope for this corpus is an agentic *development* tool, so it is software-focused and
answers gs1 at mostly_software (+0.5) or software_only (+1.0); it cannot reach any_domain (−1.0).
compound-engineering, the least-specialist new tool (ce-plan explicitly covers "software and
non-software tasks"), still lands +3.0 (specialist). The tools that would reach gs1=any_domain are
general knowledge-work collections (second-brain / PARA / cross-domain assistants), which fall
outside "agentic development approaches". The generalist pole is therefore legitimately
anchor-only for this corpus, validated by the `generalist` anchor fixture. No rubric change needed.

**Finding M (ma3 anchored-glob design) — VALIDATED, no change.** compound-engineering is a direct
confirmation: a plugin whose README states it "ships 32 skills and 0 standalone agents" reads
ma3=0 (the anchored globs `.claude/agents/*.md`, `agents/*.md`, `plugins/*/agents/*.md` skip the
42 persona files living under `skills/*/references/agents/`), so the measured count does not
miscount embedded personas, and the classified ma1 carries the construct. This is exactly the
3.0.0 lesson (structural counts must not be leaked by template/reference trees) working as
designed.

## Harness and gate status

Adding the five profiles kept everything green. The calibration harness perturbations the
objective warned about were checked directly:
- ma3 off-mode share rose from ~22% to **26.1%** (floor 20%), because the additions include both
  ma3=+1 (metaswarm, autonomous-dev) and ma3=−1 (compound-engineering) tools.
- the maturity shallow-clone guard: **1/23** targets look shallow (only claude-git-pr-skill, a
  genuine one-day commit burst, not a fetch artifact), well under the n/2 = 11 limit.
- `make check` passes end to end (ruff, format, docs-check, profiles-check over all 23,
  site-check builds the Explorer with 23 profiles, 170 tests).

No threshold, registry, or measured indicator was edited to force green; the corpus statistics
absorbed the five additions on their own.
