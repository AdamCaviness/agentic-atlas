# Versioning

Two independent version lines. Do not conflate them.

## Rubric version

Declared as `rubric_version` inside the manifest (`rubric/v1/rubric.yaml`), which is the authoritative version of the measurement standard; the rubric source lives under `rubric/v1/`. The guiding question for a bump is: **would this change move the score for identical evidence?**

- **MAJOR** (`x.0.0`): any change that can move an existing axis score given the same evidence. This includes adding or removing an indicator, changing a weight, changing the scoring formula, changing an answer-to-value mapping, redefining a pole, or changing which files are admissible as judged evidence (`evidence_exclude`). After a MAJOR bump, profiles from earlier MAJOR versions are no longer comparable.
- **MINOR** (`1.x.0`): add a whole new axis, or add optional metadata, such that every existing axis produces an identical score for identical evidence.
- **PATCH** (`1.0.x`): wording changes that cannot change any indicator value. Typos, clearer examples, expanded rationale.

Renaming an indicator id, an answer key, or an indicator kind moves no score but breaks every answers file and saved profile written against the old names, so a rename ships only inside a MAJOR bump, never on its own as a PATCH.

Calibration changes are honestly breaking, so expect MAJOR bumps to be common. That is correct for a measurement standard. A profile is only ever compared to another profile computed under the same rubric MAJOR version.

Every rubric change records an entry in `rubric/v1/CHANGELOG.md` and a rationale in the pull request.

## Engine version

Standard software semver on the `agentic_atlas` Python package, declared in `pyproject.toml`. MAJOR for breaking CLI or API changes, MINOR for features, PATCH for fixes. An engine change that alters how an existing signal is computed (for example which commit authors count as people) can move scores under an unchanged rubric, so it ships together with a rubric MAJOR bump and is recorded in the rubric changelog. The engine version is independent of the rubric version, a new engine must still correctly interpret older rubric files within the schema's supported range.

## What a profile stamps

Every emitted profile records both versions plus the target commit SHA and, for judged indicators, the model id. Two profiles are directly comparable only when their rubric MAJOR versions match.
