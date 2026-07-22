# Architecture: Engine (`agentic_atlas/`)

> Part `engine` — the deterministic Python CLI and importable library. Deep scan,
> 2026-07-22. Complements [design.md](./design.md), which states the thesis; this file is
> the module-level map.

## Executive summary

The engine reads a rubric, gathers evidence from a target repository, resolves each indicator
to a value in `[-1, 1]`, computes a signed score per axis with a fixed formula, and renders a
profile. It is stdlib-first, needs no API key, and never calls a model. Roughly 1,970 LOC
across 9 modules plus `report.py` (824 lines, the largest, mostly the HTML renderer).

The design that everything serves: **a subjective axis produces a deterministic result**
because the axis is decomposed into small indicators and the scoring is pure arithmetic.

## Module map and data flow

```
              cli.py  (argparse; console script "agentic-atlas")
                │  validate | docs | questions | profile
                ▼
   spec.load_rubric ──▶ models.Rubric (Axis[] → Indicator[])
                │
                ▼
        profiler.profile_target                     ← the SINGLE code path
          for each axis, for each indicator:
            ├─ MEASURED  → evidence.resolve_measured(ind, target)
            └─ CLASSIFIED→ classify.resolve_classified(ind, target, answers)
                │  both return models.IndicatorResult
                ▼
        scoring.score_axis ──▶ models.AxisResult
        scoring.score_profile ─▶ models.Profile
                │
                ▼
        report.render_{text,markdown,html}   /   docs.sync (README blocks)
```

## Module responsibilities

### `models.py` — data holders (invariant: no score-moving behaviour)
Frozen dataclasses only. `IndicatorKind` (MEASURED / CLASSIFIED), `Poles`, `Explain`,
`Indicator` (id, question, kind, weight, `answers` map for classified, `signal` dict for
measured), `Axis`, `Rubric` (with an `axis(id)` lookup). On the result side: `IndicatorResult`
(value, resolved flag, answer, evidence, source; plus an `unresolved(...)` classmethod shared
by both resolvers), `AxisResult` (score `None` when nothing resolved, plus `coverage`), and
`Profile` with `to_dict()`. `Profile` deliberately has **no aggregate field** — it is a vector
of axis positions, never a single number.

### `spec.py` — load and validate a rubric
`load_rubric(path)` accepts a rubric directory or its `rubric.yaml`, validates the manifest
against `rubric.schema.json` and each axis against `axis.schema.json`, and returns a typed
`Rubric`. `jsonschema` is imported lazily inside `_validate` so `models`/`scoring` stay
dependency-light. Guards enforce integrity: the manifest's `scale` is applied to every axis
(never per-axis), an axis id must match its directory name, and a missing axis file is an
error. `_parse_answers` rejects boolean YAML keys (unquoted `yes`/`no`) with a clear message,
because YAML 1.1 would coerce them.

### `scoring.py` — the deterministic core (keep pure)
No I/O, no model, no rubric-specific logic. `score_axis` computes coverage as
`resolved_weight / total_weight`, and when any weight resolved:

```
axis_score = round(clamp(scale * sum(weight_i * value_i) / sum(weight_i), -scale, +scale), 1)
```

over resolved indicators only. `score_profile` assembles the `Profile`. This module is the
first one tested and must never drift.

### `evidence.py` — measured indicators (deterministic, from the repo)
Defines `Target` (a resolved directory; caches its text corpus once) and
`resolve_measured(indicator, target)`, which dispatches on `signal.type`:

| Signal type | Reads | Bands / mapping |
|---|---|---|
| `vocabulary` | term frequency across the text corpus | banded by count |
| `path_presence` | glob matches | present/absent value |
| `path_count` | number of matching files | banded by count |
| `git_stats` | commit_count, contributor_count, tag_count, age_days | banded by count |
| `github_api` | stars/forks/watchers/open_issues for the origin remote | banded by count |

