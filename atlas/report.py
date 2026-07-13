"""Render a Profile (or several) to a human-readable report.

Renders a signed bar per axis so the sign and magnitude read at a glance. There is
no total row, by design, a profile is a position not a grade.
"""

from __future__ import annotations

from .models import AxisResult, Profile

_BAR_HALF = 20  # characters on each side of the neutral center


def _bar(score: float | None, scale: float) -> str:
    if score is None:
        return " " * _BAR_HALF + "|" + " " * _BAR_HALF + "  (no data)"
    frac = max(-1.0, min(1.0, score / scale))
    fill = round(abs(frac) * _BAR_HALF)
    if frac < 0:
        left = " " * (_BAR_HALF - fill) + "#" * fill
        right = " " * _BAR_HALF
    else:
        left = " " * _BAR_HALF
        right = "#" * fill + " " * (_BAR_HALF - fill)
    return f"{left}|{right}"


def _axis_lines(ax: AxisResult) -> list[str]:
    score = "n/a" if ax.score is None else f"{ax.score:+.1f}"
    header = f"{ax.title}  [{score} / ±{ax.scale:g}]  coverage {ax.coverage * 100:.0f}%"
    poles = f"  {ax.poles.negative:<20}{_bar(ax.score, ax.scale)}{ax.poles.positive:>20}"
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
        score = "n/a" if ax.score is None else f"{ax.score:+.1f}"
        lines.append(f"## {ax.title}: {score} (±{ax.scale:g})")
        lines.append(
            f"Poles: `{ax.poles.negative}` (-) ↔ `{ax.poles.positive}` (+). "
            f"Coverage {ax.coverage * 100:.0f}%."
        )
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
    return "\n".join(lines)


def render_text(profile: Profile) -> str:
    lines = [
        f"Profile: {profile.target}",
        f"rubric {profile.rubric_version} | engine {profile.engine_version} | "
        f"sha {(profile.target_sha or 'unknown')[:12]}",
        "",
    ]
    for ax in profile.axes:
        lines.extend(_axis_lines(ax))
        lines.append("")
    return "\n".join(lines)
