"""Resolve judged indicators from answers supplied by an external agent.

A judged indicator is a narrow question about the target that measurement cannot
answer: it needs the repository read and interpreted, then reduced to one bounded answer
backed by a quote taken verbatim from one named file in the target. The engine never calls
a model and needs no API key. Answering is done outside the engine (by the agentic-toolkit
skill, whose host agent is already an LLM with repo access); the answers are handed back as
data and this module's job is to *validate* them, deterministically.

``resolve_judged`` mirrors ``evidence.resolve_detected``: both take an indicator and a
target and return an ``IndicatorResult``, one computing from the repository, one
validating supplied data. With no answer supplied, a judged indicator is unresolved,
which is the detected-only profile a bare run produces.

Validation is what makes a judged answer defensible, and it is identical regardless of
who produced the answer: the answer must be one of the indicator's declared values, the
cited path must be a corpus text file that the rubric's ``evidence_exclude`` globs admit, and
the quote must be found verbatim inside that file. The exclusions keep release history,
tests, examples, a tool's own working folders, and its repository process files from standing
in for the method the tool ships. A missing or failing answer leaves the indicator unresolved, so the engine never
records a guess or an ungrounded citation. Validation stops fabrication; it does not stop a
real-but-cherry-picked quote, so the answer file's provenance (stamped as ``source``) and
review are the remaining line of defense.
"""

from __future__ import annotations

import posixpath
import re

from .evidence import TEXT_SUFFIXES, Target, glob_match
from .models import Indicator, IndicatorKind, IndicatorResult, Rubric

# A quote must be at least this many characters to count as evidence, so a one-word or
# punctuation "match" cannot pass the verbatim check.
MIN_QUOTE_CHARS = 12

# The answering contract printed on every `questions` payload, so a caller that is not the
# run skill gets the same rules. Built from the constants validation uses, so it cannot drift.
ANSWER_INSTRUCTIONS = (
    "Answer each question from the target repository only. Return an object keyed by "
    'indicator id: {"answer": <one allowed value>, "evidence": <a quote copied verbatim '
    'from the target>, "path": <the file the quote is in, relative to the target root>}. '
    "Feed the result back with `agentic-atlas profile --answers`. The quote is checked "
    "against that one file only. The file must have one of these extensions: "
    f"{', '.join(TEXT_SUFFIXES)}. Source files such as .py, .js, .ts, or .sh are not in the "
    "corpus and will not match. The path must not match any glob in `evidence_exclude`: "
    "release history, tests and fixtures, examples, the tool's own working folders, and its "
    "contributor guides and CI describe something other than the method the tool ships, so "
    "they are not evidence. "
    f"The quote must be at least {MIN_QUOTE_CHARS} characters. Matching collapses whitespace "
    "and ignores case. A quote that is present in an admissible file but does not represent "
    "the method will still be accepted."
)


def judged_questions(rubric: Rubric) -> list[dict]:
    """The worklist an external answerer fills in: one entry per judged indicator."""
    return [
        {
            "id": ind.id,
            "axis": axis.id,
            "question": ind.question,
            "answers": sorted(ind.answers),
        }
        for axis in rubric.axes
        for ind in axis.indicators
        if ind.kind is IndicatorKind.JUDGED
    ]


def judged_ids(rubric: Rubric) -> set[str]:
    """The ids of every judged indicator in ``rubric``, the keys an answers file may use."""
    return {q["id"] for q in judged_questions(rubric)}


def check_answer_ids(rubric: Rubric, answers: dict[str, dict] | None) -> None:
    """Reject answers keyed by an id that is not a judged indicator in ``rubric``.

    An unknown id would otherwise be ignored and its indicator left unresolved, so a typo
    or an answers file written for another rubric version would quietly lower coverage."""
    unknown = sorted(set(answers or {}) - judged_ids(rubric))
    if unknown:
        raise ValueError(
            f"answers name ids that are not judged indicators in rubric "
            f"{rubric.rubric_version}: {', '.join(unknown)}"
        )


def excluded_by(path: str, exclude: tuple[str, ...]) -> str | None:
    """The first ``exclude`` glob that ``path`` matches, or None when the path is admissible."""
    return next((g for g in exclude if glob_match(path, g)), None)


def _normalize(text: str) -> str:
    """Collapse whitespace and casefold, so a verbatim check tolerates reflow only."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def _quote_found(quote: str, text: str) -> bool:
    stripped = quote.strip()
    if len(stripped) < MIN_QUOTE_CHARS:
        return False
    return _normalize(stripped) in _normalize(text)


def _normalize_path(path: str) -> str | None:
    """The cited path in the POSIX, root-relative form ``Target.text_files`` keys by, or None
    when it points outside the target (absolute, or climbing above the root with ``..``)."""
    norm = posixpath.normpath(path.strip().replace("\\", "/"))
    if norm == ".." or norm.startswith(("/", "../")):
        return None
    return norm


def _where_else(quote: str, target: Target, exclude: tuple[str, ...], cited: str) -> str:
    """A hint naming where else the quote appears, so a retry can cite the right file.

    Only ever appended to a rejection: it locates the quote, it never resolves the answer."""
    found = [
        p for p, text in target.text_files().items() if p != cited and _quote_found(quote, text)
    ]
    admissible = [p for p in found if excluded_by(p, exclude) is None]
    if admissible:
        return f"; the quote appears in {admissible[0]!r}"
    if found:
        return f"; the quote appears only in excluded files: {', '.join(map(repr, found[:3]))}"
    return ""


def resolve_judged(
    indicator: Indicator,
    target: Target,
    answers: dict[str, dict] | None,
    source: str = "supplied",
    *,
    exclude: tuple[str, ...] = (),
) -> IndicatorResult:
    """Validate a supplied answer for one judged indicator and score it, or leave it
    unresolved. ``answers`` maps indicator id to ``{"answer", "evidence", "path"}``;
    ``exclude`` is the rubric's ``evidence_exclude`` globs."""

    def unresolved(reason: str) -> IndicatorResult:
        return IndicatorResult.unresolved(indicator, IndicatorKind.JUDGED, reason)

    entry = (answers or {}).get(indicator.id)
    if not isinstance(entry, dict):
        return unresolved("no answer supplied")
    answer = entry.get("answer")
    if answer not in indicator.answers:
        return unresolved(f"answer {answer!r} is not one of {sorted(indicator.answers)}")
    evidence = entry.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return unresolved("no evidence quote supplied")
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return unresolved("no evidence path supplied")
    path = _normalize_path(raw_path)
    if path is None:
        return unresolved(f"evidence path {raw_path!r} is outside the target")
    glob = excluded_by(path, exclude)
    if glob is not None:
        return unresolved(
            f"evidence path {path!r} is excluded as evidence (matches {glob!r})"
            + _where_else(evidence, target, exclude, path)
        )
    text = target.text_files().get(path)
    if text is None:
        why = (
            "is not in the text corpus (wrong extension, ignored directory, or too large)"
            if (target.root / path).is_file()
            else "does not exist in the target"
        )
        return unresolved(
            f"evidence path {path!r} {why}" + _where_else(evidence, target, exclude, path)
        )
    if not _quote_found(evidence, text):
        return unresolved(
            f"evidence quote was not found verbatim in {path!r}"
            + _where_else(evidence, target, exclude, path)
        )
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.JUDGED,
        weight=indicator.weight,
        value=indicator.answers[answer],
        resolved=True,
        answer=answer,
        evidence=evidence,
        source=source,
        path=path,
    )