Key correctness choices, all about **honest coverage**: an unreadable/empty target leaves
vocabulary and path signals *unresolved* rather than banding to a confident "absent" pole;
`git_stats`/`github_api` degrade to unresolved on missing history/network instead of raising;
`tag_count` requires a commit first so a history-less repo does not read as a real "0 tags".
The corpus is limited to text suffixes (`.md .markdown .txt .yaml .yml .json .toml`), skips
files > 512 KB, and ignores VCS/build/venv and vendored trees. A custom glob→regex compiler
(`_glob_regex`) gives real recursive `**` matching (fnmatch cannot), and `_term_pattern` matches
whole tokens so `ci`/`api` don't match inside `special`/`capital`. GitHub calls use
`GITHUB_TOKEN`/`GH_TOKEN` if present and record the fetched value verbatim as evidence (it is a
point-in-time host fact, not pinned by SHA).

### `classify.py` — classified indicators (validate, never generate)
`classified_questions(rubric)` emits the worklist (one entry per classified indicator: id,
axis, question, sorted allowed answers). `resolve_classified(indicator, target, answers,
source)` validates a supplied answer: it must be one of the indicator's declared values, and
the cited quote must appear **verbatim** in the target's text corpus. The verbatim check
(`_quote_found`) normalizes whitespace and casefolds so reflow/case don't matter, and requires
at least 12 characters so a trivial match cannot pass. Any missing/invalid/unfound answer
yields an unresolved result with the reason in `evidence`. This is symmetric with
`resolve_measured`: one computes, one validates, both return an `IndicatorResult`.

### `profiler.py` — the single orchestration path
`profile_target(rubric, target, answers, answers_source)` loops axes → indicators, routing
each to the measured or classified resolver, scores each axis, and stamps the profile with
the engine version (`__version__`), rubric version, and `target.git_sha()`. Both the `run`
skill and any curated public profile go through this exact function; they differ only in
whether they persist the output. There is no second code path.

### `report.py` — renderers (presentation only, no score logic)
`render_text` (optional ANSI color, opt-in via TTY + `NO_COLOR`), `render_markdown`, and
`render_html` (a self-contained interactive low-poly 3D "profile crystal", ~600 lines).
Presentation-only conventions live here: a `_COVERAGE_FLOOR` of 0.5 below which an axis reports
"needs interpretation" rather than plotting a clamped bar; a shared neutral-middle note; and
strictly non-judgmental pole colors (neither pole is "good"). Coverage is the one place a
green/yellow/red gradient is honest. There is deliberately no total row.

### `docs.py` — keep axis READMEs in sync with the rubric
`sync(path, check=False)` regenerates the scoring block of every axis `README.md` between the
`<!-- BEGIN GENERATED -->` / `<!-- END GENERATED -->` markers from the `axis.yaml`, so the
documented weights/formula can never drift from what the engine computes. `check=True` reports
drift and is wired into `make docs-check` (part of the CI gate). Preserves hand-written prose
outside the markers.

### `cli.py` — the entry point
`argparse` with four subcommands, each a thin wrapper: `validate <rubric>`,
`docs <rubric> [--check]`, `questions <target>`, and `profile <target> [--rubric]
[--answers FILE|-] [--format text|md|json|html]`. `--answers -` reads stdin so the skill can
pipe answers without a temp file. Default rubric is `rubric/v1` relative to the package.
`main()` is the `agentic-atlas` console script declared in `pyproject.toml`.

## Design invariants enforced here

1. **No aggregate score** — `Profile` has no total; renderers emit no total row.
2. **Rubric is data, engine is code** — no weights/indicators/formulas hardcoded; all read
   from `rubric/*.yaml`.
3. **Deterministic axis score** — `scoring.py` is pure arithmetic; same inputs → same output.
4. **Reproducible profiles** — rubric version, engine version, target SHA, and answer source
   stamped on every profile.
5. **`measured` vs `classified` stay separate** — two resolvers, never blurred; the engine
   validates classified answers, it never produces them.

## Testing strategy

`pytest` (`testpaths = ["tests"]`), 69 tests across 7 files, deterministic core first:
`test_scoring.py` and `test_spec.py` pin the arithmetic and loading; `test_evidence.py` (23)
and `test_classify.py` cover the two resolvers including the honest-coverage guards;
`test_profiler.py` covers the full path; `test_report.py` (23) covers the renderers;
`test_docs.py` covers README sync. Run `make test`, or the full gate with `make check`
(lint → docs-check → test). See [development-guide.md](./development-guide.md).
