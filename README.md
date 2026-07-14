# Agentic Atlas

An open methodology with tools for finding the ideal agentic workflow for you and your projects.

An "agentic workflow" are the plugins or frameworks that you use your coding harness (Codex, Claude Code, etc). Popular examples include [Superpowers](https://github.com/obra/superpowers), [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD), [GSD](https://github.com/jnuyens/gsd-plugin), [LFG](https://mcpmarket.com/tools/skills/lfg-autonomous-engineering-workflow), but this approach can profile any framework, method, or skill collection.

There's no single best agentic workflow, only a best fit for your project and how you like to work. Agentic Atlas shows you where each tool sits so you can pick.

## What it does

It is not a leaderboard. There's no ranking and no aggregate score, because collapsing independent axes into one number tells you nothing. It locates each tool on signed, bipolar axes: `0.0` is neutral, the sign says which pole the tool leans toward, and the magnitude says how strongly. A tool at `-7.8` on Greenfield ↔ Brownfield isn't worse than one at `+2.0`, it's simple aimed Greenfield projects and you are shown this to make your own conclusions on fit.

Each position is a deterministic function of small, named, evidence-backed indicators, every one cited to the target repository. So when you disagree with where a tool landed, trace it to the exact indicators behind it and open a pull request against the versioned rubric. The goal is to this methodology to be a community-maintained, open, and auditable rubric for agentic workflows.

See [`docs/design.md`](docs/design.md) for the architecture and [`docs/axes.md`](docs/axes.md) for the axis authoring method and the full candidate catalog.

## How an axis is scored

An axis is a signed spectrum (negative/positive float) between two named poles, with a symmetric scale (default `10`, so scores run `-10` to `+10`). Neither pole is a failure mode.

You never score an axis directly. It decomposes into indicators, each a narrow question with a bounded answer mapping to a value in `[-1, 1]` signed toward one pole. Two kinds:

- **measured**: computed by the engine from the repository, no model (vocabulary density, file presence, git statistics, GitHub stars). Same input, same output.
- **classified**: a model or a human reads the repository and picks from a defined answer set. The engine records the answer plus a cited quote, so it stays auditable.

The score is then arithmetic, over resolved indicators, clamped to `[-scale, +scale]`:

```
axis_score = scale * sum(weight_i * value_i) / sum(weight_i)
```

Unresolved indicators are excluded and the profile reports coverage, so you never mistake a partial profile for a complete one.

## Axes in v1

Thirteen axes ship today. The full candidate catalog is much larger, see [`docs/axes.md`](docs/axes.md); heavily correlated axes dilute a profile rather than sharpen it, so the rest are backlog.

| Axis (negative ↔ positive) | Meaning |
|---|---|
| **Interrogative ↔ Opinionated** | Elicits and asks vs prescribes a strong default path |
| **Human-in-loop ↔ Autonomous** | Frequent checkpoints vs unattended autopilot |
| **Greenfield ↔ Brownfield** | Excels from an idea vs excels inside an existing codebase |
| **Small-scope ↔ Large-scope** | One task vs the whole delivery lifecycle |
| **Prototype ↔ Production** | Fast throwaway output vs production hardening |
| **Solo ↔ Team** | Single developer vs multi-contributor and team-safe |
| **Generalist ↔ Specialist** | Any domain vs software delivery specifically |
| **Fresh ↔ Mature** | New and fast-moving vs established and battle-tested |
| **Spec-light ↔ Spec-driven** | Jumps to code vs plans and specs first |
| **Test-optional ↔ Test-first** | Testing incidental vs TDD enforced |
| **Single-agent ↔ Multi-agent** | One conversation vs specialized subagents or personas |
| **Prescriptive ↔ Composable** | Fixed pipeline vs pick-and-choose parts |
| **Lightweight ↔ Heavyweight** | Small footprint and little ceremony vs large and elaborate |

Authoritative definitions live in `rubric/v1/`.

## Usage

Everything runs through the Makefile. Run `make` to list targets.

```bash
make setup                 # create the venv and install with dev deps
make check                 # lint then test (the CI gate)
make validate              # validate the rubric against the schema
make profile TARGET=/path/to/approach JUDGE=manual ANSWERS=answers.yaml FORMAT=md
```

The `agentic-atlas` CLI is available inside the venv:

```bash
agentic-atlas validate rubric/v1                                    # check against the schema
agentic-atlas docs rubric/v1                                        # regenerate axis README scoring blocks
agentic-atlas profile /path/to/approach --judge none                # measured indicators only, no model
agentic-atlas profile /path/to/approach --judge manual --answers answers.yaml --format md
agentic-atlas compare bmad-method superpowers gsd                   # (planned) overlay tools on the same axes
```

`--judge` takes `none`, `manual`, or `anthropic`. The `/agentic-atlas` skill in [agentic-toolkit](https://github.com/adamcaviness/agentic-toolkit) wraps the engine, runs it locally on your machine, and prints a report without persisting anything.

## Reproducibility and fairness

The rubric (`rubric/`) is versioned data (axes, poles, indicators, weights) and the engine (`agentic_atlas/`) is the code that reads it, each under its own semver. See [`docs/versioning.md`](docs/versioning.md). Every profile stamps the rubric version, engine version, target commit SHA, and, for classified indicators, the model id, so any profile is reproducible and arguable.

I also maintain [agentic-toolkit](https://github.com/adamcaviness/agentic-toolkit), which is itself a profilable target and gets profiled with the same rubric and engine as everything else, no special treatment.

## Status

Early scaffold, actively developed. Working today: the per-axis rubric with schema validation, the deterministic scoring core, evidence collectors (vocabulary, path presence, git stats, GitHub API), measured-only and manual judging, text/markdown/JSON reports, and the `agentic-atlas docs` generator kept in sync by `make docs-check`. Next: the model-backed classification judge, the `compare` overlay, and more public profiles. See `docs/` and `specs/handoff.md`.

## License

MIT. See `LICENSE`.
