"""Codex plugin manifest is a peer of the Claude Code plugin manifest."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE = REPO_ROOT / ".claude-plugin" / "plugin.json"
CODEX = REPO_ROOT / ".codex-plugin" / "plugin.json"

PEER_KEYS = (
    "name",
    "description",
    "version",
    "homepage",
    "repository",
    "license",
    "keywords",
)


def test_codex_plugin_json_exists() -> None:
    assert CODEX.is_file(), f"missing {CODEX}"


def test_codex_peers_claude_identity_fields() -> None:
    claude = json.loads(CLAUDE.read_text())
    codex = json.loads(CODEX.read_text())
    for key in PEER_KEYS:
        assert key in codex, f"codex missing {key}"
        assert codex[key] == claude[key], f"mismatch on {key}"
    assert codex["author"]["name"] == claude["author"]["name"]


def test_codex_points_skills_at_plugin_skills_dir() -> None:
    codex = json.loads(CODEX.read_text())
    assert codex["skills"] == "./skills/"
    skill_dirs = [
        path
        for path in (REPO_ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    ]
    assert {path.name for path in skill_dirs} == {"run", "open-explorer", "explain"}


def test_release_please_bumps_codex_plugin_version() -> None:
    config = json.loads((REPO_ROOT / "release-please-config.json").read_text())
    extra = config["packages"]["."]["extra-files"]
    codex_entries = [
        e
        for e in extra
        if e.get("path") == ".codex-plugin/plugin.json" and e.get("jsonpath") == "$.version"
    ]
    assert len(codex_entries) == 1, "release-please must bump .codex-plugin/plugin.json $.version"
