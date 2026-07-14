"""Tests for the classified-indicator judges.

The AnthropicJudge test runs fully offline: a fake ``anthropic`` module is placed
in ``sys.modules`` so ``import anthropic`` inside ``resolve()`` picks it up without
the real package installed and without any network call. An optional live smoke
test is gated so it never runs during ``make check``.
"""

import importlib.util
import os
import sys
import types

import pytest

from agentic_atlas.evidence import Target
from agentic_atlas.judge import AnthropicJudge
from agentic_atlas.models import Indicator, IndicatorKind


def _classified_indicator() -> Indicator:
    return Indicator(
        id="c1",
        question="Does the approach document a review step?",
        kind=IndicatorKind.CLASSIFIED,
        weight=1.0,
        answers={"yes": 1.0, "no": -1.0},
    )


class _FakeBlock:
    """Stands in for an SDK content block of type ``tool_use``."""

    def __init__(self, answer: str, evidence: str):
        self.type = "tool_use"
        self.name = "record_answer"
        self.input = {"answer": answer, "evidence": evidence}


class _FakeMessage:
    def __init__(self, content):
        self.content = content


def _install_fake_anthropic(monkeypatch, *, answer: str, evidence: str, captured: dict):
    """Insert a fake ``anthropic`` module into sys.modules.

    ``captured`` collects the kwargs passed to ``messages.create`` so tests can
    assert on the outgoing request (the regression guard for the temperature bug).
    """
    module = types.ModuleType("anthropic")

    class _FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _FakeMessage([_FakeBlock(answer, evidence)])

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = _FakeMessages()

    module.Anthropic = _FakeClient
    monkeypatch.setitem(sys.modules, "anthropic", module)


def test_anthropic_judge_resolves_from_tool_use(tmp_path, monkeypatch):
    (tmp_path / "readme.md").write_text("We always run a review step before merge.")
    target = Target.from_path(tmp_path)
    indicator = _classified_indicator()
    captured: dict = {}
    _install_fake_anthropic(
        monkeypatch, answer="yes", evidence="run a review step", captured=captured
    )

    judge = AnthropicJudge(model="claude-opus-4-8")
    result = judge.resolve(indicator, target)

    assert result.resolved is True
    assert result.value == indicator.answers["yes"] == 1.0
    assert result.answer == "yes"
    assert result.evidence == "run a review step"
    assert result.source == "claude-opus-4-8"
    assert result.kind is IndicatorKind.CLASSIFIED


def test_anthropic_judge_request_omits_temperature_and_forces_tool(tmp_path, monkeypatch):
    (tmp_path / "readme.md").write_text("some text")
    target = Target.from_path(tmp_path)
    captured: dict = {}
    _install_fake_anthropic(
        monkeypatch, answer="no", evidence="no review mentioned", captured=captured
    )

    AnthropicJudge(model="claude-opus-4-8").resolve(_classified_indicator(), target)

    # Regression guard: current models reject sampling params with an HTTP 400.
    assert "temperature" not in captured
    assert "top_p" not in captured
    assert "top_k" not in captured
    # Determinism comes from the forced single-tool choice instead.
    assert captured["tool_choice"] == {"type": "tool", "name": "record_answer"}
    assert captured["model"] == "claude-opus-4-8"
    assert [t["name"] for t in captured["tools"]] == ["record_answer"]


@pytest.mark.skipif(
    importlib.util.find_spec("anthropic") is None
    or os.environ.get("ATLAS_ANTHROPIC_SMOKE") != "1",
    reason="live smoke test: set ATLAS_ANTHROPIC_SMOKE=1 with the anthropic extra installed",
)
def test_anthropic_judge_live_smoke(tmp_path):
    (tmp_path / "readme.md").write_text(
        "This project documents an explicit code review step before every merge."
    )
    target = Target.from_path(tmp_path)
    indicator = _classified_indicator()
    result = AnthropicJudge().resolve(indicator, target)
    assert result.resolved is True
    assert result.answer in indicator.answers
