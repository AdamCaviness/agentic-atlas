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
  .wrap.wide{max-width:1180px}
  .layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:30px;align-items:start}
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
  .stamps{font-family:var(--mono);font-size:.82rem;color:var(--muted);margin:0 0 2px}
  .note{color:var(--fg);font-size:.95rem;margin:10px 0 2px}
  .note a{color:var(--accent);text-decoration:underline}
  .aside{color:var(--muted);font-size:.82rem;margin:2px 0 0}
  .legend{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0 26px;padding:12px 14px;background:var(--card);
          border:1px solid var(--line);border-radius:10px;font-size:.82rem;color:var(--muted)}
  .legend .swatch{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:6px}
  .axis{border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:0 0 14px;background:var(--card)}
  .axis-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
  .axis-title{font-weight:600;font-size:1.02rem}
  .score{font-family:var(--mono);font-weight:700;font-size:1.05rem;white-space:nowrap}
  .score.neg{color:var(--neg)}.score.pos{color:var(--pos)}
  .score.none{color:var(--faint);font-weight:500;font-style:italic;font-size:.9rem}
  .score.zero{color:var(--faint)}
  .prov-tag{font-family:var(--sans);font-weight:500;font-size:.66rem;text-transform:uppercase;letter-spacing:.04em;
            color:var(--cov-low);border:1px solid var(--cov-low);border-radius:4px;padding:1px 5px;margin-left:8px;vertical-align:1px}
  .bar-row{display:grid;grid-template-columns:8.5rem 1fr 8.5rem;align-items:center;gap:12px;margin:14px 0 6px}
  .pole{font-size:.82rem;color:var(--muted)}
  .pole.left{text-align:right}.pole.right{text-align:left}
  .track{position:relative;height:26px;background:var(--track);border-radius:6px}
  .track .center{position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:var(--faint);transform:translateX(-1px)}
  .fill{position:absolute;top:3px;bottom:3px;border-radius:4px}
  .fill.neg{right:50%;background:var(--neg)}
  .fill.pos{left:50%;background:var(--pos)}
  .fill.prov{opacity:.4;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px);
             outline:1px dashed var(--faint);outline-offset:-1px}
  .track.empty{background:repeating-linear-gradient(45deg,transparent,transparent 6px,var(--track) 6px,var(--track) 12px);border:1px dashed var(--line)}
  .track.empty .center{background:var(--line)}
  .ni{display:inline-block;font-size:.8rem;color:var(--faint);position:absolute;left:50%;top:50%;
      transform:translate(-50%,-50%);background:var(--card);padding:0 8px;white-space:nowrap}
  .cov{display:flex;align-items:center;gap:10px;margin-top:8px;font-size:.78rem}
  .cov-meter{position:relative;width:120px;height:6px;background:var(--track);border-radius:3px;overflow:hidden;flex:none}
  .cov-fill{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
  .cov-floor{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:var(--faint)}
  .cov-good{background:var(--cov-good)}.cov-mid{background:var(--cov-mid)}.cov-low{background:var(--cov-low)}
  .cov-text{color:var(--muted);font-family:var(--mono)}
  .axis-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;border-top:1px solid var(--line);padding-top:14px}
  .mbtn{font:inherit;font-size:.8rem;color:var(--fg);background:var(--bg);border:1px solid var(--line);
        border-radius:8px;padding:6px 12px;cursor:pointer;transition:border-color .12s,color .12s}
  .mbtn:hover{border-color:var(--accent);color:var(--accent)}
  .mbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
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
  .hero3d .tip .ts{font-family:var(--mono);color:var(--muted)}
  .hero3d .tip .tp{color:var(--muted);font-size:.72rem}
  .hero3d .hint{position:absolute;left:0;right:0;top:10px;text-align:center;font-size:.72rem;
                color:var(--faint);pointer-events:none}
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
    neg_label = _html_escape(_humanize(ax.poles.negative))
    pos_label = _html_escape(_humanize(ax.poles.positive))

    # Details live in modal dialogs, not inline expanders, so every card keeps a fixed
    # height no matter what is opened. That fixed height is what lets the tower's bands line
    # up with the cards: opening a dialog never reflows the column. Dialogs close natively
    # (the form-method button, plus Esc); only opening and backdrop-close need _MODAL_JS.
    buttons = []
    dialogs = []
    if ax.explain.negative or ax.explain.positive:
        buttons.append(
            f'<button type="button" class="mbtn" data-dialog="poles-{idx}">what the poles mean</button>'
        )
        dialogs.append(
            f'    <dialog id="poles-{idx}" class="modal">\n'
            '      <form method="dialog"><button class="modal-x" aria-label="Close">&times;</button></form>\n'
            f'      <h3 class="modal-title">{title}</h3>\n'
            '      <p class="modal-sub">what the poles mean</p>\n'
            '      <dl class="poles">\n'
            f"        <dt>{neg_label}</dt><dd>{_html_escape(ax.explain.negative)}</dd>\n"
            f"        <dt>{pos_label}</dt><dd>{_html_escape(ax.explain.positive)}</dd>\n"
            f'        <dt class="mid">near 0</dt><dd class="mid">{_html_escape(_MIDDLE_NOTE)}</dd>\n'
            "      </dl>\n"
            "    </dialog>"
        )
    n_sig = len(ax.indicators)
    buttons.append(
        f'<button type="button" class="mbtn" data-dialog="signals-{idx}">show the {n_sig} signals behind this</button>'
    )
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
    actions = '    <div class="axis-actions">' + "".join(buttons) + "</div>"
    dialogs_html = "\n".join(dialogs)

    return (
        '  <section class="axis">\n'
        f'    <div class="axis-head"><span class="axis-title">{title}</span>{score_html}</div>\n'
        '    <div class="bar-row">\n'
        f'      <span class="pole left">{neg_label}</span>\n'
        f"      {bar}\n"
        f'      <span class="pole right">{pos_label}</span>\n'
        "    </div>\n"
        '    <div class="cov">\n'
        f'      <div class="cov-meter"><div class="cov-fill {_coverage_class(ax.coverage)}" style="width:{cov_pct}%"></div><div class="cov-floor"></div></div>\n'
        f'      <span class="cov-text">{_html_escape(cov_txt)}</span>\n'
        "    </div>\n"
        f"{actions}\n"
        f"{dialogs_html}\n"
        "  </section>"
    )


