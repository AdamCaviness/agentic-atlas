"""Tests for the report renderer: the coverage floor, coverage-by-kind, and the
opinionated first-run pointer to the skill."""

from agentic_atlas.models import (
    AxisResult,
    Explain,
    IndicatorKind,
    IndicatorResult,
    Poles,
    Profile,
)
from agentic_atlas.report import _MODAL_JS, _display_name, render_html, render_text


def _ind(kind: IndicatorKind, resolved: bool, weight: float = 1.0) -> IndicatorResult:
    return IndicatorResult(
        indicator_id="x",
        kind=kind,
        weight=weight,
        value=1.0 if resolved else None,
        resolved=resolved,
        answer="yes" if resolved else None,
    )


def _axis(title, score, coverage, indicators, explain=Explain()) -> AxisResult:
    return AxisResult(
        axis_id=title.lower(),
        title=title,
        poles=Poles(negative="left", positive="right"),
        scale=10.0,
        score=score,
        coverage=coverage,
        indicators=tuple(indicators),
        explain=explain,
    )


def _profile(axes, target="/t") -> Profile:
    return Profile(
        target=target,
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="abc123",
        axes=tuple(axes),
    )


def test_below_floor_axis_shows_needs_interpretation_and_no_bar():
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_text(_profile([ax]))
    assert "needs interpretation" in out
    assert "+10.0" not in out  # a sliver of evidence is never dressed up as a verdict
    assert "#" not in out  # no bar drawn


def test_above_floor_axis_plots_a_position():
    ax = _axis(
        "Solid",
        score=-5.5,
        coverage=0.8,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.MEASURED, True)],
    )
    out = render_text(_profile([ax]))
    assert "-5.5" in out
    assert "#" in out  # a bar is drawn
    assert "needs interpretation" not in out


def test_coverage_reported_by_kind():
    ax = _axis(
        "Split",
        score=-5.5,
        coverage=0.8,
        indicators=[
            _ind(IndicatorKind.MEASURED, True),
            _ind(IndicatorKind.MEASURED, True),
            _ind(IndicatorKind.CLASSIFIED, False),
        ],
    )
    out = render_text(_profile([ax]))
    assert "measured 2/2 · classified 0/1" in out


def test_skill_hint_shows_when_classified_unanswered():
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_text(_profile([ax]))
    assert "/agentic-atlas skill" in out


def test_no_skill_hint_when_everything_resolved():
    ax = _axis(
        "Full",
        score=-5.5,
        coverage=1.0,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, True)],
    )
    out = render_text(_profile([ax]))
    assert "/agentic-atlas skill" not in out


# --- render_html --------------------------------------------------------------------------


def test_html_is_byte_identical_for_same_profile():
    # Determinism: a pure function of the Profile, no timestamps or random ids.
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    profile = _profile([ax])
    assert render_html(profile) == render_html(profile)


def test_html_draws_a_solid_bar_above_floor():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert 'class="fill neg"' in out  # a real bar, drawn solid
    assert 'class="fill neg prov"' not in out  # not faded
    assert "low evidence" not in out  # the provisional tag is absent
    assert "nothing could be read" not in out


def test_html_always_draws_a_faded_bar_below_floor():
    # Unlike the terminal renderer, HTML never hides a scored axis: below the floor it
    # fades and tags the bar rather than dropping it.
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_html(_profile([ax]))
    assert "fill pos prov" in out  # a bar is still drawn, faded
    assert "low evidence" in out
    assert "nothing could be read" not in out
    assert "+10.0" in out  # the number is shown, just marked provisional


def test_html_null_state_when_nothing_resolved():
    # score None (nothing resolved) is the only no-bar case, and it says so plainly.
    ax = _axis(
        "Empty",
        score=None,
        coverage=0.0,
        indicators=[_ind(IndicatorKind.MEASURED, False), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_html(_profile([ax]))
    assert "nothing could be read" in out
    assert 'class="fill' not in out  # no bar drawn at all


def test_html_uses_plain_labels_not_engine_jargon():
    ax = _axis(
        "Split",
        score=-5.5,
        coverage=0.8,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, True)],
    )
    out = render_html(_profile([ax]))
    assert ">detected</span>" in out  # measured, in plain words
    assert ">judged</span>" in out  # classified, in plain words
    assert "% evidence" in out  # coverage, in plain words
    # the engine's kind vocabulary never surfaces as a visible label
    assert ">measured<" not in out
    assert ">classified<" not in out


def test_html_escapes_untrusted_evidence():
    evil = IndicatorResult(
        indicator_id="x",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        value=1.0,
        resolved=True,
        answer="a",
        evidence="<script>alert('xss')</script>",
        source="engine",
    )
    ax = _axis("Esc", score=5.0, coverage=0.8, indicators=[evil])
    out = render_html(_profile([ax]))
    assert "<script>alert" not in out  # never emitted raw
    assert "&lt;script&gt;" in out  # escaped instead


