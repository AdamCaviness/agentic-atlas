"""Load and validate a rubric file into typed dataclasses."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

from .models import Axis, Indicator, IndicatorKind, Poles, Rubric

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "rubric" / "schema.json"


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


def validate_raw(raw: dict) -> None:
    """Validate a parsed rubric dict against rubric/schema.json.

    Raises jsonschema.ValidationError on the first problem.
    """
    import jsonschema  # imported lazily so models/scoring stay dependency-light

    jsonschema.validate(instance=raw, schema=_schema())


def parse(raw: dict) -> Rubric:
    axes: list[Axis] = []
    for a in raw["axes"]:
        indicators = tuple(
            Indicator(
                id=i["id"],
                question=i["question"],
                kind=IndicatorKind(i["kind"]),
                weight=float(i["weight"]),
                answers=_parse_answers(i),
                signal=i.get("signal"),
            )
            for i in a["indicators"]
        )
        axes.append(
            Axis(
                id=a["id"],
                title=a["title"],
                poles=Poles(negative=a["poles"]["negative"], positive=a["poles"]["positive"]),
                indicators=indicators,
                scale=float(a.get("scale", 10.0)),
                description=a.get("description", ""),
            )
        )
    return Rubric(
        rubric_version=raw["rubric_version"],
        title=raw["title"],
        axes=tuple(axes),
        description=raw.get("description", ""),
    )


def _parse_answers(indicator: dict) -> dict[str, float]:
    answers: dict[str, float] = {}
    for k, v in indicator.get("answers", {}).items():
        if isinstance(k, bool):
            # YAML 1.1 turns unquoted yes/no/true/false into booleans. Answer keys
            # must be strings, so the author has to quote them.
            raise ValueError(
                f"indicator {indicator['id']!r} has a boolean answer key ({k!r}). "
                f"Quote yes/no/true/false answer keys in the rubric, e.g. \"yes\"."
            )
        answers[str(k)] = float(v)
    return answers


def load_rubric(path: str | Path, *, validate: bool = True) -> Rubric:
    raw = yaml.safe_load(Path(path).read_text())
    if validate:
        validate_raw(raw)
    return parse(raw)
