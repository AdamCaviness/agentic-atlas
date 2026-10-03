# ask-then-autopilot

A toolkit of independent skills that asks first and then runs unattended.

Before any code, it runs a brainstorming session that asks you questions about
the goal. When a design choice has several valid options, it lays out the
options and you choose. It ships no conventions of its own: each project
defines its own standards and layout. There is no required pipeline, only a
loose suggested order.

Each skill is a separate part you can use on its own, in any order, and you
compose only the parts you need.

Once you approve the goal, it runs end to end in autopilot mode. It never stops
for approval between phases. When a test or a build fails, it diagnoses the
failure and retries on its own until the check passes.