def test_html_states_there_is_no_aggregate_score():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert (
        "not a grade, a rank, or a winner" in out
    )  # the no-aggregate invariant, stated to the reader


def test_html_neutral_score_reads_as_neutral_not_positive():
    ax = _axis("Mid", score=0.0, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert '<span class="score zero">0.0</span>' in out  # neutral, no forced sign


def test_html_shows_pole_meanings_in_a_modal_when_present():
    ax = _axis(
        "GB",
        score=-5.5,
        coverage=0.8,
        indicators=[_ind(IndicatorKind.MEASURED, True)],
        explain=Explain(negative="excels from an idea", positive="excels in existing code"),
    )
    out = render_html(_profile([ax]))
    assert 'class="info" data-dialog="poles-0"' in out  # the poles info-icon trigger
    assert '<dialog id="poles-0" class="modal">' in out  # opens a modal, not an inline expander
    assert "excels from an idea" in out
    assert "excels in existing code" in out
    # the shared neutral note is stated per axis, not authored per axis
    assert "serves both ends well, or neither" in out


def test_html_omits_pole_modal_when_no_meanings_authored():
    ax = _axis("Bare", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert 'data-dialog="poles-0"' not in out
    assert "<details>" not in out  # no inline expanders anywhere; details live in dialogs


def test_html_signals_open_in_a_modal_and_cards_stay_fixed_height():
    # The signals detail is a dialog (opened by a button), so opening it never reflows the
    # card. That fixed height is what lets the tower align with the cards.
    ax = _axis("A vs B", score=1.0, coverage=1.0, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert 'data-dialog="signals-0"' in out
    assert '<dialog id="signals-0" class="modal modal-wide">' in out
    assert "<details>" not in out and "<summary>" not in out
    assert _MODAL_JS in out  # the tiny open/close handler is shipped


def test_display_name_takes_last_segment_of_path_or_git_url():
    assert _display_name("/Users/adam/_opensource/superpowers") == "superpowers"
    assert _display_name("/Users/adam/_opensource/superpowers/") == "superpowers"
    assert _display_name("https://github.com/obra/superpowers.git") == "superpowers"
    assert _display_name("https://github.com/obra/superpowers") == "superpowers"
    assert _display_name("superpowers") == "superpowers"


def test_html_header_shows_name_not_full_path():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax], target="/Users/adam/_opensource/superpowers"))
    # with no upstream remote, the single project visual shows the short name, not the full path
    assert '<span class="pname">superpowers</span>' in out
    assert "/Users/adam/_opensource/superpowers" not in out
    assert '<div class="stamps">rubric' in out


def test_html_hero_tower_present_with_axis_data():
    ax = _axis(
        "Greenfield vs Brownfield",
        score=2.7,
        coverage=1.0,
        indicators=[_ind(IndicatorKind.MEASURED, True)],
    )
    out = render_html(_profile([ax]))
    assert 'id="atlas-hero"' in out  # the 3D tower container
    assert "<canvas>" in out
    assert "<script>" in out  # the only (inline) script on the page
    assert '"Greenfield vs Brownfield"' in out  # axis title embedded for the tower to read


def test_html_hero_absent_when_no_axes():
    out = render_html(_profile([]))
    assert "atlas-hero" not in out
    assert "<script>" not in out  # nothing to plot, so no tower and no script


def test_html_hero_data_cannot_break_out_of_script():
    # A title is embedded into a <script> block as JSON; a "</script>" in it must not close
    # the tag early. "<" is escaped to <, so only the real closing tag remains.
    ax = _axis(
        "Evil </script> axis",
        score=1.0,
        coverage=1.0,
        indicators=[_ind(IndicatorKind.MEASURED, True)],
    )
    out = render_html(_profile([ax]))
    # two legitimate scripts (the tower and the modal handler); the title must add no more
    assert out.count("</script>") == 2
    assert "\\u003c/script>" in out  # the title's "<" was neutralized


def test_html_and_text_humanize_underscored_pole_ids():
    # Pole ids are stored as scoring keys; readers should never see the underscores.
    ax = AxisResult(
        axis_id="a",
        title="A",
        poles=Poles(negative="human_in_loop", positive="multi_agent"),
        scale=10.0,
        score=-5.5,
        coverage=0.8,
        indicators=(_ind(IndicatorKind.MEASURED, True),),
    )
    html = render_html(_profile([ax]))
    text = render_text(_profile([ax]))
    for out in (html, text):
        assert "human in loop" in out
        assert "multi agent" in out
        assert "human_in_loop" not in out
        assert "multi_agent" not in out
    assert "+0.0" not in out  # a zero is never dressed up as a faint positive
    assert 'class="fill' not in out  # a neutral axis has no lean fill


def test_text_neutral_score_has_no_forced_sign():
    ax = _axis("Mid", score=0.0, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_text(_profile([ax]))
    assert "0.0" in out
    assert "+0.0" not in out
