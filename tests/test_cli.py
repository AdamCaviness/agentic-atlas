"""Tests for the CLI surface that is not already covered through the engine tests, chiefly
the `render` command: re-emitting a saved profile JSON without re-running the engine."""

import json

from agentic_atlas.cli import main
from agentic_atlas.models import (
    AxisResult,
    Explain,
    IndicatorKind,
    IndicatorResult,
    Poles,
    Profile,
)
from agentic_atlas.report import render_html


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
                kind=IndicatorKind.MEASURED,
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


def test_render_bad_path_exits_nonzero(capsys):
    try:
        main(["render", "/no/such/profile.json"])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover - the command must not succeed on a missing file
        raise AssertionError("render should fail on a missing profile file")
