"""Gather evidence from a target and resolve detected indicators.

Detected indicators are deterministic given their input: the engine computes them
directly from the repository with no model. Signal types supported today:

- ``vocabulary``    term density across the text corpus, banded by count.
- ``path_presence`` glob matches to a present/absent value.
- ``path_count``    the number of files matching any glob, banded to a value, so
  many matching files reads differently from a handful.
- ``git_stats``     a fact read from the target's git history (commit count,
  contributors, age, tags), banded to a value.
- ``github_api``    a point-in-time fact from the GitHub host API for the origin
  remote (stars, forks, watchers, open issues), banded to a value.

``git_stats`` and ``github_api`` can fail to resolve (no git history, no origin
remote, no network). ``vocabulary``, ``path_presence``, and ``path_count`` likewise
stay unresolved when the target has no readable text corpus or no files at all: an
unreadable target must not read as a confident position at the absent pole. When an indicator does not
resolve it is marked unresolved and counted against coverage rather than crashing the
profile. ``github_api`` is point-in-time and not pinned by the target SHA, so the
fetched value is recorded verbatim as evidence, which is the honesty signal for a
mutable host fact.

Adding a signal type means extending ``resolve_detected`` and the schema, and is a
rubric-affecting change only if an existing rubric starts using it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .models import Indicator, IndicatorKind, IndicatorResult


@lru_cache(maxsize=256)
def _glob_regex(pattern: str) -> re.Pattern:
    """Compile a glob to regex with recursive ``**`` support.

    fnmatch treats ``**`` as ``*`` and does not cross directories usefully, so a
    pattern like ``**/skills/**`` fails to match a top-level ``skills/`` directory.
    This translation makes ``**`` match any number of path segments, ``*`` match
    within a segment, and ``?`` match one non-separator character.
    """
    out, i, n = "", 0, len(pattern)
    while i < n:
        c = pattern[i]
        i += 1
        if c == "*":
            if i < n and pattern[i] == "*":
                i += 1
                if i < n and pattern[i] == "/":
                    i += 1
                    out += "(?:.*/)?"
                else:
                    out += ".*"
            else:
                out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
    return re.compile(f"^{out}$", re.DOTALL)


def glob_match(path: str, pattern: str) -> bool:
    """True when ``path`` (POSIX, relative to the target root) matches the rubric glob
    ``pattern``. The one glob dialect of the rubric: path signals and the judged-evidence
    exclusions both match through here, case-sensitively."""
    return _glob_regex(pattern).match(path) is not None


@lru_cache(maxsize=1024)
def _term_pattern(term: str) -> re.Pattern:
    """Match ``term`` as a whole token.

    A short term like ``ci`` or ``api`` must not match inside an unrelated word
    (``special``, ``capital``); lookarounds require a non-word character (or the
    string edge) on both sides, which also handles multi-word and hyphenated terms.
    """
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def _count_terms(corpus: str, terms: list[str]) -> int:
    return sum(len(_term_pattern(t.lower()).findall(corpus)) for t in terms)


# File extensions that make up a methodology's readable surface.
# A tuple so the judged-answer instructions list them in a stable, readable order.
TEXT_SUFFIXES = (".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".toml")
_MAX_FILE_BYTES = 512_000
# Directories that never hold the methodology's own authored content: VCS internals, build
# artifacts and virtualenvs, and vendored third-party dependencies. A project's methodology
# signal must not be diluted by code it merely bundles, so vendored trees are excluded the
# same way ``node_modules`` already is.
_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "vendor",
    "vendored",
    "third_party",
    "third-party",
}
# OS and editor cruft that should never count as target content or a matched path.
_IGNORE_FILES = {".DS_Store", "Thumbs.db"}

# Git-history metrics that a shallow clone truncates. On a shallow checkout only the tip
# of history is present, so these collapse to a false "fresh" floor (commit_count=1,
# age_days=0, contributor_count=1, tag_count=0). They resolve as unresolved there rather
# than fabricate a position. The github_api stars indicator is not a git-history metric,
# so it is unaffected.
_SHALLOW_SENSITIVE_METRICS = frozenset(
    {"commit_count", "contributor_count", "tag_count", "age_days"}
)


_NOREPLY = re.compile(r"^(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$")


