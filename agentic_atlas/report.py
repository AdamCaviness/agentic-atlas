"""Render a Profile (or several) to a human-readable report.

Renders a signed bar per axis so the sign and magnitude read at a glance. There is
no total row, by design, a profile is a position not a grade.

The text renderer can emit ANSI color (opt-in via ``color=True``, decided by the
CLI from TTY detection and ``NO_COLOR``). The two poles get distinct, non-judgmental
hues, neither pole is "good", so color must never imply valence. Coverage is the one
quality signal where a green/yellow/red gradient is honest: higher means the axis
position rests on more of its intended evidence.
"""

from __future__ import annotations

import json
from html import escape as _html_escape

from .models import AxisResult, IndicatorKind, Profile


def _humanize(pole: str) -> str:
    """Pole ids are stored as scoring keys (``human_in_loop``, ``single_agent``); show them
    as words. Underscore to space keeps the same length, so terminal column widths hold."""
    return pole.replace("_", " ")


# The neutral middle means the same thing on every axis, so it is stated once here rather
# than authored per axis: a position near 0 is a genuine lack of lean, which can be a tool
# that serves both ends well or one that serves neither. The signals disambiguate.
_MIDDLE_NOTE = (
    "leans neither way, which can mean it serves both ends well, or neither. "
    "The signals below tell you which."
)

_BAR_HALF = 20  # characters on each side of the neutral center

# Below this fraction of resolved weight, an axis has too little evidence to plot a
# position. It reports "needs interpretation" instead of a bar so a sliver of measured
# evidence is never dressed up as a confident, clamped verdict. Tunable, presentation
# only: the score and coverage are still emitted verbatim in the JSON.
_COVERAGE_FLOOR = 0.5

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_NEG = "\033[36m"  # cyan, the left/negative pole
_POS = "\033[35m"  # magenta, the right/positive pole
_COV_GOOD = "\033[32m"  # green
_COV_MID = "\033[33m"  # yellow
_COV_LOW = "\033[31m"  # red


def _paint(text: str, *codes: str, on: bool) -> str:
    if not on or not text:
        return text
    return "".join(codes) + text + _RESET


def _coverage_code(coverage: float) -> str:
    if coverage >= 0.67:
        return _COV_GOOD
    if coverage >= 0.34:
        return _COV_MID
    return _COV_LOW


def _bar(score: float | None, scale: float, color: bool = False) -> str:
    if score is None:
        return " " * _BAR_HALF + _paint("|", _DIM, on=color) + " " * _BAR_HALF + "  (no data)"
    frac = max(-1.0, min(1.0, score / scale))
    fill = round(abs(frac) * _BAR_HALF)
    if frac < 0:
        left = " " * (_BAR_HALF - fill) + _paint("#" * fill, _NEG, on=color)
        right = " " * _BAR_HALF
    else:
        left = " " * _BAR_HALF
        right = _paint("#" * fill, _POS, on=color) + " " * (_BAR_HALF - fill)
    return f"{left}{_paint('|', _DIM, on=color)}{right}"


_SKILL_HINT = (
    "of {total} axes need interpretation for lack of classified answers. "
    "Run the /agentic-atlas skill in agentic-toolkit (inside Claude Code) to answer them "
    "with your coding agent, no API key, and get a complete profile."
)


def _needs_interpretation(ax: AxisResult) -> bool:
    return ax.score is None or ax.coverage < _COVERAGE_FLOOR


def _skill_hint(profile: Profile) -> str | None:
    """The opinionated first-run pointer: how to resolve the unplottable axes.

    Shown only when axes are unplottable *because classified answers are missing*, which
    is the bare deterministic run. Once the skill supplies answers there is nothing to
    nudge toward, so the hint disappears.
    """
    pending = [ax for ax in profile.axes if _needs_interpretation(ax)]
    has_unanswered_classified = any(
        ir.kind is IndicatorKind.CLASSIFIED and not ir.resolved
        for ax in pending
        for ir in ax.indicators
    )
    if not pending or not has_unanswered_classified:
        return None
    return f"{len(pending)} " + _SKILL_HINT.format(total=len(profile.axes))


def _kind_counts(ax: AxisResult) -> tuple[int, int, int, int]:
    """Resolved/total indicator counts split by kind: (m_resolved, m_total, c_resolved, c_total)."""
    m_total = m_res = c_total = c_res = 0
    for ir in ax.indicators:
        if ir.kind is IndicatorKind.MEASURED:
            m_total += 1
            m_res += ir.resolved
        else:
            c_total += 1
            c_res += ir.resolved
    return m_res, m_total, c_res, c_total


def _coverage_detail(ax: AxisResult, color: bool = False) -> str:
    # Split coverage by kind so a keyless run reads as "you ran the measured half," not
    # a broken percentage. Classified indicators need answers from the toolkit skill.
    m_res, m_total, c_res, c_total = _kind_counts(ax)
    text = f"measured {m_res}/{m_total} · classified {c_res}/{c_total}"
    return _paint(text, _coverage_code(ax.coverage), on=color)


def _axis_lines(ax: AxisResult, color: bool = False) -> list[str]:
    detail = _coverage_detail(ax, color)
    title = _paint(ax.title, _BOLD, on=color)
    if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
        # Not enough resolved weight to claim a position. Say so, and draw no bar.
        return [f"{title}  {_paint('needs interpretation', _DIM, on=color)}  {detail}"]
    if ax.score == 0:
        # Exactly neutral reads as neutral, not a faint positive: no forced sign, no pole hue.
        score_txt = _paint("0.0", _DIM, _BOLD, on=color)
    else:
        side = _NEG if ax.score < 0 else _POS
        score_txt = _paint(f"{ax.score:+.1f}", side, _BOLD, on=color)
    # Scale is a rubric-wide constant stated once in the header, so the per-axis line
    # just shows the signed value.
    header = f"{title}  {score_txt}  {detail}"
    neg, pos = _humanize(ax.poles.negative), _humanize(ax.poles.positive)
    poles = f"  {neg:<20}{_bar(ax.score, ax.scale, color)}{pos:>20}"
    return [header, poles]


