# heavy-flow

A rigorous, staged methodology.

Before any code, you must write a specification: a full PRD capturing the
requirements and acceptance criteria, plus a design doc and an implementation
plan. All of these are saved to disk and reviewed. The specification is the
source of truth, so keep the spec, the plan, and the requirements updated as
the design doc evolves.

The process runs in ordered phases with gates between them. Each phase has a
defined role, a ceremony, and a template artifact that must be produced. The
phases are mandatory and strictly ordered, and you cannot skip or reorder them.
It prescribes one strong default path and drives it, rather than opening with a
round of questions. It pauses for explicit human approval at every phase gate
before continuing.

It spans the entire delivery lifecycle, from idea through release. Every change
ships production-hardened, with CI, security review, and observability. It is
built specifically for software delivery, not for any other domain. It assumes
an existing codebase, and ships steps to ingest and map that code before
changing it.

Testing is enforced test-first: write a failing test, then code to make it
pass, and track coverage. Red-green is mandatory and coverage gates the merge.

Work is split across many specialist subagents that orchestrate and delegate:
a planner persona, a reviewer persona, and an implementer persona. Work is
assigned and claimed across a team, with mandatory human review and handoffs
between contributors.
