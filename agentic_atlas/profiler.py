"""Orchestrate a full profile: evidence, then judged answers, then scoring.

This is the single code path. The /agentic-atlas skill and any curated public profile both
run through here, they differ only in whether they persist the result.

The two indicator forms are resolved by two symmetric functions: detected indicators by
``evidence.resolve_detected`` (computed from the repository), judged indicators by
``judged.resolve_judged`` (validated from answers the caller supplies). With no
answers, judged indicators stay unresolved and the profile is detected-only.
"""

from __future__ import annotations

from . import __version__
from .evidence import Target, resolve_detected
from .judged import check_answer_ids, resolve_judged
from .models import IndicatorKind, Profile, Rubric
from .scoring import score_axis, score_profile


def profile_target(
    rubric: Rubric,
    target: Target,
    answers: dict[str, dict] | None = None,
    answers_source: str = "supplied",
) -> Profile:
    check_answer_ids(rubric, answers)
    axis_results = []
    for axis in rubric.axes:
        results = []
        for ind in axis.indicators:
            if ind.kind is IndicatorKind.DETECTED:
                results.append(resolve_detected(ind, target))
            else:
                results.append(resolve_judged(ind, target, answers, answers_source))
        axis_results.append(score_axis(axis, results))

    return score_profile(
        target=str(target.root),
        rubric_version=rubric.rubric_version,
        engine_version=__version__,
        target_sha=target.git_sha(),
        target_url=target.git_origin(),
        target_version=target.git_version(),
        axis_results=axis_results,
    )