# One continuous wireframe tube for the whole profile, in the rail beside the cards and the
# same height as them. Each axis's band is a straight vertical segment at its own signed
# offset, so a zero or no-reading axis sits dead centered and a neighbor's lean never bleeds
# in; the tube bends only in the short, neutrally colored necks that bridge the gaps between
# cards. Band heights are measured from the DOM cards, so segment i lines up with card i, and
# the orthographic, yaw-only view keeps that vertical alignment while it spins. A triangle
# wireframe over a quiet occluder body gives the unfinished low-poly look; cyan leans toward
# the negative pole, magenta toward the positive. It auto-rotates, pauses on hover, drags to
# spin either way, and picks the band under the cursor (an offscreen id pass) to name the axis.
# Raw WebGL, no libraries, self-contained for file:// use. Axis data is injected as JSON at
# ``/*__AXES__*/`` so the emitted bytes stay a deterministic function of the Profile.
_HERO_JS = r"""(function(){
  var host=document.getElementById('atlas-hero');
  if(!host) return;
  var canvas=host.querySelector('canvas');
  var tip=host.querySelector('.tip');
  var AXES=/*__AXES__*/;
  function fail(){ canvas.style.display='none';
    var h=host.querySelector('.hint'); if(h) h.style.display='none';
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
      CARD=hex(css('--card')), FG=hex(css('--fg')), FILL=mix(CARD,FG,0.14), NECK=FAINT;

  // shaders: flat color, plus an id pass for hover picking (no lighting needed)
  function sh(t,s){ var o=gl.createShader(t); gl.shaderSource(o,s); gl.compileShader(o);
    if(!gl.getShaderParameter(o,gl.COMPILE_STATUS)) console.log(gl.getShaderInfoLog(o)); return o; }
  var prog=gl.createProgram();
  gl.attachShader(prog,sh(gl.VERTEX_SHADER,
    'attribute vec3 aPos;attribute vec3 aColor;attribute vec3 aId;uniform mat4 uMVP;'+
    'varying vec3 vC;varying vec3 vId;void main(){vC=aColor;vId=aId;gl_Position=uMVP*vec4(aPos,1.0);}'));
  gl.attachShader(prog,sh(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump int;varying vec3 vC;varying vec3 vId;uniform int uMode;'+
    'void main(){gl_FragColor=(uMode==1)?vec4(vId,1.0):vec4(vC,1.0);}'));
  gl.linkProgram(prog); gl.useProgram(prog);
  var aPos=gl.getAttribLocation(prog,'aPos'), aColor=gl.getAttribLocation(prog,'aColor'),
      aId=gl.getAttribLocation(prog,'aId'), uMVP=gl.getUniformLocation(prog,'uMVP'),
      uMode=gl.getUniformLocation(prog,'uMode');
  function up(buf,data){ if(!buf) buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STATIC_DRAW); return buf; }
  function attr(loc,b){ if(loc<0)return; gl.enableVertexAttribArray(loc);
    gl.bindBuffer(gl.ARRAY_BUFFER,b); gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0); }

  // matrices (column-major); orthographic so vertical position never foreshortens
  function ident(){ return new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]); }
  function mul(a,b){ var o=new Float32Array(16);
    for(var c=0;c<4;c++)for(var r=0;r<4;r++){var s=0;for(var k=0;k<4;k++)s+=a[k*4+r]*b[c*4+k];o[c*4+r]=s;} return o; }
  function rotY(r){ var c=Math.cos(r),s=Math.sin(r),o=ident(); o[0]=c;o[2]=-s;o[8]=s;o[10]=c; return o; }
  function ortho(hw,hh,nf){ var o=ident(); o[0]=1/hw;o[5]=1/hh;o[10]=-1/nf; return o; }

  // state
  var K=6, TAU=6.2831853, N=AXES.length;
  var ry=0.5, inside=false, dragging=false, lastX=0, hovered=-1;
  var proj=ident(), vw=1, vh=1, pickFB=null, pickTex=null, pickDepth=null;
  var bPos=null,bCol=null,bId=null,bWpos=null,bWcol=null, fillCount=0, wireCount=0, halfW=1, halfH=1;

  // geometry: ONE tube whose bands sit exactly beside their cards
  function buildGeom(){
    var narrow=window.matchMedia('(max-width:880px)').matches;
    var cards=document.querySelectorAll('.col-main .axis');
    var tops=[], bots=[], hostH;
    if(!narrow && cards.length===N){
      var main=document.querySelector('.col-main');
      hostH=main.offsetHeight; host.style.height=hostH+'px';
      var refTop=host.getBoundingClientRect().top;
      for(var c=0;c<N;c++){ var r=cards[c].getBoundingClientRect(); tops.push(r.top-refTop); bots.push(r.bottom-refTop); }
    } else {
      host.style.height=''; hostH=host.clientHeight;
      var pad=hostH*0.07, bh=(hostH-2*pad)/N;
      for(var c2=0;c2<N;c2++){ tops.push(pad+c2*bh+bh*0.12); bots.push(pad+(c2+1)*bh-bh*0.12); }
    }
    var W=host.clientWidth; halfW=W/2; halfH=hostH/2;
    var R=Math.max(12, Math.min(W*0.15, hostH/N*0.34)), MAXOFF=W*0.30;
    function xoff(i){ var a=AXES[i], has=(a.s!==null&&a.s!==undefined);
      var f=has?Math.max(-1,Math.min(1,a.s/a.sc)):0; return f*MAXOFF; }
    function lean(i){ var a=AXES[i], has=(a.s!==null&&a.s!==undefined);
      var f=has?Math.max(-1,Math.min(1,a.s/a.sc)):0;
      return has?mix(FAINT, f<0?NEG:POS, 0.32+0.68*Math.min(Math.abs(f),1)):FAINT; }
    function wy(py){ return hostH/2-py; }
    function ring(x,py){ var o=[],cy=wy(py); for(var j=0;j<K;j++){var t=j/K*TAU;o.push([x+R*Math.cos(t),cy,R*Math.sin(t)]);} o.cx=x; o.cy=cy; return o; }

    var pos=[],col=[],ids=[],wpos=[],wcol=[];
    function tri(A,B,C,c,id){ var P=[A,B,C]; for(var k=0;k<3;k++){pos.push(P[k][0],P[k][1],P[k][2]);col.push(c[0],c[1],c[2]);ids.push(id[0],id[1],id[2]);} }
    function wl(a,b,c){ wpos.push(a[0],a[1],a[2],b[0],b[1],b[2]); wcol.push(c[0],c[1],c[2],c[0],c[1],c[2]); }
    function connect(rA,rB,wc,id){ for(var j=0;j<K;j++){ var j1=(j+1)%K,a0=rA[j],a1=rA[j1],b0=rB[j],b1=rB[j1];
      tri(a0,b0,b1,FILL,id); tri(a0,b1,a1,FILL,id); wl(a0,b0,wc); wl(a0,b1,wc); } }
    function wring(rg,c){ for(var j=0;j<K;j++) wl(rg[j],rg[(j+1)%K],c); }

    var prevBot=null;
    for(var i=0;i<N;i++){
      var x=xoff(i), lc=lean(i), id=[((i+1)&255)/255,0,0];
      var rt=ring(x,tops[i]), rb=ring(x,bots[i]);
      if(prevBot) connect(prevBot,rt,NECK,id);   // neck across the gap (neutral joint)
      connect(rt,rb,lc,id);                        // the card's own straight band
      wring(rt,lc); wring(rb,lc);
      prevBot=rb;
    }
    (function(){ var rg=ring(xoff(0),tops[0]); for(var j=0;j<K;j++) tri([rg.cx,rg.cy,0],rg[(j+1)%K],rg[j],FILL,[1/255,0,0]); })();
    (function(){ var rg=ring(xoff(N-1),bots[N-1]); for(var j=0;j<K;j++) tri([rg.cx,rg.cy,0],rg[j],rg[(j+1)%K],FILL,[(N&255)/255,0,0]); })();

    fillCount=pos.length/3; wireCount=wpos.length/3;
    bPos=up(bPos,pos); bCol=up(bCol,col); bId=up(bId,ids); bWpos=up(bWpos,wpos); bWcol=up(bWcol,wcol);
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
    attr(aPos,bPos); attr(aColor,bCol); attr(aId,bId);
    gl.uniform1i(uMode, forPick?1:0);
    if(!forPick){ gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(1.1,1.1); }
    gl.drawArrays(gl.TRIANGLES,0,fillCount);
    if(!forPick){
      gl.disable(gl.POLYGON_OFFSET_FILL);
      if(aId>=0){ gl.disableVertexAttribArray(aId); gl.vertexAttrib3f(aId,0,0,0); }
      attr(aPos,bWpos); attr(aColor,bWcol);
      gl.drawArrays(gl.LINES,0,wireCount);
    } else gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  }
  function pick(px,py){ draw(true); var b=new Uint8Array(4);
    gl.bindFramebuffer(gl.FRAMEBUFFER,pickFB); gl.readPixels(px,vh-py,1,1,gl.RGBA,gl.UNSIGNED_BYTE,b);
    gl.bindFramebuffer(gl.FRAMEBUFFER,null); var id=b[0]; return (id>=1&&id<=N)?id-1:-1; }

  function fmt(s){ return (s>=0?'+':'')+s.toFixed(1); }
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
  function showTip(i,cx,cy){ var a=AXES[i], sc=(a.s===null||a.s===undefined)?'no reading':fmt(a.s);
    tip.innerHTML='<b>'+esc(a.t)+'</b> <span class="ts">'+esc(sc)+'</span><br><span class="tp">'+esc(a.n)+' ↔ '+esc(a.p)+'</span>';
    tip.style.opacity='1'; var tw=tip.offsetWidth, th=tip.offsetHeight;
    tip.style.left=Math.max(6,Math.min(cx+14, host.clientWidth-tw-6))+'px';
    tip.style.top=Math.max(6,Math.min(cy+14, host.clientHeight-th-6))+'px'; }
  function hideTip(){ tip.style.opacity='0'; hovered=-1; }

  function loc(e){ var r=canvas.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top,w:r.width,h:r.height}; }
  host.addEventListener('pointerenter',function(){ inside=true; });
  host.addEventListener('pointerleave',function(){ inside=false; dragging=false; hideTip(); });
  canvas.addEventListener('pointerdown',function(e){ dragging=true; lastX=e.clientX; hideTip();
    try{canvas.setPointerCapture(e.pointerId);}catch(_){} });
  canvas.addEventListener('pointerup',function(e){ dragging=false; try{canvas.releasePointerCapture(e.pointerId);}catch(_){} });
  canvas.addEventListener('pointermove',function(e){
    if(dragging){ ry+=(e.clientX-lastX)*0.01; lastX=e.clientX; return; }
    var p=loc(e), i=pick(Math.round(p.x/p.w*vw), Math.round(p.y/p.h*vh));
    if(i>=0){ hovered=i; showTip(i,p.x,p.y); } else hideTip(); });

  var last=0;
  function frame(ts){ if(!last) last=ts; var dt=Math.min((ts-last)/1000,0.05); last=ts;
    if(!inside&&!dragging) ry+=dt*0.5; draw(false); requestAnimationFrame(frame); }
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
        '    <div class="hint">drag to spin · hover the shape to read an axis</div>\n'
        '    <div class="fallback">One wireframe tube for the whole profile: it bends toward '
        "each axis's pole by that axis's score.</div>\n"
        "  </section>\n"
        f"  <script>{js}</script>"
    )


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
    name = _html_escape(_display_name(profile.target))
    target_full = _html_escape(profile.target)
    stamps = (
        f"rubric {_html_escape(profile.rubric_version)} · "
        f"engine {_html_escape(profile.engine_version)} · "
        f"sha {_html_escape((profile.target_sha or 'unknown')[:12])}"
    )
    hint = _skill_hint(profile)
    hint_html = f'\n  <p class="footer-hint">{_html_escape(hint)}</p>' if hint else ""
    header = f"""  <header>
    <h1>Agentic Atlas Profile</h1>
    <span class="target-pill" title="{target_full}">{name}</span>
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
    main = f"{header}\n{axes_html}{hint_html}"
    if hero:
        # Tower in the right rail, cards (and the header) in the left column. Both columns
        # start at the same top, so the tower spans the header-plus-cards height and its
        # measured bands line up with the cards. The header shares the left column, so its
        # width still tracks the cards below it.
        body = (
            '<div class="wrap wide">\n  <div class="layout">\n'
            f'    <aside class="col-rail">\n{hero}\n    </aside>\n'
            f'    <div class="col-main">\n{main}\n    </div>\n'
            "  </div>\n</div>"
        )
    else:
        body = f'<div class="wrap">\n{main}\n</div>'
    if profile.axes:
        # One delegated listener drives every card's detail dialogs.
        body += f"\n<script>{_MODAL_JS}</script>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Atlas Profile: {_html_escape(profile.target)}</title>
<style>{_HTML_CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""
