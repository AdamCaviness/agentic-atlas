"""Tests for the committed profile corpus and its maintenance script: refresh pin selection
(default-branch HEAD, never older releases), answer replay, and the evidence-path rules every
current-rubric profile must meet."""

import importlib.util
import json
from pathlib import Path

import pytest

from agentic_atlas.judged import excluded_by
from agentic_atlas.spec import load_rubric

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("corpus_script", _ROOT / "scripts" / "corpus.py")
corpus = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(corpus)

_RUBRIC = load_rubric(_ROOT / "rubric" / "v1")
_PROFILES = sorted((_ROOT / "profiles").glob("*.json"))


def test_refresh_ref_always_uses_default_branch(tmp_path, monkeypatch):
    # Even when a GitHub Release exists, checkout HEAD so pins never move backwards onto
    # an older tag (which drops judged quotes). Reason still names the latest release.
    dest = tmp_path / "repo"
    dest.mkdir()
    monkeypatch.setattr(corpus, "_parse_github_slug", lambda url: ("owner", "repo"))
    monkeypatch.setattr(corpus, "_fetch_github_latest_release_tag", lambda o, r: "v1.1.0")
    monkeypatch.setattr(corpus, "_tag_exists", lambda d, tag: tag == "v1.1.0")
    monkeypatch.setattr(corpus, "_default_ref", lambda d: "origin/main")

    ref, reason = corpus._refresh_ref(dest, "https://github.com/owner/repo.git")
    assert ref == "origin/main"
    assert reason == "default-branch (latest release v1.1.0)"


def test_refresh_ref_without_github_remote(tmp_path, monkeypatch):
    dest = tmp_path / "repo"
    dest.mkdir()
    monkeypatch.setattr(corpus, "_parse_github_slug", lambda url: None)
    monkeypatch.setattr(corpus, "_default_ref", lambda d: "origin/master")

    ref, reason = corpus._refresh_ref(dest, "https://gitlab.com/owner/repo.git")
    assert ref == "origin/master"
    assert reason == "default-branch"


def test_refresh_ref_without_releases(tmp_path, monkeypatch):
    dest = tmp_path / "repo"
    dest.mkdir()
    monkeypatch.setattr(corpus, "_parse_github_slug", lambda url: ("owner", "repo"))
    monkeypatch.setattr(corpus, "_fetch_github_latest_release_tag", lambda o, r: None)
    monkeypatch.setattr(corpus, "_default_ref", lambda d: "origin/main")

    ref, reason = corpus._refresh_ref(dest, "https://github.com/owner/repo.git")
    assert ref == "origin/main"
    assert reason == "default-branch"


def test_reconstruct_answers_carries_the_evidence_path():
    profile = {
        "rubric_version": "5.0.0",
        "axes": [
            {
                "indicators": [
                    {"indicator_id": "repo-age", "kind": "detected", "resolved": True},
                    {
                        "indicator_id": "spec-required",
                        "kind": "judged",
                        "resolved": True,
                        "answer": "required",
                        "evidence": "Write the spec first.",
                        "path": "docs/method.md",
                        "source": "agentic-atlas:model",
                    },
                    {"indicator_id": "tests-first", "kind": "judged", "resolved": False},
                ]
            }
        ],
    }
    answers, source = corpus._reconstruct_answers(profile)
    assert answers == {
        "spec-required": {
            "answer": "required",
            "evidence": "Write the spec first.",
            "path": "docs/method.md",
        }
    }
    assert source == "agentic-atlas:model"


def test_reconstruct_answers_refuses_a_profile_without_evidence_paths():
    # A rubric 4.x profile has no paths. Replaying it would leave every judged indicator
    # unresolved and a --write would erase its judged positions, so it is skipped instead.
    profile = {
        "rubric_version": "4.0.0",
        "axes": [
            {
                "indicators": [
                    {
                        "indicator_id": "spec-required",
                        "kind": "judged",
                        "resolved": True,
                        "answer": "required",
                        "evidence": "Write the spec first.",
                        "source": "agentic-atlas:model",
                    }
                ]
            }
        ],
    }
    with pytest.raises(SystemExit, match=r"1 judged answer\(s\) have no evidence path"):
        corpus._reconstruct_answers(profile)


def _major(version: str) -> int:
    return int(version.split(".", 1)[0])


@pytest.mark.parametrize("path", _PROFILES, ids=lambda p: p.stem)
def test_current_rubric_profiles_cite_admissible_evidence_files(path):
    # A profile scored under the current rubric MAJOR must name an admissible file for every
    # resolved judged answer. A profile from an older MAJOR predates that rule and is not
    # comparable to the current rubric anyway, so it is skipped (visible in `pytest -rs`)
    # until it is re-answered; once the corpus is re-answered, every profile is checked.
    profile = json.loads(path.read_text())
    if _major(profile["rubric_version"]) < _major(_RUBRIC.rubric_version):
        pytest.skip(
            f"rubric {profile['rubric_version']} profile predates evidence paths; "
            "re-answer it with /agentic-atlas:run <url> --save"
        )
    problems = _evidence_path_problems(profile)
    assert not problems, f"{path.stem}: " + "; ".join(problems)


def test_evidence_path_gate_flags_missing_and_excluded_paths():
    def judged(iid: str, cited: str | None) -> dict:
        return {"indicator_id": iid, "kind": "judged", "resolved": True, "path": cited}

    profile = {
        "axes": [
            {
                "indicators": [
                    judged("starting-point", "README.md"),
                    judged("spec-required", None),
                    judged("tests-first", "CHANGELOG.md"),
                    {"indicator_id": "repo-age", "kind": "detected", "resolved": True},
                ]
            }
        ]
    }
    assert _evidence_path_problems(profile) == [
        "spec-required: no path",
        "tests-first: 'CHANGELOG.md' matches '**/CHANGELOG.*'",
    ]


def _evidence_path_problems(profile: dict) -> list[str]:
    """Each resolved judged answer in ``profile`` that names no file or an excluded one."""
    problems = []
    for ax in profile["axes"]:
        for ind in ax["indicators"]:
            if ind["kind"] != "judged" or not ind["resolved"]:
                continue
            cited = ind.get("path")
            if not cited:
                problems.append(f"{ind['indicator_id']}: no path")
            elif glob := excluded_by(cited, _RUBRIC.evidence_exclude):
                problems.append(f"{ind['indicator_id']}: {cited!r} matches {glob!r}")
    return problems