def _contributor_count(authors: list[tuple[str, str]], exclude_authors: tuple[str, ...]) -> int:
    """Count distinct people among commit ``(name, email)`` pairs.

    One person often commits under several identities (a work and a personal email, a
    GitHub noreply address, a renamed display name). Identities that share a normalized
    name, an email, or a GitHub noreply login are merged into one person. Identities
    matching any ``exclude_authors`` regex (tested against ``"name <email>"``, ignoring
    case) are automation or AI authors, not people, and are dropped before merging.
    """
    excluded = [re.compile(p, re.IGNORECASE) for p in exclude_authors]
    parent: dict[str, str] = {}

    def find(k: str) -> str:
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    people: set[str] = set()
    for name, email in set(authors):
        name, email = name.strip(), email.strip().lower()
        if any(rx.search(f"{name} <{email}>") for rx in excluded):
            continue
        keys = [f"email:{email}"] if email else []
        if name:
            keys.append("name:" + " ".join(name.casefold().split()))
        login = _NOREPLY.match(email)
        if login:
            keys.append("name:" + login.group(1).casefold())
        if not keys:
            continue
        for k in keys[1:]:
            parent[find(k)] = find(keys[0])
        people.add(keys[0])
    return len({find(k) for k in people})


@dataclass
class Target:
    """A profiling target: a local directory, optionally a git checkout."""

    root: Path
    # Text files are read from disk once and reused: the detected vocabulary signals ask for
    # the joined corpus and the judged verbatim-quote check asks for one file, per indicator.
    _text: dict[str, str] | None = field(default=None, repr=False, compare=False)
    _corpus: dict[str, str] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_path(cls, path: str | Path) -> Target:
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"target is not a directory: {root}")
        return cls(root=root)

    def _run_git(self, *args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", str(self.root), *args],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    def git_sha(self) -> str | None:
        return self._run_git("rev-parse", "HEAD") or None

    def git_version(self) -> str | None:
        """Raw ``git describe --tags`` at HEAD, stored as ``Profile.target_version``.

        Returns an exact tag when HEAD is tagged, otherwise a describe stamp
        (e.g. ``v6.1.1-14-gd884ae0``) naming the nearest ancestor tag and how far past
        it the profiled commit sits. Returns None when the checkout has no tags (or is
        not a git repo). Reader-facing formatting lives in ``report._project_stamp``.
        """
        # A fixed abbreviation length keeps the stamp stable: git's default grows with the
        # object count, so a later fetch would otherwise change the stamp for the same commit.
        return self._run_git("describe", "--tags", "--abbrev=12", "HEAD") or None

    def is_shallow(self) -> bool:
        """True when the checkout has only partial history (a shallow clone).

        ``git clone --depth N`` fetches only the tip of history, so the git-history
        metrics would collapse to a false "fresh" floor and measure the fetch, not the
        project. Detected via a cheap ``.git/shallow`` stat first, then the authoritative
        ``git rev-parse`` (which also covers worktrees where ``.git`` is a file).
        """
        if (self.root / ".git" / "shallow").exists():
            return True
        return self._run_git("rev-parse", "--is-shallow-repository") == "true"

    def git_origin(self) -> str | None:
        """The target's origin remote URL, or None (no git checkout, or no origin remote)."""
        return self._run_git("remote", "get-url", "origin") or None

    def git_metric(self, metric: str, exclude_authors: tuple[str, ...] = ()) -> int | float | None:
        """Return a deterministic git-history metric, or None if unavailable.

        ``age_days`` spans the first commit to HEAD (git log lists newest first),
        so it is a function of the checked-out history, not of wall-clock now.
        ``contributor_count`` counts people, see ``_contributor_count``; the rubric
        supplies ``exclude_authors`` so the engine embeds no list of automation names.
        ``tag_count`` counts only tags reachable from HEAD, so a later fetch of newer
        tags or tags on other branches cannot change the value for the same commit.

        A shallow checkout truncates history, so the history-derived metrics return
        None (unresolved) rather than a false "fresh" floor. See ``is_shallow``.
        """
        if metric in _SHALLOW_SENSITIVE_METRICS and self.is_shallow():
            return None
        if metric == "commit_count":
            out = self._run_git("rev-list", "--count", "HEAD")
            return int(out) if out and out.isdigit() else None
        if metric == "contributor_count":
            out = self._run_git("log", "--use-mailmap", "--format=%aN%x00%aE")
            if not out:
                return None
            authors = [tuple(line.split("\0", 1)) for line in out.splitlines() if "\0" in line]
            return _contributor_count(authors, exclude_authors)
        if metric == "tag_count":
            # `git tag --list` succeeds with empty output on a repo with no commits,
            # which would read as a real "0 tags" (fresh) signal. Require a commit first
            # so a history-less target leaves this unresolved like the other git metrics.
            if self.git_sha() is None:
                return None
            out = self._run_git("tag", "--merged", "HEAD")
            if out is None:
                return None
            return len([line for line in out.splitlines() if line.strip()])
        if metric == "age_days":
            out = self._run_git("log", "--format=%ct")
            if not out:
                return None
            stamps = [int(x) for x in out.splitlines() if x.strip().isdigit()]
            if not stamps:
                return None
            return (stamps[0] - stamps[-1]) / 86400.0
        return None

    def github_slug(self) -> tuple[str, str] | None:
        url = self._run_git("remote", "get-url", "origin")
        return _parse_github_slug(url) if url else None

    def _files(self) -> list[Path]:
        files: list[Path] = []
        # Sorted so evidence strings and the corpus are deterministic across machines,
        # not dependent on filesystem walk order.
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            if p.name in _IGNORE_FILES:
                continue
            if any(part in _IGNORE_DIRS for part in p.relative_to(self.root).parts):
                continue
            files.append(p)
        return files

    def text_files(self) -> dict[str, str]:
        """The raw text of every file in the text corpus, keyed by POSIX path relative to
        the root, in sorted path order. A file is in the corpus when its extension is in
        ``TEXT_SUFFIXES``, it sits outside the ignored directories, and it is at most
        ``_MAX_FILE_BYTES``; everything else is not readable evidence."""
        if self._text is None:
            files: dict[str, str] = {}
            for p in self._files():
                if p.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                try:
                    if p.stat().st_size > _MAX_FILE_BYTES:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                files[p.relative_to(self.root).as_posix()] = text
            self._text = files
        return self._text

    def text_corpus(self, *, lower: bool = True) -> str:
        if "raw" not in self._corpus:
            self._corpus["raw"] = "\n".join(self.text_files().values())
        if not lower:
            return self._corpus["raw"]
        if "lower" not in self._corpus:
            self._corpus["lower"] = self._corpus["raw"].lower()
        return self._corpus["lower"]

    def relative_paths(self) -> list[str]:
        return [p.relative_to(self.root).as_posix() for p in self._files()]


def resolve_detected(indicator: Indicator, target: Target) -> IndicatorResult:
    signal = indicator.signal or {}
    stype = signal.get("type")
    if stype == "vocabulary":
        return _resolve_vocabulary(indicator, target, signal)
    if stype == "path_presence":
        return _resolve_path_presence(indicator, target, signal)
    if stype == "path_count":
        return _resolve_path_count(indicator, target, signal)
    if stype == "git_stats":
        return _resolve_git_stats(indicator, target, signal)
    if stype == "github_api":
        return _resolve_github_api(indicator, target, signal)
    raise ValueError(f"unknown detected signal type {stype!r} for indicator {indicator.id}")


def _unresolved_detected(indicator: Indicator, reason: str) -> IndicatorResult:
    """A detected indicator the engine could not compute (missing git/network).

    Marked unresolved so it is excluded from scoring and counted against coverage,
    exactly like an unanswered judged indicator.
    """
    return IndicatorResult.unresolved(indicator, IndicatorKind.DETECTED, reason, source="engine")


def _resolve_vocabulary(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    corpus = target.text_corpus()
    if not corpus.strip():
        # Nothing readable to count. A zero here would mean "read the repo and this
        # vocabulary is genuinely absent", but there is no repo text at all, so banding
        # it would slam the axis to the absent pole at a confident-looking value.
        # Leave it unresolved so an unreadable target stays off the score.
        return _unresolved_detected(indicator, "no readable text corpus in target")
    count = _count_terms(corpus, signal["terms"])
    value = _band_value(count, signal["bands"])
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.DETECTED,
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
    if not paths:
        # No files to look at. "absent" among real files is a signal; "absent" from an
        # empty target is not, so it stays unresolved rather than reading as the absent pole.
        return _unresolved_detected(indicator, "target has no files")
    matched = [p for p in paths if any(glob_match(p, g) for g in signal["globs"])]
    present = bool(matched)
    value = float(signal["present"]) if present else float(signal["absent"])
    evidence = f"matched {matched[:5]}" if present else f"no path matched {signal['globs']}"
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.DETECTED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer="present" if present else "absent",
        evidence=evidence,
        source="engine",
    )


def _resolve_path_count(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    paths = target.relative_paths()
    if not paths:
        # No files to count. A zero here would read as "counted the files and none
        # matched", but there are no files at all, so it stays unresolved rather than
        # banding an empty target to the low pole. Same guard as path_presence.
        return _unresolved_detected(indicator, "target has no files")
    count = sum(1 for p in paths if any(glob_match(p, g) for g in signal["globs"]))
    value = _band_value(count, signal["bands"])
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.DETECTED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=str(count),
        evidence=f"{count} files matched {signal['globs']}",
        source="engine",
    )


def _resolve_git_stats(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    metric = signal["metric"]
    exclude = tuple(signal.get("exclude_authors", ()))
    if exclude and metric != "contributor_count":
        raise ValueError(
            f"indicator {indicator.id}: exclude_authors applies only to contributor_count"
        )
    raw = target.git_metric(metric, exclude)
    if raw is None:
        # Name the shallow clone explicitly: on a truncated history the metric is not
        # "no git history", it is untrustworthy, and the evidence must say so honestly.
        detail = (
            "shallow clone, history truncated"
            if target.is_shallow()
            else "target has no git history"
        )
        return _unresolved_detected(indicator, f"git metric {metric!r} unavailable ({detail})")
    value = _band_value(raw, signal["bands"])
    answer = f"{raw:.1f}" if isinstance(raw, float) else str(raw)
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.DETECTED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=answer,
        evidence=f"git {metric} = {answer}",
        source="engine",
    )


_GITHUB_METRIC_KEYS = {
    "stars": "stargazers_count",
    "forks": "forks_count",
    "watchers": "subscribers_count",
    "open_issues": "open_issues_count",
}


def _parse_github_slug(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from an https or ssh GitHub remote URL, or None."""
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    return (m.group(1), m.group(2)) if m else None


@lru_cache(maxsize=64)
def _fetch_github_repo(owner: str, repo: str) -> dict | None:
    """Fetch the repo object from the GitHub API, or None on any failure.

    Uses ``GITHUB_TOKEN``/``GH_TOKEN`` if present (higher rate limit). Returns None
    on missing network, non-200, timeout, or malformed JSON so callers degrade to
    an unresolved indicator rather than raising.
    """
    return _github_api_json(f"https://api.github.com/repos/{owner}/{repo}")


@lru_cache(maxsize=64)
def _fetch_github_latest_release_tag(owner: str, repo: str) -> str | None:
    """The latest published (non-draft, non-prerelease) GitHub Release tag, or None.

    Matches what visitors see as the current version on the repo's Releases page.
    """
    data = _github_api_json(f"https://api.github.com/repos/{owner}/{repo}/releases/latest")
    if not data:
        return None
    tag = data.get("tag_name")
    return tag if isinstance(tag, str) and tag else None


def _github_api_json(url: str) -> dict | None:
    """GET a GitHub API URL and return parsed JSON, or None on any failure."""
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentic-atlas",
        },
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def _resolve_github_api(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    slug = target.github_slug()
    if slug is None:
        return _unresolved_detected(indicator, "no GitHub origin remote on target")
    data = _fetch_github_repo(*slug)
    if data is None:
        return _unresolved_detected(
            indicator, "GitHub API unavailable (no network or rate limited)"
        )
    key = _GITHUB_METRIC_KEYS[signal["metric"]]
    raw = data.get(key)
    if not isinstance(raw, (int, float)):
        return _unresolved_detected(indicator, f"GitHub API response missing {key!r}")
    value = _band_value(raw, signal["bands"])
    owner, repo = slug
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.DETECTED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=str(raw),
        evidence=f"{signal['metric']} = {raw} for {owner}/{repo} via GitHub API",
        source="engine",
    )
