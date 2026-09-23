"""Tests for corpus refresh pin selection (default-branch HEAD, never older releases)."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "corpus_script",
    Path(__file__).resolve().parent.parent / "scripts" / "corpus.py",
)
corpus = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(corpus)


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