def render_markdown(profile: Profile) -> str:
    lines = [
        f"# Profile: {profile.target}",
        "",
        f"- rubric: `{profile.rubric_version}`",
        f"- engine: `{profile.engine_version}`",
        f"- target sha: `{profile.target_sha or 'unknown'}`",
        "",
        "No aggregate score by design. Each axis is an independent position.",
        "",
    ]
    for ax in profile.axes:
        if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
            score = "needs interpretation"
        else:
            score = f"{ax.score:+.1f} (±{ax.scale:g})"
        m_res, m_total, c_res, c_total = _kind_counts(ax)
        neg, pos = _humanize(ax.poles.negative), _humanize(ax.poles.positive)
        lines.append(f"## {ax.title}: {score}")
        lines.append(
            f"Poles: `{neg}` (-) ↔ `{pos}` (+). "
            f"Coverage: measured {m_res}/{m_total}, classified {c_res}/{c_total}."
        )
        if ax.explain.negative or ax.explain.positive:
            lines.append("")
            lines.append(f"- **{neg}** (-): {ax.explain.negative}")
            lines.append(f"- **{pos}** (+): {ax.explain.positive}")
            lines.append(f"- **near 0**: {_MIDDLE_NOTE}")
        lines.append("")
        lines.append("| indicator | kind | weight | answer | value | evidence | source |")
        lines.append("|---|---|---|---|---|---|---|")
        for ir in ax.indicators:
            val = "" if ir.value is None else f"{ir.value:+.2f}"
            ev = (ir.evidence or "").replace("|", "\\|")[:80]
            lines.append(
                f"| {ir.indicator_id} | {ir.kind.value} | {ir.weight:g} | "
                f"{ir.answer or '-'} | {val} | {ev} | {ir.source or '-'} |"
            )
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(f"> {hint}")
    return "\n".join(lines)


def render_text(profile: Profile, color: bool = False) -> str:
    lines = [
        f"Profile: {profile.target}",
        _paint(
            f"rubric {profile.rubric_version} | engine {profile.engine_version} | "
            f"sha {(profile.target_sha or 'unknown')[:12]}",
            _DIM,
            on=color,
        ),
    ]
    if profile.axes:
        # Scale is rubric-wide, so every axis shares it. State it once here.
        scale = profile.axes[0].scale
        lines.append(_paint(f"scale ±{scale:g} per axis · no aggregate score", _DIM, on=color))
    lines.append("")
    for ax in profile.axes:
        lines.extend(_axis_lines(ax, color=color))
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(_paint(f"→ {hint}", _BOLD, on=color))
    return "\n".join(lines)


# Plain, self-explanatory labels for the two indicator kinds. The JSON keeps the precise
# vocabulary (measured/classified); the HTML view never shows it, because those words mean
# nothing to a first-time reader. "detected" = the engine found it; "judged" = a reviewer
# read the repo and decided.
_KIND_LABEL = {IndicatorKind.MEASURED: "detected", IndicatorKind.CLASSIFIED: "judged"}

# The rubric is the whole point: a profile is only meaningful relative to it, so the page
# links there. Points at the rubric root, which lists the versioned major directories, so it
# stays valid across rubric versions.
_RUBRIC_URL = "https://github.com/AdamCaviness/agentic-atlas/tree/main/rubric"

# The hosted Explorer: the interactive map of all published profiles. Every profile page links
# home to it through the brand mark, so a reader who lands on one profile can step back to the
# whole set. Absolute so the link resolves the same whether the page is opened from the hosted
# site, the built local site, or a standalone file.
_HOME_URL = "https://adamcaviness.github.io/agentic-atlas/"


def _display_name(target: str) -> str:
    """The target's last path segment, for the header pill. ``/a/b/superpowers`` and
    ``https://github.com/obra/superpowers.git`` both read as ``superpowers``. The full target
    stays in the pill's title attribute, the stamps, and the JSON, so provenance is not lost."""
    name = target.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name or target

