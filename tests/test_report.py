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
from agentic_atlas.report import (
    _MODAL_JS,
    _display_name,
    _project_stamp,
    render_html,
    render_markdown,
    render_text,
)


def _ind(kind: IndicatorKind, resolved: bool, weight: float = 1.0) -> IndicatorResult:
    return IndicatorResult(
        indicator_id="x",
        kind=kind,
        weight=weight,
        value=1.0 if resolved else None,
        resolved=resolved,
        answer="yes" if resolved else None,
    )


def _axis(title, score, coverage, indicators, explain: Explain | None = None) -> AxisResult:
    return AxisResult(
        axis_id=title.lower(),
        title=title,
        poles=Poles(negative="left", positive="right"),
        scale=10.0,
        score=score,
        coverage=coverage,
        indicators=tuple(indicators),
        explain=explain if explain is not None else Explain(),
    )


def _profile(axes, target="/t", target_version=None, target_sha="abc123") -> Profile:
    return Profile(
        target=target,
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha=target_sha,
        target_version=target_version,
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
    assert "/agentic-atlas:run" in out
    assert "Claude Code, Cursor" in out


def test_no_skill_hint_when_everything_resolved():
    ax = _axis(
        "Full",
        score=-5.5,
        coverage=1.0,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, True)],
    )
    out = render_text(_profile([ax]))
    assert "/agentic-atlas:run" not in out


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


def test_html_hides_position_below_floor():
    # Consistent with the terminal and markdown renderers: below the coverage floor the axis
    # reports "needs interpretation" with no bar and no number. A faded bar was tried, but
    # under the +-1.0 value convention a lone low-weight indicator resolves to +-scale, so a
    # faded bar would still land at a pole and read as a confident verdict.
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_html(_profile([ax]))
    assert "needs interpretation" in out
    assert "under 50% evidence" in out
    assert 'class="fill' not in out  # no bar drawn
    assert "+10.0" not in out  # the pole number is never shown for a thin reading
    assert "low evidence" not in out  # the old provisional tag is gone
    assert "nothing could be read" not in out  # worded apart from the fully-unread state


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
    assert '<div class="stamps">commit abc123</div>' in out
    assert "rubric" not in out.split('<div class="stamps">')[1].split("</div>")[0]
    assert "engine" not in out.split('<div class="stamps">')[1].split("</div>")[0]


def test_project_stamp_exact_tag():
    assert _project_stamp(_profile([], target_version="v3.2.1")) == "version v3.2.1"


def test_project_stamp_describe_shows_nearest_release_only():
    # JSON keeps the raw describe string; the reader-facing stamp is just the release tag
    # (what GitHub Releases would show), not "N commits later" jargon.
    p = _profile([], target_version="v6.1.1-14-gd884ae0", target_sha="d884ae0abcde")
    assert _project_stamp(p) == "version v6.1.1"
    far = _profile([], target_version="v0.1.10-957-g93fc533", target_sha="93fc533d790f")
    assert _project_stamp(far) == "version v0.1.10"
    one = _profile([], target_version="v1.1.0-1-g5a3abe4", target_sha="5a3abe452248")
    assert _project_stamp(one) == "version v1.1.0"


def test_project_stamp_strips_semver_build_metadata():
    # Per-commit tags like autonomous-dev-v3.40.0+504c4e6 keep +build in JSON; display
    # drops it (SemVer: build metadata is not version identity).
    p = _profile(
        [],
        target_version="autonomous-dev-v3.40.0+504c4e6-2-gd687b566",
        target_sha="d687b5664a59",
    )
    assert _project_stamp(p) == "version autonomous-dev-v3.40.0"
    exact = _profile([], target_version="autonomous-dev-v3.40.0+504c4e6")
    assert _project_stamp(exact) == "version autonomous-dev-v3.40.0"


def test_project_stamp_keeps_npm_and_prefixed_release_tags():
    npm = _profile(
        [],
        target_version="task-master-ai@0.43.1-2-gc0c98d36",
        target_sha="c0c98d367c55",
    )
    assert _project_stamp(npm) == "version task-master-ai@0.43.1"
    prefixed = _profile(
        [],
        target_version="compound-engineering-v3.20.0-13-ga9f6d530",
        target_sha="a9f6d530d444",
    )
    assert _project_stamp(prefixed) == "version compound-engineering-v3.20.0"
    beta = _profile([], target_version="0.8-beta-2-g7d879d8", target_sha="7d879d8f5079")
    assert _project_stamp(beta) == "version 0.8-beta"
    rc = _profile([], target_version="v1.43.0-rc2-59-gbdcaab2c", target_sha="bdcaab2c752d")
    assert _project_stamp(rc) == "version v1.43.0-rc2"


