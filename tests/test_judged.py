"""Tests for judged-indicator resolution.

The engine never calls a model, so these are pure and need no network or fake client.
They exercise the deterministic validation that makes a supplied judged answer
trustworthy: the answer must be a declared value, the cited path must be an admissible corpus
file, and the quote must appear verbatim in that file, or the indicator is left unresolved.
"""

import pytest

from agentic_atlas.evidence import Target
from agentic_atlas.judged import check_answer_ids, judged_questions, resolve_judged
from agentic_atlas.models import Axis, Indicator, IndicatorKind, Poles, Rubric


def _judged_indicator() -> Indicator:
    return Indicator(
        id="c1",
        question="Does the approach document a review step?",
        kind=IndicatorKind.JUDGED,
        weight=1.0,
        answers={"yes": 1.0, "no": -1.0},
    )


def _target(tmp_path, text: str) -> Target:
    (tmp_path / "readme.md").write_text(text)
    return Target.from_path(tmp_path)


def _answer(answer, evidence, path="readme.md"):
    return {"c1": {"answer": answer, "evidence": evidence, "path": path}}


# Stand-ins for a rubric's evidence_exclude list: the engine embeds no patterns of its own.
_EXCLUDE = ("**/CHANGELOG*", "examples/**")


def test_no_answer_leaves_judged_unresolved(tmp_path):
    result = resolve_judged(_judged_indicator(), Target.from_path(tmp_path), None)
    assert result.resolved is False
    assert result.value is None


def test_resolves_with_verbatim_quote(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(),
        target,
        _answer("yes", "run a review step before every merge"),
        source="agentic-toolkit:test",
    )
    assert result.resolved is True
    assert result.value == 1.0
    assert result.answer == "yes"
    assert result.evidence == "run a review step before every merge"
    assert result.source == "agentic-toolkit:test"
    assert result.path == "readme.md"


def test_verbatim_check_tolerates_whitespace_reflow(tmp_path):
    target = _target(tmp_path, "We always run\na review step before every merge.")
    result = resolve_judged(_judged_indicator(), target, _answer("yes", "run a review step"))
    assert result.resolved is True


def test_fabricated_quote_is_rejected(tmp_path):
    target = _target(tmp_path, "This project has some text but says nothing about reviews.")
    result = resolve_judged(
        _judged_indicator(), target, _answer("yes", "enforces a mandatory review gate")
    )
    assert result.resolved is False
    assert result.value is None
    assert result.source is None


def test_out_of_enum_answer_is_rejected(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(), target, _answer("maybe", "run a review step before every merge")
    )
    assert result.resolved is False
    assert result.value is None


def test_trivially_short_quote_is_rejected(tmp_path):
    target = _target(tmp_path, "We run a review step before every merge.")
    result = resolve_judged(_judged_indicator(), target, _answer("yes", "review"))
    assert result.resolved is False


def test_missing_path_is_rejected(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    entry = {"c1": {"answer": "yes", "evidence": "run a review step before every merge"}}
    result = resolve_judged(_judged_indicator(), target, entry)
    assert result.resolved is False
    assert result.evidence == "no evidence path supplied"
    assert result.path is None


def test_quote_must_be_in_the_cited_file(tmp_path):
    # The quote exists in the target, but not in the file the answer names. The reason names
    # the cited file and points at the admissible file that holds the quote, for a retry.
    target = _target(tmp_path, "An unrelated overview of the project.")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "flow.md").write_text("We always run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(), target, _answer("yes", "run a review step before every merge")
    )
    assert result.resolved is False
    assert result.value is None
    assert result.evidence == (
        "evidence quote was not found verbatim in 'readme.md'; the quote appears in 'docs/flow.md'"
    )


def test_quote_from_an_excluded_path_is_rejected(tmp_path):
    target = _target(tmp_path, "An unrelated overview of the project.")
    (tmp_path / "CHANGELOG.md").write_text("1.2.0: we now run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(),
        target,
        _answer("yes", "run a review step before every merge", path="CHANGELOG.md"),
        exclude=_EXCLUDE,
    )
    assert result.resolved is False
    assert result.value is None
    assert (
        result.evidence
        == "evidence path 'CHANGELOG.md' is excluded as evidence (matches '**/CHANGELOG*')"
    )