# Inlined so the page is self-contained: no external fonts, stylesheets, or scripts, so it
# renders identically from a file:// path in any harness. Two non-judgmental pole hues mirror
# the terminal renderer (neither pole is "good"); coverage keeps a separate green/amber/red
# gradient, the one honest quality signal. Theme-aware via prefers-color-scheme.
_HTML_CSS = """
  :root {
    --bg:#fff;--fg:#1a1a1a;--muted:#6b7280;--faint:#9ca3af;--card:#f7f7f8;--line:#e5e7eb;--track:#e9eaed;
    --neg:#0891b2;--pos:#9333ea;--cov-good:#16a34a;--cov-mid:#d97706;--cov-low:#dc2626;--accent:#4f46e5;--pill-fg:#fff;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;--card:#161b22;--line:#30363d;--track:#21262d;
    --neg:#22d3ee;--pos:#c084fc;--cov-good:#3fb950;--cov-mid:#d29922;--cov-low:#f85149;--accent:#818cf8;--pill-fg:#0d1117;
  }}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.5}
  .wrap{max-width:880px;margin:0 auto;padding:32px 20px 64px}
  .wrap.wide{max-width:940px}
  .layout{display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:28px;align-items:start}
  .col-main{grid-column:1;grid-row:1;min-width:0}
  .col-rail{grid-column:2;grid-row:1}
  @media (max-width:880px){
    .layout{grid-template-columns:1fr}
    .col-main,.col-rail{grid-column:1}
    .col-rail{margin-bottom:22px}
  }
  header h1{font-size:1.5rem;margin:0 0 8px;font-weight:650}
  .target-pill{display:inline-block;font-weight:650;font-size:1.15rem;color:var(--pill-fg);
               background:var(--accent);padding:3px 14px;border-radius:999px;margin:0 0 10px;word-break:break-word}
  .brand{display:flex;align-items:center;gap:11px;margin:0 0 12px}
  .brand .home{display:inline-flex;align-items:center;gap:11px;color:inherit;text-decoration:none;cursor:pointer;
               margin:-6px 0 -6px -8px;padding:6px 8px;border-radius:10px;transition:background .12s ease,box-shadow .12s ease}
  .brand .home:hover{background:var(--card);box-shadow:0 1px 4px rgba(0,0,0,.10)}
  .brand .home:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .brand .mark{width:32px;height:33px;flex:none}
  .brand .word{font-size:1.55rem;font-weight:750;letter-spacing:-.01em;line-height:1;background:linear-gradient(100deg,var(--neg),var(--accent) 52%,var(--pos));-webkit-background-clip:text;background-clip:text;color:transparent}
  .brand .ptitle{font-size:1.55rem;font-weight:400;line-height:1;color:var(--fg)}
  .project{margin:0 0 10px;font-size:1.02rem}
  .project a{display:inline-flex;align-items:center;gap:8px;color:var(--fg);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:5px 15px}
  .project a:hover{border-color:var(--accent);color:var(--accent)}
  .project .gh{flex:none;width:18px;height:18px}
  .project .pname{font-weight:600}
  .stamps{font-family:var(--mono);font-size:.82rem;color:var(--muted);margin:0 0 2px}
  .note{color:var(--fg);font-size:.95rem;margin:10px 0 2px}
  .note a{color:var(--accent);text-decoration:underline}
  .aside{color:var(--muted);font-size:.82rem;margin:2px 0 0}
  .legend{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0 26px;padding:12px 14px;background:var(--card);
          border:1px solid var(--line);border-radius:10px;font-size:.82rem;color:var(--muted)}
  .legend .swatch{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:6px}
  .axis{border:1px solid var(--line);border-radius:12px;padding:13px 16px;margin:0 0 11px;background:var(--card)}
  .axis-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
  .axis-title{font-weight:600;font-size:.95rem}
  .ahl{display:inline-flex;align-items:center;gap:8px}
  .axis-title em{font-style:italic;font-weight:400;color:var(--muted)}
  .score{font-family:var(--mono);font-weight:700;font-size:.98rem;white-space:nowrap}
  .score.neg{color:var(--neg)}.score.pos{color:var(--pos)}
  .score.none{color:var(--faint);font-weight:500;font-style:italic;font-size:.9rem}
  .score.zero{color:var(--faint)}
  .prov-tag{font-family:var(--sans);font-weight:500;font-size:.66rem;text-transform:uppercase;letter-spacing:.04em;
            color:var(--cov-low);border:1px solid var(--cov-low);border-radius:4px;padding:1px 5px;margin-left:8px;vertical-align:1px}
  .bar-row{display:grid;grid-template-columns:8.5rem 1fr 8.5rem;align-items:center;gap:12px;margin:10px 0 4px}
  .pole{font-size:.78rem;color:var(--muted)}
  .pole.left{text-align:right}.pole.right{text-align:left}
  .track{position:relative;height:22px;background:var(--track);border-radius:6px}
  .track .center{position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:var(--faint);transform:translateX(-1px)}
  .fill{position:absolute;top:3px;bottom:3px}
  .fill.neg{right:50%;background:var(--neg);border-radius:4px 0 0 4px}
  .fill.pos{left:50%;background:var(--pos);border-radius:0 4px 4px 0}
  .fill.prov{opacity:.4;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px);
             outline:1px dashed var(--faint);outline-offset:-1px}
  .track.empty{background:repeating-linear-gradient(45deg,transparent,transparent 6px,var(--track) 6px,var(--track) 12px);border:1px dashed var(--line)}
  .track.empty .center{background:var(--line)}
  .ni{display:inline-block;font-size:.8rem;color:var(--faint);position:absolute;left:50%;top:50%;
      transform:translate(-50%,-50%);background:var(--card);padding:0 8px;white-space:nowrap}
  .cov{display:flex;align-items:center;gap:10px;width:100%;background:none;border:0;padding:6px 0 0;margin:0;font:inherit;color:inherit;text-align:left;cursor:pointer}
  .cov-meter{position:relative;width:120px;height:6px;background:var(--track);border-radius:3px;overflow:hidden;flex:none}
  .cov-fill{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
  .cov-floor{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:var(--faint)}
  .cov-good{background:var(--cov-good)}.cov-mid{background:var(--cov-mid)}.cov-low{background:var(--cov-low)}
  .cov-text{color:var(--muted);font-family:var(--mono);font-size:.82rem}
  .cov-more{margin-left:auto;font-size:.8rem;color:var(--muted);white-space:nowrap}
  .cov:hover .cov-more{color:var(--accent)}
  .mbtn{font:inherit;font-size:.8rem;color:var(--fg);background:var(--bg);border:1px solid var(--line);
        border-radius:8px;padding:6px 12px;cursor:pointer;transition:border-color .12s,color .12s}
  .mbtn:hover{border-color:var(--accent);color:var(--accent)}
  .mbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .info{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;padding:0;border:1px solid var(--faint);color:var(--muted);background:none;border-radius:50%;font:600 .66rem/1 var(--sans);cursor:pointer;vertical-align:middle}
  .info:hover{border-color:var(--accent);color:var(--accent)}
  .info:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  dialog.modal{max-width:560px;width:calc(100% - 32px);border:1px solid var(--line);border-radius:14px;
               background:var(--card);color:var(--fg);padding:22px 24px 24px;box-shadow:0 24px 70px rgba(0,0,0,.4)}
  dialog.modal.modal-wide{max-width:760px}
  dialog.modal::backdrop{background:rgba(0,0,0,.5)}
  dialog.modal form{margin:0}
  .modal-x{float:right;font-size:1.4rem;line-height:1;background:none;border:0;color:var(--muted);cursor:pointer;padding:0 4px}
  .modal-x:hover{color:var(--fg)}
  .modal-x:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .modal-title{margin:0 0 2px;font-size:1.05rem;font-weight:650}
  .modal-sub{margin:0 0 14px;font-size:.82rem;color:var(--muted)}
  dl.poles{display:grid;grid-template-columns:auto 1fr;gap:5px 14px;margin:12px 0 2px;font-size:.82rem}
  dl.poles dt{font-weight:600;color:var(--fg);white-space:nowrap}
  dl.poles dd{margin:0;color:var(--muted)}
  dl.poles dt.neg{color:var(--neg)}dl.poles dt.pos{color:var(--pos)}
  dl.poles dt.mid,dl.poles dd.mid{color:var(--faint)}
  table{width:100%;border-collapse:collapse;margin-top:10px;font-size:.78rem}
  .table-scroll{overflow-x:auto}
  th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--muted);font-weight:600;white-space:nowrap}
  td.evidence{color:var(--muted);font-family:var(--mono);font-size:.72rem;min-width:16rem}
  .kind{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;padding:1px 6px;border-radius:4px;border:1px solid var(--line);color:var(--muted)}
  .val{font-family:var(--mono)}
  .footer-hint{margin-top:22px;padding:12px 14px;border-left:3px solid var(--cov-mid);background:var(--card);
               border-radius:0 8px 8px 0;font-size:.85rem;color:var(--muted)}
  .hero3d{position:relative;width:100%;height:60vh;margin:0;
          border:1px solid var(--line);border-radius:12px;background:var(--card);overflow:hidden;
          touch-action:none;user-select:none}
  .hero3d canvas{display:block;width:100%;height:100%;cursor:grab}
  .hero3d canvas:active{cursor:grabbing}
  .hero3d .tip{position:absolute;left:0;top:0;pointer-events:none;opacity:0;transition:opacity .1s;
               max-width:80%;padding:6px 9px;border-radius:8px;font-size:.78rem;line-height:1.35;
               background:var(--bg);border:1px solid var(--line);color:var(--fg);
               box-shadow:0 4px 14px rgba(0,0,0,.18);z-index:2}
  .hero3d .tip .th{font-weight:650}
  .hero3d .tip .th.pos{color:var(--pos)}.hero3d .tip .th.neg{color:var(--neg)}
  .hero3d .tip .tp{color:var(--muted);font-size:.72rem}
  .hero3d .fallback{display:none;position:absolute;inset:0;align-items:center;justify-content:center;
                    padding:0 22px;text-align:center;font-size:.85rem;color:var(--muted)}
"""


