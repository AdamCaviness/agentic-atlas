"""Tests that the shipped rubric loads and validates."""

from pathlib import Path

from atlas.models import IndicatorKind
from atlas.spec import load_rubric

_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1.0.0.yaml"


def test_shipped_rubric_validates_and_parses():
    r = load_rubric(_RUBRIC, validate=True)
    assert r.rubric_version == "1.0.0"
    assert {a.id for a in r.axes} == {
        "greenfield_vs_brownfield",
        "interrogative_vs_opinionated",
        "autonomous_vs_human_in_loop",
    }


def test_classified_indicators_have_answers():
    r = load_rubric(_RUBRIC)
    for axis in r.axes:
        for ind in axis.indicators:
            if ind.kind is IndicatorKind.CLASSIFIED:
                assert ind.answers, f"{ind.id} classified but has no answers"
            else:
                assert ind.signal, f"{ind.id} measured but has no signal"


def test_answer_values_in_range():
    r = load_rubric(_RUBRIC)
    for axis in r.axes:
        for ind in axis.indicators:
            for v in ind.answers.values():
                assert -1.0 <= v <= 1.0