def test_excluded_path_rejection_points_to_an_admissible_copy(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    (tmp_path / "CHANGELOG.md").write_text("1.2.0: we now run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(),
        target,
        _answer("yes", "run a review step before every merge", path="CHANGELOG.md"),
        exclude=_EXCLUDE,
    )
    assert result.resolved is False
    assert result.evidence.endswith("; the quote appears in 'readme.md'")


def test_mismatch_names_excluded_files_when_they_are_the_only_source(tmp_path):
    target = _target(tmp_path, "An unrelated overview of the project.")
    (tmp_path / "examples" / "demo").mkdir(parents=True)
    (tmp_path / "examples" / "demo" / "notes.md").write_text("run a review step before merge")
    result = resolve_judged(
        _judged_indicator(),
        target,
        _answer("yes", "run a review step before merge"),
        exclude=_EXCLUDE,
    )
    assert result.resolved is False
    assert result.evidence.endswith(
        "; the quote appears only in excluded files: 'examples/demo/notes.md'"
    )


def test_exclusions_come_only_from_the_caller(tmp_path):
    # With no exclusions supplied, a changelog is as admissible as any other corpus file:
    # which files count as evidence is rubric data, not engine code.
    (tmp_path / "CHANGELOG.md").write_text("1.2.0: we now run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(),
        Target.from_path(tmp_path),
        _answer("yes", "run a review step before every merge", path="CHANGELOG.md"),
    )
    assert result.resolved is True
    assert result.path == "CHANGELOG.md"


def test_admissible_path_is_normalized_and_recorded(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "flow.md").write_text("We always run a review step before every merge.")
    result = resolve_judged(
        _judged_indicator(),
        Target.from_path(tmp_path),
        _answer("yes", "run a review step before every merge", path="./docs/flow.md"),
        exclude=_EXCLUDE,
    )
    assert result.resolved is True
    assert result.value == 1.0
    assert result.path == "docs/flow.md"


@pytest.mark.parametrize(
    "path,reason",
    [
        ("missing.md", "evidence path 'missing.md' does not exist in the target"),
        ("../readme.md", "evidence path '../readme.md' is outside the target"),
        ("/etc/hosts", "evidence path '/etc/hosts' is outside the target"),
        (
            "tool.py",
            (
                "evidence path 'tool.py' is not in the text corpus "
                "(wrong extension, ignored directory, or too large)"
            ),
        ),
    ],
)
def test_path_that_is_not_a_corpus_file_is_rejected(tmp_path, path, reason):
    target = _target(tmp_path, "An unrelated overview of the project.")
    (tmp_path / "tool.py").write_text("# run a review step before every merge")
    result = resolve_judged(
        _judged_indicator(), target, _answer("yes", "run a review step before every merge", path)
    )
    assert result.resolved is False
    assert result.evidence == reason


def test_missing_indicator_answer_is_unresolved(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    # answers dict present but without an entry for this indicator
    result = resolve_judged(_judged_indicator(), target, {"other": {}})
    assert result.resolved is False
    assert result.value is None


def test_judged_questions_lists_only_judged_indicators():
    rubric = Rubric(
        rubric_version="0.0.0",
        title="t",
        axes=(
            Axis(
                id="ax",
                title="Ax",
                poles=Poles(negative="a", positive="b"),
                indicators=(
                    _judged_indicator(),
                    Indicator(
                        id="m1",
                        question="detected",
                        kind=IndicatorKind.DETECTED,
                        weight=1.0,
                        signal={"type": "vocabulary", "terms": ["x"], "bands": []},
                    ),
                ),
            ),
        ),
    )
    qs = judged_questions(rubric)
    assert [q["id"] for q in qs] == ["c1"]
    assert qs[0]["axis"] == "ax"
    assert qs[0]["answers"] == ["no", "yes"]


def _one_axis_rubric() -> Rubric:
    return Rubric(
        rubric_version="9.9.9",
        title="t",
        axes=(
            Axis(
                id="ax",
                title="Ax",
                poles=Poles(negative="a", positive="b"),
                indicators=(_judged_indicator(),),
            ),
        ),
    )


def test_unknown_answer_id_is_rejected():
    # A typo or an answers file written for another rubric version must fail loudly, not
    # silently leave the intended indicator unresolved and lower coverage.
    with pytest.raises(ValueError, match="9.9.9: c2"):
        check_answer_ids(_one_axis_rubric(), {"c1": {}, "c2": {}})


def test_known_answer_ids_pass():
    check_answer_ids(_one_axis_rubric(), {"c1": {}})
    check_answer_ids(_one_axis_rubric(), None)
