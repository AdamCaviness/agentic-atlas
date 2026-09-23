"""Tests for the CLI surface that is not already covered through the engine tests, chiefly
the `render` command: re-emitting a saved profile JSON without re-running the engine."""

import json

from agentic_atlas.cli import _DEFAULT_RUBRIC, main
from agentic_atlas.evidence import TEXT_SUFFIXES
from agentic_atlas.judged import ANSWER_INSTRUCTIONS, MIN_QUOTE_CHARS
from agentic_atlas.models import (
    AxisResult,
    Explain,
    IndicatorKind,
    IndicatorResult,
    Poles,
    Profile,
)
from agentic_atlas.report import render_html
from agentic_atlas.spec import load_rubric


def _profile() -> Profile:
    ax = AxisResult(
        axis_id="a",
        title="A vs B",
        poles=Poles(negative="left", positive="right"),
        scale=10.0,
        score=-3.0,
        coverage=0.75,
        indicators=(
            IndicatorResult(
                indicator_id="x",
                kind=IndicatorKind.DETECTED,
                weight=1.0,
                value=1.0,
                resolved=True,
                answer="yes",
                source="engine",
            ),
        ),
        explain=Explain(negative="one", positive="two"),
    )
    return Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="abc123",
        axes=(ax,),
    )


def test_render_reemits_saved_profile_json_as_html(tmp_path, capsys):
    # `render <profile.json>` must reproduce render_html byte-for-byte, which is what lets the
    # committed corpus be checked for drift against its JSON.
    profile = _profile()
    path = tmp_path / "p.json"
    path.write_text(json.dumps(profile.to_dict()))

    assert main(["render", str(path), "--format", "html"]) == 0
    assert capsys.readouterr().out == render_html(profile) + "\n"


def test_answer_instructions_state_the_validation_contract():
    # Non-skill callers only see this string. It must name every corpus suffix and the
    # quote floor that validation enforces, and that a real-but-unrepresentative quote scores.
    for suffix in TEXT_SUFFIXES:
        assert suffix in ANSWER_INSTRUCTIONS
    assert f"{MIN_QUOTE_CHARS} characters" in ANSWER_INSTRUCTIONS
    assert "will still be accepted" in ANSWER_INSTRUCTIONS
    # Every answer names the file its quote is in, and that file must pass the exclusions.
    assert '"path"' in ANSWER_INSTRUCTIONS
    assert "evidence_exclude" in ANSWER_INSTRUCTIONS


def test_questions_emits_the_contract_instructions(tmp_path, capsys):
    (tmp_path / "README.md").write_text("a target with a text corpus")
    assert main(["questions", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["instructions"] == ANSWER_INSTRUCTIONS
    rubric = load_rubric(_DEFAULT_RUBRIC)
    assert payload["rubric_version"] == rubric.rubric_version
    # The answerer sees the rubric's exclusions up front, not only through rejections.
    assert payload["evidence_exclude"] == list(rubric.evidence_exclude)


def test_render_bad_path_exits_nonzero(capsys):
    try:
        main(["render", "/no/such/profile.json"])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover - the command must not succeed on a missing file
        raise AssertionError("render should fail on a missing profile file")


def test_render_old_rubric_profile_names_the_rubric_version(tmp_path):
    # A profile saved under rubric 3.x uses the retired kind "measured". It must fail with a
    # message naming its rubric version and how to regenerate it, not a traceback.
    data = _profile().to_dict()
    data["rubric_version"] = "3.0.0"
    data["axes"][0]["indicators"][0]["kind"] = "measured"
    path = tmp_path / "old.json"
    path.write_text(json.dumps(data))
    try:
        main(["render", str(path)])
    except SystemExit as exc:
        assert "rubric '3.0.0'" in str(exc.code)
        assert "Re-run `agentic-atlas profile`" in str(exc.code)
    else:  # pragma: no cover - the command must not succeed on an old profile
        raise AssertionError("render should fail on a pre-4.0 profile")
