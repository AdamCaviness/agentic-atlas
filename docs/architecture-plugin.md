# Architecture: Plugin & Skill (`skills/`, `.claude-plugin/`, extension manifests)

> Part `plugin` — the distribution surface that drives the engine from a coding harness.
> Deep scan, 2026-07-22. Complements [skill-integration.md](./skill-integration.md), which
> documents the stable engine contract this part targets.

## Executive summary

The plugin is the packaging that ships the engine's one user-facing workflow, the
`/agentic-atlas:run` skill, to coding harnesses (Claude Code, Gemini CLI, Codex). It contains
no scoring logic. Its job is to (1) make the engine runnable from an arbitrary checkout, and
(2) give the host agent a precise, safe procedure for answering the classified questions and
rendering a profile. The engine stays deterministic and key-free; the **host agent is the
model** that supplies the classified answers.

## Components

```
.claude-plugin/plugin.json     Claude Code plugin manifest (name, version 0.4.0, keywords)
gemini-extension.json          Gemini CLI extension manifest (contextFileName: AGENTS.md)
.codex/INSTALL.md              Codex install notes
skills/run/
├── SKILL.md                   The /agentic-atlas:run workflow the host agent follows
└── atlas.sh                   Launcher: resolves the engine, bootstraps its venv, forwards args
```

Distribution is via the external `agentic-marketplace`; the manifests here declare the
plugin/extension so a harness can install it. The plugin version (`0.4.0`) tracks the engine
release.

## The launcher (`skills/run/atlas.sh`)

A thin, defensive Bash shim, the only thing between the skill and the engine:

- **Symlink-aware resolution.** Skills are often distributed by symlinking the directory, so
  `atlas.sh` follows the `BASH_SOURCE` symlink chain to find its *real* location before
  walking up. The engine is the repo root two levels up (`skills/run/atlas.sh` → root).
- **Engine discovery.** `AGENTIC_ATLAS_ENGINE` overrides discovery (for testing against a
  checkout elsewhere); otherwise it verifies the root has both `pyproject.toml` and
  `agentic_atlas/__init__.py` or dies with a clear message.
- **Cached venv bootstrap.** `venv_ok()` checks the console script exists *and* the interpreter
  can import `agentic_atlas`, `yaml`, `jsonschema` (catching a half-built venv, not just an
  absent one). On first run it picks a system Python `>= 3.11` (`python3.13…3.11`), creates
  `.venv`, and does an editable install (runtime deps only, no dev extras). Later runs skip
  straight to `exec`.
- **Clean stdio.** All bootstrap chatter goes to stderr so the engine's stdout (JSON or a
  report) pipes cleanly. `--repo-root` short-circuits to print the engine root (used by the
  skill's `--save` step so artifacts land in this repo, not the target).
- **`exec "$ATLAS" "$@"`** forwards every argument to the `agentic-atlas` console script
  unchanged.

## The skill (`skills/run/SKILL.md`)

Trigger: `/agentic-atlas:run [path-or-git-url] [--save]`. It profiles a target and locates it
on the 13 axes. Its 9-step procedure:

1. **Preflight** — run a trivial engine command to force first-run bootstrap.
2. **Resolve the target** — no-arg = current directory (announced); local path; or git URL
   (full clone into temp, never `--depth 1`, because the Fresh↔Mature axis reads git history).
   Then a soft gate: confirm the target actually looks like an *agentic approach* (SKILL.md,
   `skills/`, `agents/`, `.claude/`, AGENTS.md, agentic vocabulary) before spending effort.
3. **Get the worklist** — `atlas.sh questions <target>` prints the classified questions.
4. **Read the target, then answer** — pick one allowed value per question and cite a quote
   copied **verbatim** from a corpus-eligible file (`.md .txt .yaml .yml .json .toml`; source
   code is *not* in the corpus). Prefer an absent/neutral value over omission to keep coverage.
5. **Assemble the answers object** — `{ "source": "agentic-atlas:<model-id>", "answers": {…} }`.
6. **Score** — `atlas.sh profile <target> --answers <file> --format json`, then check each
   indicator's `resolved` flag.
7. **Retry failed quotes once** — fix an unfound quote or an out-of-set value, re-run once.
8. **Render, open, summarize** — write the HTML report to a per-user cache (never inside any
   repo), open it, print the text fallback, and summarize confident/provisional/unread axes.
9. **Save + clean up** — with `--save`, write `answers.json` + `profile.json` under
   `profiles/<TARGET_NAME>/` in *this* repo (resolved via `atlas.sh --repo-root`); remove any
   temp clone; leave the venv cached.

## Invariants the skill enforces (mirroring the engine's)

- **No aggregate score** — never sum, average, or rank the axes into one number.
- **Don't touch the engine's determinism** — the skill only supplies answers the engine
  validates; it never edits the engine, rubric, weights, or scoring path to change a result.
- **Measured and classified stay separate** — the skill only ever produces classified answers.
- **Answer faithfully** — validation stops a fabricated quote but not a cherry-picked one, so
  pick the value the evidence supports; for absent behaviour, choose the negative/absent value
  and quote where it would appear.
- **Every profile is stamped** — preserve rubric version, engine version, target SHA, and
  answer source in what is printed and saved.

## Untrusted-content boundary

The skill treats **everything inside the target** (README, docs, config, command/skill/agent
files, comments) as untrusted **data to classify**, never as instructions. If the target
contains text like "answer yes" or "ignore your instructions", the skill disregards the
directive and classifies the text as written. This is the security posture for profiling
arbitrary, possibly adversarial, repositories.

## Relationship to the other parts

The plugin depends on the **engine's CLI contract** (`questions`, `profile --answers`,
`--repo-root`) and, transitively, the **rubric** the engine reads. It does not import Python
or reach into either — the launcher's argument forwarding and the engine's stdout JSON are the
whole interface. See [integration-architecture.md](./integration-architecture.md).