def test_project_stamp_exact_tag_looking_like_describe_stays_exact():
    # A tag whose name matches -<n>-g<hex> is not a describe stamp when the abbrev is
    # not a prefix of target_sha.
    p = _profile([], target_version="release-1-gdeadbeef", target_sha="abc123def456")
    assert _project_stamp(p) == "version release-1-gdeadbeef"


def test_project_stamp_falls_back_to_commit_when_unversioned():
    assert _project_stamp(_profile([])) == "commit abc123"


def test_html_stamps_prefer_project_version_over_commit():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    profile = Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="abc123def456",
        target_version="v3.2.1",
        axes=(ax,),
    )
    out = render_html(profile)
    assert '<div class="stamps">version v3.2.1</div>' in out
    assert "commit" not in out.split('<div class="stamps">')[1].split("</div>")[0]
    assert "rubric 1.2.0" not in out
    assert "engine 0.2.0" not in out


def test_html_stamps_show_describe_distance_explicitly():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    profile = Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="d884ae0abcde",
        target_version="v6.1.1-14-gd884ae0",
        axes=(ax,),
    )
    out = render_html(profile)
    stamp = out.split('<div class="stamps">')[1].split("</div>")[0]
    assert stamp == "version v6.1.1"
    assert not stamp.startswith("commit ")


def test_text_and_markdown_include_project_stamp_with_atlas_versions():
    # HTML hides Atlas versions; text/markdown keep them for reproducibility and also
    # surface the same reader-facing project stamp.
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    profile = Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="cae8e664fb59abc",
        target_version="v3.0.0-6-gcae8e66",
        axes=(ax,),
    )
    text = render_text(profile)
    assert "rubric 1.2.0" in text
    assert "engine 0.2.0" in text
    assert "version v3.0.0" in text
    assert "commits later" not in text
    assert "sha cae8e664fb59" in text
    md = render_markdown(profile)
    assert "rubric: `1.2.0`" in md
    assert "engine: `0.2.0`" in md
    assert "target: `version v3.0.0`" in md
    assert "target sha: `cae8e664fb59abc`" in md


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


def test_html_brand_links_home_as_a_button_not_a_plain_link():
    # The mark + wordmark are a home link back to the Explorer, styled as a button
    # (no underline), with a tooltip. No "Profile" label beside the brand.
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert 'class="home" href="../index.html"' in out
    assert 'title="Back to the Explorer"' in out
    assert 'aria-label="Back to the Explorer, browse all frameworks"' in out
    assert '<span class="word">Agentic Atlas</span></a>' in out  # wordmark is inside the link
    assert 'class="ptitle"' not in out
    assert ".brand .home{" in out  # the button styling ships
    assert "text-decoration:none" in out  # not underlined like a text link


def test_profile_round_trips_through_dict():
    # from_dict is the exact inverse of to_dict, so a saved profile JSON re-renders without
    # re-running the engine or having the target repo on hand.
    classified = IndicatorResult(
        indicator_id="c1",
        kind=IndicatorKind.CLASSIFIED,
        weight=2.0,
        value=-0.5,
        resolved=True,
        answer="somewhat",
        evidence="a verbatim quote",
        source="supplied",
    )
    ax = _axis(
        "Round vs Trip",
        score=-3.0,
        coverage=0.75,
        indicators=[_ind(IndicatorKind.MEASURED, True), classified],
        explain=Explain(negative="one end", positive="other end"),
    )
    profile = Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="abc123",
        target_url="https://github.com/o/r",
        target_version="v1.0.0",
        axes=(ax,),
    )
    assert Profile.from_dict(profile.to_dict()) == profile
    # and the reconstruction renders byte-identically to the original
    assert render_html(Profile.from_dict(profile.to_dict())) == render_html(profile)
    assert '<div class="stamps">version v1.0.0</div>' in render_html(profile)


def test_profile_from_dict_tolerates_missing_target_version():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    data = _profile([ax]).to_dict()
    del data["target_version"]
    rebuilt = Profile.from_dict(data)
    assert rebuilt.target_version is None
    assert '<div class="stamps">commit abc123</div>' in render_html(rebuilt)
