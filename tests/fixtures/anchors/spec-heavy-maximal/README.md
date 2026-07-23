# heavy-flow

A rigorous, staged methodology.

Before any code, you must write a specification: a full PRD capturing the
requirements and acceptance criteria, plus a design doc and an implementation
plan. All of these are saved to disk and reviewed. The specification is the
source of truth, so keep the spec, the plan, and the requirements updated as
the design doc evolves.

The process runs in ordered phases with gates between them. Each phase has a
defined role, a ceremony, and a template artifact that must be produced.

Testing is enforced test-first: write a failing test, then code to make it
pass, and track coverage. Red-green is mandatory and coverage gates the merge.

Work is split across many specialist subagents that orchestrate and delegate:
a planner persona, a reviewer persona, and an implementer persona.
