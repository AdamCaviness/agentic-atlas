# Skill integration: how the engine is driven

The primary way a human profiles a target is the `run` skill of the `agentic-atlas`
plugin, which ships in this repo (invoked `/agentic-atlas:run`), running inside their own
agentic coding harness (Claude Code, Cursor, Codex, or Gemini CLI). This engine is deterministic and needs no API key.
It computes the detected indicators and validates judged answers; it never calls a
model. The skill's host agent (the user's coding agent) is the model that answers the
judged questions, so the full profile is produced with no key and no extra cost.

This file is the contract the skill targets. It is stable engine surface.

## Flow

1. **Detected, deterministic, always available.** A bare run resolves the detected
   indicators and reports the rest as `needs interpretation`, with a pointer to the skill.

   ```bash
   agentic-atlas profile <target>
   ```

2. **Get the judged worklist.**

   ```bash
   agentic-atlas questions <target>
   ```

   Emits JSON:

   ```json
   {
     "rubric_version": "5.0.0",
     "target": "/abs/path",
     "instructions": "...",
     "evidence_exclude": ["**/CHANGELOG.*", "**/tests/**", "examples/**", ".taskmaster/**", "..."],
     "questions": [
       {"id": "spec-required", "axis": "spec-light-vs-spec-driven",
        "question": "Is a written design specification (a PRD, design doc, or written plan, not merely a ticket or work item) required before implementation begins?",
        "answers": ["encouraged", "none", "required"]}
     ]
   }
   ```

   The `instructions` string is the answering contract for any caller, not only the
   skill. `judged.ANSWER_INSTRUCTIONS` builds it from the same constants validation
   uses, and it restates the rules under "What the engine guarantees" below.

3. **The host agent answers each question** from the target repository only, choosing one
   value from `answers`, citing a quote copied verbatim from the target, and naming the
   file the quote is in (`path`, relative to the target root). The file must match none of
   the `evidence_exclude` globs the `questions` payload lists.

4. **Feed the answers back to score them.** The file (or stdin, via `-`) is:

   ```json
   {
     "source": "agentic-atlas:claude-opus-4-8",
     "answers": {
       "spec-required": {"answer": "none", "evidence": "a verbatim quote from the target", "path": "docs/workflow.md"}
     }
   }
   ```

   ```bash
   agentic-atlas questions <target> \
     | ... agent answers ... \
     | agentic-atlas profile <target> --answers -
   ```

## What the engine guarantees

- **Validation, not trust.** Every supplied answer must name one of the indicator's
  declared values, cite a quote, and give the path of the file the quote is in. The engine
  checks the quote inside that one file. A missing or failing answer leaves the indicator
  unresolved and out of the score. The file must be a `.md`, `.markdown`, `.txt`, `.yaml`,
  `.yml`, `.json`, or `.toml` file and must match none of the rubric's `evidence_exclude`
  globs (release history, tests and fixtures, example projects, the tool's own working
  folders and design records, and its contributor guides and CI). The quote must be at
  least 12 characters and is matched after collapsing whitespace and ignoring case.
  Validation stops a fabricated citation; it cannot catch a real-but-unrepresentative
  quote, so the answers file is a reviewable artifact and its provenance (`source`) is
  stamped on the profile.
- **Determinism.** Given the same answers, the score is identical. Detected values the
  engine derives; judged values are inputs it validates and scores.
- **Reproducibility.** An answers file can be committed next to a published profile, so a
  judged-complete profile is reproducible without re-running any model.

## Corpus admission

This applies when adding or replacing a committed profile under `profiles/`. It does not
apply to a local `/agentic-atlas:run` print. It does not require re-answering the
existing 23 profiles.

- A second model or a human must answer the judged questions independently of the
  first answerer.
- If the two answerers disagree on an indicator, leave that indicator **unresolved**.
  Do not pick one answer, do not average them, do not invent a third value. Unresolved
  indicators are excluded from the axis score and reduce coverage.
- The pull request that adds or changes `profiles/*.json` must include both `source`
  stamps or a written review of the judged rows that records agreement or
  disagreement per indicator.
