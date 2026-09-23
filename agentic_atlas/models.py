"""Dataclasses for rubrics and profiles.

These are plain data holders. All scoring policy lives in the rubric file and is
applied by ``agentic_atlas.scoring``. No behaviour that could move a score belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IndicatorKind(str, Enum):
    """How an indicator gets its value. ``detected``: the engine computes it from the
    repository with no model. ``judged``: an agent reads the repository and picks one
    allowed answer, backed by a verbatim quote the engine verifies."""

    DETECTED = "detected"
    JUDGED = "judged"


@dataclass(frozen=True)
class Poles:
    negative: str
    positive: str


@dataclass(frozen=True)
class Explain:
    """Plain-language meaning of each pole, shown in the report so a reader who does not
    already know the pole words still understands the axis. The neutral middle is not stored
    per axis: it means the same thing on every axis (a tool near 0 does both ends well, or
    neither), so the renderer states it once rather than repeating it on every axis."""

    negative: str = ""
    positive: str = ""


@dataclass(frozen=True)
class Indicator:
    id: str
    question: str
    kind: IndicatorKind
    weight: float
    # For judged indicators: answer key -> value in [-1, 1].
    answers: dict[str, float] = field(default_factory=dict)
    # For detected indicators: raw signal spec, interpreted by agentic_atlas.evidence.
    signal: dict | None = None


@dataclass(frozen=True)
class Axis:
    id: str
    title: str
    poles: Poles
    indicators: tuple[Indicator, ...]
    scale: float = 10.0
    description: str = ""
    explain: Explain = Explain()


@dataclass(frozen=True)
class Rubric:
    rubric_version: str
    title: str
    axes: tuple[Axis, ...]
    description: str = ""
    # Globs for files a judged answer may not cite as evidence (rubric data, interpreted by
    # ``agentic_atlas.judged``). Empty means every corpus text file is admissible.
    evidence_exclude: tuple[str, ...] = ()

    def axis(self, axis_id: str) -> Axis:
        for a in self.axes:
            if a.id == axis_id:
                return a
        raise KeyError(f"no axis {axis_id!r} in rubric {self.rubric_version}")


@dataclass(frozen=True)
class IndicatorResult:
    """The resolved value of one indicator, with its provenance.

    ``value`` is in [-1, 1]. ``resolved`` is False when the indicator could not be
    evaluated (for example a judged indicator with no answer supplied), in which case it
    is excluded from scoring and counted against coverage.
    """

    indicator_id: str
    kind: IndicatorKind
    weight: float
    value: float | None
    resolved: bool
    answer: str | None = None
    evidence: str | None = None
    source: str | None = None  # "engine" for detected, answer-file provenance for judged
    # For a resolved judged indicator: the file, relative to the target root, that holds the
    # evidence quote. None for detected indicators, unresolved ones, and profiles written
    # before rubric 5.0.0 made the path part of every judged answer.
    path: str | None = None

    @classmethod
    def unresolved(
        cls,
        indicator: Indicator,
        kind: IndicatorKind,
        reason: str | None = None,
        source: str | None = None,
    ) -> IndicatorResult:
        """An indicator that could not be resolved: excluded from scoring, counted
        against coverage. Shared by the detected and judged resolvers so the
        unresolved shape is defined once."""
        return cls(
            indicator_id=indicator.id,
            kind=kind,
            weight=indicator.weight,
            value=None,
            resolved=False,
            answer=None,
            evidence=reason,
            source=source,
        )


@dataclass(frozen=True)
class AxisResult:
    axis_id: str
    title: str
    poles: Poles
    scale: float
    score: float | None  # None when no indicator resolved
    coverage: float  # fraction of weight that was resolvable, 0.0..1.0
    indicators: tuple[IndicatorResult, ...]
    explain: Explain = Explain()


@dataclass(frozen=True)
class Profile:
    """A full profile of one target. This is the emitted artifact.

    Note: there is deliberately no aggregate score. A profile is a vector of
    signed axis positions, never a single number.
    """

    target: str
    rubric_version: str
    engine_version: str
    target_sha: str | None
    axes: tuple[AxisResult, ...]
    # Origin remote URL of the target (provenance + a link on the report); None when the
    # target has no git origin. Optional so it never shifts an axis score.
    target_url: str | None = None
    # Raw ``git describe --tags`` at the profiled commit (exact tag, or tag-N-gSHA when
    # past a tag), or None when the checkout has no tags. Stored for reproducibility;
    # reader-facing stamps are formatted in ``report._project_stamp``.
    target_version: str | None = None

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "rubric_version": self.rubric_version,
            "engine_version": self.engine_version,
            "target_sha": self.target_sha,
            "target_url": self.target_url,
            "target_version": self.target_version,
            "axes": [
                {
                    "axis_id": ax.axis_id,
                    "title": ax.title,
                    "poles": {"negative": ax.poles.negative, "positive": ax.poles.positive},
                    "explain": {
                        "negative": ax.explain.negative,
                        "positive": ax.explain.positive,
                    },
                    "scale": ax.scale,
                    "score": ax.score,
                    "coverage": ax.coverage,
                    "indicators": [
                        {
                            "indicator_id": ir.indicator_id,
                            "kind": ir.kind.value,
                            "weight": ir.weight,
                            "value": ir.value,
                            "resolved": ir.resolved,
                            "answer": ir.answer,
                            "evidence": ir.evidence,
                            "path": ir.path,
                            "source": ir.source,
                        }
                        for ir in ax.indicators
                    ],
                }
                for ax in self.axes
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Profile:
        """Rebuild a Profile from ``to_dict`` output. The exact inverse of ``to_dict``,
        so a saved profile JSON round-trips and can be re-rendered without re-running the
        engine or having the target repository on hand."""
        return cls(
            target=data["target"],
            rubric_version=data["rubric_version"],
            engine_version=data["engine_version"],
            target_sha=data.get("target_sha"),
            target_url=data.get("target_url"),
            target_version=data.get("target_version"),
            axes=tuple(
                AxisResult(
                    axis_id=ax["axis_id"],
                    title=ax["title"],
                    poles=Poles(ax["poles"]["negative"], ax["poles"]["positive"]),
                    scale=ax["scale"],
                    score=ax["score"],
                    coverage=ax["coverage"],
                    explain=Explain(
                        ax.get("explain", {}).get("negative", ""),
                        ax.get("explain", {}).get("positive", ""),
                    ),
                    indicators=tuple(
                        IndicatorResult(
                            indicator_id=ir["indicator_id"],
                            kind=IndicatorKind(ir["kind"]),
                            weight=ir["weight"],
                            value=ir["value"],
                            resolved=ir["resolved"],
                            answer=ir.get("answer"),
                            evidence=ir.get("evidence"),
                            source=ir.get("source"),
                            path=ir.get("path"),
                        )
                        for ir in ax["indicators"]
                    ),
                )
                for ax in data["axes"]
            ),
        )
