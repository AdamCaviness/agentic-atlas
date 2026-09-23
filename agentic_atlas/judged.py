"""Resolve judged indicators from answers supplied by an external agent.

A judged indicator is a narrow question about the target that measurement cannot
answer: it needs the repository read and interpreted, then reduced to one bounded answer
backed by a quote taken verbatim from the target. The engine never calls a model and
needs no API key. Answering is done outside the engine (by the agentic-toolkit skill,
whose host agent is already an LLM with repo access); the answers are handed back as data
and this module's job is to *validate* them, deterministically.

``resolve_judged`` mirrors ``evidence.resolve_detected``: both take an indicator and a
target and return an ``IndicatorResult``, one computing from the repository, one
validating supplied data. With no answer supplied, a judged indicator is unresolved,
which is the detected-only profile a bare run produces.

Validation is what makes a judged answer defensible, and it is identical regardless of
who produced the answer: the answer must be one of the indicator's declared values, and
the cited quote must be found verbatim in the target material. A missing or failing answer
leaves the indicator unresolved, so the engine never records a guess or an ungrounded
citation. Validation stops fabrication; it does not stop a real-but-cherry-picked quote,
so the answer file's provenance (stamped as ``source``) and review are the remaining
line of defense.
"""

from __future__ import annotations

import re

from .evidence import TEXT_SUFFIXES, Target
from .models import Indicator, IndicatorKind, IndicatorResult, Rubric

# A quote must be at least this many characters to count as evidence, so a one-word or
# punctuation "match" cannot pass the verbatim check.
MIN_QUOTE_CHARS = 12

# The answering contract printed on every `questions` payload, so a caller that is not the
# run skill gets the same rules. Built from the constants validation uses, so it cannot drift.
ANSWER_INSTRUCTIONS = (
    "Answer each question from the target repository only. Return an object keyed by "
    'indicator id: {"answer": <one allowed value>, "evidence": <a quote copied verbatim '
    "from the target>}. Feed the result back with `agentic-atlas profile --answers`. "
    f"The quote must appear in a file with one of these extensions: {', '.join(TEXT_SUFFIXES)}. "
    "Quotes from source files such as .py, .js, .ts, or .sh are not in the corpus and will "
    f"not match. The quote must be at least {MIN_QUOTE_CHARS} characters. Matching collapses "
    "whitespace and ignores case. A quote that is present in those files but does not "
    "represent the method will still be accepted."
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


def _normalize(text: str) -> str:
    """Collapse whitespace and casefold, so a verbatim check tolerates reflow only."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def _quote_found(quote: str, corpus: str) -> bool:
    stripped = quote.strip()
    if len(stripped) < MIN_QUOTE_CHARS:
        return False
    return _normalize(stripped) in _normalize(corpus)


def resolve_judged(
    indicator: Indicator,
    target: Target,
    answers: dict[str, dict] | None,
    source: str = "supplied",
) -> IndicatorResult:
    """Validate a supplied answer for one judged indicator and score it, or leave it
    unresolved. ``answers`` maps indicator id to ``{"answer": ..., "evidence": ...}``."""
    entry = (answers or {}).get(indicator.id)
    if not isinstance(entry, dict):
        return IndicatorResult.unresolved(indicator, IndicatorKind.JUDGED, "no answer supplied")
    answer = entry.get("answer")
    if answer not in indicator.answers:
        return IndicatorResult.unresolved(
            indicator,
            IndicatorKind.JUDGED,
            f"answer {answer!r} is not one of {sorted(indicator.answers)}",
        )
    evidence = entry.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return IndicatorResult.unresolved(
            indicator, IndicatorKind.JUDGED, "no evidence quote supplied"
        )
    if not _quote_found(evidence, target.text_corpus(lower=False)):
        return IndicatorResult.unresolved(
            indicator,
            IndicatorKind.JUDGED,
            "evidence quote was not found verbatim in the target",
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
    )
