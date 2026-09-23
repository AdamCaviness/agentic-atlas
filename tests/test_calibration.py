"""Corpus calibration harness: the acceptance instrument for the rubric.

This suite runs the shipped rubric over the frozen reference corpus (the committed
profiles under ``profiles/``) and asserts the health properties a well-calibrated rubric
must have: no indicator is constant across the corpus, multi-band detected indicators
actually use their bands, every axis can reach both poles, the maturity axis is not a
shallow-clone artifact, and every axis offers a near-zero answer. See
``docs/rubric-v2-plan.md`` for the invariant spine (AD-1..AD-7) these checks enforce.

Known defects ship as strict ``xfail`` entries in the registries below, so the CI gate stays
green while the live defect list stays explicit, and a fix flips the entry to an xpass
failure, which is the signal to delete it.

Coverage: this harness enforces AD-2 (no saturating detected indicator), AD-3 (both poles
reachable), and AD-6 (a near-zero answer exists) mechanically, and detects the AD-7 maturity
artifact. AD-1 (reproducibility), AD-4 (detected does not dominate), and AD-5 (no conflation)
are authoring constraints checked at review or by schema, not by a corpus statistic. Spread is
not validity: an indicator can discriminate the corpus and still measure the wrong thing,
so ``test_anchor_placement`` is the load-bearing validity check. It profiles crafted anchor
fixtures with known poles (tests/fixtures/anchors/) and asserts each lands on the expected
side, so an axis that cannot place a clear-cut target is caught even when the corpus happens
to spread.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import pytest

from agentic_atlas.models import (
    Axis,
    IndicatorKind,
    IndicatorResult,
    Profile,
)
from agentic_atlas.scoring import score_axis
from agentic_atlas.spec import load_rubric

_ROOT = Path(__file__).resolve().parent.parent
_RUBRIC_DIR = _ROOT / "rubric" / "v1"


# --- Calibration defect registries. -------------------------------------------------------
# Each registry lists known defects as strict xfails, keyed to the fix that removes them, so
# the CI gate stays green while the live defect list stays explicit. All are empty: every
# axis reaches +-scale, no detected indicator is constant or saturates, and every axis offers
# a near-zero answer. A regression re-adds an entry here, rather than silently flipping a
# shipped health property.

CONSTANT_INDICATORS: dict[str, str] = {}

# Detected indicators whose signal defines >= 3 bands but that collapse to < 3 distinct
# values across the corpus: the bands are never exercised (AD-2). git_stats indicators are
# exempt: their band edges are set from the construct (how old, how many people), and a
# young field legitimately leaves the top age band empty (see the maturity guard below).
# Detected signals must read structure a tool ships, not the tool's own engineering or a
# file count whose absence proves nothing, so the only detected indicators left are the
# git-history facts on fresh-vs-mature; everything else is judged with a cited quote.
COLLAPSED_BANDS: dict[str, str] = {}

# Calibration thresholds. Tunable knobs, deliberately named here rather than buried inline;
# v2 may promote them to versioned rubric data (docs/rubric-v2-plan.md, deferred question).
MIN_DISTINCT_BANDS = 3  # a >=3-band signal must exercise at least three of its bands
MIN_OFF_MODE_SHARE = 0.2  # at least a fifth of the corpus must sit off the single top band

# Axes with no judged answer that can land near zero, so the middle of the construct is
# forced off-center (AD-6).
AXES_WITHOUT_NEUTRAL: dict[str, str] = {}
# Empty: every axis has a judged answer that maps to 0.0.

# Every axis is converted to the +-1.0 value convention (AD-3): each bipolar indicator's
# extremes are +-1.0, so the weighted mean reaches +-scale with no engine rescale. That is
# all 13 axes. An axis absent from this set is treated as a known-unreachable
# defect (strict xfail), so adding an axis that has not been converted fails loudly here.
SCALE_REACHED_AXES = {
    "greenfield-vs-brownfield",
    "small-scope-vs-large-scope",
    "prototype-vs-production",
    "solo-vs-team",
    "generalist-vs-specialist",
    "fresh-vs-mature",
    "interrogative-vs-opinionated",
    "autonomous-vs-human-in-loop",
    "spec-light-vs-spec-driven",
    "test-optional-vs-test-first",
    "single-agent-vs-multi-agent",
    "prescriptive-vs-composable",
    "lightweight-vs-heavyweight",
}

UNREACHABLE_SCALE_REASON = (
    "AD-3: this axis is not in SCALE_REACHED_AXES, so it has not been converted to the +-1.0 "
    "value convention and cannot reach +-scale on both poles. Convert its indicator extremes "
    "to +-1.0 (redesigning any one-directional indicator to be genuinely bipolar)."
)

# --- Fixtures -------------------------------------------------------------------------------


def _load_corpus() -> list[Profile]:
    paths = sorted(glob.glob(str(_ROOT / "profiles" / "*.json")))
    profiles = [Profile.from_dict(json.loads(Path(p).read_text())) for p in paths]
    assert profiles, "no committed profiles found under profiles/*.json"
    return profiles


CORPUS = _load_corpus()
RUBRIC = load_rubric(_RUBRIC_DIR)


def _indicator_values(axis_id: str, indicator_id: str) -> list[float]:
    """Every resolved value for one indicator across the corpus."""
    out: list[float] = []
    for prof in CORPUS:
        ax = next(a for a in prof.axes if a.axis_id == axis_id)
        ir = next(r for r in ax.indicators if r.indicator_id == indicator_id)
        if ir.resolved and ir.value is not None:
            out.append(ir.value)
    return out


def _indicator_answers(axis_id: str, indicator_id: str) -> list[str]:
    out: list[str] = []
    for prof in CORPUS:
        ax = next(a for a in prof.axes if a.axis_id == axis_id)
        ir = next(r for r in ax.indicators if r.indicator_id == indicator_id)
        if ir.resolved and ir.answer is not None:
            out.append(ir.answer)
    return out


def _extreme_values(indicator) -> list[float]:
    if indicator.answers:
        return list(indicator.answers.values())
    return [b["value"] for b in (indicator.signal or {}).get("bands", [])] or [0.0]


def _reachable_range(axis: Axis) -> tuple[float, float]:
    """The axis score if every indicator is pinned to its most-negative / most-positive
    value. Runs the real ``score_axis`` on synthetic indicator results rather than
    reimplementing the arithmetic, so this instrument tracks the engine (including any
    future AD-3 rescale) instead of drifting from it."""

    def _pinned(pick) -> list[IndicatorResult]:
        return [
            IndicatorResult(
                indicator_id=i.id,
                kind=i.kind,
                weight=i.weight,
                value=pick(_extreme_values(i)),
                resolved=True,
            )
            for i in axis.indicators
        ]

    lo = score_axis(axis, _pinned(min)).score
    hi = score_axis(axis, _pinned(max)).score
    return (lo, hi)


def _distinct_ratio(values: list[float]) -> float:
    """Share of the corpus that does NOT sit on the single most common value. A 16/1/1 split
    scores 2/18, catching a near-constant indicator that a raw distinct-count would pass."""
    if not values:
        return 0.0
    top = max(values.count(v) for v in set(values))
    return (len(values) - top) / len(values)


def _all_indicators():
    return [(ax.id, ind) for ax in RUBRIC.axes for ind in ax.indicators]


def _multiband_detected():
    """Detected indicators with >= 3 bands, excluding git_stats (whose collapse is a data
    artifact tracked separately)."""
    out = []
    for ax in RUBRIC.axes:
        for ind in ax.indicators:
            if ind.kind is not IndicatorKind.DETECTED:
                continue
            sig = ind.signal or {}
            if sig.get("type") == "git_stats":
                continue
            if len(sig.get("bands", [])) >= 3:
                out.append((ax.id, ind.id))
    return out


# --- Constancy, split by kind because the two kinds mean different things ---------------------
# A constant *detected* indicator is a discrimination failure (the engine computes the same
# value everywhere). A constant *judged* indicator is a degenerate-question signal (every
# answerer picked the same option across varied targets). Same numeric check, different fault,
# so they are separate tests with separate messages rather than one bar over both kinds.

_DETECTED_IDS = [
    (aid, ind.id) for aid, ind in _all_indicators() if ind.kind is IndicatorKind.DETECTED
]
_JUDGED_IDS = [(aid, ind.id) for aid, ind in _all_indicators() if ind.kind is IndicatorKind.JUDGED]


def _maybe_xfail(aid: str, iid: str, registry: dict):
    if iid in registry:
        return pytest.param(aid, iid, marks=pytest.mark.xfail(reason=registry[iid], strict=True))
    return (aid, iid)


@pytest.mark.parametrize(
    "axis_id,indicator_id", [_maybe_xfail(a, i, CONSTANT_INDICATORS) for a, i in _DETECTED_IDS]
)
def test_detected_indicator_discriminates(axis_id, indicator_id):
    values = _indicator_values(axis_id, indicator_id)
    assert len(set(values)) >= 2, (
        f"{axis_id}/{indicator_id} is constant across the corpus "
        f"(value {values[0] if values else 'unresolved'}); it adds fixed bias, not signal."
    )


@pytest.mark.parametrize(
    "axis_id,indicator_id", [_maybe_xfail(a, i, CONSTANT_INDICATORS) for a, i in _JUDGED_IDS]
)
def test_judged_question_is_not_degenerate(axis_id, indicator_id):
    # Variance here is not proof the question is sound (answerers may just differ), but a
    # judged indicator constant across 18 varied targets signals a degenerate question or
    # answer set, e.g. spec-documents where every tool resolves to "yes".
    values = _indicator_values(axis_id, indicator_id)
    assert len(set(values)) >= 2, (
        f"{axis_id}/{indicator_id} drew the same answer for all {len(values)} targets; the "
        f"question or its answer set is likely degenerate."
    )


# --- AD-2: multi-band detected indicators actually use their bands --------------------------


@pytest.mark.parametrize(
    "axis_id,indicator_id",
    [
        pytest.param(
            aid,
            iid,
            marks=pytest.mark.xfail(reason=COLLAPSED_BANDS[iid], strict=True),
        )
        if iid in COLLAPSED_BANDS
        else (aid, iid)
        for aid, iid in _multiband_detected()
    ],
)
def test_multiband_indicator_uses_its_bands(axis_id, indicator_id):
    values = _indicator_values(axis_id, indicator_id)
    distinct = len(set(values))
    off_mode = _distinct_ratio(values)
    assert distinct >= MIN_DISTINCT_BANDS and off_mode >= MIN_OFF_MODE_SHARE, (
        f"{axis_id}/{indicator_id} saturates: {distinct} distinct value(s), "
        f"{off_mode:.0%} of the corpus off the top band "
        f"(need >= {MIN_DISTINCT_BANDS} distinct and >= {MIN_OFF_MODE_SHARE:.0%} off-mode)."
    )


# --- AD-3: every axis can reach both poles --------------------------------------------------


@pytest.mark.parametrize(
    "axis_id",
    [
        ax.id
        if ax.id in SCALE_REACHED_AXES
        else pytest.param(
            ax.id, marks=pytest.mark.xfail(reason=UNREACHABLE_SCALE_REASON, strict=True)
        )
        for ax in RUBRIC.axes
    ],
)
def test_axis_reaches_both_poles(axis_id):
    axis = RUBRIC.axis(axis_id)
    lo, hi = _reachable_range(axis)
    assert lo == pytest.approx(-axis.scale, abs=0.05) and hi == pytest.approx(
        axis.scale, abs=0.05
    ), (
        f"{axis_id} reachable range is [{lo:+.1f}, {hi:+.1f}], not the full [-{axis.scale}, +{axis.scale}]."
    )


# --- AD-6: every axis offers a near-zero answer ---------------------------------------------


@pytest.mark.parametrize(
    "axis_id",
    [
        pytest.param(
            ax.id, marks=pytest.mark.xfail(reason=AXES_WITHOUT_NEUTRAL[ax.id], strict=True)
        )
        if ax.id in AXES_WITHOUT_NEUTRAL
        else ax.id
        for ax in RUBRIC.axes
    ],
)
def test_axis_offers_a_neutral_answer(axis_id):
    axis = RUBRIC.axis(axis_id)
    values = [v for ind in axis.indicators for v in ind.answers.values()]
    assert any(abs(v) <= 0.1 for v in values), (
        f"{axis_id} has no judged answer within [-0.1, 0.1]: the construct has no way to "
        f"express a neutral or balanced position, so the middle is forced off-center."
    )


# --- AD-2/AD-7: the maturity axis is not a shallow-clone artifact ----------------------------
# Regression guard: the corpus is profiled from full clones, so fresh-vs-mature measures each
# project's real git history. A shallow clone would collapse every git indicator to the "fresh"
# floor (commit_count == 1, age_days == 0), which this asserts the corpus never does.


def test_maturity_is_not_a_shallow_clone_artifact():
    commits = [int(a) for a in _indicator_answers("fresh-vs-mature", "commit-count")]
    ages = [float(a) for a in _indicator_answers("fresh-vs-mature", "repo-age")]
    # Every target has git history in the corpus, so a shrunk denominator would itself be a
    # signal something is off; require the full corpus before judging the ratio.
    assert len(commits) == len(CORPUS) and len(ages) == len(CORPUS), (
        "repo-age/commit-count did not resolve for the whole corpus; cannot assess the shallow-clone artifact."
    )
    shallow = sum(1 for c, a in zip(commits, ages) if c <= 1 or a == 0.0)
    assert shallow <= len(CORPUS) // 2, (
        f"{shallow}/{len(CORPUS)} targets report commit_count <= 1 or age_days == 0: the "
        f"corpus was profiled from shallow clones, so fresh-vs-mature measures the fetch, not "
        f"the project."
    )


# --- Anchors: the validity backstop (AD-7) --------------------------------------------------
# Spread is not validity: an indicator can discriminate these 18 tools and still measure the
# wrong construct. Anchors are purpose-built fixture repos with known poles
# (docs/rubric-v2-plan.md#anchors), profiled here and asserted onto the expected pole. The
# three below run today; the skip guard only fires if a future anchor is listed without its
# fixture, so adding a row to ANCHORS never silently no-ops.

_ANCHOR_DIR = _ROOT / "tests" / "fixtures" / "anchors"

# fixture name -> {axis_id: expected pole sign (-1 negative, +1 positive)}. Each pairing is
# verified against the shipped rubric by the fixture's crafted content plus its pinned answers
# (tests/fixtures/anchors/<name>/ and the sibling <name>.answers.json).
# Every axis has at least one pole-anchor here except fresh-vs-mature, whose signal is the
# target's git history: an in-tree fixture would read the enclosing repo's history, not the
# fixture's, so it cannot be anchored this way. That axis is guarded instead by
# test_maturity_is_not_a_shallow_clone_artifact and its corpus git spread.
ANCHORS = {
    "spec-light-minimal": {
        "greenfield-vs-brownfield": -1,
        "small-scope-vs-large-scope": -1,
        "prototype-vs-production": -1,
        "solo-vs-team": -1,
        "spec-light-vs-spec-driven": -1,
        "lightweight-vs-heavyweight": -1,
        "test-optional-vs-test-first": -1,
        "single-agent-vs-multi-agent": -1,
    },
    "spec-heavy-maximal": {
        "greenfield-vs-brownfield": +1,
        "small-scope-vs-large-scope": +1,
        "prototype-vs-production": +1,
        "solo-vs-team": +1,
        "generalist-vs-specialist": +1,
        "interrogative-vs-opinionated": +1,
        "autonomous-vs-human-in-loop": -1,
        "spec-light-vs-spec-driven": +1,
        "test-optional-vs-test-first": +1,
        "single-agent-vs-multi-agent": +1,
        "prescriptive-vs-composable": -1,
        "lightweight-vs-heavyweight": +1,
    },
    "generalist": {"generalist-vs-specialist": -1},
}


@pytest.mark.parametrize(
    "anchor,axis_id,expected_sign",
    [(name, axis_id, sign) for name, axes in ANCHORS.items() for axis_id, sign in axes.items()],
)
def test_anchor_placement(anchor, axis_id, expected_sign):
    fixture = _ANCHOR_DIR / anchor
    if not fixture.is_dir():
        pytest.skip(
            f"anchor fixture {anchor!r} listed in ANCHORS but missing under "
            f"{_ANCHOR_DIR}; build it (docs/rubric-v2-plan.md#anchors)"
        )
    from agentic_atlas.evidence import Target
    from agentic_atlas.profiler import profile_target

    # Answers live in a sibling file, not inside the profiled tree, so they never leak into
    # the target's text corpus and skew the detected indicators or self-satisfy a quote check.
    answers_path = _ANCHOR_DIR / f"{anchor}.answers.json"
    answers = (
        json.loads(answers_path.read_text()).get("answers") if answers_path.is_file() else None
    )
    prof = profile_target(
        RUBRIC, Target.from_path(fixture), answers=answers, answers_source="anchor"
    )
    ax = next(a for a in prof.axes if a.axis_id == axis_id)
    assert ax.score is not None, f"{anchor}: {axis_id} did not resolve"
    assert (ax.score > 0) == (expected_sign > 0), (
        f"{anchor}: {axis_id} scored {ax.score:+.1f}, expected the "
        f"{'positive' if expected_sign > 0 else 'negative'} pole."
    )


# --- A guard on the harness itself: the registries must not drift from the rubric -----------


def test_defect_registries_reference_real_indicators():
    ids = {ind.id for _, ind in _all_indicators()}
    axis_ids = {ax.id for ax in RUBRIC.axes}
    unknown = (set(CONSTANT_INDICATORS) | set(COLLAPSED_BANDS)) - ids
    assert not unknown, f"defect registry names unknown indicators: {sorted(unknown)}"
    unknown_axes = set(AXES_WITHOUT_NEUTRAL) - axis_ids
    assert not unknown_axes, f"neutral-answer registry names unknown axes: {sorted(unknown_axes)}"
