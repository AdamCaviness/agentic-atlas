"""Resolve classified indicators.

A classified indicator requires reading the target and choosing one answer from a
small, defined set. The judge records the chosen answer plus a cited quote, so the
result is auditable regardless of who produced it. Every judge stamps a ``source``
(a model id, or ``"manual"``) onto the result.

Three judges ship:

- ``NoneJudge``: resolves nothing. Classified indicators are marked unresolved and
  excluded from scoring, which yields a fully deterministic, measured-only profile.
- ``ManualJudge``: reads answers a human prepared, keyed by indicator id.
- ``AnthropicJudge``: asks a Claude model to pick an answer and cite evidence.
"""

from __future__ import annotations

from typing import Protocol

from .evidence import Target
from .models import Indicator, IndicatorKind, IndicatorResult


class Judge(Protocol):
    def resolve(self, indicator: Indicator, target: Target) -> IndicatorResult: ...


def _unresolved(indicator: Indicator) -> IndicatorResult:
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.CLASSIFIED,
        weight=indicator.weight,
        value=None,
        resolved=False,
        answer=None,
        evidence=None,
        source=None,
    )


class NoneJudge:
    """Resolves no classified indicators. Produces a measured-only profile."""

    def resolve(self, indicator: Indicator, target: Target) -> IndicatorResult:
        return _unresolved(indicator)


class ManualJudge:
    """Resolve from a prepared mapping of indicator id to answer.

    The mapping values may be either a bare answer key, or a dict of
    ``{answer: <key>, evidence: <quote>}``.
    """

    def __init__(self, answers: dict[str, object]):
        self._answers = answers

    def resolve(self, indicator: Indicator, target: Target) -> IndicatorResult:
        entry = self._answers.get(indicator.id)
        if entry is None:
            return _unresolved(indicator)
        if isinstance(entry, dict):
            answer = entry.get("answer")
            evidence = entry.get("evidence")
        else:
            answer, evidence = str(entry), None
        if answer not in indicator.answers:
            raise ValueError(
                f"answer {answer!r} for indicator {indicator.id} is not one of "
                f"{sorted(indicator.answers)}"
            )
        return IndicatorResult(
            indicator_id=indicator.id,
            kind=IndicatorKind.CLASSIFIED,
            weight=indicator.weight,
            value=indicator.answers[answer],
            resolved=True,
            answer=answer,
            evidence=evidence,
            source="manual",
        )


class AnthropicJudge:
    """Ask a Claude model to pick a bounded answer and cite evidence.

    Requires the ``anthropic`` extra and an API key in the environment. Uses a
    forced tool call so the answer is constrained to the indicator's answer set,
    and low temperature for reproducibility. The model id is stamped as the source.
    """

    def __init__(self, model: str = "claude-opus-4-8", max_evidence_chars: int = 40_000):
        self.model = model
        self.max_evidence_chars = max_evidence_chars

    def resolve(self, indicator: Indicator, target: Target) -> IndicatorResult:
        import anthropic  # requires the "anthropic" optional dependency

        client = anthropic.Anthropic()
        options = sorted(indicator.answers)
        corpus = target.text_corpus()[: self.max_evidence_chars]

        tool = {
            "name": "record_answer",
            "description": "Record the chosen answer and the exact evidence quote.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "enum": options},
                    "evidence": {
                        "type": "string",
                        "description": "A short verbatim quote from the target supporting the answer.",
                    },
                },
                "required": ["answer", "evidence"],
            },
        }
        prompt = (
            f"Question about an agentic workflow: {indicator.question}\n\n"
            f"Choose exactly one answer from: {options}.\n"
            f"Base the answer only on the target material below and quote the evidence.\n\n"
            f"--- TARGET MATERIAL ---\n{corpus}"
        )
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            tools=[tool],
            tool_choice={"type": "tool", "name": "record_answer"},
            messages=[{"role": "user", "content": prompt}],
        )
        block = next(b for b in msg.content if getattr(b, "type", None) == "tool_use")
        answer = block.input["answer"]
        evidence = block.input.get("evidence")
        return IndicatorResult(
            indicator_id=indicator.id,
            kind=IndicatorKind.CLASSIFIED,
            weight=indicator.weight,
            value=indicator.answers[answer],
            resolved=True,
            answer=answer,
            evidence=evidence,
            source=self.model,
        )
