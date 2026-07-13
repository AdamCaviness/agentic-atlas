# Agentic Workflow Atlas

An open, versioned rubric for profiling agentic development workflows, frameworks, methods, and skill systems for Claude Code and similar coding agents.

Profilable targets include [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD), [Superpowers](https://github.com/obra/superpowers), [GSD](https://github.com/jnuyens/gsd-plugin), [LFG](https://mcpmarket.com/tools/skills/lfg-autonomous-engineering-workflow), and any comparable workflow, framework, or skill collection.

## Purpose

**To let a person decide, as easily as possible, which workflow best suits their project and their way of working.**

There is no "best" agentic workflow, there is only a best fit. A method that is superb for greenfield product generation can be poor inside a large legacy codebase. A rigorous, ceremony-heavy pipeline that a team loves can be miserable for a solo developer shipping a prototype. Atlas exists so you can answer two questions and get a direct recommendation:

1. **What is my project like?** (greenfield or brownfield, small or large, prototype or production, solo or team)
2. **How do I like to work?** (interrogative or opinionated, autonomous or hands-on, lightweight or thorough)

Then you overlay two or three candidate workflows on the axes that matter to you and read the fit off the chart, instead of reading a dozen blog posts that each say "here is my take."

## Core thesis

Every comparison of these tools today is a subjective take. Atlas replaces the take with a **function**.

- It does **not** rank tools and produces **no aggregate score**. Collapsing independent axes into one number is meaningless, and a leaderboard invites exactly the fight ("who are you to grade me") that the project wants to avoid.
- Instead it **locates** each tool on signed, bipolar axes. `0.0` is neutral balance, the sign says which pole the tool leans toward, and the magnitude says how strongly. A tool at `-7.8` on Greenfield↔Brownfield is not "worse" than one at `+2.0`, it is positioned differently, and you choose by context.
- Each axis position is a **deterministic function of many small, named, evidence-backed indicators**. Every indicator is cited to the target repository. Disagreement therefore routes to a specific line of a specific YAML file and is settled by a pull request with a version bump, not by argument.
- The rubric is deliberately **opinionated**. That is the point. It is transparent, versioned under semver, and contestable in the open. It is not perfect, it is something concrete, inspectable, and improvable, which is strictly better than a vibe.

See `docs/design.md` for the architecture and `docs/axes.md` for the axis authoring method.

## How an axis is scored

Every axis is a signed spectrum between two named poles, with a symmetric scale (default `10`, so scores run `-10` to `+10`). Both poles are legitimate design choices, neither is framed as the failure mode.

An axis is never scored directly. It is decomposed into indicators, each a narrow question with a bounded answer that maps to a value in `[-1, 1]` signed toward one pole. Indicators come in two kinds:

- **`measured`**: computed deterministically by the engine from the repository (vocabulary density, file presence, command inventory, git statistics, host API facts like stars and release cadence). Same input, same output, no model.
- **`classified`**: requires reading and selecting from a small, defined answer set. A model or a human picks the answer and the engine records the answer **plus a cited quote**, so it stays auditable.

The axis score is then pure arithmetic:

```
axis_score = scale * sum(weight_i * value_i) / sum(weight_i)
```

computed over resolved indicators, clamped to `[-scale, +scale]`. Unresolved indicators are excluded and the profile reports coverage, so a partial profile is never mistaken for a complete one.

## The axis catalog

This is the working catalog of candidate axes, grouped by the decision each one helps a reader make. Sign conventions are shown as `negative ↔ positive`. Axes marked **[v1.0.0]** ship in the first rubric, the rest are the backlog. The final shipped set will be curated, not every axis below survives, because heavily correlated axes dilute a profile rather than sharpen it.

Every axis is a complex measurement built from several indicators. The example indicators listed are illustrative, the authoritative definitions live in `rubric/`.

### A. Interaction and control style (how you drive it)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Interrogative ↔ Opinionated** **[v1.0.0]** | Elicits and asks vs prescribes a strong default path | brainstorming phase present, directive vocabulary density, fixed pipeline enforced |
| **Human-in-loop ↔ Autonomous** **[v1.0.0]** | Frequent checkpoints vs unattended autopilot | approval-between-phases, autopilot mode advertised, checkpoint vocabulary density |
| **Conversational ↔ Command-driven** | Free chat vs slash commands and structured invocation | command/skill count, ratio of prose docs to command specs |
| **Permissive ↔ Guardrailed** | Runs freely vs guards destructive actions | confirmation gates on destructive ops, safety language, dry-run defaults |
| **Magic ↔ Mechanical** | Hides steps for low cognitive load vs exposes every step for control and auditability | visibility of intermediate artifacts, explicit phase logs, hidden automation |

### B. Project and context fit (what it is for)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Greenfield ↔ Brownfield** **[v1.0.0]** | Excels from an idea vs excels inside an existing codebase | spec-from-idea first step, codebase-ingestion steps, brownfield vocabulary, small-diff default |
| **Small-scope ↔ Large-scope** | One task vs the whole delivery lifecycle | phases covered (idea to release), single-command vs multi-stage, role coverage |
| **Prototype ↔ Production** | Fast throwaway output vs production hardening | testing and review emphasis, CI/deploy awareness, "vibe" vs "production" language |
| **Solo ↔ Team** | Single developer vs multi-contributor and team-safe | claim/assignment safety, shared state, review handoffs, role personas |
| **Generalist ↔ Specialist** | Any domain vs software delivery specifically | domain-agnostic framing vs code-specific tooling and vocabulary |
| **Fresh ↔ Mature** | New, fast-moving, cutting-edge vs established, stable, battle-tested | repository age, commit count, contributor count, release cadence, stars and forks, breaking-change frequency, test and docs completeness |

### C. Process and methodology (how it works)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Spec-light ↔ Spec-driven** | Jumps to code vs plans and specs first | mandatory PRD/plan step, spec artifacts, plan-before-code enforcement |
| **Test-optional ↔ Test-first** | Testing incidental vs TDD enforced | red-green-refactor language, test-first gates, coverage expectations |
| **Informal ↔ Ceremonial** | Minimal ritual vs roles, phases, and agile ceremony | named roles/personas, phase gates, ceremony vocabulary |
| **Single-pass ↔ Review-looped** | One shot vs built-in critique and iteration | self-review/critic steps, iteration loops, verification stages |
| **Implementation-first ↔ Planning-first** | Starts building vs invests up front in planning | ordering of first actions, depth of planning artifacts |

### D. Architecture and mechanics (how it is built)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Single-agent ↔ Multi-agent** | One conversation vs specialized subagents or personas | subagent usage, persona definitions, orchestration layer |
| **Prescriptive ↔ Composable** | Fixed pipeline vs pick-and-choose parts | modular skill count, optional vs required steps, dependency between steps |
| **Stateless ↔ Stateful** | No memory vs persistent project state and memory | memory files, cross-session state, project-state backing store |
| **Monolithic-context ↔ Context-partitioned** | One long session vs fresh-context phases | fresh-context spawning, per-phase context isolation, context-rot mitigation |
| **Bare ↔ Integration-heavy** | Few dependencies vs many MCP servers, hooks, and tools | MCP/hook/integration count, external tool requirements |

### E. Cost, footprint, and portability (what it takes to run)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Lightweight ↔ Heavyweight** | Small footprint and little ceremony vs large and elaborate | file count, install steps, config surface, concepts to learn |
| **Context-frugal ↔ Context-hungry** | Token disciplined vs consumes large context | fresh-context patterns, prompt sizes, token-saving mechanisms |
| **Model-agnostic ↔ Model-specific** | Portable across agents vs tied to one host | multi-host support, Claude-only features, portability claims |
| **Fast-start ↔ High-setup** | Useful immediately vs significant setup before value | steps to first useful run, prerequisites, configuration required |

### F. Audience and learnability (who it is for)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Beginner-friendly ↔ Expert-oriented** | Gentle on-ramp vs assumes expertise | onboarding quality, jargon density, worked examples |
| **Low-config ↔ Highly-configurable** | Works out of the box vs extensive knobs | default coverage, number of configuration options, extension points |

## Usage

```bash
# Validate a rubric file against the schema
atlas validate rubric/v1.0.0.yaml

# Profile a target using only measured indicators (fully deterministic, no model)
atlas profile /path/to/some-workflow --judge none

# Profile with classified indicators resolved from a prepared answers file
atlas profile /path/to/some-workflow --judge manual --answers answers.yaml --format md

# (planned) Overlay several tools on the same axes
atlas compare bmad-method superpowers gsd
```

The `/atlas` skill in [agentic-toolkit](https://github.com/adamavo/agentic-toolkit) wraps this engine, runs it locally on the user's machine, and prints a report without persisting anything.

## Spec plus interpreter

The repository holds two independently versioned things:

1. **The rubric** (`rubric/`) is versioned data: axis definitions, poles, indicators, and weights. It evolves under its own semver, independent of the engine. See `docs/versioning.md`.
2. **The engine** (`atlas/`) is the Python code that reads a rubric, gathers evidence, resolves indicators, scores axes with the fixed formula, and renders a profile.

Every emitted profile stamps the **rubric version**, **engine version**, **target commit SHA**, and, for classified indicators, the **model id**, so any profile is reproducible and arguable.

## Fairness and conflict of interest

The author also ships [agentic-toolkit](https://github.com/adamavo/agentic-toolkit), itself a profilable target. Credibility is defended structurally, not by promise: agentic-toolkit is profiled publicly with the same rubric and no special path, rubric changes are pull requests with written rationale and a version bump, any profiled project may contest a specific indicator via an issue, and there is no aggregate score to tilt. See `docs/conflict-of-interest.md`.

## Status

Early scaffold. The deterministic core (spec loading, validation, scoring), a working evidence collector (vocabulary and path-presence signals), manual and measured-only judging, and text/markdown/JSON reports are implemented and tested. In active development: the full curated axis set, git and host-API evidence collectors (for Fresh↔Mature and similar), the classification judge wired to a model, and the `compare` overlay. See `docs/` and the handoff notes.

## License

MIT. See `LICENSE`.
