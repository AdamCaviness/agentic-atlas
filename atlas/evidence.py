"""Gather evidence from a target and resolve measured indicators.

Measured indicators are deterministic: the engine computes them directly from the
repository with no model. Two signal types are supported today, ``vocabulary`` and
``path_presence``. Adding a signal type means extending ``resolve_measured`` and the
schema, and is a rubric-affecting change only if an existing rubric starts using it.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from .models import Indicator, IndicatorKind, IndicatorResult

# File extensions that make up a workflow's readable surface.
_TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".toml"}
_MAX_FILE_BYTES = 512_000
_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


@dataclass
class Target:
    """A profiling target: a local directory, optionally a git checkout."""

    root: Path

    @classmethod
    def from_path(cls, path: str | Path) -> "Target":
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"target is not a directory: {root}")
        return cls(root=root)

    def git_sha(self) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return out.stdout.strip() or None if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    def _files(self) -> list[Path]:
        files: list[Path] = []
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in _IGNORE_DIRS for part in p.relative_to(self.root).parts):
                continue
            files.append(p)
        return files

    def text_corpus(self) -> str:
        chunks: list[str] = []
        for p in self._files():
            if p.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            try:
                if p.stat().st_size > _MAX_FILE_BYTES:
                    continue
                chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
        return "\n".join(chunks).lower()

    def relative_paths(self) -> list[str]:
        return [str(p.relative_to(self.root)) for p in self._files()]


def resolve_measured(indicator: Indicator, target: Target) -> IndicatorResult:
    signal = indicator.signal or {}
    stype = signal.get("type")
    if stype == "vocabulary":
        return _resolve_vocabulary(indicator, target, signal)
    if stype == "path_presence":
        return _resolve_path_presence(indicator, target, signal)
    raise ValueError(f"unknown measured signal type {stype!r} for indicator {indicator.id}")


def _resolve_vocabulary(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    corpus = target.text_corpus()
    count = sum(corpus.count(term.lower()) for term in signal["terms"])
    value = _band_value(count, signal["bands"])
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=str(count),
        evidence=f"{count} occurrences of {signal['terms']} across the text corpus",
        source="engine",
    )


def _band_value(count: int, bands: list[dict]) -> float:
    for band in bands:
        max_count = band.get("max_count")
        if max_count is None or count <= max_count:
            return float(band["value"])
    # No catch-all band matched. Fall back to the last band's value.
    return float(bands[-1]["value"])


def _resolve_path_presence(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    paths = target.relative_paths()
    matched = [p for p in paths if any(fnmatch(p, g) for g in signal["globs"])]
    present = bool(matched)
    value = float(signal["present"]) if present else float(signal["absent"])
    evidence = (
        f"matched {matched[:5]}" if present else f"no path matched {signal['globs']}"
    )
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer="present" if present else "absent",
        evidence=evidence,
        source="engine",
    )
