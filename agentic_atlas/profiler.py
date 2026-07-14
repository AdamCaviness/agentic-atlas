"""Orchestrate a full profile: evidence, then judgment, then scoring.

This is the single code path. The /agentic-atlas skill and any curated public profile both
run through here, they differ only in whether they persist the result.
"""

from __future__ import annotations

from . import __version__
from .evidence import Target, resolve_measured
from .judge import Judge, NoneJudge
from .models import IndicatorKind, Profile, Rubric
from .scoring import score_axis, score_profile


def profile_target(rubric: Rubric, target: Target, judge: Judge | None = None) -> Profile:
    judge = judge or NoneJudge()
    axis_results = []
    for axis in rubric.axes:
        results = []
        for ind in axis.indicators:
            if ind.kind is IndicatorKind.MEASURED:
                results.append(resolve_measured(ind, target))
            else:
                results.append(judge.resolve(ind, target))
        axis_results.append(score_axis(axis, results))

    return score_profile(
        target=str(target.root),
        rubric_version=rubric.rubric_version,
        engine_version=__version__,
        target_sha=target.git_sha(),
        axis_results=axis_results,
    )
