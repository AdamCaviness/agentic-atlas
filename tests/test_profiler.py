"""End-to-end profiler tests: detected-only, deterministic, no model or network.

These exercise the whole pipeline (evidence -> judged answers -> scoring) against the shipped
v1 rubric on a synthetic target, with no answers supplied.
"""

from pathlib import Path

from agentic_atlas.evidence import Target
from agentic_atlas.models import IndicatorKind
from agentic_atlas.profiler import profile_target
from agentic_atlas.spec import load_rubric

_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


def _synthetic_target(tmp_path) -> Target:
    (tmp_path / "README.md").write_text(
        "This project enforces a mandatory review step and a spec-driven PRD before code. "
        "We always require approval and confirmation at each checkpoint."
    )
    return Target.from_path(tmp_path)


def test_profile_detected_only_is_well_formed(tmp_path):
    rubric = load_rubric(_RUBRIC)
    profile = profile_target(rubric, _synthetic_target(tmp_path))

    assert [a.axis_id for a in profile.axes] == [ax.id for ax in rubric.axes]
    assert profile.rubric_version == rubric.rubric_version
    assert profile.engine_version

    for ax in profile.axes:
        assert 0.0 <= ax.coverage <= 1.0
        # detected-only run: no judged indicator resolves
        judged = [i for i in ax.indicators if i.kind is IndicatorKind.JUDGED]
        assert all(not i.resolved for i in judged)
        # a resolved score stays within the axis scale; otherwise it is None
        if ax.score is not None:
            assert -ax.scale <= ax.score <= ax.scale


def test_profile_is_deterministic(tmp_path):
    rubric = load_rubric(_RUBRIC)
    target = _synthetic_target(tmp_path)
    first = profile_target(rubric, target).to_dict()
    second = profile_target(rubric, target).to_dict()
    # the synthetic target has no git, so target_sha is None; drop it defensively
    first.pop("target_sha")
    second.pop("target_sha")
    assert first == second


def test_profile_applies_the_rubric_evidence_exclusions(tmp_path):
    # End to end through the shipped rubric: a quote cited from an admissible file resolves
    # and records its path; the same quote cited from a changelog is rejected, because the
    # rubric's evidence_exclude reaches the judged resolver.
    rubric = load_rubric(_RUBRIC)
    quote = "Write the failing test first, then the code."
    (tmp_path / "README.md").write_text(quote)
    (tmp_path / "CHANGELOG.md").write_text(f"2.0.0: {quote}")
    target = Target.from_path(tmp_path)

    def tests_first(path: str):
        answers = {"tests-first": {"answer": "enforced", "evidence": quote, "path": path}}
        profile = profile_target(rubric, target, answers=answers)
        return next(
            ir for ax in profile.axes for ir in ax.indicators if ir.indicator_id == "tests-first"
        )

    admitted = tests_first("README.md")
    assert admitted.resolved and admitted.path == "README.md"
    rejected = tests_first("CHANGELOG.md")
    assert not rejected.resolved and rejected.path is None
    assert rejected.evidence.startswith("evidence path 'CHANGELOG.md' is excluded as evidence")
    assert rejected.evidence.endswith("; the quote appears in 'README.md'")


def test_to_dict_carries_pole_meanings(tmp_path):
    # The emitted artifact exposes each pole's plain-language meaning, so a consumer of the
    # JSON (not just the HTML) can render it.
    rubric = load_rubric(_RUBRIC)
    data = profile_target(rubric, _synthetic_target(tmp_path)).to_dict()
    for ax in data["axes"]:
        assert ax["explain"]["negative"]
        assert ax["explain"]["positive"]