def _coverage_class(coverage: float) -> str:
    """Map coverage to the green/amber/red gradient the terminal renderer also uses."""
    if coverage >= 0.67:
        return "cov-good"
    if coverage >= 0.34:
        return "cov-mid"
    return "cov-low"


def _html_indicator_rows(ax: AxisResult) -> str:
    rows = []
    for ir in ax.indicators:
        val = "" if ir.value is None else f"{ir.value:+.2f}"
        rows.append(
            "<tr>"
            f"<td>{_html_escape(ir.indicator_id)}</td>"
            f'<td><span class="kind">{_KIND_LABEL[ir.kind]}</span></td>'
            f"<td>{ir.weight:g}</td>"
            f"<td>{_html_escape(ir.answer or '-')}</td>"
            f'<td class="val">{val}</td>'
            f'<td class="evidence">{_html_escape(ir.evidence or "")}</td>'
            f"<td>{_html_escape(ir.source or '-')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _html_axis(ax: AxisResult, idx: int) -> str:
    m_res, m_total, c_res, c_total = _kind_counts(ax)
    cov_pct = round(ax.coverage * 100)
    cov_txt = f"detected {m_res}/{m_total} · judged {c_res}/{c_total} · {cov_pct}% evidence"

    if ax.score is None:
        # Nothing resolved: there is no number to place, so draw no bar and say so.
        # Only an unreadable target (or a bare run with no answers) reaches this.
        score_html = '<span class="score none">nothing could be read</span>'
        bar = (
            '<div class="track empty"><div class="center"></div>'
            '<span class="ni">no evidence found</span></div>'
        )
    else:
        # Below the floor the axis still has a number but rests on thin evidence. Unlike the
        # terminal renderer, which hides it, HTML can fade it: always draw a bar, but a
        # provisional one, so a sliver of evidence is never mistaken for a confident verdict.
        provisional = ax.coverage < _COVERAGE_FLOOR
        tag = (
            '<span class="prov-tag" title="thin evidence, under 50%">low evidence</span>'
            if provisional
            else ""
        )
        if ax.score == 0:
            # Exactly neutral: no lean, no forced sign, no fill, just the centered marker.
            score_html = f'<span class="score zero">0.0</span>{tag}'
            bar = '<div class="track"><div class="center"></div></div>'
        else:
            side = "neg" if ax.score < 0 else "pos"
            width = abs(ax.score) / ax.scale * 50
            score_html = f'<span class="score {side}">{ax.score:+.1f}</span>{tag}'
            fill_cls = f"fill {side}" + (" prov" if provisional else "")
            bar = (
                f'<div class="track"><div class="{fill_cls}" style="width:{width:g}%"></div>'
                '<div class="center"></div></div>'
            )

    title = _html_escape(ax.title)
    title_disp = title.replace(" vs ", " <em>vs</em> ")
    neg_label = _html_escape(_humanize(ax.poles.negative))
    pos_label = _html_escape(_humanize(ax.poles.positive))

    # Details live in modal dialogs, not inline expanders, so every card keeps a fixed
    # height no matter what is opened. That fixed height is what lets the tower's bands line
    # up with the cards: opening a dialog never reflows the column. Dialogs close natively
    # (the form-method button, plus Esc); only opening and backdrop-close need _MODAL_JS.
    poles_info = ""
    dialogs = []
    if ax.explain.negative or ax.explain.positive:
        poles_info = (
            f'<button type="button" class="info" data-dialog="poles-{idx}" aria-label="what the poles mean" title="what the poles mean">i</button>'
        )
        dialogs.append(
            f'    <dialog id="poles-{idx}" class="modal">\n'
            '      <form method="dialog"><button class="modal-x" aria-label="Close">&times;</button></form>\n'
            f'      <h3 class="modal-title">{title}</h3>\n'
            '      <p class="modal-sub">what the poles mean</p>\n'
            '      <dl class="poles">\n'
            f'        <dt class="neg">{neg_label}</dt><dd>{_html_escape(ax.explain.negative)}</dd>\n'
            f'        <dt class="pos">{pos_label}</dt><dd>{_html_escape(ax.explain.positive)}</dd>\n'
            f'        <dt class="mid">near 0</dt><dd class="mid">{_html_escape(_MIDDLE_NOTE)}</dd>\n'
            "      </dl>\n"
            "    </dialog>"
        )
    n_sig = len(ax.indicators)
    dialogs.append(
        f'    <dialog id="signals-{idx}" class="modal modal-wide">\n'
        '      <form method="dialog"><button class="modal-x" aria-label="Close">&times;</button></form>\n'
        f'      <h3 class="modal-title">{title}</h3>\n'
        f'      <p class="modal-sub">{n_sig} signals behind this position</p>\n'
        '      <div class="table-scroll"><table>'
        "<thead><tr><th>id</th><th>kind</th><th>wt</th><th>answer</th>"
        "<th>value</th><th>evidence</th><th>source</th></tr></thead>"
        f"<tbody>{_html_indicator_rows(ax)}</tbody></table></div>\n"
        "    </dialog>"
    )
    dialogs_html = "\n".join(dialogs)

    return (
        '  <section class="axis">\n'
        f'    <div class="axis-head"><span class="ahl"><span class="axis-title">{title_disp}</span>{poles_info}</span>{score_html}</div>\n'
        '    <div class="bar-row">\n'
        f'      <span class="pole left">{neg_label}</span>\n'
        f"      {bar}\n"
        f'      <span class="pole right">{pos_label}</span>\n'
        "    </div>\n"
        f'    <button type="button" class="cov" data-dialog="signals-{idx}" title="show the {n_sig} signals behind this">\n'
        f'      <div class="cov-meter"><div class="cov-fill {_coverage_class(ax.coverage)}" style="width:{cov_pct}%"></div><div class="cov-floor"></div></div>\n'
        f'      <span class="cov-text">{_html_escape(cov_txt)}</span>\n'
        '      <span class="cov-more">signals &rsaquo;</span>\n'
        "    </button>\n"
        f"{dialogs_html}\n"
        "  </section>"
    )


# A low-poly crystal in the rail beside the cards, the same height as them and aligned band
# to card. It is NOT a tube: each cross-section is a small kite that pushes a tip outward in
# that axis's lean direction, its length the score, so a zero or no-reading axis is a centered
# symmetric diamond that points nowhere. The body hugs a central spine inside an (invisible)
# bounding cylinder; consecutive axes are lofted into one continuous faceted mesh, bent only
# in the neutral necks that bridge the gaps between cards. Flat-shaded triangles with a faint
# wireframe give the unfinished low-poly-game look; cyan tips lean to the negative pole,
# magenta to the positive. Orthographic, yaw-only rotation keeps the vertical alignment while
# it spins; it auto-rotates, pauses on hover, drags to spin, and picks the band under the
# cursor to name the axis. Raw WebGL, self-contained for file:// use, axis data injected as
# JSON at ``/*__AXES__*/`` so the emitted bytes stay a deterministic function of the Profile.
_HERO_JS = r"""(function(){
  var host=document.getElementById('atlas-hero');
  if(!host) return;
  var canvas=host.querySelector('canvas');
  var tip=host.querySelector('.tip');
  var AXES=/*__AXES__*/;
  function fail(){ canvas.style.display='none';
    var f=host.querySelector('.fallback'); if(f) f.style.display='flex'; }
  if(!AXES.length){ host.style.display='none'; return; }
  var gl=null;
  try{ gl=canvas.getContext('webgl',{antialias:true,alpha:true,premultipliedAlpha:false})
        ||canvas.getContext('experimental-webgl'); }catch(e){}
  if(!gl){ fail(); return; }

  function css(n){ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function hex(h){ h=(h||'').replace('#',''); if(h.length===3){h=h[0]+h[0]+h[1]+h[1]+h[2]+h[2];}
    var n=parseInt(h,16); if(isNaN(n)) return [.5,.5,.5];
    return [((n>>16)&255)/255,((n>>8)&255)/255,(n&255)/255]; }
  function mix(a,b,t){ return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]; }
  var NEG=hex(css('--neg')), POS=hex(css('--pos')), FAINT=hex(css('--faint')),
      CARD=hex(css('--card')), FG=hex(css('--fg')), NECK=mix(FAINT,CARD,0.35), WIRE=FAINT;

  // shaders: flat-shaded (per-face normal), an id pass for picking, and a flat-color wire pass
  function sh(t,s){ var o=gl.createShader(t); gl.shaderSource(o,s); gl.compileShader(o);
    if(!gl.getShaderParameter(o,gl.COMPILE_STATUS)) console.log(gl.getShaderInfoLog(o)); return o; }
  var prog=gl.createProgram();
  gl.attachShader(prog,sh(gl.VERTEX_SHADER,
    'attribute vec3 aPos;attribute vec3 aNormal;attribute vec3 aColor;attribute vec3 aId;'+
    'uniform mat4 uMVP;uniform mat3 uNMat;varying vec3 vN;varying vec3 vC;varying vec3 vId;'+
    'void main(){vN=uNMat*aNormal;vC=aColor;vId=aId;gl_Position=uMVP*vec4(aPos,1.0);}'));
  gl.attachShader(prog,sh(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump int;varying vec3 vN;varying vec3 vC;varying vec3 vId;'+
    'uniform int uMode;uniform vec3 uLight;void main(){'+
    'if(uMode==1){gl_FragColor=vec4(vId,1.0);return;}'+
    'if(uMode==2){gl_FragColor=vec4(vC,1.0);return;}'+
    'vec3 n=normalize(vN);float d=max(dot(n,normalize(uLight)),0.0);'+
    'float b=floor(d*4.0+0.5)/4.0;gl_FragColor=vec4(vC*(0.45+0.6*b),1.0);}'));
  gl.linkProgram(prog); gl.useProgram(prog);
  var aPos=gl.getAttribLocation(prog,'aPos'), aNormal=gl.getAttribLocation(prog,'aNormal'),
      aColor=gl.getAttribLocation(prog,'aColor'), aId=gl.getAttribLocation(prog,'aId'),
      uMVP=gl.getUniformLocation(prog,'uMVP'), uNMat=gl.getUniformLocation(prog,'uNMat'),
      uMode=gl.getUniformLocation(prog,'uMode'), uLight=gl.getUniformLocation(prog,'uLight');
  function up(buf,data){ if(!buf) buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STATIC_DRAW); return buf; }
  function attr(loc,b){ if(loc<0)return; gl.enableVertexAttribArray(loc);
    gl.bindBuffer(gl.ARRAY_BUFFER,b); gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0); }

  // matrices (column-major); orthographic so vertical position never foreshortens
  function ident(){ return new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]); }
  function mul(a,b){ var o=new Float32Array(16);
    for(var c=0;c<4;c++)for(var r=0;r<4;r++){var s=0;for(var k=0;k<4;k++)s+=a[k*4+r]*b[c*4+k];o[c*4+r]=s;} return o; }
  function rotY(r){ var c=Math.cos(r),s=Math.sin(r),o=ident(); o[0]=c;o[2]=-s;o[8]=s;o[10]=c; return o; }
  function nmat3(r){ var c=Math.cos(r),s=Math.sin(r); return new Float32Array([c,0,-s,0,1,0,s,0,c]); }
  function ortho(hw,hh,nf){ var o=ident(); o[0]=1/hw;o[5]=1/hh;o[10]=-1/nf; return o; }

  // state
  var N=AXES.length;
  var ry=0, inside=false, dragging=false, lastX=0, hovered=-1;
  var proj=ident(), vw=1, vh=1, pickFB=null, pickTex=null, pickDepth=null;
  var bPos=null,bNrm=null,bCol=null,bId=null,bWpos=null,bWcol=null, fillCount=0, wireCount=0, halfW=1, halfH=1;

  // geometry: one lofted crystal whose kite cross-section points a tip in each axis's lean dir
  function buildGeom(){
    var narrow=window.matchMedia('(max-width:880px)').matches;
    var cards=document.querySelectorAll('.col-main .axis');
    var tops=[], bots=[], hostH;
    if(!narrow && cards.length===N){
      // Bound the container to the cards: top of the first card, bottom of the last, offset
      // below the header so the shape spans exactly the sections it describes.
      var railTop=host.parentElement.getBoundingClientRect().top;
      var rects=[]; for(var c=0;c<N;c++) rects.push(cards[c].getBoundingClientRect());
      var firstTop=rects[0].top, lastBot=rects[N-1].bottom;
      hostH=lastBot-firstTop;
      host.style.marginTop=(firstTop-railTop)+'px'; host.style.height=hostH+'px';
      for(var c3=0;c3<N;c3++){ tops.push(rects[c3].top-firstTop); bots.push(rects[c3].bottom-firstTop); }
    } else {
      host.style.marginTop=''; host.style.height=''; hostH=host.clientHeight;
      var pad=hostH*0.07, bh=(hostH-2*pad)/N;
      for(var c2=0;c2<N;c2++){ tops.push(pad+c2*bh+bh*0.12); bots.push(pad+(c2+1)*bh-bh*0.12); }
    }
    var W=host.clientWidth; halfW=W/2; halfH=hostH/2;
    // A substantial spine (coreR/sideR) is the body inside the invisible bounding cylinder; the
    // tip reaches out up to MAXOFF past the spine at the card's center, tapering back at the edges.
    // Fractions of the (small) rail width, so the shape fills it snugly with a little margin.
    var MAXOFF=W*0.28, coreR=Math.max(6,W*0.13), sideR=Math.max(8,W*0.16);

    function reach(i){ var a=AXES[i]; return (a.s===null||a.s===undefined)?0:Math.min(Math.abs(a.s/a.sc),1)*MAXOFF; }
    function sgn(i){ var a=AXES[i]; return (a.s!==null&&a.s!==undefined&&a.s<0)?-1:1; }
    function lean(i){ var a=AXES[i], has=(a.s!==null&&a.s!==undefined);
      var f=has?Math.max(-1,Math.min(1,a.s/a.sc)):0;
      return has?mix(FAINT, f<0?NEG:POS, 0.32+0.68*Math.min(Math.abs(f),1)):FAINT; }
    function wy(py){ return hostH/2-py; }
    // kite cross-section, verts E(+x),N(+z),W(-x),S(-z). A "core" ring is a small centered
    // diamond; a "tip" ring pushes one side out to reach, making the apex point in the lean dir.
    function core(py){ var y=wy(py); return [[coreR,y,0],[0,y,sideR],[-coreR,y,0],[0,y,-sideR]]; }
    function tipRing(i,py){ var e=reach(i), sg=sgn(i), y=wy(py);
      var r=(sg>0)?coreR+e:coreR, l=(sg<0)?coreR+e:coreR;
      return [[r,y,0],[0,y,sideR],[-l,y,0],[0,y,-sideR]]; }

    var pos=[],nrm=[],col=[],ids=[],wpos=[],wcol=[];
    function triFlat(A,B,C,c,id){
      var ux=B[0]-A[0],uy=B[1]-A[1],uz=B[2]-A[2],vx=C[0]-A[0],vy=C[1]-A[1],vz=C[2]-A[2];
      var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,l=Math.sqrt(nx*nx+ny*ny+nz*nz)||1; nx/=l;ny/=l;nz/=l;
      var cxp=(A[0]+B[0]+C[0])/3, czp=(A[2]+B[2]+C[2])/3;      // point normals outward from the spine
      if(nx*cxp+nz*czp<0){ nx=-nx;ny=-ny;nz=-nz; }
      var P=[A,B,C]; for(var k=0;k<3;k++){ pos.push(P[k][0],P[k][1],P[k][2]); nrm.push(nx,ny,nz);
        col.push(c[0],c[1],c[2]); ids.push(id[0],id[1],id[2]); } }
    function wl(a,b){ wpos.push(a[0],a[1],a[2],b[0],b[1],b[2]); wcol.push(WIRE[0],WIRE[1],WIRE[2],WIRE[0],WIRE[1],WIRE[2]); }
    function loft(r0,r1,c,id){ for(var j=0;j<4;j++){ var j1=(j+1)%4;
      triFlat(r0[j],r0[j1],r1[j1],c,id); triFlat(r0[j],r1[j1],r1[j],c,id);
      wl(r0[j],r0[j1]); wl(r0[j],r1[j]); wl(r0[j],r1[j1]); } }
    function cap(rg,c,id){ var C=[(rg[0][0]+rg[1][0]+rg[2][0]+rg[3][0])/4, rg[0][1], (rg[0][2]+rg[1][2]+rg[2][2]+rg[3][2])/4];
      for(var j=0;j<4;j++){ var j1=(j+1)%4; triFlat(C,rg[j],rg[j1],c,id); wl(rg[j],rg[j1]); } }

    var prevBot=null;
    for(var i=0;i<N;i++){
      var mid=(tops[i]+bots[i])/2, lc=lean(i), id=[((i+1)&255)/255,0,0];
      var ct=core(tops[i]), mt=tipRing(i,mid), cb=core(bots[i]);
      if(prevBot) loft(prevBot,ct,NECK,id);   // thin spine joint across the gap (neutral)
      loft(ct,mt,lc,id); loft(mt,cb,lc,id);     // the axis's spike: out to the point, back in
      prevBot=cb;
    }
    cap(core(tops[0]), NECK, [1/255,0,0]);
    cap(core(bots[N-1]), NECK, [(N&255)/255,0,0]);

    fillCount=pos.length/3; wireCount=wpos.length/3;
    bPos=up(bPos,pos); bNrm=up(bNrm,nrm); bCol=up(bCol,col); bId=up(bId,ids); bWpos=up(bWpos,wpos); bWcol=up(bWcol,wcol);
  }

  function resize(){
    var dpr=Math.min(window.devicePixelRatio||1,2);
    buildGeom();
    var w=Math.max(1,Math.round(host.clientWidth*dpr)), h=Math.max(1,Math.round(host.clientHeight*dpr));
    vw=w; vh=h; canvas.width=w; canvas.height=h;
    proj=ortho(halfW,halfH,4000);
    if(pickFB) gl.deleteFramebuffer(pickFB);
    if(pickTex) gl.deleteTexture(pickTex);
    if(pickDepth) gl.deleteRenderbuffer(pickDepth);
    pickTex=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,pickTex);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    pickDepth=gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER,pickDepth);
    gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,w,h);
    pickFB=gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER,pickFB);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,pickTex,0);
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,pickDepth);
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  }

  function draw(forPick){
    gl.bindFramebuffer(gl.FRAMEBUFFER, forPick?pickFB:null);
    gl.viewport(0,0,vw,vh);
    gl.clearColor(0,0,0, forPick?1:0);
    gl.enable(gl.DEPTH_TEST); gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.useProgram(prog);
    gl.uniformMatrix4fv(uMVP,false,mul(proj,rotY(ry)));
    gl.uniformMatrix3fv(uNMat,false,nmat3(ry));
    gl.uniform3f(uLight,0.5,0.8,0.6);
    attr(aPos,bPos); attr(aNormal,bNrm); attr(aColor,bCol); attr(aId,bId);
    gl.uniform1i(uMode, forPick?1:0);
    if(!forPick){ gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(1.1,1.1); }
    gl.drawArrays(gl.TRIANGLES,0,fillCount);
    if(!forPick){
      gl.disable(gl.POLYGON_OFFSET_FILL);
      if(aNormal>=0){ gl.disableVertexAttribArray(aNormal); gl.vertexAttrib3f(aNormal,0,1,0); }
      if(aId>=0){ gl.disableVertexAttribArray(aId); gl.vertexAttrib3f(aId,0,0,0); }
      attr(aPos,bWpos); attr(aColor,bWcol);
      gl.uniform1i(uMode,2);
      gl.drawArrays(gl.LINES,0,wireCount);
    } else gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  }
  function pick(px,py){ draw(true); var b=new Uint8Array(4);
    gl.bindFramebuffer(gl.FRAMEBUFFER,pickFB); gl.readPixels(px,vh-py,1,1,gl.RGBA,gl.UNSIGNED_BYTE,b);
    gl.bindFramebuffer(gl.FRAMEBUFFER,null); var id=b[0]; return (id>=1&&id<=N)?id-1:-1; }

  function fmt(s){ return (s>=0?'+':'')+s.toFixed(1); }
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
  function showTip(i,cx,cy){ var a=AXES[i], head, cls='';
    // Header says which pole it leans toward and by how much, as one phrase, not both names.
    if(a.s===null||a.s===undefined) head='No reading';
    else if(a.s===0) head='Leans neither way';
    else if(a.s>0){ head='Leans '+a.p+' '+fmt(a.s); cls=' pos'; }
    else { head='Leans '+a.n+' '+fmt(a.s); cls=' neg'; }
    tip.innerHTML='<b class="th'+cls+'">'+esc(head)+'</b><br><span class="tp">'+esc(a.t)+'</span>';
    tip.style.opacity='1'; var tw=tip.offsetWidth, th=tip.offsetHeight;
    tip.style.left=Math.max(6,Math.min(cx+14, host.clientWidth-tw-6))+'px';
    tip.style.top=Math.max(6,Math.min(cy+14, host.clientHeight-th-6))+'px'; }
  function hideTip(){ tip.style.opacity='0'; hovered=-1; }

  function loc(e){ var r=canvas.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top,w:r.width,h:r.height}; }
  host.addEventListener('pointerenter',function(){ inside=true; });
  host.addEventListener('pointerleave',function(){ inside=false; dragging=false; hideTip(); });
  canvas.addEventListener('pointerdown',function(e){ dragging=true; done=true; lastX=e.clientX; hideTip();
    try{canvas.setPointerCapture(e.pointerId);}catch(_){} });
  canvas.addEventListener('pointerup',function(e){ dragging=false; try{canvas.releasePointerCapture(e.pointerId);}catch(_){} });
  canvas.addEventListener('pointermove',function(e){
    if(dragging){ ry+=(e.clientX-lastX)*0.01; lastX=e.clientX; return; }
    var p=loc(e), i=pick(Math.round(p.x/p.w*vw), Math.round(p.y/p.h*vh));
    if(i>=0){ hovered=i; showTip(i,p.x,p.y); } else hideTip(); });

  // One 50%-faster revolution from the aligned orientation, then stop aligned so the tips line
  // up with the card bars. Dragging cancels the intro; reduced-motion skips it and rests aligned.
  var last=0, TAU=Math.PI*2, ALIGN=0, spun=0, done=false;
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches){ ry=ALIGN; done=true; }
  function frame(ts){ if(!last) last=ts; var dt=Math.min((ts-last)/1000,0.05); last=ts;
    if(!done&&!dragging){ var step=dt*1.5; ry+=step; spun+=step; if(spun>=TAU){ ry=ALIGN; done=true; } }
    draw(false); requestAnimationFrame(frame); }
  if(window.ResizeObserver){ var ro=new ResizeObserver(function(){ resize(); });
    var m=document.querySelector('.col-main'); if(m) ro.observe(m); }
  window.addEventListener('resize',function(){ resize(); });
  window.addEventListener('load',function(){ resize(); });
  resize(); draw(false); requestAnimationFrame(frame);
})();"""


# Opens a card's detail dialog on button click and closes it on a backdrop click. Native
# <dialog> handles Esc and the form-method close button, so this is all the script modals
# need. Delegated from the document, so it covers every card with one listener.
_MODAL_JS = (
    "(function(){document.addEventListener('click',function(e){"
    "var o=e.target.closest('[data-dialog]');"
    "if(o){var d=document.getElementById(o.getAttribute('data-dialog'));"
    "if(d&&d.showModal&&!d.open)d.showModal();return;}"
    "if(e.target.tagName==='DIALOG')e.target.close();});})();"
)


def _hero_data(profile: Profile) -> str:
    """The per-axis payload the tower reads, as safe-to-embed JSON. Keys are terse (the mesh
    builder is the only reader): title, signed score (null when nothing resolved), scale,
    negative/positive pole labels. Deterministic: fixed key order, rounded floats, and ``<``
    escaped to ``\\u003c`` so a title can never break out of the surrounding <script>."""
    data = [
        {
            "t": ax.title,
            "s": None if ax.score is None else round(ax.score, 3),
            "sc": ax.scale,
            "n": _humanize(ax.poles.negative),
            "p": _humanize(ax.poles.positive),
        }
        for ax in profile.axes
    ]
    return json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")


def _hero_html(profile: Profile) -> str:
    """The rotating profile tower: a hero visual above the axis cards. Empty when there are no
    axes to plot, so the page degrades to just the cards."""
    if not profile.axes:
        return ""
    js = _HERO_JS.replace("/*__AXES__*/", _hero_data(profile))
    return (
        '  <section class="hero3d" id="atlas-hero">\n'
        "    <canvas></canvas>\n"
        '    <div class="tip" role="status"></div>\n'
        '    <div class="fallback">A low-poly shape of the profile: a tip points out for each '
        "axis in its lean direction, its length the score.</div>\n"
        "  </section>\n"
        f"  <script>{js}</script>"
    )


# GitHub mark, inlined so the report stays self-contained (no external asset).
_GH_MARK = (
    "<svg class='gh' viewBox='0 0 16 16' width='15' height='15' fill='currentColor' aria-hidden='true'>"
    "<path d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49"
    "-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82"
    ".72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08"
    "-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82"
    " 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48"
    " 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z'></path></svg>"
)


# External-link glyph, appended to project links that open in a new tab.
# The 2D brand crystal (matches the dashboard). Theme-aware via the CSS pole vars.
_CRYSTAL_MARK = (
    "<svg class='mark' viewBox='0 0 30 31' aria-hidden='true'>"
    "<polygon points='15,1 4,11 15,11' fill='var(--neg)'/>"
    "<polygon points='15,1 26,11 15,11' fill='var(--pos)'/>"
    "<polygon points='4,11 15,11 15,30' fill='var(--neg)' opacity='.8'/>"
    "<polygon points='26,11 15,11 15,30' fill='var(--pos)' opacity='.8'/>"
    "<polygon points='15,1 4,11 15,30 26,11' fill='none' stroke='var(--accent)' stroke-width='1' opacity='.55'/>"
    "</svg>"
)


def _github_slug(url: str | None) -> tuple[str, str] | None:
    if not url or "github.com" not in url:
        return None
    tail = url.split("github.com", 1)[1].lstrip(":/")
    if tail.endswith(".git"):
        tail = tail[:-4]
    parts = [p for p in tail.rstrip("/").split("/") if p]
    return (parts[0], parts[1]) if len(parts) >= 2 else None


def _project_html(url: str | None, name: str) -> str:
    """The single project-identity visual. GitHub origin -> mark + owner/repo (new tab);
    other http(s) origin -> a plain link; no upstream at all -> just the project name."""
    slug = _github_slug(url) if url else None
    if slug:
        owner, repo = slug
        href = f"https://github.com/{owner}/{repo}"
        return (
            f'<div class="project"><a href="{_html_escape(href)}" target="_blank" rel="noopener" '
            f'title="Open {_html_escape(owner)}/{_html_escape(repo)} on GitHub" '
            f'aria-label="Open {_html_escape(owner)}/{_html_escape(repo)} on GitHub, opens in a new tab">'
            f'{_GH_MARK}<span>{_html_escape(owner)}/{_html_escape(repo)}</span></a></div>'
        )
    if url:
        clean = url[:-4] if url.endswith(".git") else url
        if clean.startswith("http"):
            label = clean.split("://", 1)[-1]
            return (
                f'<div class="project"><a href="{_html_escape(clean)}" target="_blank" rel="noopener" '
                f'aria-label="Open {_html_escape(label)}, opens in a new tab">'
                f'{_html_escape(label)}</a></div>'
            )
    return f'<div class="project"><span class="pname">{_html_escape(name)}</span></div>'


def render_html(profile: Profile) -> str:
    """Render a Profile to a self-contained HTML page.

    A pure function of the Profile: byte-identical for identical input, with no
    timestamps, random ids, or locale-dependent formatting, mirroring the purity of
    ``render_text`` and ``render_markdown``.

    Unlike the terminal renderer, HTML always draws a bar when a score exists: a
    thinly-covered axis is faded and tagged ("low evidence") rather than hidden,
    because HTML can show low confidence where a terminal cannot. A bar is omitted
    only when nothing resolved at all (``score is None``), which reads as "nothing
    could be read". The user-facing language is plain: the two indicator kinds show
    as "detected" and "judged", and coverage reads as "evidence".

    Beside the cards, in a right rail the same height as them, sits an interactive
    WebGL "profile tower" (see ``_HERO_JS``) that measures the cards and lines its
    bands up with them; a tiny delegated handler (see ``_MODAL_JS``) opens the per-card
    detail dialogs. Both scripts are inline and self-contained, so the page still needs
    no external resources, and the geometry varies only in the injected axis data, so
    the emitted bytes stay a deterministic function of the Profile.
    """
    scale = profile.axes[0].scale if profile.axes else 10.0
    axes_html = "\n".join(_html_axis(ax, i) for i, ax in enumerate(profile.axes))
    project = _project_html(profile.target_url, _display_name(profile.target))
    stamps = (
        f"rubric {_html_escape(profile.rubric_version)} · "
        f"engine {_html_escape(profile.engine_version)} · "
        f"sha {_html_escape((profile.target_sha or 'unknown')[:12])}"
    )
    hint = _skill_hint(profile)
    hint_html = f'\n  <p class="footer-hint">{_html_escape(hint)}</p>' if hint else ""
    header = f"""  <header>
    <div class="brand"><a class="home" href="{_HOME_URL}" title="Back to the Explorer" aria-label="Back to the Explorer, browse all profiles">{_CRYSTAL_MARK}<span class="word">Agentic Atlas</span></a><span class="ptitle">Profile</span></div>
    {project}
    <div class="stamps">{stamps}</div>
    <p class="note">These results are non-judgmental measurements against the <a href="{_RUBRIC_URL}" target="_blank" rel="noopener">rubric</a>, not a grade, a rank, or a winner, because there is no single best practice for how you or your projects work. Sometimes you just want to know what fits a large legacy or brownfield codebase versus what you would reach for on a fresh startup idea.</p>
    <p class="aside">Scale &plusmn;{scale:g} per axis. A score near 0 leans neither way, which can mean a tool serves both ends well or neither; open an axis to see what the poles mean. A bar's evidence meter shows how much of the intended evidence was found; a faded bar rests on thin evidence. Each position draws on signals the engine <strong>detected</strong> from the repo and ones a reviewer <strong>judged</strong> by reading it.</p>
    <div class="legend">
      <span><span class="swatch" style="background:var(--neg)"></span><span class="swatch" style="background:var(--pos)"></span>the bar leans toward the end it favors</span>
      <span><span class="swatch" style="background:var(--cov-good)"></span>evidence found</span>
      <span>open an axis for its poles and signals</span>
    </div>
  </header>"""
    hero = _hero_html(profile)
    cards = f"{axes_html}{hint_html}"
    if hero:
        # The header ("top data") spans the top; below it a centered block pairs the small
        # tower with the cards. Both columns start at the same top (no header inside them), so
        # the tower spans exactly the cards and its measured bands line up with them.
        body = (
            '<div class="wrap wide">\n'
            f"{header}\n"
            '  <div class="layout">\n'
            f'    <aside class="col-rail">\n{hero}\n    </aside>\n'
            f'    <div class="col-main">\n{cards}\n    </div>\n'
            "  </div>\n</div>"
        )
    else:
        body = f'<div class="wrap">\n{header}\n{cards}\n</div>'
    if profile.axes:
        # One delegated listener drives every card's detail dialogs.
        body += f"\n<script>{_MODAL_JS}</script>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Atlas Profile: {_html_escape(_display_name(profile.target))}</title>
<style>{_HTML_CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""
